from __future__ import annotations

import io
import zipfile

from .ghsl_native import native_download_params, validate_native_download

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


def _download(img, roi, scale_m: float, timeout: int = 180) -> bytes:
    import requests
    url = img.getDownloadUrl({"scale": scale_m, "crs": "EPSG:4326", "region": roi, "format": "GEO_TIFF"})
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        raise ConnectionError(f"HTTP:{resp.status_code}")
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


def fetch_ghsl_raster(ee, kind: str, bbox: tuple, year: int) -> tuple[bytes, int]:
    """Download a bounded *native 100m equal-area* GHSL window.

    GHSL values are quantities per source pixel (m²/people). EPSG:4326
    nearest-neighbor reprojection then unadjusted summation is incorrect.
    """
    import requests
    if kind not in GHSL_DATASETS:
        raise ValueError("kind phải là 'built' hoặc 'pop'")
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
    url = image.getDownloadUrl(params)
    resp = requests.get(url, timeout=180)
    if resp.status_code != 200:
        raise ConnectionError(f"HTTP:{resp.status_code}")
    raw = extract_tif_bytes(resp.content)
    validate_native_download(raw, params)
    return raw, epoch
