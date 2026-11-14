"""Conservative, source-grid-preserving GHSL download geometry.

GHSL built_surface / population_count are amounts PER 100m native pixel,
not densities. We must not nearest-neighbor resample into EPSG:4326 then
sum duplicated per-pixel amounts. This module computes a bounded window
on the *original* pixel lattice. The requested image must be clipped to
its geographic ROI before getDownloadURL (region ignored with CRS+transform).
"""
from __future__ import annotations

import math
from rasterio.warp import transform_bounds

SOURCE_SCALE_M = 100.0
MAX_NATIVE_PIXELS = 3_000_000


def native_download_params(projection_info: dict, bbox: tuple, max_pixels=MAX_NATIVE_PIXELS) -> dict:
    """Align a small local GHSL window exactly to the source's 100m lattice.

    Unlike a crs+scale request, the transformed pixel window shares the
    source grid's integer cell origins. Region is intentionally omitted,
    because Earth Engine ignores it when both crs and crs_transform are given.
    """
    crs = projection_info.get('crs') or projection_info.get('wkt')
    tr = projection_info.get('transform')
    if not isinstance(crs, str) or not crs.strip():
        raise ValueError('GHSL native CRS missing: cannot conserve cell amounts')
    if not isinstance(tr, (list, tuple)) or len(tr) != 6:
        raise ValueError('GHSL native affine transform missing')
    a,b,c,d,e,f = map(float,tr)
    if not (math.isclose(a,SOURCE_SCALE_M,abs_tol=1e-4) and
            math.isclose(e,-SOURCE_SCALE_M,abs_tol=1e-4) and
            abs(b)<1e-7 and abs(d)<1e-7):
        raise ValueError('GHSL is not an axis-aligned 100m source grid')
    if not isinstance(bbox,(tuple,list)) or len(bbox)!=4:
        raise ValueError('bbox must be WGS84 xmin,ymin,xmax,ymax')
    xmin,ymin,xmax,ymax = map(float,bbox)
    if not all(math.isfinite(v) for v in (xmin,ymin,xmax,ymax)) or xmin>=xmax or ymin>=ymax:
        raise ValueError('Invalid GHSL bounding box')
    x0,y0,x1,y1=transform_bounds('EPSG:4326',crs,xmin,ymin,xmax,ymax,densify_pts=41)
    col_start = math.floor((x0-c)/a)
    col_end = math.ceil((x1-c)/a)
    row_start = math.floor((f-y1)/(-e))
    row_end = math.ceil((f-y0)/(-e))
    width=col_end-col_start
    height=row_end-row_start
    if min(width,height)<=0 or width*height>max_pixels or width>10000 or height>10000:
        raise ValueError(f'GHSL requested native window too large: {width}x{height} pixels')
    out_transform = [a,0.0,c+col_start*a,0.0,e,f+row_start*e]
    return {
        'crs':crs,
        'crs_transform':out_transform,
        'dimensions':[width,height],
        'format':'GEO_TIFF',
    }


def validate_native_download(raw: bytes, params: dict) -> None:
    """Reject mismatched CRS, resolution, origin, size before zonal aggregation."""
    from rasterio.io import MemoryFile
    from rasterio.crs import CRS
    with MemoryFile(raw) as mf, mf.open() as ds:
        expected_crs=CRS.from_user_input(params['crs'])
        transform = params['crs_transform']
        if ds.count!=1 or ds.crs != expected_crs:
            raise ValueError('GHSL native download band/CRS differs from request')
        if [ds.width,ds.height] != list(params['dimensions']):
            raise ValueError('GHSL native download dimensions changed')
        aff=ds.transform
        for actual,expected in zip((aff.a,aff.b,aff.c,aff.d,aff.e,aff.f),transform):
            if not math.isclose(actual,expected,rel_tol=0,abs_tol=1e-5):
                raise ValueError('GHSL source-grid alignment changed during download')
