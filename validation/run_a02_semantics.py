"""Reproduce synthetic missingness sensitivity; run from the repository root.

python validation/run_a02_semantics.py
No live Earth Engine access. No scientific missingness policy is selected here.
"""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ntl.lisa_core import build_queen_neighbors, gini, run_lisa, run_spacetime_lisa


def global_moran(x, y, values):
    """Binary Queen Global I, same convention as app; no inference/p-value."""
    n = len(values)
    neighbors = build_queen_neighbors(x, y, 500, np.ones(n, bool))
    z = values - values.mean()
    valid = neighbors >= 0
    numerator = (z[:, None] * z[np.maximum(neighbors, 0)] * valid).sum()
    return float(n / valid.sum() * numerator / (z @ z))


def measure(x, y, values):
    out = run_lisa(x, y, values, np.full(len(values), .25), 500,
                   perms=99, min_cluster_cells=1)
    return {"mean_ntl": float(values.mean()), "zero_cell_share": float((values == 0).mean()),
            "gini": float(gini(values)), "global_moran_binary_queen": global_moran(x, y, values),
            "lisa_classes": out.cell_df.lisa_class.tolist()}


def main():
    x, y = np.meshgrid(np.arange(6)*500+250, np.arange(6)*500+250)
    x, y = x.ravel(), y.ravel()
    baseline = (1 + x/500 + y/500 + (x > 1500)*8).astype(float)
    baseline[0] = 0  # genuine measured zero
    missing = np.array([8, 9, 14, 15, 20, 21])
    filled = baseline.copy()
    filled[missing] = 0
    keep = ~np.isin(np.arange(36), missing)
    full = measure(x, y, baseline)
    legacy = measure(x, y, filled)
    observed = measure(x[keep], y[keep], baseline[keep])
    st = run_spacetime_lisa(x, y, baseline, filled, np.full(36, .25), 500,
                            year_t0=2014, year_t1=2020)
    st_unchanged = run_spacetime_lisa(x, y, baseline, baseline, np.full(36, .25), 500,
                                      year_t0=2014, year_t1=2020)
    result = {
        "evidence_type": "synthetic sensitivity, not observed field error",
        "base_commit": "719ccf1953373326fac8451e7e0571e09961acf9",
        "seed": 42, "permutations": 99,
        "missing_indices": missing.tolist(), "input_baseline": baseline.tolist(),
        "baseline_complete": full, "missing_legacy_zero_fill": legacy,
        "observed_only_sensitivity": observed,
        "lisa_changed_cells_from_missing": sum(a != b for a, b in zip(full["lisa_classes"], legacy["lisa_classes"])),
        "spacetime_regime_changed_cells": int((st.st_cell_df.spacetime_regime != st_unchanged.st_cell_df.spacetime_regime).sum()),
        "spacetime_regimes_with_missing": st.st_cell_df.spacetime_regime.tolist(),
        "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "rasterio", "exactextract", "geopandas"]},
    }
    reference = Path("validation/evidence/yanqing/rasters/yanqing_viirs_2014_reference.tif")
    if reference.exists():
        import rasterio
        from ntl.zonal import read_valid_band
        with rasterio.open(reference) as src:
            a = read_valid_band(src, clip_negative=False)
            result["repository_reference_raster"] = {
                "path": str(reference), "sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
                "bands": src.count, "finite_pixels": int(np.isfinite(a).sum()),
                "zero_pixels": int((a == 0).sum()), "negative_pixels": int((a < 0).sum()),
                "monthly_observation_coverage": "unknown: legacy raster has no observation-count bands",
            }
    target = Path("validation/evidence/a02/synthetic_sensitivity.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
