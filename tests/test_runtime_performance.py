"""Focused tests for owner-visible in-app timings (no Streamlit account needed)."""
from pathlib import Path
import importlib.util
import json
import time

import pytest

SPEC=importlib.util.spec_from_file_location('profile_module', Path(__file__).parents[1]/'ntl'/'performance.py')
perf=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(perf)


def test_stage_and_export_contains_only_operational_metrics():
    rec=perf.PerformanceRecorder(sample_interval_s=0.05)
    with rec.stage('raster.fetch'):
        time.sleep(0.06)
    rec.finish_pipeline(success=True)
    result=rec.export()
    assert result['schema']=='spatial_app_perf_v1'
    assert result['pipeline_success'] is True
    assert result['pipeline_wall_time_s'] >= 0.05
    assert result['stages'][0]['wall_time_s'] >= 0.05
    assert result['stages'][0]['status']=='ok'
    assert result['sampled_process_peak_mib'] is None or result['sampled_process_peak_mib']>0
    assert 'process; not isolated per user' in result['measurement_scope']
    assert 'secret' not in json.dumps(result).lower()


def test_failure_recorded_without_sensitive_error_message():
    rec=perf.PerformanceRecorder()
    with pytest.raises(ValueError,match='secret-value'):
        with rec.stage('ghsl.fetch'):
            raise ValueError('secret-value')
    rec.finish_pipeline(success=False)
    row=rec.export()['stages'][0]
    assert rec.export()['pipeline_success'] is False
    assert row['status']=='error' and row['error_type']=='ValueError'
    assert 'secret-value' not in json.dumps(rec.export())


def test_calls_and_fallback():
    rec=perf.PerformanceRecorder()
    assert perf.measured_call(rec,'sum',sum,[1,2,3])==6
    assert rec.records[0]['stage']=='sum'
    assert perf.measured_call(None,'sum',sum,[1,2,3])==6
    with perf.profile_stage(None, 'unused'):
        pass


def test_stage_validation():
    rec=perf.PerformanceRecorder()
    with pytest.raises(ValueError):
        with rec.stage(''):
            pass
