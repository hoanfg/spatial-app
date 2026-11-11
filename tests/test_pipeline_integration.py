"""Cross-module regression checks using small synthetic rasters and grids.

These tests deliberately do not require Earth Engine or the Streamlit application
entrypoint. They check contracts shared by raster extraction, LISA, Space-Time,
and CSV export; independently collected field imagery remains separate evidence.
"""
from __future__ import annotations

import io

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

rasterio = pytest.importorskip("rasterio")
pytest.importorskip("exactextract")
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from ntl.lisa_core import run_lisa, run_spacetime_lisa
from ntl.spacetime_labels import format_regime_summary
from ntl.zonal import zonal_stat


def _tif(values, *, nodata=None):
    values = np.asarray(values, dtype=np.float32)
    rows, cols = values.shape
    with MemoryFile() as mf:
        with mf.open(
            driver="GTiff", height=rows, width=cols, count=1,
            dtype="float32", crs="EPSG:32650",
            transform=from_origin(500_000, 4_002_000, 500, 500),
            nodata=nodata,
        ) as dst:
            dst.write(values, 1)
        return mf.read()


def _grid():
    # Raster is 4 by 4 of 500 m pixels; one polygon for each pixel.
    polygons = []
    for r in range(4):
        for c in range(4):
            x0 = 500_000 + 500 * c
            y0 = 4_002_000 - 500 * (r + 1)
            polygons.append(box(x0, y0, x0 + 500, y0 + 500))
    grid = gpd.GeoDataFrame(
        {"grid_id": np.arange(16), "area_km2": 0.25},
        geometry=polygons, crs="EPSG:32650",
    )
    return grid


def _coords(grid):
    centers = grid.geometry.centroid
    return centers.x.to_numpy(), centers.y.to_numpy()


def test_raster_to_lisa_to_csv_roundtrip():
    grid = _grid()
    values = np.array([
        [0, 1, 2, 3],
        [1, 2, 4, 5],
        [2, 4, 9, 11],
        [3, 5, 11, 15],
    ], dtype=float)
    extracted = zonal_stat(_tif(values), grid, fill_missing=None)
    assert extracted.tolist() == pytest.approx(values.ravel().tolist())

    x, y = _coords(grid)
    result = run_lisa(
        x, y, extracted.to_numpy(), grid.area_km2.to_numpy(), 500,
        perms=19, alpha=0.05, fdr=False, min_cluster_cells=1,
    )
    assert len(result.cell_df) == len(grid)
    assert not result.cell_df["lisa_class"].isna().any()
    assert result.cell_df.loc[0, "lisa_class"] == "Dark (NTL=0)"

    exported = pd.DataFrame({
        "grid_id": grid.grid_id.to_numpy(),
        "ntl_mean": extracted.to_numpy(),
        "lisa_class": result.cell_df["lisa_class"].to_numpy(),
    })
    recovered = pd.read_csv(io.StringIO(exported.to_csv(index=False)))
    assert recovered.grid_id.tolist() == list(range(16))
    assert recovered.ntl_mean.tolist() == pytest.approx(values.ravel().tolist())
    assert recovered.lisa_class.tolist() == exported.lisa_class.tolist()


def test_missing_raster_pixel_remains_distinguishable_before_fill():
    grid = _grid()
    values = np.ones((4, 4), dtype=float)
    values[0, 0] = 0  # observed zero
    values[0, 1] = -9999  # missing sentinel
    values[0, 2] = -2  # valid negative, clipped to zero
    raw = _tif(values, nodata=-9999)
    observed = zonal_stat(raw, grid, clip_negative=True, fill_missing=None)
    assert observed.iloc[0] == 0.0
    assert np.isnan(observed.iloc[1])
    assert observed.iloc[2] == 0.0

    filled = zonal_stat(raw, grid, clip_negative=True, fill_missing=0.0)
    assert filled.iloc[:3].tolist() == [0.0, 0.0, 0.0]
    # This is the application's current fill-to-zero policy; it is not
    # equivalent to retaining an observational-coverage flag.
    assert int(observed.isna().sum()) == 1


def test_spacetime_codes_and_presentation_are_separate():
    grid = _grid()
    x, y = _coords(grid)
    v0 = np.arange(1, 17, dtype=float)
    v1 = np.array([1, 2, 2, 4, 3, 4, 4, 4, 2, 3, 3, 4, 1, 2, 2, 3.], float)
    out = run_spacetime_lisa(
        x, y, v0, v1, grid.area_km2.to_numpy(), 500,
        year_t0=2014, year_t1=2020,
    )
    original = out.regime_summary.copy(deep=True)
    localized = format_regime_summary(original, lang="en")
    pd.testing.assert_frame_equal(out.regime_summary, original)
    assert "Synchronized Relative Decline" in localized["regime"].values
    assert "4_Synchronized_Decline" in out.regime_summary["regime"].values
    assert "spacetime_regime" in out.st_cell_df.columns
    assert set(out.st_cell_df.spacetime_regime).issubset(
        set(original.regime).union({"Excluded_or_Static"})
    )


def test_spacetime_csv_schema_and_rounding():
    grid = _grid()
    x, y = _coords(grid)
    v0 = np.array([1., 2., 3., 4.] * 4)
    v1 = np.array([1.5, 2.5, 3.5, 4.5] * 4)
    out = run_spacetime_lisa(
        x, y, v0, v1, grid.area_km2.to_numpy(), 500,
        year_t0=2014, year_t1=2020,
    )
    csv = pd.read_csv(io.StringIO(out.st_cell_df.to_csv(index=False)))
    assert len(csv) == len(grid)
    for col in (
        "ntl_2014", "ntl_2020", "delta_z", "delta_lag_z",
        "movement_magnitude", "spacetime_regime",
    ):
        assert col in csv.columns
    assert csv.spacetime_regime.tolist() == out.st_cell_df.spacetime_regime.tolist()
