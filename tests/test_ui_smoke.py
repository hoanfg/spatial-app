"""
Kiểm thử khói giao diện LISA bằng streamlit.testing.v1.AppTest, với dữ liệu tổng hợp (không cần Earth Engine).

Mục đích: bắt lỗi giao diện (KeyError, import, sai khóa dữ liệu) ngay trên CI trước khi lên Streamlit Cloud.
Test tự bỏ qua nếu thiếu streamlit/geopandas. Lần đầu có thể cần chỉnh cho khớp phiên bản Streamlit của bạn.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

pytest.importorskip("streamlit")
pytest.importorskip("geopandas")
pytest.importorskip("folium")
pytest.importorskip("streamlit_folium")
pytest.importorskip("altair")

from streamlit.testing.v1 import AppTest  # noqa: E402


def _app():
    """Chạy render_lisa_tab trên lưới 20x20 ô 500 m có cụm sáng ở giữa."""
    import geopandas as gpd
    import numpy as np
    import pandas as pd
    from shapely.geometry import box

    from ntl.lisa_ui import render_lisa_tab

    size, nx = 500.0, 20
    rng = np.random.default_rng(0)
    polys, ntl = [], []
    for j in range(nx):
        for i in range(nx):
            x0, y0 = 500_000.0 + i * size, 5_300_000.0 + j * size
            polys.append(box(x0, y0, x0 + size, y0 + size))
            d = np.hypot(i - 10, j - 10)
            ntl.append(max(0.1, 30.0 * np.exp(-d / 3.0) + rng.normal(0, 0.5)))
    grid = gpd.GeoDataFrame(
        {"grid_id": np.arange(1, len(polys) + 1), "ntl_mean": ntl, "area_km2": 0.25},
        geometry=polys, crs=32633,
    )
    export_df = pd.DataFrame({"grid_id": grid["grid_id"], "ntl_mean": grid["ntl_mean"]})
    boundary = gpd.GeoDataFrame(geometry=[grid.unary_union.convex_hull], crs=32633).to_crs(4326)
    res = {"size": 500, "year": 2025, "ts": "test", "iso3": "AUT", "boundary_wgs": boundary}
    render_lisa_tab(res=res, grid_utm=grid, export_df=export_df, lang="vi", region_id="AUT_test",
                    region_label="Test", render_cap=30_000, basemap="CartoDB dark_matter",
                    fetch_year_ntl_fn=None, available_years=[2014, 2025])


def test_lisa_tab_renders_without_exception():
    at = AppTest.from_function(_app, default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]


def test_lisa_diagnostics_panel_present():
    at = AppTest.from_function(_app, default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]
    labels = [e.label for e in at.expander]
    assert any("Kiểm định độ tin cậy" in str(x) for x in labels), labels
