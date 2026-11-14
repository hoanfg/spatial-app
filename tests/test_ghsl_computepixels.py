"""GHSL native download via computePixels (NPY) instead of GEO_TIFF.

Regression: getDownloadUrl(format=GEO_TIFF) returned 400 INVALID_ARGUMENT
"Unable to write GeoTIFFs in projection ... World_Mollweide".
"""
import io
import sys
import types

import numpy as np
import pytest

from ntl import ee_extra

TRANSFORM = [100.0, 0.0, 11030200.0, 0.0, -100.0, 3800200.0]
PARAMS = {"crs": "PROJCS[\"World_Mollweide\"]", "crs_transform": TRANSFORM,
          "dimensions": [4, 3], "format": "GEO_TIFF"}


def _npy(arr, field="built_surface"):
    out = np.zeros(arr.shape, dtype=[(field, "<f4")])
    out[field] = arr
    buf = io.BytesIO()
    np.save(buf, out)
    return buf.getvalue()


def _fake_ee(monkeypatch, payload, calls):
    def compute_pixels(request):
        calls.append(request)
        return payload
    monkeypatch.setitem(sys.modules, "ee",
                        types.SimpleNamespace(data=types.SimpleNamespace(computePixels=compute_pixels)))


def test_pixel_grid_wkt_and_epsg():
    g = ee_extra._pixel_grid(PARAMS)
    assert g["dimensions"] == {"width": 4, "height": 3}
    assert g["affineTransform"] == {"scaleX": 100.0, "shearX": 0.0, "translateX": 11030200.0,
                                    "shearY": 0.0, "scaleY": -100.0, "translateY": 3800200.0}
    assert g["crsWkt"] == PARAMS["crs"] and "crsCode" not in g
    g2 = ee_extra._pixel_grid({**PARAMS, "crs": "epsg:4326"})
    assert g2["crsCode"] == "EPSG:4326" and "crsWkt" not in g2


def test_npy_parsing_and_shape_check():
    arr = np.arange(12, dtype="float32").reshape(3, 4)
    np.testing.assert_array_equal(ee_extra._npy_to_float32(_npy(arr), 4, 3), arr)
    with pytest.raises(ValueError, match="dimensions"):
        ee_extra._npy_to_float32(_npy(arr), 3, 4)
    with pytest.raises(ValueError, match="NPY"):
        ee_extra._npy_to_float32(b"<html>error</html>", 4, 3)
    two = np.zeros((3, 4), dtype=[("a", "<f4"), ("b", "<f4")])
    buf = io.BytesIO()
    np.save(buf, two)
    with pytest.raises(ValueError, match="một băng"):
        ee_extra._npy_to_float32(buf.getvalue(), 4, 3)


def test_download_native_requests_npy_on_exact_grid(monkeypatch):
    arr = np.arange(12, dtype="float32").reshape(3, 4)
    calls, written = [], []
    _fake_ee(monkeypatch, _npy(arr), calls)
    monkeypatch.setattr(ee_extra, "_write_geotiff",
                        lambda a, p: (written.append((a, p)), b"II*\x00")[1])
    image = object()
    assert ee_extra._download_native(image, PARAMS) == b"II*\x00"
    (req,) = calls
    assert req["expression"] is image and req["fileFormat"] == "NPY"
    assert req["grid"] == ee_extra._pixel_grid(PARAMS)
    np.testing.assert_array_equal(written[0][0], arr)
    assert written[0][1] is PARAMS


def test_download_native_rejects_wrong_shape(monkeypatch):
    _fake_ee(monkeypatch, _npy(np.zeros((5, 5), dtype="float32")), [])
    with pytest.raises(ValueError, match="dimensions"):
        ee_extra._download_native(object(), PARAMS)


def test_written_geotiff_keeps_projection_and_lattice(monkeypatch):
    rasterio = pytest.importorskip("rasterio")
    from rasterio.crs import CRS
    from rasterio.io import MemoryFile
    from ntl.ghsl_native import validate_native_download

    params = {**PARAMS, "crs": CRS.from_string("ESRI:54009").to_wkt()}
    arr = np.arange(12, dtype="float32").reshape(3, 4)
    _fake_ee(monkeypatch, _npy(arr), [])
    raw = ee_extra._download_native(object(), params)
    validate_native_download(raw, params)       # CRS, dimensions and origin match the request
    with MemoryFile(raw) as mf, mf.open() as ds:
        np.testing.assert_array_equal(ds.read(1), arr)
        assert tuple(ds.transform)[:6] == tuple(TRANSFORM)
