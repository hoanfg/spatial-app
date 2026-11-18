from __future__ import annotations

import io
import math
import zipfile

from .ghsl_native import native_download_params

GHSL_DATASETS = {
    "built": "JRC/GHSL/P2023A/GHS_BUILT_S",
    "pop": "JRC/GHSL/P2023A/GHS_POP",
}
GHSL_SCALE_M = 100.0
GHSL_LAST_OBSERVED = 2020
MAX_PIXELS = 3_000_000
MAX_TILE_REQUEST_BYTES = 32 * 1024 * 1024
FLOAT32_BYTES = 4


def nearest_epoch(year: int, last_observed: int = GHSL_LAST_OBSERVED) -> int:

    e = int(5 * round(int(year) / 5.0))
    return max(1975, min(e, int(last_observed)))


def estimate_pixels(bbox: tuple, scale_m: float) -> float:

    minx, miny, maxx, maxy = bbox
    mid = math.radians((miny + maxy) / 2.0)
    w_m = (maxx - minx) * 111_320.0 * math.cos(mid)
    h_m = (maxy - miny) * 110_574.0
    return (w_m / scale_m) * (h_m / scale_m)


def tile_bboxes(bbox: tuple, scale_m: float, band_count: int = 1,
                max_request_bytes: int = MAX_TILE_REQUEST_BYTES) -> list[tuple]:
    """Split a WGS84 rectangle so each float32 request stays below the byte budget."""
    minx, miny, maxx, maxy = (float(v) for v in bbox)
    if minx >= maxx or miny >= maxy:
        raise ValueError("Invalid WGS84 bounding box")
    if scale_m <= 0 or band_count <= 0 or max_request_bytes <= 0:
        raise ValueError("Scale, band count and request budget must be positive")

    pixels = max(1.0, estimate_pixels((minx, miny, maxx, maxy), scale_m))
    target_pixels = max_request_bytes / (FLOAT32_BYTES * band_count)
    required = max(1, int(math.ceil(pixels / target_pixels)))
    if required == 1:
        return [(minx, miny, maxx, maxy)]

    mid_lat = math.radians((miny + maxy) / 2.0)
    width_m = max((maxx - minx) * 111_320.0 * abs(math.cos(mid_lat)), 1.0)
    height_m = max((maxy - miny) * 110_574.0, 1.0)
    aspect = width_m / height_m
    nx = max(1, int(math.ceil(math.sqrt(required * aspect))))
    ny = max(1, int(math.ceil(required / nx)))
    while pixels / (nx * ny) > target_pixels:
        if width_m / nx >= height_m / ny:
            nx += 1
        else:
            ny += 1

    dx, dy = (maxx - minx) / nx, (maxy - miny) / ny
    return [
        (minx + ix * dx, miny + iy * dy,
         maxx if ix == nx - 1 else minx + (ix + 1) * dx,
         maxy if iy == ny - 1 else miny + (iy + 1) * dy)
        for iy in range(ny) for ix in range(nx)
    ]


def extract_tif_bytes(content: bytes) -> bytes:

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

    try:
        detail = " ".join((resp.text or "").split())[:limit]
    except Exception:
        detail = ""
    return ConnectionError(f"HTTP:{resp.status_code}" + (f" - {detail}" if detail else ""))


def _download(img, roi, scale_m: float, timeout: int = 180) -> bytes:
    import requests
    url = img.getDownloadUrl({"scale": scale_m, "crs": "EPSG:4326", "region": roi, "format": "GEO_TIFF"})
    resp = requests.get(url, timeout=timeout)
    if resp.status_code != 200:
        raise _http_error(resp)
    return extract_tif_bytes(resp.content)


def merge_geotiffs(parts: list[bytes]) -> bytes:
    """Merge aligned in-memory GeoTIFF tiles and retain band descriptions."""
    if not parts:
        raise ValueError("No GeoTIFF tiles to merge")
    if len(parts) == 1:
        return parts[0]

    from contextlib import ExitStack
    from rasterio.io import MemoryFile
    from rasterio.merge import merge

    with ExitStack() as stack:
        memory_files = [stack.enter_context(MemoryFile(raw)) for raw in parts]
        sources = [stack.enter_context(mf.open()) for mf in memory_files]
        mosaic, transform = merge(sources, method="first")
        profile = sources[0].profile.copy()
        descriptions = sources[0].descriptions
        profile.update(
            driver="GTiff", height=mosaic.shape[1], width=mosaic.shape[2],
            count=mosaic.shape[0], transform=transform, compress="deflate",
        )
        with MemoryFile() as output:
            with output.open(**profile) as dst:
                dst.write(mosaic)
                for band_no, description in enumerate(descriptions, start=1):
                    if description:
                        dst.set_band_description(band_no, description)
            return output.read()


