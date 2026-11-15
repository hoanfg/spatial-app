
"""A02 batch-vs-legacy numerical equivalence, without private field imagery."""
import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from shapely.geometry import box

from ntl.semantics import QUALITY_BANDS, cell_quality
from ntl.zonal import zonal_stat, zonal_mean_multiband


def synthetic_case():
    # 3x4 source pixels: measured zeros, flags, variable valid months,
    # partial polygons, missing pixel, and a polygon outside source extent.
    bands = np.zeros((6, 3, 4), dtype="float32")
    bands[0] = np.array([[2, 0, 1, 10], [3, 1, 0, 4], [5, 7, 0, 9]], dtype="float32")
    bands[1] = [[1, 1, 1, 1], [1, 1, 0, 1], [1, 1, 1, 1]]
    bands[2] = [[0, 0, 0, 1], [0, 0, 0, 0], [1, 0, 0, 0]]
    bands[3] = [[0, 1, 0, 0], [0, 0, 0, 0], [0, 0, 1, 0]]
    bands[4] = [[12, 9, 11, 12], [8, 7, 0, 10], [12, 12, 12, 6]]
    bands[5] = (bands[4] < 3).astype("float32")
    bands[2, 0, 2] = np.nan
    bands[4, 2, 0] = np.inf
    with MemoryFile() as mf:
        with mf.open(driver="GTiff", height=3, width=4, count=6,
                     dtype="float32", crs="EPSG:32650",
                     transform=from_origin(500000, 4001500, 500, 500)) as dst:
            dst.write(bands)
            dst.write_mask(np.array([[255, 255, 255, 255],
                                     [255, 255, 0, 255],
                                     [255, 255, 255, 255]], dtype="uint8"))
            for n, label in enumerate(("avg_rad",) + QUALITY_BANDS, start=1):
                dst.set_band_description(n, label)
        raw = mf.read()
    x, y = 500000, 4001500
    g = gpd.GeoDataFrame({"grid_id": [90, 11, 3, 44, 56]},
        geometry=[
            box(x, y-500, x+500, y),
            box(x+250, y-750, x+750, y-250),  # fractionally covered pixels
            box(x+500, y-1000, x+1500, y),    # includes masked pixels
            box(x+2000, y-500, x+2500, y),    # outside -> NaN
            box(x, y-1500, x+2000, y),        # whole footprint
        ], crs="EPSG:32650")
    return raw, g


def legacy_bandwise(raw, grid):
    return pd.DataFrame({
        name: zonal_stat(raw, grid, band=i, clip_negative=False, fill_missing=None)
        for i, name in enumerate(QUALITY_BANDS, start=2)
    })


def test_batch_exactly_matches_legacy_five_band_contract():
    raw, grid = synthetic_case()
    for data in (grid, grid.iloc[[4, 0, 3, 1, 2]].copy()):
        legacy = legacy_bandwise(raw, data)
        fast = zonal_mean_multiband(raw, data, bands=(2, 3, 4, 5, 6), names=QUALITY_BANDS)
        assert fast.columns.tolist() == list(QUALITY_BANDS)
        np.testing.assert_allclose(fast.to_numpy(float), legacy.to_numpy(float),
                                   rtol=0, atol=1e-7, equal_nan=True)
        new_quality = cell_quality(raw, data)
        np.testing.assert_allclose(new_quality[list(QUALITY_BANDS)].to_numpy(float),
                                   legacy.to_numpy(float),
                                   rtol=0, atol=1e-7, equal_nan=True)
        assert new_quality.dq_ntl_policy.eq("legacy_zero_fill").all()
        assert new_quality.iloc[3 if data is grid else 2].dq_status == "unknown"


def test_supported_schema_means_one_exactextract_call(monkeypatch):
    import exactextract
    raw, grid = synthetic_case()
    original = exactextract.exact_extract
    count = {"n": 0}
    def counted(*args, **kwargs):
        count["n"] += 1
        return original(*args, **kwargs)
    monkeypatch.setattr(exactextract, "exact_extract", counted)
    cell_quality(raw, grid)
    assert count["n"] == 1


def test_batch_incorrect_band_contract_is_rejected():
    raw, grid = synthetic_case()
    with pytest.raises(ValueError, match="inconsistent"):
        zonal_mean_multiband(raw, grid, bands=(2, 3, 4), names=QUALITY_BANDS)
    with pytest.raises(ValueError, match="inconsistent"):
        zonal_mean_multiband(raw, grid, bands=(2, 3), names=("same", "same"))
