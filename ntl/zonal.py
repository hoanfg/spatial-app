"""Trích xuất theo ô từ GeoTIFF dựng trong bộ nhớ (cần rasterio và exactextract, import khi gọi)."""
from __future__ import annotations

import os
import tempfile

import numpy as np
import pandas as pd


def zonal_stat(tif_bytes: bytes, grid_wgs, stat: str = "mean", clip_negative: bool = True,
               id_col: str = "grid_id", fill_missing: float | None = 0.0) -> pd.Series:
    """Giá trị `stat` ('mean' hoặc 'sum') của raster trên từng ô, trả Series theo thứ tự grid_wgs[id_col].

    clip_negative=True giống pipeline chính (NaN/inf -> 0, rồi cắt âm về 0). False giữ nguyên giá trị âm.
    fill_missing: giá trị thay cho ô không có kết quả; None để giữ NaN."""
    from exactextract import exact_extract
    import rasterio
    from rasterio.io import MemoryFile

    with MemoryFile(tif_bytes) as mf:
        with mf.open() as src:
            arr = src.read(1).astype("float32")
            crs, transform, h, w = src.crs, src.transform, src.height, src.width
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    if clip_negative:
        arr = np.clip(arr, 0.0, None)

    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tf:
            tmp = tf.name
        with rasterio.open(tmp, "w", driver="GTiff", height=h, width=w, count=1,
                           dtype="float32", crs=crs, transform=transform) as dst:
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
