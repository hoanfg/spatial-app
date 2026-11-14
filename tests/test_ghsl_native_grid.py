"""Targeted GHSL source-lattice regression, not a repeat of historical V11."""
from pathlib import Path
import importlib.util

import numpy as np
import pytest
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import Affine

SPEC=importlib.util.spec_from_file_location('ghsl_native_staged',Path(__file__).parents[1]/'ntl'/'ghsl_native.py')
native=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native)

BBOX=(121.35299,31.16607,121.57693,31.33889)


def test_source_aligned_native_window():
    info={'crs':'ESRI:54009','transform':[100,0,-18041000,0,-100,9001000]}
    params=native.native_download_params(info,BBOX)
    assert params['crs']=='ESRI:54009'
    assert params['crs_transform'][2] % 100==0
    assert params['crs_transform'][5] % 100==0
    assert 0<params['dimensions'][0]*params['dimensions'][1]<3_000_000
    assert 'region' not in params and 'scale' not in params


def test_wkt_crs_fallback_and_fail_closed():
    crs=rasterio.crs.CRS.from_string('ESRI:54009').to_wkt()
    params=native.native_download_params({'wkt':crs,'transform':[100,0,-18041000,0,-100,9001000]},BBOX)
    assert params['crs']==crs
    with pytest.raises(ValueError,match='100m'):
        native.native_download_params({'crs':'ESRI:54009','transform':[200,0,0,0,-200,0]},BBOX)
    with pytest.raises(ValueError,match='CRS'):
        native.native_download_params({'transform':[100,0,0,0,-100,0]},BBOX)
    with pytest.raises(ValueError,match='too large'):
        native.native_download_params({'crs':'ESRI:54009','transform':[100,0,-18041000,0,-100,9001000]},BBOX,max_pixels=10)


def test_realistic_download_must_match_native_grid():
    info={'crs':'ESRI:54009','transform':[100,0,-18041000,0,-100,9001000]}
    params=native.native_download_params(info,BBOX)
    w,h=params['dimensions'];tr=params['crs_transform']
    transform=Affine(*tr)
    with MemoryFile() as mf:
        with mf.open(driver='GTiff',width=w,height=h,count=1,dtype='float32',
                     crs=info['crs'],transform=transform) as dst:
            dst.write(np.zeros((h,w),dtype=np.float32),1)
        raw=mf.read()
    native.validate_native_download(raw,params)
    wrong=dict(params,dimensions=[w+1,h])
    with pytest.raises(ValueError,match='dimensions'):
        native.validate_native_download(raw,wrong)


def test_real_shanghai_reference_projection_window_matches_field_export():
    """Field metadata (not raw user TIFF): SHA hashes retained in private evidence."""
    native_projection={
        'crs':'ESRI:54009',
        'transform':[100,0,11030200,0,-100,3800200],
    }
    params=native.native_download_params(native_projection,BBOX)
    assert params['dimensions']==[331,202]
    assert params['crs_transform']==[100.0,0.0,11030200.0,0.0,-100.0,3800200.0]
