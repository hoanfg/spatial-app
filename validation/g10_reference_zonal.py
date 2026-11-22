#!/usr/bin/env python3
"""Build G10/G18 source-reference cell CSV from separate Earth Engine export.

Input raster must follow g10_independent_support_gee.js source band order:
1 ref_observed_fraction, 2 ref_mean_valid_months, 3 ref_cf_cvg_total.

This is a source-vs-app check, not a proof of field validity, sampling
independence or calibrated causal/statistical inference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.io import MemoryFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ntl.zonal import zonal_stat

BANDS = ("ref_observed_fraction", "ref_mean_valid_months", "ref_cf_cvg_total")


def make_reference(raster_bytes: bytes, grid: gpd.GeoDataFrame,
                   *, trusted_gee_export: bool = False) -> pd.DataFrame:
    if grid.crs is None or "grid_id" not in grid:
        raise ValueError("Grid must have CRS and grid_id")
    if len(grid) == 0 or grid["grid_id"].isna().any() or grid["grid_id"].duplicated().any():
        raise ValueError("Grid IDs must be present and unique")
    with MemoryFile(raster_bytes) as mf, mf.open() as raster:
        if raster.count != 3 or raster.crs is None:
            raise ValueError("Source reference must contain 3 bands and valid CRS")
        labels = tuple((v or "").strip() for v in raster.descriptions)
        if labels != BANDS and not (trusted_gee_export and all(not x for x in labels)):
            raise ValueError(
                "Unlabeled/conflicting band order: verify source raster or explicitly pass "
                "--trusted-gee-export for the named GEE export script"
            )
        grid_aligned = grid.to_crs(raster.crs)
    data = {"grid_id": grid["grid_id"].to_numpy()}
    for band_no, name in enumerate(BANDS, start=1):
        data[name] = zonal_stat(
            raster_bytes, grid_aligned, "mean", clip_negative=False,
            fill_missing=None, band=band_no,
        ).to_numpy(float)
    out = pd.DataFrame(data)
    if out[list(BANDS)].isna().any().any():
        raise ValueError("Source raster does not overlap every analysis cell")
    frac = out[BANDS[0]].to_numpy(float)
    months = out[BANDS[1]].to_numpy(float)
    cf = out[BANDS[2]].to_numpy(float)
    if (np.any(frac < 0) or np.any(frac > 1 + 1e-6)
            or np.any(months < 0) or np.any(months > 12 + 1e-6)
            or np.any(cf < 0) or np.any((months > 0) & (cf <= 0))):
        raise ValueError("Source observation indicators/counts are incoherent")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-raster", type=Path, required=True)
    ap.add_argument("--grid-geojson", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--trusted-gee-export", action="store_true")
    args = ap.parse_args()
    raw = args.source_raster.read_bytes()
    grid = gpd.read_file(args.grid_geojson)
    table = make_reference(raw, grid, trusted_gee_export=args.trusted_gee_export)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)
    metadata = {
        "role": "G10/G18 independent source-observation cell reference",
        "provenance_assertion": "Year/product identity must be verified against the actual Earth Engine task",
        "year_declared": args.year,
        "raster_sha256": hashlib.sha256(raw).hexdigest(),
        "grid_geojson_sha256": hashlib.sha256(args.grid_geojson.read_bytes()).hexdigest(),
        "reference_csv_sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(),
        "n_cells": int(len(table)),
        "n_missing_observation_cells": int((table["ref_observed_fraction"] <= 0).sum()),
        "band_schema": list(BANDS),
        "trusted_unlabeled_source_order": args.trusted_gee_export,
    }
    args.out.with_suffix(".meta.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(table)} cells to {args.out}")


if __name__ == "__main__":
    main()
