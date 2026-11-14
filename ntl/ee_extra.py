from __future__ import annotations

import io
import zipfile

from .ghsl_native import native_download_params

GHSL_DATASETS = {
    "built": "JRC/GHSL/P2023A/GHS_BUILT_S",   # diện tích xây dựng (m2 mỗi ô 100 m)
    "pop": "JRC/GHSL/P2023A/GHS_POP",         # dân số (người mỗi ô 100 m)
}
GHSL_SCALE_M = 100.0
GHSL_LAST_OBSERVED = 2020   # các epoch sau năm này là ước tính/dự báo, không phải quan sát
MAX_PIXELS = 3_000_000      # trần số pixel cho một lần tải, tránh vượt giới hạn getDownloadUrl


def nearest_epoch(year: int, last_observed: int = GHSL_LAST_OBSERVED) -> int:
    """Epoch 5 năm gần nhất của GHSL, không vượt quá năm quan sát cuối."""
    e = int(5 * round(int(year) / 5.0))
    return max(1975, min(e, int(last_observed)))


def estimate_pixels(bbox: tuple, scale_m: float) -> float:
    """Số pixel xấp xỉ của bbox (độ) ở độ phân giải scale_m."""
    import math
    minx, miny, maxx, maxy = bbox
    mid = math.radians((miny + maxy) / 2.0)
    w_m = (maxx - minx) * 111_320.0 * math.cos(mid)
    h_m = (maxy - miny) * 110_574.0
    return (w_m / scale_m) * (h_m / scale_m)


def extract_tif_bytes(content: bytes) -> bytes:
    """Lấy file .tif từ phản hồi getDownloadUrl (có thể là zip)."""
    if content[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".tif")]
            if not names:
                raise ValueError("ZIP không chứa .tif")
            content = z.read(names[0])
    if content[:2] not in (b"II", b"MM"):
        raise ValueError("Phản hồi không phải GeoTIFF")
    return content


def _http_error(resp, limit: int = 300) -> ConnectionError:
    """ConnectionError giữ tiền tố 'HTTP:<mã>' và đính kèm lý do Earth Engine trả về (nếu có)."""
    try:
        detail = " ".join((resp.text or "").split())[:limit]
    except Exception:  # noqa: BLE001  (phản hồi nhị phân hoặc không đọc được)
        detail = ""
    return ConnectionError(f"HTTP:{resp.status_code}" + (f" - {detail}" if detail else ""))


def _download(img, roi, scale_m: float, timeout: int = 180) -> bytes:
    import requests
    url = img.getDownloadUrl({"scale": scale_m, "crs": "EPSG:4326", "region": roi, "format": "GEO_TIFF"})
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        raise _http_error(resp)
    return extract_tif_bytes(resp.content)


def _monthly_masked(ee, dataset: str, year: int, roi, cf_min: int):
    col = (ee.ImageCollection(dataset)
           .filterDate(f"{int(year)}-01-01", f"{int(year) + 1}-01-01")
           .filterBounds(roi))
    if col.size().getInfo() == 0:
        raise LookupError("EMPTY")
    return col.map(lambda img: img.select("avg_rad").updateMask(img.select("cf_cvg").gte(int(cf_min))))


def fetch_ntl_variant(ee, dataset: str, bbox: tuple, year: int, scale_m: float,
                      cf_min: int = 1, reducer: str = "median") -> bytes:
    """Raster NTL của năm với ngưỡng cf_cvg >= cf_min và reducer 'median' hoặc 'mean' (cf_min=1, median = bản chính)."""
    if reducer not in ("median", "mean"):
        raise ValueError("reducer phải là 'median' hoặc 'mean'")
    roi = ee.Geometry.Rectangle(list(bbox))
    masked = _monthly_masked(ee, dataset, year, roi, cf_min)
    img = (masked.median() if reducer == "median" else masked.mean())
    img = img.select("avg_rad").unmask(0.0).toFloat().clip(roi)
    return _download(img, roi, scale_m)


def fetch_obs_count_raster(ee, dataset: str, bbox: tuple, year: int, scale_m: float, cf_min: int = 1) -> bytes:
    """Raster đếm số tháng có quan sát không mây (cf_cvg >= cf_min) tại mỗi pixel; 0 nghĩa là không có tháng nào."""
    roi = ee.Geometry.Rectangle(list(bbox))
    masked = _monthly_masked(ee, dataset, year, roi, cf_min)
    img = masked.count().unmask(0.0).toFloat().clip(roi)
    return _download(img, roi, scale_m)


