#!/usr/bin/env python3
"""Descriptive fixed-block spatial resampling, not formal FDR or a causal test.

Inputs: per-cell *_same_grid_cells_with_proxies.csv and same-run app GeoJSON.
GeoJSON and joined tables must share unique grid_id values. Reuses app geometry.
"""
import argparse
import json
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

SITES = {
    "BAOAN": ("bao_an", 32650),
    "QIMEN": ("qimen", 32650),
    "SHANGHAI": ("shanghai", 32651),
}
MEASURES = {
    "roads": "osm_2026_road_km_per_km2",
    "buildings": "osm_2026_buildings_sum_fraction",
    "eog_annual": "eog_annual_band2_mean",
    "wsf2019": "wsf2019_rawclass_255_share",
}

def rank_correlation(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 30 or np.unique(a[ok]).size < 2 or np.unique(b[ok]).size < 2:
        return None
    return float(spearmanr(a[ok], b[ok]).statistic)

def run_site(root, site, block_m=2000, reps=500, seed=20261122):
    slug, utm = SITES[site]
    csv = root / "spatial_app_grid_validation" / (site + "_same_grid_cells_with_proxies.csv")
    geojson = root / (slug + "_NTL_2020_500m.geojson")
    if not geojson.is_file():
        geojson = geojson.with_suffix(".geojson.bin")
    frame = pd.read_csv(csv)
    grid = gpd.read_file(geojson)
    if not frame.grid_id.is_unique or not grid.grid_id.is_unique:
        raise ValueError(site + ": non-unique grid_id")
    if len(frame) != len(grid) or set(frame.grid_id) != set(grid.grid_id):
        raise ValueError(site + ": CSV and GeoJSON grid_id mismatch")
    centers = grid.set_index("grid_id").loc[frame.grid_id].to_crs(epsg=utm).geometry.centroid
    xy = np.column_stack((centers.x.to_numpy(), centers.y.to_numpy()))
    labels, which = np.unique(np.floor(xy / block_m).astype("int64"), axis=0, return_inverse=True)
    groups = [np.flatnonzero(which == i) for i in range(len(labels))]
    rng = np.random.default_rng(seed)
    selections = [
        np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        for _ in range(reps)
    ]
    outcome = frame.ntl_mean.to_numpy(dtype=float)
    measurements = {}
    for label, col in MEASURES.items():
        x = frame[col].to_numpy(dtype=float)
        observed = rank_correlation(outcome, x)
        samples = [rank_correlation(outcome[idx], x[idx]) for idx in selections]
        finite = np.asarray([v for v in samples if v is not None and np.isfinite(v)])
        measurements[label] = {
            "rho": observed,
            "resample_median": float(np.median(finite)) if finite.size else None,
            "resample_p025": float(np.percentile(finite, 2.5)) if finite.size else None,
            "resample_p975": float(np.percentile(finite, 97.5)) if finite.size else None,
            "replicates_finite": int(finite.size),
            "cell_pairs": int((np.isfinite(outcome) & np.isfinite(x)).sum()),
        }
    return {
        "site": site, "n_cells": len(frame), "n_spatial_blocks": len(labels),
        "block_size_m": block_m, "reps": reps, "seed": seed,
        "interpretation": "Descriptive resampling sensitivity; not calibrated CI/FDR",
        "measures": measurements,
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--seed", type=int, default=20261122)
    ap.add_argument("--block-m", type=int, default=2000)
    a = ap.parse_args()
    results = {s: run_site(a.root, s, a.block_m, a.reps, a.seed) for s in SITES}
    destination = a.output or (a.root / "spatial_block_sensitivity.json")
    destination.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for site, info in results.items():
        print(site, info["n_cells"], info["n_spatial_blocks"], info["measures"]["roads"])
