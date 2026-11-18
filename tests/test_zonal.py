
import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")
pytest.importorskip("exactextract")
gpd = pytest.importorskip("geopandas")

from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from shapely.geometry import box

from ntl.zonal import zonal_stat


def _tif(arr, nodata=None, mask=None):
    h, w = arr.shape
    with MemoryFile() as mf:
        with mf.open(driver="GTiff", height=h, width=w, count=1, dtype="float32", crs="EPSG:4326",
                     transform=from_origin(0, h, 1, 1), nodata=nodata) as dst:
            dst.write(arr.astype("float32"), 1)
            if mask is not None:
                dst.write_mask(mask)
        return mf.read()


def _grid():

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


@pytest.mark.parametrize('clip', [False, True])
@pytest.mark.parametrize('kind', ['sentinel', 'nan', 'inf', 'mask'])
def test_missing_pixel_excluded_before_clipping(kind, clip):
    missing = {'sentinel': -9999., 'nan': np.nan, 'inf': np.inf, 'mask': -9999.}[kind]
    data = _tif(np.array([[10., missing]]),
                nodata=-9999. if kind == 'sentinel' else None,
                mask=np.array([[255, 0]], dtype='uint8') if kind == 'mask' else None)
    grid = gpd.GeoDataFrame({'grid_id': [42, 7, 99]},
        geometry=[box(0, 0, 2, 1), box(1, 0, 2, 1), box(4, 0, 5, 1)], crs='EPSG:4326')
    means = zonal_stat(data, grid, clip_negative=clip, fill_missing=None)
    assert means[0] == pytest.approx(10.)
    assert means[1:].isna().all()
    assert zonal_stat(data, grid, 'sum', clip_negative=clip).tolist() == pytest.approx([10., 0., 0.])


def _ghsl_native_tif(values, *, crs="ESRI:54009"):
    """Synthetic equal-area source-grid quantity raster, not EPSG:4326."""
    values = np.asarray(values, dtype="float32")
    with MemoryFile() as mf:
        with mf.open(driver="GTiff", width=values.shape[1], height=values.shape[0],
                     count=1, dtype="float32", crs=crs,
                     transform=from_origin(11030200, 3800200, 100, 100)) as dst:
            dst.write(values, 1)
        return mf.read()


def test_ghsl_native_zonal_sum_reprojects_polygons_not_raster():
    from ntl.zonal import zonal_sum_native
    x, top = 11030200, 3800200
    arr = np.arange(1, 17, dtype="float32").reshape(4, 4)
    projected = gpd.GeoDataFrame({"grid_id": [9, 3]},
        geometry=[box(x, top - 400, x + 200, top),
                  box(x + 200, top - 400, x + 400, top)],
        crs="ESRI:54009")
    geographic = projected.to_crs("EPSG:4326")
    with MemoryFile(_ghsl_native_tif(arr)) as mf, mf.open() as src:
        assert src.crs.to_string() == "ESRI:54009"
        # The old call passed geographic polygons directly to this raster.
        assert not geographic.geometry.intersects(box(*src.bounds)).any()
        assert geographic.to_crs(src.crs).geometry.intersects(box(*src.bounds)).all()
    amounts = zonal_sum_native(_ghsl_native_tif(arr), geographic)
    assert amounts.tolist() == pytest.approx([60.0, 76.0], abs=0.08)
    assert geographic.grid_id.tolist() == [9, 3]


def test_ghsl_native_zonal_sum_rejects_missing_crs_and_no_overlap():
    from ntl.zonal import zonal_sum_native
    tif = _ghsl_native_tif(np.ones((4, 4), dtype="float32"))
    without_crs = gpd.GeoDataFrame({"grid_id": [1]},
        geometry=[box(0, 0, 100, 100)])
    with pytest.raises(ValueError, match="no CRS"):
        zonal_sum_native(tif, without_crs)
    outside = gpd.GeoDataFrame({"grid_id": [1]},
        geometry=[box(0, 0, 100, 100)], crs="ESRI:54009")
    with pytest.raises(ValueError, match="no spatial overlap"):
        zonal_sum_native(tif, outside)


def test_ghsl_native_zonal_sum_keeps_true_zero_values():
    from ntl.zonal import zonal_sum_native
    x, top = 11030200, 3800200
    p = gpd.GeoDataFrame({"grid_id": [5]},
        geometry=[box(x, top - 400, x + 400, top)], crs="ESRI:54009")
    values = zonal_sum_native(_ghsl_native_tif(np.zeros((4, 4))), p.to_crs("EPSG:4326"))
    assert values.tolist() == [0.0]


def test_ghsl_ui_must_use_native_crs_zonal_extraction():
    import ast
    from pathlib import Path
    module = ast.parse((Path(__file__).parents[1] / "ntl" / "quality_ui.py").read_text(encoding="utf-8"))
    ghsl_calls = [
        node for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name) and node.func.id == "measured_call"
        and any(isinstance(arg, ast.Name) and arg.id == "zonal_sum_native"
                for arg in node.args)
    ]
    assert len(ghsl_calls) == 1, "GHSL must reproject polygons to the raster CRS before extraction"