def _is_request_size_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "request size" in message or "50331648" in message or "must be less than or equal" in message


def download_tiled_geotiff(ee, img, bbox: tuple, scale_m: float, band_count: int = 1,
                           max_request_bytes: int = MAX_TILE_REQUEST_BYTES,
                           timeout: int = 180) -> bytes:
    """Download a large Earth Engine rectangle in tiles without changing resolution."""
    initial = tile_bboxes(bbox, scale_m, band_count, max_request_bytes)

    def fetch_box(box, depth=0):
        roi = ee.Geometry.Rectangle(list(box))
        try:
            return [_download(img, roi, scale_m, timeout=timeout)]
        except Exception as exc:  # noqa: BLE001
            if depth >= 5 or not _is_request_size_error(exc):
                raise
            children = tile_bboxes(box, scale_m, band_count, max_request_bytes // 4)
            if len(children) == 1:
                minx, miny, maxx, maxy = box
                midx, midy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
                children = [
                    (minx, miny, midx, midy), (midx, miny, maxx, midy),
                    (minx, midy, midx, maxy), (midx, midy, maxx, maxy),
                ]
            out = []
            for child in children:
                out.extend(fetch_box(child, depth + 1))
            return out

    parts = []
    for box in initial:
        parts.extend(fetch_box(box))
    return merge_geotiffs(parts)


def _monthly_masked(ee, dataset: str, year: int, roi, cf_min: int):
    col = (ee.ImageCollection(dataset)
           .filterDate(f"{int(year)}-01-01", f"{int(year) + 1}-01-01")
           .filterBounds(roi))
    if col.size().getInfo() == 0:
        raise LookupError("EMPTY")
    return col.map(lambda img: img.select("avg_rad").updateMask(img.select("cf_cvg").gte(int(cf_min))))


def fetch_ntl_variant(ee, dataset: str, bbox: tuple, year: int, scale_m: float,
                      cf_min: int = 1, reducer: str = "median") -> bytes:

    if reducer not in ("median", "mean"):
        raise ValueError("reducer phải là 'median' hoặc 'mean'")
    roi = ee.Geometry.Rectangle(list(bbox))
    masked = _monthly_masked(ee, dataset, year, roi, cf_min)
    img = (masked.median() if reducer == "median" else masked.mean())
    img = img.select("avg_rad").unmask(0.0).toFloat().clip(roi)
    return download_tiled_geotiff(ee, img, bbox, scale_m, band_count=1)


def fetch_obs_count_raster(ee, dataset: str, bbox: tuple, year: int, scale_m: float, cf_min: int = 1) -> bytes:

    roi = ee.Geometry.Rectangle(list(bbox))
    masked = _monthly_masked(ee, dataset, year, roi, cf_min)
    img = masked.count().unmask(0.0).toFloat().clip(roi)
    return download_tiled_geotiff(ee, img, bbox, scale_m, band_count=1)


def _pixel_grid(params: dict) -> dict:

    import re
    a, b, c, d, e, f = (float(v) for v in params["crs_transform"])
    width, height = (int(v) for v in params["dimensions"])
    crs = str(params["crs"]).strip()
    grid = {"dimensions": {"width": width, "height": height},
            "affineTransform": {"scaleX": a, "shearX": b, "translateX": c,
                                "shearY": d, "scaleY": e, "translateY": f}}
    if re.fullmatch(r"EPSG:\d+", crs, flags=re.IGNORECASE):
        grid["crsCode"] = crs.upper()
    else:
        if re.fullmatch(r"[A-Za-z-]+:\d+", crs):
            from rasterio.crs import CRS
            crs = CRS.from_user_input(crs).to_wkt()
        grid["crsWkt"] = crs
    return grid


def _npy_to_float32(content: bytes, width: int, height: int):

    import io
    import numpy as np
    try:
        arr = np.load(io.BytesIO(content), allow_pickle=False)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Phản hồi computePixels không phải NPY") from exc
    if arr.dtype.names:
        if len(arr.dtype.names) != 1:
            raise ValueError("GHSL native download phải có đúng một băng")
        arr = arr[arr.dtype.names[0]]
    arr = np.squeeze(np.asarray(arr, dtype="float32"))
    if arr.shape != (height, width):
        raise ValueError(f"GHSL native download dimensions changed: {arr.shape} != {(height, width)}")
    return arr


def _write_geotiff(arr, params: dict) -> bytes:

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
