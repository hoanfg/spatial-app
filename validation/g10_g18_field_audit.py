#!/usr/bin/env python3
"""G10/G18: bounded sensitivity on a genuine exported A02 low-support CSV.

No input is silently invented, and all-observed Bao'an evidence is NOT
accepted as an incomplete-support field validation. This does not alter
production VIIRS/Local Moran/Gini or historical validation artifacts.

Run:
 python validation/g10_g18_field_audit.py --input YOUR_A02_CELLS.csv --out-dir audit_out

A candidate run requires real source support evidence and independent
source checks before being called field-validated. The optional independent
reference matches source support metadata but does not alone validate
source provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ntl.lisa_core import run_lisa

REQUIRED = {
    "grid_id", "cell_size_m", "area_km2", "ntl_mean",
    "dq_status", "dq_observed_fraction", "dq_mean_valid_months",
}
POLICIES = ("legacy_positive", "supported_positive", "supported_with_zeros", "naive_all_zeros")


def load_candidate(path: Path, *, max_cells: int = 20_000):
    raw = path.read_bytes()
    df = pd.read_csv(path)
    missing = sorted(REQUIRED - set(df.columns))
    if missing:
        raise ValueError(f"Missing required A02/source fields: {missing}")
    if len(df) < 30 or len(df) > max_cells:
        raise ValueError(f"Audit requires 30..{max_cells} cells, got {len(df)}")
    if df.grid_id.isna().any() or df.grid_id.duplicated().any():
        raise ValueError("grid_id must be nonmissing and unique")
    pairs = {}
    for col in df:
        match = re.fullmatch(r"centroid_([xy])_epsg(\d+)", col)
        if match:
            pairs.setdefault(match.group(2), {})[match.group(1)] = col
    epsgs = [key for key, pair in pairs.items() if set(pair) == {"x", "y"}]
    if len(epsgs) != 1:
        raise ValueError("Exactly one matching projected centroid x/y EPSG pair is required")
    pair = pairs[epsgs[0]]
    df = df.sort_values("grid_id", kind="stable").reset_index(drop=True)
    numbers = {key: pd.to_numeric(df[key], errors="raise").to_numpy(float)
               for key in ["ntl_mean", "area_km2", "cell_size_m",
                           "dq_observed_fraction", "dq_mean_valid_months",
                           pair["x"], pair["y"]]}
    if any(not np.isfinite(v).all() for v in numbers.values()):
        raise ValueError("No NaN/infinite cell values accepted: inspect the source and A02 schema")
    size = numbers["cell_size_m"]
    if np.unique(size).size != 1 or size[0] <= 0:
        raise ValueError("A single positive cell size is required")
    ntl = numbers["ntl_mean"]
    frac = numbers["dq_observed_fraction"]
    months = numbers["dq_mean_valid_months"]
    if np.any(ntl < 0) or np.any((frac < 0) | (frac > 1)) or np.any(months < 0):
        raise ValueError("Inconsistent NTL or observation-support values")
    status = df["dq_status"].astype("string").fillna("unknown").to_numpy(dtype=str)
    allowed = ("observed", "partial_observation", "no_observation")
    if not np.isin(status, allowed).all():
        raise ValueError("Unknown/invalid A02 support: cannot infer true missingness")
    noobs = status == "no_observation"
    known = ~noobs
    if not noobs.any():
        raise ValueError("This is an all-observed case, not a real incomplete-coverage G10/G18 audit")
    if ((frac[noobs] > 1e-6).any() or (months[noobs] > 1e-6).any()
            or (np.abs(ntl[noobs]) > 1e-6).any()):
        raise ValueError("No-observation cells contradict A02 support or legacy zero-fill")
    if (frac[known] <= 0).any() or (months[known] <= 0).any():
        raise ValueError("Observed/partial cells have no positive observation support")
    if ((status == "observed") & (frac < 1 - 1e-6)).any():
        raise ValueError("Fully observed status has partial pixel coverage")
    supported_zero = known & (ntl == 0)
    if not supported_zero.any():
        raise ValueError("No supported zero found: cannot distinguish G18 zero policies")
    area = numbers["area_km2"]
    if (area <= 0).any() or (area > (size[0] / 1000.0) ** 2 * 1.001).any():
        raise ValueError("Area inconsistent with positive full-cell geometry")
    support = {
        "n_cells": int(len(df)),
        "n_no_observation": int(noobs.sum()),
        "n_supported_zero_after_clipping": int(supported_zero.sum()),
        "n_partial_observation": int((status == "partial_observation").sum()),
        "n_low_valid_months_lt3": int(np.sum(known & (months < 3))),
    }
    if "dq_negative_fraction" in df:
        neg = pd.to_numeric(df["dq_negative_fraction"], errors="coerce").to_numpy(float)
        support["n_supported_zero_with_negative_radiance"] = int(
            (supported_zero & np.isfinite(neg) & (neg > 0)).sum()
        )
        support["n_supported_zero_without_negative_radiance"] = int(
            (supported_zero & np.isfinite(neg) & (neg <= 0)).sum()
        )
    return {
        "df": df, "cx": numbers[pair["x"]], "cy": numbers[pair["y"]],
        "area": area, "ntl": ntl, "size": float(size[0]),
        "known": known, "noobs": noobs, "support": support,
        "input_sha256": hashlib.sha256(raw).hexdigest(), "epsg": int(epsgs[0]),
    }


def _independent_support_check(df: pd.DataFrame, path: Path):
    """Check separately extracted source-support fields against app A02 data.

    The independent file must have grid_id, ref_observed_fraction and
    ref_mean_valid_months. Matching numbers are necessary but do not certify
    whether an analyst really extracted the independent source separately.
    """
    ref = pd.read_csv(path)
    needed = ["grid_id", "ref_observed_fraction", "ref_mean_valid_months"]
    if any(col not in ref for col in needed):
        raise ValueError(f"Reference must contain {needed}")
    if ref.grid_id.duplicated().any() or ref.grid_id.isna().any():
        raise ValueError("Reference grid_id must be nonmissing and unique")
    merged = df[["grid_id", "dq_observed_fraction", "dq_mean_valid_months"]].merge(
        ref[needed], on="grid_id", how="left", validate="one_to_one",
    )
    if len(ref) != len(df) or merged[needed[1:]].isna().any().any():
        raise ValueError("Independent reference must match every analysis grid_id exactly")
    residuals = {
        "observed_fraction_max_abs": float(np.max(np.abs(
            merged["dq_observed_fraction"].to_numpy(float)
            - merged["ref_observed_fraction"].to_numpy(float)))),
        "valid_months_max_abs": float(np.max(np.abs(
            merged["dq_mean_valid_months"].to_numpy(float)
            - merged["ref_mean_valid_months"].to_numpy(float)))),
    }
    residuals["within_tolerance_1e_3"] = bool(
        residuals["observed_fraction_max_abs"] <= 0.001
        and residuals["valid_months_max_abs"] <= 0.001
    )
    return residuals


def run_field_audit(source, *, perms=199, alpha=0.05, seed=42, fdr=True):
    if perms < 19 or not (0 < alpha < 1):
        raise ValueError("Predeclare positive permutations (>=19) and 0 < alpha < 1")
    n = len(source["ntl"])
    runs = {}
    names = {}
    for policy in POLICIES:
        used = np.ones(n, bool) if policy in ("legacy_positive", "naive_all_zeros") else source["known"]
        include_zeros = policy in ("supported_with_zeros", "naive_all_zeros")
        out = run_lisa(
            source["cx"][used], source["cy"][used], source["ntl"][used],
            source["area"][used], source["size"], perms=perms, alpha=alpha,
            seed=seed, fdr=fdr, include_zeros=include_zeros,
        )
        idx = np.flatnonzero(used)
        cls = np.full(n, "NOT_IN_ANALYSIS", dtype=object)
        pval = np.full(n, np.nan)
        neighbors = np.full(n, -1, dtype=int)
        cls[idx] = out.cell_df["lisa_class"].to_numpy(str)
        pval[idx] = out.cell_df["lisa_p_sim"].to_numpy(float)
        neighbors[idx] = out.cell_df["lisa_n_neighbors"].to_numpy(int)
        runs[policy] = (cls, pval, neighbors)
        names[policy] = {
            "locations": int(used.sum()),
            "tested": int(out.region_metrics["n_cells_tested"]),
            "hh_cells": int((cls == "High-High").sum()),
            "ll_cells": int((cls == "Low-Low").sum()),
            "n_significant": int(out.cell_df["lisa_significant"].sum()),
            "n_no_observation_tested": int(np.isfinite(pval[source["noobs"]]).sum()),
        }
    comparison = {}
    common = source["known"]
    for left, right in (
        ("legacy_positive", "supported_positive"),
        ("supported_positive", "supported_with_zeros"),
        ("supported_with_zeros", "naive_all_zeros"),
    ):
        ca, pa, na = runs[left]
        cb, pb, nb = runs[right]
        overlap = common & np.isfinite(pa) & np.isfinite(pb)
        comparison[f"{left}_versus_{right}"] = {
            "changed_classes_on_supported_cells": int(np.sum(common & (ca != cb))),
            "changed_neighbor_counts_on_supported_cells": int(np.sum(common & (na != nb))),
            "tested_overlap": int(overlap.sum()),
            "different_raw_p_on_overlap_gt_1e_5": int(np.sum(
                np.abs(pa[overlap] - pb[overlap]) > 1e-5)),
        }
    per_cell = source["df"][["grid_id", "ntl_mean", "dq_status", "dq_mean_valid_months"]].copy()
    for policy, (cls, pval, neighbors) in runs.items():
        per_cell[policy + "_class"] = cls
        per_cell[policy + "_p"] = pval
        per_cell[policy + "_neighbors"] = neighbors
    report = {
        "gap": ["G10", "G18"],
        "status": "candidate_real_support_sensitivity_not_independently_certified",
        "cannot_claim_g10_monthly_weighting_validated": True,
        "input_sha256": source["input_sha256"], "epsg": source["epsg"],
        "cell_size_m": source["size"], "perms": int(perms),
        "alpha": float(alpha), "seed": int(seed), "fdr": bool(fdr),
        "source_support": source["support"],
        "runs": names, "comparisons": comparison,
        "limitations": [
            "Data provenance and independent source support must be verified separately.",
            "dq_mean_valid_months is not the total cf_cvg observation count.",
            "Supported post-clipping zeros may include negative radiance clipped to zero.",
            "Changing the set of locations changes normalization, neighbors, and the tested family.",
            "Pseudo p-value differences can also reflect changing Monte Carlo draw sequences.",
            "This audit cannot establish a universally correct zero/weighting policy or nominal FDR.",
            "Previously deposited A02/V11/Shanghai field evidence is neither rerun nor superseded.",
        ],
    }
    return report, per_cell


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, type=Path, help="Original genuine A02 cell CSV")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--independent-reference", type=Path, default=None)
    ap.add_argument("--perms", type=int, default=199)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-fdr", action="store_true")
    ap.add_argument("--max-cells", type=int, default=20_000)
    args = ap.parse_args()
    source = load_candidate(args.input, max_cells=args.max_cells)
    report, cells = run_field_audit(
        source, perms=args.perms, alpha=args.alpha,
        seed=args.seed, fdr=not args.no_fdr,
    )
    if args.independent_reference:
        report["reference_check"] = _independent_support_check(
            source["df"], args.independent_reference
        )
        report["independent_reference_sha256"] = hashlib.sha256(
            args.independent_reference.read_bytes()
        ).hexdigest()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    output = args.out_dir / "cell_comparison.csv"
    cells.to_csv(output, index=False)
    report["cell_comparison_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    (args.out_dir / "summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": report["status"], "output": str(args.out_dir)}))


if __name__ == "__main__":
    main()
