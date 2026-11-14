"""Focused field regression for the real CSV symptom (not a new NTL test suite)."""
import importlib.util
from pathlib import Path
import sys
import types

import numpy as np
import pandas as pd
import pytest
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

MODULE_PATH = Path(__file__).resolve().parents[1] / 'ntl' / 'semantics.py'
spec = importlib.util.spec_from_file_location('staged_a02_semantics', MODULE_PATH)
sem = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sem)


def make_tif(named=False, count=6, monthly_count=12, corrupt=False):
    # 3 valid physical pixels: no observation, measured zero, observed negative
    values = np.array([
        [0, 0, -2], # historical NTL before clipping
        [0, 1, 1],  # observed
        [0, 0, 1],  # negative
        [0, 1, 0],  # zero
        [0, monthly_count, 10],
        [1, 0, 0],
    ], dtype='float32').reshape(6, 1, 3)
    if corrupt:
        values[1, 0, 1] = 0  # 12 valid months but observed=0
    with MemoryFile() as mf:
        with mf.open(driver='GTiff',width=3,height=1,count=count,dtype='float32',
                     crs='EPSG:4326', transform=from_origin(100,30,.004,.004)) as dst:
            dst.write(values[:count])
            if named:
                for i, name in enumerate(('avg_rad',)+sem.QUALITY_BANDS[:count-1],start=1):
                    dst.set_band_description(i,name)
        return mf.read()


def test_six_band_labeled_is_accepted():
    assert sem.quality_raster_schema(make_tif(named=True))['status'] == 'named'


def test_real_world_unlabeled_with_known_producer_is_accepted():
    info = sem.quality_raster_schema(make_tif(),trusted_producer=True)
    assert info['supported'] and info['status']=='validated_producer_order'


def test_unlabeled_untrusted_fails_closed():
    info = sem.quality_raster_schema(make_tif())
    assert not info['supported'] and info['status']=='unlabeled_untrusted'


def test_wrong_band_count_fails_closed():
    info = sem.quality_raster_schema(make_tif(count=1), trusted_producer=True)
    assert not info['supported'] and info['status']=='wrong_band_count'


def test_conflicting_descriptions_fail_even_with_trusted_producer():
    raw=make_tif(named=True)
    with MemoryFile(raw) as mf, mf.open() as ds:
        profile=ds.profile;arr=ds.read(); descriptions=list(ds.descriptions)
    with MemoryFile() as mf:
        with mf.open(**profile) as dst:
            dst.write(arr)
            descriptions[3]='unexpected_data'
            for i,name in enumerate(descriptions,start=1): dst.set_band_description(i,name)
        raw=mf.read()
    info=sem.quality_raster_schema(raw,trusted_producer=True)
    assert not info['supported'] and info['status']=='conflicting_band_descriptions'


def test_nonintegral_month_count_rejected():
    assert sem.quality_raster_schema(make_tif(monthly_count=3.2),trusted_producer=True)['status']=='invalid_unlabeled_values'


def test_incoherent_observation_rejected():
    assert sem.quality_raster_schema(make_tif(corrupt=True),trusted_producer=True)['status']=='invalid_unlabeled_values'


def test_cell_quality_status_no_forced_unknown(monkeypatch):
    # Fake only zonal reducer; validates band contract and metadata behavior,
    # not a second test of exactextract or previously validated NTL sums.
    import rasterio
    fake=types.ModuleType('ntl.zonal')
    def zonal(raw, grid, *, band, clip_negative, fill_missing):
        with MemoryFile(raw) as mf, mf.open() as ds:
            vals=ds.read(band).ravel()
        return pd.Series(vals)
    fake.zonal_stat=zonal
    monkeypatch.setitem(sys.modules,'ntl.zonal',fake)
    grid=pd.DataFrame({'grid_id':[0,1,2]})
    good=sem.cell_quality(make_tif(), grid, trusted_producer=True)
    assert good.dq_status.tolist()==['no_observation','observed','observed']
    assert good.dq_mean_valid_months.tolist()==[0,12,10]
    assert good.dq_negative_fraction.tolist()==[0,0,1]
    assert good.attrs['quality_raster_schema']['status']=='validated_producer_order'
    unknown=sem.cell_quality(make_tif(),grid)
    assert unknown.dq_status.eq('unknown').all()
