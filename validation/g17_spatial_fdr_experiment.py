#!/usr/bin/env python3
"""G17: FDR under spatial dependence, with known-null and LISA stress studies.

Two separate experiments are required for scientifically valid interpretation:
 A) Gaussian p-values have *known* marginal nulls, so BH/BY empirical FDR
    and injection-detection power can be assessed under spatial dependence.
 B) The production local_moran conditional-permutation p-values are run on
    exchangeable iid data (all local spatial-randomization nulls true) and on
    spatially correlated fields (exchangeability fails). The latter is a
    rejection-sensitivity stress study, NOT an empirical FDR estimate.

This does not revalidate the BH step-up arithmetic already completed in A03.
No data in this script come from a real VIIRS scene.
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
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ntl.lisa_core import (  # noqa: E402
    ROOK_DROP_COLS,
    bh_reject,
    build_queen_neighbors,
    local_moran,
)

DEST = ROOT / "validation" / "evidence" / "g17_spatial_fdr"
SEED = 17026
SIDE = 8
N = SIDE * SIDE
CELL_M = 500.0
ALPHA = 0.05
PERMS_LISA = 999
N_GAUSSIAN = 400
N_LISA = 24
RHO_GAUSSIAN = (0.0, 0.5, 0.8, -0.5)
RHO_LISA = (0.0, 0.8, -0.5)
WEIGHTS = ("queen", "rook")
ALT_MEAN_Z = 2.75
METHODS = ("unadjusted", "bh", "by")
CSV_COLUMNS = (
    "study", "weights", "rho", "scenario", "replicate", "truth_scope", "m",
    "n_injected", "n_rej_unadjusted", "n_fp_unadjusted", "n_tp_unadjusted",
    "n_rej_bh", "n_fp_bh", "n_tp_bh",
    "n_rej_by", "n_fp_by", "n_tp_by",
)


def geometry():
    xx, yy = np.meshgrid(np.arange(SIDE), np.arange(SIDE))
    ix, iy = xx.ravel(), yy.ravel()
    cx = 500000.0 + (ix + 0.5) * CELL_M
    cy = 2000000.0 + (iy + 0.5) * CELL_M
    # A fixed, predeclared signal footprint: nine of 64 cells.
    signal = (ix >= 2) & (ix <= 4) & (iy >= 2) & (iy <= 4)
    assert int(signal.sum()) == 9
    return ix, iy, cx, cy, signal


def neighbors_and_weight_matrix(cx, cy, weights):
    nbr = build_queen_neighbors(
        cx, cy, CELL_M, np.ones(N, dtype=bool)
    )
    if weights == "rook":
        nbr = nbr.copy()
        nbr[:, ROOK_DROP_COLS] = -1
    k = (nbr >= 0).sum(axis=1)
    assert np.all(k > 0)
    w = np.zeros((N, N), float)
    for i in range(N):
        w[i, nbr[i, nbr[i] >= 0]] = 1.0 / k[i]
    assert np.allclose(w.sum(axis=1), 1.0, atol=1e-12)
    return nbr, w, k


def spatial_cholesky(w, rho):
    """Generate field z = D^-1/2 (I-rho W)^-1 epsilon with exact unit marginals.

    W is the row-standardized matrix from the same Queen/Rook neighbor graph.
    rho is a simulation parameter, NOT the app's spatial_ar1_persistence.
    """
    s = np.linalg.solve(np.eye(N) - rho * w, np.eye(N))
    covariance = s @ s.T
    sd = np.sqrt(np.diag(covariance))
    correlation = covariance / np.outer(sd, sd)
    assert np.allclose(np.diag(correlation), 1, atol=1e-10)
    return np.linalg.cholesky(correlation)


def rejections(p):
    m = len(p)
    harmonic = float(np.sum(1.0 / np.arange(1, m + 1)))
    out = {
        "unadjusted": np.asarray(p < ALPHA, dtype=bool),
        "bh": bh_reject(p, ALPHA),
        "by": bh_reject(p, ALPHA / harmonic),
    }
    if np.any(out["by"] & ~out["bh"]):
        raise AssertionError("BY must be a subset of BH on the same p family")
    return out


def one_row(study, weights, rho, scenario, rep, truth_scope, p, injected):
    out = {
        "study": study,
        "weights": weights,
        "rho": f"{rho:+.2f}",
        "scenario": scenario,
        "replicate": rep,
        "truth_scope": truth_scope,
        "m": len(p),
        "n_injected": "" if injected is None else int(injected.sum()),
    }
    for name, rej in rejections(p).items():
        out[f"n_rej_{name}"] = int(rej.sum())
        out[f"n_fp_{name}"] = "" if injected is None else int(np.sum(rej & ~injected))
        out[f"n_tp_{name}"] = "" if injected is None else int(np.sum(rej & injected))
    return out


def _csv_text(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def wilson_95(success, n):
    """Wilson interval for Bernoulli any-rejection probability."""
    if n == 0:
        return [None, None]
    z = 1.95996398454
    p = success / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    radius = z * np.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return [round(float(max(0, center - radius)), 6),
            round(float(min(1, center + radius)), 6)]


def mean_with_mc_se(v):
    a = np.asarray(v, float)
    if a.size == 0:
        return None, None, [None, None]
    mean = float(a.mean())
    se = float(a.std(ddof=1) / np.sqrt(a.size)) if a.size > 1 else 0.0
    return (
        round(mean, 6),
        round(se, 6),
        [round(max(0.0, mean - 1.96 * se), 6),
         round(min(1.0, mean + 1.96 * se), 6)],
    )


def summarize(rows):
    keys = sorted({
        (r["study"], r["weights"], r["rho"], r["scenario"], r["truth_scope"])
        for r in rows
    })
    results = []
    for key in keys:
        subset = [r for r in rows
                  if (r["study"], r["weights"], r["rho"], r["scenario"],
                      r["truth_scope"]) == key]
        entry = dict(zip(
            ("study", "weights", "rho", "scenario", "truth_scope"), key
        ))
        entry["replications"] = len(subset)
        entry["n_hypotheses"] = N
        entry["methods"] = {}
        for method in METHODS:
            rejs = np.array([int(r[f"n_rej_{method}"]) for r in subset])
            keyout = {
                "mean_rejections": round(float(rejs.mean()), 4),
                "any_rejection_rate": round(float((rejs > 0).mean()), 6),
                "any_rejection_wilson95": wilson_95(int((rejs > 0).sum()), len(rejs)),
            }
            truth = key[-1]
            if truth in ("valid_known_nulls", "exchangeable_all_null"):
                fp = np.array([int(r[f"n_fp_{method}"]) for r in subset])
                tp = np.array([int(r[f"n_tp_{method}"]) for r in subset])
                fdp = fp / np.maximum(1, rejs)
                keyout["empirical_fdr"], keyout["fdr_mc_se"], keyout["fdr_mc_ci95_normal"] = mean_with_mc_se(fdp)
                keyout["mean_false_rejections"] = round(float(fp.mean()), 4)
                if any(int(r["n_injected"]) > 0 for r in subset):
                    power = tp / float(int(subset[0]["n_injected"]))
                    keyout["injection_power"], keyout["power_mc_se"], keyout["power_mc_ci95_normal"] = mean_with_mc_se(power)
                else:
                    keyout["injection_power"] = None
            else:
                # A spatially dependent field has real local associations;
                # no "all local nulls true" ground truth exists here.
                keyout["empirical_fdr"] = None
                keyout["injection_power"] = None
            entry["methods"][method] = keyout
        results.append(entry)
    return results


def run_experiment():
    ix, iy, cx, cy, signal = geometry()
    all_member = np.ones(N, dtype=bool)
    rows = []
    spatial_details = {}
    for w_index, weights in enumerate(WEIGHTS):
        nbr, w, k = neighbors_and_weight_matrix(cx, cy, weights)
        spatial_details[weights] = {
            "minimum_neighbors": int(k.min()),
            "maximum_neighbors": int(k.max()),
            "average_neighbors": round(float(k.mean()), 4),
        }
        for rho_index, rho in enumerate(RHO_GAUSSIAN):
            chol = spatial_cholesky(w, rho)
            rng = np.random.default_rng(SEED + 1000 * w_index + 100 * rho_index)
            innovations = rng.standard_normal((N_GAUSSIAN, N))
            correlated = innovations @ chol.T
            assert np.isfinite(correlated).all()
            for rep in range(N_GAUSSIAN):
                base = correlated[rep]
                for scenario, injected in (
                    ("global_null", np.zeros(N, dtype=bool)),
                    ("fixed_3x3_mean_shift", signal),
                ):
                    scores = base + ALT_MEAN_Z * injected
                    # These are exact Gaussian marginal p-values. All null
                    # hypotheses have N(0,1) scores despite correlation.
                    p = 2.0 * norm.sf(np.abs(scores))
                    rows.append(one_row(
                        "gaussian_valid_p", weights, rho, scenario, rep,
                        "valid_known_nulls", p, injected
                    ))
        for rho_index, rho in enumerate(RHO_LISA):
            chol = spatial_cholesky(w, rho)
            rng = np.random.default_rng(
                SEED + 20000 + 1000 * w_index + 100 * rho_index
            )
            fields = rng.standard_normal((N_LISA, N)) @ chol.T
            for rep in range(N_LISA):
                # Strictly positive lognormal light, no missing-data policy
                # confound (G18 is a separate already completed experiment).
                ntl = np.exp(0.55 * fields[rep])
                z = (ntl - ntl.mean()) / ntl.std(ddof=1)
                _, _, p, _ = local_moran(
                    z, nbr, all_member, all_member,
                    perms=PERMS_LISA,
                    seed=SEED + 100000 + 10000 * w_index
                    + 1000 * rho_index + rep,
                    two_sided=True,
                )
                if not np.isfinite(p).all():
                    raise AssertionError("All 64 cells should be tested")
                if rho == 0.0:
                    truth_scope = "exchangeable_all_null"
                    injected = np.zeros(N, dtype=bool)
                    scenario = "iid_spatial_randomization_null"
                else:
                    truth_scope = "nonexchangeable_unidentified_truth"
                    injected = None
                    scenario = "correlated_background_no_injection"
                rows.append(one_row(
                    "lisa_conditional_permutation", weights, rho, scenario,
                    rep, truth_scope, p, injected
                ))

    design_rows = []
    for i in range(N):
        design_rows.append({
            "grid_id": i, "grid_ix": int(ix[i]), "grid_iy": int(iy[i]),
            "centroid_x_m": round(float(cx[i]), 1),
            "centroid_y_m": round(float(cy[i]), 1),
            "injected_mean_shift": int(signal[i]),
            "injected_delta_z": ALT_MEAN_Z if signal[i] else 0.0,
        })
    design_csv = _csv_text(design_rows, list(design_rows[0]))
    replicate_csv = _csv_text(rows, CSV_COLUMNS)
    summary = {
        "gap": "G17",
        "status": "synthetic_fdr_and_spatial_stress_only_real_data_open",
        "field_validation": False,
        "source": "generated Gaussian copula with spatial linear filter, and lognormal LISA field",
        "study_seed": SEED,
        "cell_size_m": CELL_M,
        "shape": [SIDE, SIDE],
        "cells": N,
        "gaussian_replications_per_case": N_GAUSSIAN,
        "lisa_replications_per_case": N_LISA,
        "lisa_permutations": PERMS_LISA,
        "lisa_p_min_two_sided": 2.0 / (PERMS_LISA + 1),
        "alpha": ALPHA,
        "rho_gaussian": list(RHO_GAUSSIAN),
        "rho_lisa": list(RHO_LISA),
        "weights": list(WEIGHTS),
        "gaussian_alternative_z_mean_shift": ALT_MEAN_Z,
        "n_injected": int(signal.sum()),
        "spatial_neighbors": spatial_details,
        "software": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
        "sha256": {
            "generator_py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "design_csv": hashlib.sha256(design_csv.encode("utf-8")).hexdigest(),
            "replicates_csv": hashlib.sha256(replicate_csv.encode("utf-8")).hexdigest(),
        },
        "methods": {
            "unadjusted": "two-sided p < alpha",
            "bh": "production bh_reject(p, alpha)",
            "by": "production bh_reject(p, alpha/H_m), H_m=sum(1/i)",
        },
        "known_truth": {
            "gaussian_valid_p": (
                "All marginal nulls are standard normal even for spatially "
                "dependent scores; injected 3x3 cells have nonzero mean. "
                "The non-injected cell nulls are exactly true."
            ),
            "lisa_iid": (
                "iid continuous lognormal values are exchangeable under "
                "the conditional spatial-randomization null; all tests null."
            ),
            "lisa_correlated": (
                "Nonzero rho induces spatial association and breaks "
                "exchangeability. A field with no planted shock is NOT "
                "an all-null local Moran field. Rejection frequency is "
                "descriptive, not false-discovery-rate evidence."
            ),
        },
        "limitations": [
            "Monte Carlo intervals represent finite simulation uncertainty only.",
            "The Gaussian experiment tests BH/BY with valid marginal p-values; it is NOT a validation of the local Moran permutation p construction.",
            "The iid local Moran test is a valid exchangeability stress case; clustered or negatively correlated lognormal fields violate its permutation null.",
            "No evidence that local spatial p-values satisfy PRDS is supplied.",
            "A Gaussian correlated p-value design does not model all possible dependencies.",
            "Both the hypothesis family and p-value resolution must be reported for any application-specific FDR claim.",
            "The app's existing BH routine, its default settings and A03 evidence are unchanged.",
            "No independent VIIRS support case or empirical LISA FDR certification is claimed.",
        ],
        "results": summarize(rows),
    }
    outputs = {
        "design.csv": design_csv,
        "replicates.csv": replicate_csv,
        "summary.json": json.dumps(
            summary, ensure_ascii=False, indent=2, allow_nan=False
        ) + "\n",
    }
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-ci", action="store_true",
                        help="Emit chunked base64 for archival through GitHub Actions")
    parser.add_argument("--verify", action="store_true",
                        help="Verify all three committed evidence files byte-for-byte")
    args = parser.parse_args()
    outputs = run_experiment()
    info = json.loads(outputs["summary.json"])
    assert len(info["results"]) == len(WEIGHTS) * (2 * len(RHO_GAUSSIAN) + len(RHO_LISA))
    assert info["n_injected"] == 9
    assert any(
        x["study"] == "lisa_conditional_permutation"
        and x["truth_scope"] == "nonexchangeable_unidentified_truth"
        and x["methods"]["bh"]["empirical_fdr"] is None
        for x in info["results"]
    )
    print("G17_SUMMARY " + json.dumps({
        "status": info["status"],
        "design": info["shape"],
        "gaussian_replications_per_case": N_GAUSSIAN,
        "lisa_replications_per_case": N_LISA,
        "gaussian_results": [
            {
                "weights": x["weights"],
                "rho": x["rho"],
                "scenario": x["scenario"],
                "bh_fdr": x["methods"]["bh"]["empirical_fdr"],
                "by_fdr": x["methods"]["by"]["empirical_fdr"],
                "bh_power": x["methods"]["bh"]["injection_power"],
                "by_power": x["methods"]["by"]["injection_power"],
            }
            for x in info["results"] if x["study"] == "gaussian_valid_p"
        ],
        "lisa_results": [
            {
                "weights": x["weights"],
                "rho": x["rho"],
                "truth_scope": x["truth_scope"],
                "bh_any_reject": x["methods"]["bh"]["any_rejection_rate"],
                "by_any_reject": x["methods"]["by"]["any_rejection_rate"],
            }
            for x in info["results"] if x["study"] == "lisa_conditional_permutation"
        ],
    }, sort_keys=True))
    if args.verify:
        for filename, body in outputs.items():
            target = DEST / filename
            if not target.is_file():
                raise SystemExit(f"Missing G17 evidence: {target}")
            if target.read_text(encoding="utf-8") != body:
                raise SystemExit(f"G17 evidence mismatch: {target}")
        print("G17 archived evidence matches generator output")
    if args.emit_ci:
        for filename, body in outputs.items():
            b64 = base64.b64encode(body.encode("utf-8")).decode("ascii")
            print(f"G17_BEGIN {filename}")
            for i in range(0, len(b64), 4000):
                print(b64[i:i + 4000])
            print(f"G17_END {filename}")


if __name__ == "__main__":
    main()
