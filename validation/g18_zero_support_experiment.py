#!/usr/bin/env python3
"""G18 synthetic sensitivity evidence for observed zeros versus unobserved cells.

The study is deliberately synthetic; it does NOT recheck A02, V11 or A03,
does NOT supply an external field validation, and does NOT change production
LISA or its default zero policy. The previously archived validations stand.

Run from repository root:
    python validation/g18_zero_support_experiment.py --emit-ci
    python validation/g18_zero_support_experiment.py --verify

The historical LISA export labels are retained by the application.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ntl.lisa_core import run_lisa

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "validation" / "evidence" / "g18_zero_support"
PERMS = 999
ALPHA = 0.05
SEED = 42
CELL_M = 500.0
STUDY_SEED = 18026
SCHEMAS = ("positive_only", "observed_zeros", "naive_missing_as_zero")
CORRECTIONS = ("unadjusted", "bh_fdr")
LABELS = ("High-High", "Low-Low", "High-Low", "Low-High")


def synthetic_cells():
    """Fixed 12x12 synthetic NTL surface; source status is known by construction."""
    side = 12
    xx, yy = np.meshgrid(np.arange(side), np.arange(side))
    ix = xx.ravel()
    iy = yy.ravel()
    rng = np.random.default_rng(STUDY_SEED)
    radial = (ix - 6.5) ** 2 + (iy - 6.0) ** 2
    ntl = np.maximum(
        0.08,
        1.0 + 38.0 * np.exp(-radial / (2.0 * 2.5 ** 2))
        + rng.normal(0.0, 0.35, len(ix)),
    )
    # Observed zero: verified by construction, not a missing-value replacement.
    observed_zero = ((ix <= 3) & (iy <= 3)) | ((ix >= 8) & (iy >= 9))
    # Unobserved: a separate non-overlapping, contiguous spatial pattern.
    missing = ((ix == 5) & (iy >= 2) & (iy <= 5)) | (
        (ix >= 9) & (ix <= 10) & (iy >= 3) & (iy <= 5)
    )
    if np.any(observed_zero & missing):
        raise AssertionError("Synthetic support categories must not overlap")
    ntl[observed_zero | missing] = 0.0
    status = np.full(len(ix), "observed_positive", dtype=object)
    status[observed_zero] = "observed_zero"
    status[missing] = "no_observation"

    # For an audited rerun the committed input CSV, not platform-specific
    # last-bit results of exp(), is the exact numeric source of truth. Retain
    # the seed/formula above as an independent within-tolerance source check.
    archived = EVIDENCE / "synthetic_input.csv"
    if archived.is_file():
        with archived.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != len(ix):
            raise ValueError("G18 source CSV has the wrong cell count")
        if any(int(row["grid_id"]) != i
               or int(row["grid_ix"]) != int(ix[i])
               or int(row["grid_iy"]) != int(iy[i])
               or row["synthetic_support"] != status[i]
               for i, row in enumerate(rows)):
            raise ValueError("G18 source CSV conflicts with the fixed spatial/support design")
        archived_ntl = np.array(
            [float(row["ntl_legacy_zero_fill"]) for row in rows], dtype=float
        )
        if not np.allclose(archived_ntl, ntl, rtol=0.0, atol=1.0e-10):
            raise ValueError("G18 source CSV differs materially from the seeded generator")
        ntl = archived_ntl
    return {
        "grid_id": np.arange(len(ix), dtype=int),
        "ix": ix, "iy": iy,
        "cx": 500_000.0 + (ix + 0.5) * CELL_M,
        "cy": 2_000_000.0 + (iy + 0.5) * CELL_M,
        "area": np.full(len(ix), 0.25),
        "ntl": ntl, "status": status,
    }


def _call_lisa(cells, name, *, fdr):
    # A run_lisa input with NaNs currently fails during its unconditional Gini
    # calculation. For this audit ONLY, unknown-support cells are excluded as
    # locations from both the focal population and the neighbor graph.
    known = cells["status"] != "no_observation"
    used = np.ones(len(known), dtype=bool) if name == "naive_missing_as_zero" else known
    include_zeros = name != "positive_only"
    return used, run_lisa(
        cells["cx"][used], cells["cy"][used],
        cells["ntl"][used], cells["area"][used], CELL_M,
        lit_threshold=0.0, edge_tol=0.99, perms=PERMS, alpha=ALPHA,
        fdr=fdr, log_transform=False, min_neighbors=1,
        min_cluster_cells=4, seed=SEED, include_zeros=include_zeros,
        weights="queen",
    )


def _as_numeric(value):
    return None if not np.isfinite(value) else float(value)


def _jaccard(a, b):
    union = int(np.sum(a | b))
    return round(float(np.sum(a & b) / union), 6) if union else None


def _csv_text(rows, fields):
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def run_experiment():
    cells = synthetic_cells()
    n = len(cells["ntl"])
    counts = {name: int(np.sum(cells["status"] == name)) for name in (
        "observed_positive", "observed_zero", "no_observation",
    )}
    in_rows = [{
        "grid_id": int(cells["grid_id"][i]),
        "grid_ix": int(cells["ix"][i]), "grid_iy": int(cells["iy"][i]),
        "centroid_x_m": round(float(cells["cx"][i]), 1),
        "centroid_y_m": round(float(cells["cy"][i]), 1),
        "area_km2": 0.25,
        "ntl_legacy_zero_fill": repr(float(cells["ntl"][i])),
        "synthetic_support": str(cells["status"][i]),
    } for i in range(n)]
    input_csv = _csv_text(in_rows, list(in_rows[0]))

    runs = {}
    results = {}
    comparison_rows = [{
        "grid_id": int(cells["grid_id"][i]),
        "synthetic_support": str(cells["status"][i]),
        "ntl_legacy_zero_fill": repr(float(cells["ntl"][i])),
    } for i in range(n)]
    for correction in CORRECTIONS:
        is_fdr = correction == "bh_fdr"
        for schema in SCHEMAS:
            used, result = _call_lisa(cells, schema, fdr=is_fdr)
            key = schema + "__" + correction
            df = result.cell_df.reset_index(drop=True)
            indices = np.flatnonzero(used)
            full_class = np.full(n, "EXCLUDED_UNOBSERVED", dtype=object)
            full_p = np.full(n, np.nan, dtype=float)
            full_neighbors = np.full(n, -1, dtype=int)
            full_class[indices] = df["lisa_class"].to_numpy()
            full_p[indices] = df["lisa_p_sim"].to_numpy(float)
            full_neighbors[indices] = df["lisa_n_neighbors"].to_numpy(int)
            for i in range(n):
                comparison_rows[i][key + "_class"] = str(full_class[i])
                comparison_rows[i][key + "_p"] = (
                    "" if not np.isfinite(full_p[i]) else f"{full_p[i]:.5f}"
                )
                comparison_rows[i][key + "_neighbors"] = (
                    "" if full_neighbors[i] < 0 else int(full_neighbors[i])
                )
            runs[key] = (full_class, full_p, full_neighbors)
            metrics = result.region_metrics
            results[key] = {
                "locations_in_analysis": int(used.sum()),
                "tested_cells": int(metrics["n_cells_tested"]),
                "statistically_significant_cells": int(df["lisa_significant"].sum()),
                "hh_cells": int(np.sum(full_class == "High-High")),
                "ll_cells": int(np.sum(full_class == "Low-Low")),
                "hl_cells": int(np.sum(full_class == "High-Low")),
                "lh_cells": int(np.sum(full_class == "Low-High")),
                "dark_class_cells": int(np.sum(full_class == "Dark (NTL=0)")),
                "observed_zero_cells_tested": int(np.sum(
                    (cells["status"] == "observed_zero") & np.isfinite(full_p)
                )),
                "unobserved_cells_tested": int(np.sum(
                    (cells["status"] == "no_observation") & np.isfinite(full_p)
                )),
                "hotspot_clusters_min_4": int(metrics["n_hh_clusters"]),
                "fdr": is_fdr, "permutations": PERMS, "alpha": ALPHA,
            }

    common = cells["status"] != "no_observation"
    comparisons = {}
    for correction in CORRECTIONS:
        for left, right in (("positive_only", "observed_zeros"),
                            ("observed_zeros", "naive_missing_as_zero")):
            key_a = left + "__" + correction
            key_b = right + "__" + correction
            a, pa, na = runs[key_a]
            b, pb, nb = runs[key_b]
            both = common & np.isfinite(pa) & np.isfinite(pb)
            comparisons[left + "_vs_" + right + "__" + correction] = {
                "common_supported_locations": int(common.sum()),
                "changed_class_on_common_support": int(np.sum(
                    (a != b) & common
                )),
                "changed_neighbor_count_on_common_support": int(np.sum(
                    (na != nb) & common
                )),
                "overlap_tested_cells": int(both.sum()),
                "changed_p_on_overlap_1e-5": int(np.sum(
                    np.abs(pa[both] - pb[both]) > 1.0e-5
                )),
                "hh_jaccard_on_common_support": _jaccard(
                    (a == "High-High") & common,
                    (b == "High-High") & common,
                ),
                "ll_jaccard_on_common_support": _jaccard(
                    (a == "Low-Low") & common,
                    (b == "Low-Low") & common,
                ),
            }

    result_csv = _csv_text(comparison_rows, list(comparison_rows[0]))
    summary = {
        "gap": "G18",
        "status": "synthetic_sensitivity_only_real_support_case_open",
        "field_validation": False,
        "input_origin": "fixed_generated_synthetic_cells",
        "study_seed": STUDY_SEED,
        "software_versions": {"numpy": np.__version__, "pandas": pd.__version__, "scipy": scipy.__version__},
        "synthetic_input_sha256": hashlib.sha256(input_csv.encode("utf-8")).hexdigest(),
        "cell_comparison_sha256": hashlib.sha256(result_csv.encode("utf-8")).hexdigest(),
        "lisa_seed": SEED,
        "lisa_permutations": PERMS,
        "lisa_alpha": ALPHA,
        "weights": "queen",
        "cell_size_m": CELL_M,
        "shape": [12, 12],
        "n_cells": n,
        "support_counts": counts,
        "policies": {
            "positive_only": "only supported cells; include_zeros=False",
            "observed_zeros": "only supported cells; include_zeros=True",
            "naive_missing_as_zero": (
                "all cells including false zero-filled unknown support; include_zeros=True"
            ),
        },
        "inference": "separate unadjusted and BH-FDR runs, not pooled",
        "runs": results,
        "comparisons": comparisons,
        "limitations": [
            "All support masks and radiance values are synthetic, not A02 field evidence.",
            "The missing-support locations are excluded from safe LISA runs by "
            "subsetting geometry, because run_lisa Gini currently rejects NaN.",
            "Changing the analysis population changes reference normalization "
            "and the tested family as well as the neighborhood graph.",
            "Differences quantify specification sensitivity, not the truth of "
            "any HH/LL classification or the external validity of either policy.",
            "No historical V11, GHSL, A02 observed-case, A03 or A04 evidence was rerun.",
            "The production default include_zeros=False is unchanged.",
        ],
    }
    summary_text = json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    return {
        "synthetic_input.csv": input_csv,
        "cell_comparison.csv": result_csv,
        "summary.json": summary_text,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-ci", action="store_true", help="Print artifacts as delimited base64 for archival")
    parser.add_argument("--verify", action="store_true", help="Require stored artifacts to match this deterministic run")
    args = parser.parse_args()
    outputs = run_experiment()
    meta = json.loads(outputs["summary.json"])
    assert meta["support_counts"]["no_observation"] > 0
    assert meta["support_counts"]["observed_zero"] > 0
    assert meta["runs"]["observed_zeros__bh_fdr"]["unobserved_cells_tested"] == 0
    assert meta["runs"]["naive_missing_as_zero__bh_fdr"]["unobserved_cells_tested"] > 0
    print("G18 structured summary:", json.dumps({
        "support_counts": meta["support_counts"],
        "runs": meta["runs"],
        "comparisons": meta["comparisons"],
    }, sort_keys=True))
    if args.verify:
        for name, data in outputs.items():
            path = EVIDENCE / name
            if not path.is_file():
                raise SystemExit(f"Missing committed evidence: {path}")
            if path.read_text(encoding="utf-8") != data:
                raise SystemExit(f"Evidence differs from generated run: {path}")
        print("G18 evidence verified against committed input, cells and summary")
    if args.emit_ci:
        for name, data in outputs.items():
            print("G18_BEGIN " + name)
            print(base64.b64encode(data.encode("utf-8")).decode("ascii"))
            print("G18_END " + name)


if __name__ == "__main__":
    main()
