from __future__ import annotations

import os
import tempfile
from time import perf_counter

import numpy as np
import pandas as pd


def read_valid_band(src, clip_negative: bool = True):
    """Preserve source masks and nonfinite missing pixels before clipping."""
    arr = src.read(1, masked=True).astype("float32").filled(np.nan)
    arr[~np.isfinite(arr)] = np.nan
    return np.maximum(arr, 0.0) if clip_negative else arr


def zonal_stat(tif_bytes: bytes, grid_wgs, stat: str = "mean", clip_negative: bool = True,
               id_col: str = "grid_id", fill_missing: float | None = 0.0,
               band: int = 1) -> pd.Series:
    """Giá trị `stat` ('mean' hoặc 'sum') của raster trên từng ô, trả Series theo thứ tự grid_wgs[id_col].

    Missing/masked/nonfinite pixels are excluded; clip_negative clips valid negatives only.
    fill_missing: giá trị thay cho ô không có kết quả; None để giữ NaN."""
    from exactextract import exact_extract
    import rasterio
    from rasterio.io import MemoryFile

    with MemoryFile(tif_bytes) as mf:
        with mf.open() as src:
            arr = src.read(band, masked=True).astype("float32").filled(np.nan)
            arr[~np.isfinite(arr)] = np.nan
            if clip_negative:
                arr = np.maximum(arr, 0.0)
            crs, transform, h, w = src.crs, src.transform, src.height, src.width

    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tf:
            tmp = tf.name
        with rasterio.open(tmp, "w", driver="GTiff", height=h, width=w, count=1,
                           dtype="float32", crs=crs, transform=transform, nodata=np.nan) as dst:
            dst.write(arr, 1)
        df = exact_extract(tmp, grid_wgs[[id_col, "geometry"]], [stat], include_cols=[id_col], output="pandas")
    finally:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
    col = next(c for c in df.columns if stat in str(c).lower())
    df[id_col] = pd.to_numeric(df[id_col], errors="coerce").astype("int64")
    vals = pd.to_numeric(df[col], errors="coerce")
    merged = grid_wgs[[id_col]].merge(pd.DataFrame({id_col: df[id_col], "v": vals}), on=id_col, how="left")
    out = merged["v"]
    if fill_missing is not None:
        out = out.fillna(fill_missing)
    return out.reset_index(drop=True)

def zonal_sum_native(tif_bytes: bytes, grid, *, id_col: str = "grid_id",
                     fill_missing: float | None = 0.0) -> pd.Series:
    """Area-fraction-weighted sum of source-pixel quantities on their native grid.

    exactextract warns about mismatched feature/raster CRS but does not
    automatically reproject polygons. GHSL is stored in ESRI:54009 (100 m
    Mollweide); passing WGS84 degree coordinates silently produces empty
    zonal results, and filling those with zero destroys external validation.

    Keep the source raster pixel lattice unchanged. Reproject only the
    vector polygons, preserve id/order, and distinguish no-overlap from
    legitimate zero-valued source pixels.
    """
    from rasterio.io import MemoryFile
    from shapely.geometry import box

    if getattr(grid, "crs", None) is None:
        raise ValueError("GHSL zonal polygons have no CRS")
    if len(grid) == 0:
        raise ValueError("GHSL zonal grid contains no polygons")

    with MemoryFile(tif_bytes) as mf, mf.open() as src:
        if src.crs is None:
            raise ValueError("GHSL raster has no CRS")
        raster_crs = src.crs
        raster_footprint = box(*src.bounds)

    aligned_grid = grid.to_crs(raster_crs)
    if not aligned_grid.geometry.intersects(raster_footprint).any():
        raise ValueError(
            "GHSL native raster and grid have no spatial overlap after CRS alignment"
        )

    sums = zonal_stat(tif_bytes, aligned_grid, stat="sum",
                      clip_negative=True, id_col=id_col, fill_missing=None)
    if sums.isna().all():
        raise ValueError(
            "GHSL native zonal extraction yielded no observed pixel intersections"
        )
    # After excluding absent/masked pixels, retain the application's
    # explicit zero-fill policy; never fabricate overlap from an empty result.
    if fill_missing is not None:
        sums = sums.fillna(fill_missing)
    return sums.reset_index(drop=True)


def zonal_mean_multiband(tif_bytes: bytes, grid, *, bands: tuple[int, ...],
                         names: tuple[str, ...], id_col: str = "grid_id",
                         timings: dict | None = None) -> pd.DataFrame:
    """Calculate area-weighted quality means together, preserving old numeric semantics.

    The legacy path called zonal_stat five times, repeatedly decoding/writing
    each quality band and traversing the same polygons. Here a single in-memory
    five-band float32 raster retains the identical nodata/NaN policy, while
    exactextract processes all named sources in a single invocation.

    The input remains read-only; no changes to VIIRS, LISA or GHSL values.
    """
    from exactextract import exact_extract
    from exactextract.raster import RasterioRasterSource
    from rasterio.io import MemoryFile

    if len(bands) != len(names) or not bands or len(set(names)) != len(names):
        raise ValueError("Quality bands/names are inconsistent")
    if len(grid) == 0:
        return pd.DataFrame(columns=names, index=grid.index).reset_index(drop=True)

    started = perf_counter()
    with MemoryFile(tif_bytes) as source_file, source_file.open() as source:
        stack = source.read(list(bands), masked=True).astype("float32").filled(np.nan)
        stack[~np.isfinite(stack)] = np.nan
        if timings is not None:
            timings['raster_read_normalize_s'] = round(perf_counter() - started, 4)

        started = perf_counter()
        with MemoryFile() as normalized_file:
            with normalized_file.open(
                driver="GTiff", width=source.width, height=source.height,
                count=len(bands), dtype="float32", crs=source.crs,
                transform=source.transform, nodata=np.nan
            ) as output:
                output.write(stack)
            if timings is not None:
                timings['memory_geotiff_write_s'] = round(perf_counter() - started, 4)
            with normalized_file.open() as normalized:
                layers = [
                    RasterioRasterSource(normalized, band_idx=i, name=name)
                    for i, name in enumerate(names, start=1)
                ]
                started = perf_counter()
                data = exact_extract(
                    layers, grid[[id_col, "geometry"]], ["mean"],
                    include_cols=[id_col], output="pandas"
                )
                if timings is not None:
                    timings['polygon_extract_s'] = round(perf_counter() - started, 4)

    started = perf_counter()
    expected = {f"{name}_mean" for name in names}
    if not expected.issubset(data.columns):
        raise ValueError(
            "Unexpected multi-band zonal columns: "
            + ", ".join(map(str, data.columns))
        )
    data[id_col] = pd.to_numeric(data[id_col], errors="coerce").astype("int64")
    columns = {name: pd.to_numeric(data[f"{name}_mean"], errors="coerce")
               for name in names}
    table = pd.DataFrame({id_col: data[id_col], **columns})
    # Match the old one-band merge: preserve input order, NaN for missing
    # intersections, and source grid_id identity (including reordered cells).
    merged = grid[[id_col]].merge(table, on=id_col, how="left")
    result = merged[list(names)].reset_index(drop=True)
    if timings is not None:
        timings['join_s'] = round(perf_counter() - started, 4)
    return result
