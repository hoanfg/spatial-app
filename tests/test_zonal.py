"""Kiểm thử zonal_stat trên GeoTIFF nhỏ dựng trong bộ nhớ (bỏ qua nếu thiếu thư viện địa không gian)."""
import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")
pytest.importorskip("exactextract")
gpd = pytest.importorskip("geopandas")

from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from shapely.geometry import box

from ntl.zonal import zonal_stat


def _tif(arr):
    h, w = arr.shape
    with MemoryFile() as mf:
        with mf.open(driver="GTiff", height=h, width=w, count=1, dtype="float32", crs="EPSG:4326",
                     transform=from_origin(0, h, 1, 1)) as dst:
            dst.write(arr.astype("float32"), 1)
        return mf.read()


def _grid():
    # hai ô, mỗi ô phủ đúng 2x2 pixel
    return gpd.GeoDataFrame({"grid_id": [0, 1]}, geometry=[box(0, 0, 2, 2), box(2, 0, 4, 2)], crs="EPSG:4326")


def test_clip_vs_unclipped_mean():
    arr = np.array([[1, 1, -2, -2], [1, 1, 4, 4]], dtype="float32")
    g = _grid()
    clipped = zonal_stat(_tif(arr), g, "mean", clip_negative=True)
    raw = zonal_stat(_tif(arr), g, "mean", clip_negative=False)
    assert clipped.tolist() == pytest.approx([1.0, 2.0])
    assert raw.tolist() == pytest.approx([1.0, 1.0])  # (-2-2+4+4)/4


def test_sum_and_nan_filled():
    arr = np.array([[1, 1, np.nan, np.nan], [1, 1, np.nan, np.nan]], dtype="float32")
    s = zonal_stat(_tif(arr), _grid(), "sum")
    assert s.tolist() == pytest.approx([4.0, 0.0])