def _pixel_grid(params: dict) -> dict:
    """Chuyển tham số lưới gốc (native_download_params) thành PixelGrid của computePixels."""
    import re
    a, b, c, d, e, f = (float(v) for v in params["crs_transform"])
    width, height = (int(v) for v in params["dimensions"])
    crs = str(params["crs"]).strip()
    grid = {"dimensions": {"width": width, "height": height},
            "affineTransform": {"scaleX": a, "shearX": b, "translateX": c,
                                "shearY": d, "scaleY": e, "translateY": f}}
    if re.fullmatch(r"EPSG:\d+", crs, flags=re.IGNORECASE):
        grid["crsCode"] = crs.upper()
    else:  # WKT, hoặc mã ESRI:/SR-ORG: mà EE không nhận như crsCode
        if re.fullmatch(r"[A-Za-z-]+:\d+", crs):
            from rasterio.crs import CRS
            crs = CRS.from_user_input(crs).to_wkt()
        grid["crsWkt"] = crs
    return grid


def _npy_to_float32(content: bytes, width: int, height: int):
    """Đọc phản hồi NPY của computePixels thành mảng float32 (height, width) của đúng một băng."""
    import io
    import numpy as np
    try:
        arr = np.load(io.BytesIO(content), allow_pickle=False)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Phản hồi computePixels không phải NPY") from exc
    if arr.dtype.names:  # mảng có cấu trúc: mỗi băng là một trường
        if len(arr.dtype.names) != 1:
            raise ValueError("GHSL native download phải có đúng một băng")
        arr = arr[arr.dtype.names[0]]
    arr = np.squeeze(np.asarray(arr, dtype="float32"))
    if arr.shape != (height, width):
        raise ValueError(f"GHSL native download dimensions changed: {arr.shape} != {(height, width)}")
    return arr


def _write_geotiff(arr, params: dict) -> bytes:
    """Ghi GeoTIFF một băng trên đúng CRS và affine đã yêu cầu (GDAL ghi được Mollweide, Earth Engine thì không)."""
    from rasterio.crs import CRS
    from rasterio.io import MemoryFile
    from rasterio.transform import Affine
    height, width = arr.shape
    with MemoryFile() as mf:
        with mf.open(driver="GTiff", height=height, width=width, count=1, dtype="float32",
                     crs=CRS.from_user_input(params["crs"]),
                     transform=Affine(*(float(v) for v in params["crs_transform"]))) as dst:
            dst.write(arr, 1)
        return mf.read()


def _download_native(image, params: dict, timeout: int = 180) -> bytes:
    """Fetch exactly the requested native GHSL lattice and return it as a GeoTIFF.

    getDownloadUrl(format=GEO_TIFF) fails for GHSL with 400 INVALID_ARGUMENT
    ("Unable to write GeoTIFFs in projection ... World_Mollweide"). computePixels
    can return the same grid as NPY, which has no projection limit, and we write
    the GeoTIFF locally. The grid is requested and written from the same params,
    and the array shape is checked, so the lattice cannot silently drift.
    ``timeout`` is kept for call compatibility; computePixels does not take one.
    """
    import ee
    content = ee.data.computePixels({"expression": image, "fileFormat": "NPY",
                                     "grid": _pixel_grid(params)})
    width, height = (int(v) for v in params["dimensions"])
    return _write_geotiff(_npy_to_float32(content, width, height), params)


def fetch_ghsl_raster(ee, kind: str, bbox: tuple, year: int) -> tuple[bytes, int]:
    """Download a bounded *native 100m equal-area* GHSL window.

    GHSL values are quantities per source pixel (m²/people). EPSG:4326
    nearest-neighbor reprojection then unadjusted summation is incorrect.
    """
    if kind not in GHSL_DATASETS:
        raise ValueError("kind phải là 'built' hoặc 'pop'")
    # Retain the preflight that rejects very large requests before Earth Engine.
    if estimate_pixels(bbox, GHSL_SCALE_M) > MAX_PIXELS:
        raise ValueError("Vùng quá lớn để tải GHSL ở 100 m; hãy chọn địa phương nhỏ hơn.")
    epoch = nearest_epoch(year)
    roi = ee.Geometry.Rectangle(list(bbox))
    col = ee.ImageCollection(GHSL_DATASETS[kind]).filter(
        ee.Filter.calendarRange(epoch, epoch, "year"))
    if col.size().getInfo() == 0:
        raise LookupError("EMPTY")
    source = col.first().select([0])
    params = native_download_params(source.projection().getInfo(), bbox,
                                    max_pixels=MAX_PIXELS)
    image = source.unmask(0.0).toFloat().clip(roi)
    return _download_native(image, params), epoch
