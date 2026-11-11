from __future__ import annotations

import os
import tempfile

import numpy as np
import pandas as pd


def read_valid_band(src, clip_negative: bool = True):
    """Preserve source masks and nonfinite missing pixels before clipping."""
    arr = src.read(1, masked=True).astype("float32").filled(np.nan)
    arr[~np.isfinite(arr)] = np.nan
    return np.maximum(arr, 0.0) if clip_negative else arr


def zonal_stat(tif_bytes: bytes, grid_wgs, stat: str = "mean", clip_negative: bool = True,
               id_col: str = "grid_id", fill_missing: float | None = 0.0) -> pd.Series:
    """Giá trị `stat` ('mean' hoặc 'sum') của raster trên từng ô, trả Series theo thứ tự grid_wgs[id_col].

    Missing/masked/nonfinite pixels are excluded; clip_negative clips valid negatives only.
    fill_missing: giá trị thay cho ô không có kết quả; None để giữ NaN."""
    from exactextract import exact_extract
    import rasterio
    from rasterio.io import MemoryFile

    with MemoryFile(tif_bytes) as mf:
        with mf.open() as src:
            arr = read_valid_band(src, clip_negative)
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
