"""Opt-in, local Streamlit runtime measurements; no server logs required.

Uses perf_counter for elapsed time. On Linux, /proc/self/status provides RSS.
RSS/HWM is PROCESS-WIDE: concurrent sessions, caching, and background tasks
can contribute. Sampling does not measure GPU memory or remote Earth Engine.
No locations, credentials, exception messages, or user data are recorded.
"""
from __future__ import annotations

from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
import json
import os
import sys
import threading
import time


def process_rss_mb() -> float | None:
    """Current resident-memory usage of the Streamlit process, if available."""
    try:
        with open('/proc/self/status', encoding='ascii') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return float(line.split()[1]) / 1024.0  # kB -> MiB
    except (OSError, ValueError, IndexError):
        pass
    # Optional dependency; no extra requirements.txt entry needed for Cloud.
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 2 ** 20
    except (ImportError, OSError, AttributeError):
        return None


class PerformanceRecorder:
    """Small, session-scoped record of a single analysis and later UI actions."""

    def __init__(self, sample_interval_s: float = 0.1):
        self.created_utc = datetime.now(timezone.utc).isoformat(timespec='seconds')
        self._interval = max(0.05, float(sample_interval_s))
        self._start = time.perf_counter()
        self.records: list[dict] = []
        self.pipeline_wall_time_s: float | None = None
        self.pipeline_success: bool | None = None

    @contextmanager
    def stage(self, label: str):
        """Measure elapsed wall time and sampled process RSS during this stage."""
        label = str(label)
        if not label or len(label) > 100:
            raise ValueError('Invalid performance stage label')
        start_t = time.perf_counter()
        start_rss = process_rss_mb()
        stop = threading.Event()
        values: list[float] = []
        if start_rss is not None:
            values.append(start_rss)

        def sample():
            while not stop.wait(self._interval):
                rss = process_rss_mb()
                if rss is not None:
                    values.append(rss)

        # Boundaries and image analysis may allocate/release memory within a stage.
        t = threading.Thread(target=sample, name='ntl-rss-sampler', daemon=True)
        t.start()
        status = 'ok'
        error_type = None
        try:
            yield
        except BaseException as exc:
            status = 'error'
            error_type = type(exc).__name__  # never store exception text
            raise
        finally:
            stop.set()
            t.join(timeout=max(0.25, self._interval * 2))
            end_rss = process_rss_mb()
            if end_rss is not None:
                values.append(end_rss)
            self.records.append({
                'stage': label,
                'wall_time_s': round(time.perf_counter() - start_t, 4),
                'rss_before_mib': round(start_rss, 3) if start_rss is not None else None,
                'rss_after_mib': round(end_rss, 3) if end_rss is not None else None,
                'rss_sampled_peak_mib': round(max(values), 3) if values else None,
                'status': status,
                'error_type': error_type,
            })

    def call(self, label, function, *args, **kwargs):
        with self.stage(label):
            return function(*args, **kwargs)

    def finish_pipeline(self, *, success: bool = True) -> None:
        """Freeze end-to-end pipeline time before subsequent UI/LISA actions."""
        if self.pipeline_wall_time_s is None:
            self.pipeline_wall_time_s = round(time.perf_counter() - self._start, 4)
            self.pipeline_success = bool(success)

    def export(self) -> dict:
        peaks = [row['rss_sampled_peak_mib'] for row in self.records if row['rss_sampled_peak_mib'] is not None]
        return {
            'schema': 'spatial_app_perf_v1',
            'created_utc': self.created_utc,
            'python_version': '.'.join(map(str, sys.version_info[:3])),
            'measurement_scope': 'Streamlit server process; not isolated per user/session',
            'memory_measurement': 'sampled RSS; may miss sub-100ms peaks; not Cloud RAM limit',
            'earth_engine_measurement': 'local download/request time only; not EE compute resource usage',
            'sample_interval_s': self._interval,
            'time_since_recorder_created_s': round(time.perf_counter() - self._start, 4),
            'measured_stage_sum_s': round(sum(r['wall_time_s'] for r in self.records), 4),
            'pipeline_wall_time_s': self.pipeline_wall_time_s,
            'pipeline_success': self.pipeline_success,
            'sampled_process_peak_mib': round(max(peaks), 3) if peaks else None,
            'stages': list(self.records),
        }


def measured_call(monitor, label, function, *args, **kwargs):
    if monitor is None:
        return function(*args, **kwargs)
    return monitor.call(label, function, *args, **kwargs)


def profile_stage(monitor, label):
    return monitor.stage(label) if monitor is not None else nullcontext()


def render_performance_panel(recorder, lang='vi'):
    """Use an expander and direct JSON/CSV downloads, not Cloud Manage app."""
    if recorder is None:
        return
    import io
    import pandas as pd
    import streamlit as st
    data = recorder.export()
    vi = lang != 'en'
    with st.expander('⏱️ Hiệu suất xử lý (không cần Cloud logs)' if vi
                     else '⏱️ Runtime performance (no Cloud logs needed)', expanded=False):
        if not data['stages']:
            st.info('Chưa có phép đo.' if vi else 'No measurements recorded yet.')
            return
        rows = pd.DataFrame(data['stages'])
        a, b, c = st.columns(3)
        a.metric('Tổng thời gian phân tích' if vi else 'Analysis wall time',
                 (f"{data['pipeline_wall_time_s']:.2f} s"
                  if data['pipeline_wall_time_s'] is not None else 'N/A'))
        b.metric('RAM đỉnh lấy mẫu (tiến trình)' if vi else 'Peak sampled process RAM',
                 (f"{data['sampled_process_peak_mib']:.1f} MiB"
                  if data['sampled_process_peak_mib'] is not None else 'N/A'))
        c.metric('Số bước được đo' if vi else 'Measured stages', len(rows))
        st.dataframe(rows, hide_index=True, width="stretch")
        st.caption(('RAM là số đo toàn tiến trình Streamlit, có thể gồm phiên khác; đỉnh được lấy mẫu '
                    'nên không nhất thiết là RAM cao nhất thực. Thời gian EE chỉ tính chờ/tải từ ứng dụng.'
                    if vi else 'RAM covers the whole Streamlit process and may include other sessions. '
                    'Sampling may miss a short peak. Earth Engine measures local wait/download only.'))
        d1, d2 = st.columns(2)
        d1.download_button('⬇️ JSON', data=json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'),
                           file_name='spatial_app_performance.json', mime='application/json',
                           key='dl_spatial_perf_json')
        d2.download_button('⬇️ CSV', data=rows.to_csv(index=False).encode('utf-8-sig'),
                           file_name='spatial_app_performance.csv', mime='text/csv',
                           key='dl_spatial_perf_csv')
