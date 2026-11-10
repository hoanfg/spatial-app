"""Kiểm thử cho các module chất lượng dữ liệu, độ vững và kiểm chứng ngoài (T21-T28)."""
from __future__ import annotations

import io
import math
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ntl import data_quality as dq  # noqa: E402
from ntl import ee_extra, robustness as rob, validation as val  # noqa: E402
from ntl.lisa_core import build_queen_neighbors, run_lisa  # noqa: E402

CELL = 500.0


def make_grid(nx, ny, size=CELL, x0=500_000.0, y0=2_000_000.0):
    xs = x0 + (np.arange(nx) + 0.5) * size
    ys = y0 + (np.arange(ny) + 0.5) * size
    xx, yy = np.meshgrid(xs, ys)
    return xx.ravel(), yy.ravel(), np.full(xx.size, (size / 1000.0) ** 2)


def hot_field(nx=30, ny=30, seed=0, centre=(15, 15), radius=4.0, noise=0.4):
    """Nền thấp có nhiễu, một cụm sáng tròn ở giữa: LISA phải tìm ra cụm này một cách ổn định."""
    cx, cy, area = make_grid(nx, ny)
    ix, iy = np.arange(cx.size) % nx, np.arange(cx.size) // nx
    d = np.hypot(ix - centre[0], iy - centre[1])
    rng = np.random.default_rng(seed)
    ntl = np.clip(2.0 + 40.0 * np.exp(-(d / radius) ** 2) + rng.normal(0, noise, cx.size), 0.05, None)
    return cx, cy, ntl, area


def base_kwargs(cx, cy, ntl, area, **over):
    kw = dict(cx=cx, cy=cy, ntl=ntl, area_km2=area, cell_size_m=CELL, lit_threshold=0.0, edge_tol=0.99,
              perms=999, alpha=0.05, fdr=True, log_transform=False, min_neighbors=1, min_cluster_cells=4)
    kw.update(over)
    return kw


# T21 ---------------------------------------------------------------------------------------
def test_T21_rook_weights():
    cx, cy, ntl, area = hot_field()
    kw = base_kwargs(cx, cy, ntl, area)
    q = run_lisa(**kw)
    assert run_lisa(**kw, weights="queen").cell_df.equals(q.cell_df)  # mặc định không đổi
    r = run_lisa(**kw, weights="rook")
    hh_q = (q.cell_df["lisa_class"] == "High-High").sum()
    hh_r = (r.cell_df["lisa_class"] == "High-High").sum()
    assert hh_q >= 30 and hh_r >= 30
    # Rook chỉ giữ 4 láng giềng chung cạnh
    members = np.ones(cx.size, bool)
    nbr = build_queen_neighbors(cx, cy, CELL, members)
    from ntl.lisa_core import ROOK_DROP_COLS
    kept = np.setdiff1d(np.arange(8), ROOK_DROP_COLS)
    ix = np.floor(cx / CELL).astype(int)
    iy = np.floor(cy / CELL).astype(int)
    interior = np.flatnonzero(nbr.min(axis=1) >= 0)
    for i in interior[:50]:
        for c in kept:   # láng giềng giữ lại phải chung cạnh: lệch đúng một ô theo một trục
            j = nbr[i, c]
            assert abs(ix[j] - ix[i]) + abs(iy[j] - iy[i]) == 1
        for c in ROOK_DROP_COLS:  # láng giềng bị bỏ là ô chéo
            j = nbr[i, c]
            assert abs(ix[j] - ix[i]) == 1 and abs(iy[j] - iy[i]) == 1
    with pytest.raises(ValueError):
        run_lisa(**kw, weights="bishop")


# T22 ---------------------------------------------------------------------------------------
def test_T22_data_quality_report():
    arr = np.array([[1.0, -0.5, np.nan], [0.0, 2.0, np.inf], [-1.0, 0.0, 3.0]])
    r = dq.raster_report(arr)
    assert r["n_pixels"] == 9
    assert math.isclose(r["nodata_share"], 2 / 9)
    assert math.isclose(r["neg_share"], 2 / 7)       # chia cho pixel hữu hạn
    assert math.isclose(r["zero_share"], 2 / 7)
    assert r["min"] == -1.0 and r["max"] == 3.0
    assert dq.raster_report(np.array([]))["n_pixels"] == 0

    c = dq.cell_report(100, 3, 2, np.r_[np.zeros(60), np.ones(40)])
    assert c["cells_missing_stats"] == 5 and math.isclose(c["zero_cell_share"], 0.6)

    o = dq.obs_report(np.array([0, 0, 1, 2, 3, 12, 12, 12, 12, 12]))
    assert math.isclose(o["no_obs_share"], 0.2) and math.isclose(o["low_obs_share"], 0.4)
    assert o["median_months"] == 12.0 or o["median_months"] == 7.5  # trung vị của dãy trên

    flags = {f["key"]: f["level"] for f in dq.quality_flags(r, c, o)}
    assert flags["nodata"] == "warn" and flags["neg"] == "warn" and flags["missing"] == "warn"
    assert flags["zero"] == "info" and flags["obs"] == "warn"
    clean = {f["level"] for f in dq.quality_flags(dq.raster_report(np.ones((4, 4))),
                                                  dq.cell_report(10, 0, 0, np.ones(10)))}
    assert clean == {"ok"}

    exp = dq.quality_export(r, c, o)
    assert exp["ntl_nodata_handling"] == "unmask_to_0"
    assert exp["dq_cells_missing_stats"] == 5 and "dq_no_obs_pixel_share" in exp


# T23 ---------------------------------------------------------------------------------------
def test_T23_aggregate_blocks_and_maup():
    cx, cy, area = make_grid(4, 4)
    ntl = np.arange(16, dtype=float)
    agg = rob.aggregate_blocks(cx, cy, ntl, area, CELL, 2)
    assert len(agg["ntl"]) == 4 and agg["cell_size_m"] == 1000.0
    assert np.allclose(agg["area_km2"], 4 * 0.25)
    # ô lớn đầu tiên gồm các ô 0, 1, 4, 5
    first = agg["ntl"][0]
    assert math.isclose(first, np.mean([0, 1, 4, 5]))
    assert math.isclose(float((agg["ntl"] * agg["area_km2"]).sum()), float((ntl * area).sum()))  # bảo toàn tổng SOL

    # khối bị khuyết ô (ô biên) có diện tích nhỏ hơn đầy đủ
    keep = np.ones(16, bool)
    keep[5] = False
    part = rob.aggregate_blocks(cx[keep], cy[keep], ntl[keep], area[keep], CELL, 2)
    assert part["area_km2"].min() < 1.0

    cx, cy, ntl, area = hot_field(40, 40, centre=(20, 20), radius=5.0)
    kw = base_kwargs(cx, cy, ntl, area)
    base_hh = rob.hh_mask(run_lisa(**kw))
    assert base_hh.sum() >= 30
    m = rob.maup_compare(kw, base_hh, 2)
    assert m["n_hh_fine"] > 0 and m["n_hh_coarse"] > 0
    assert 0.0 <= m["fine_inside_coarse"] <= 1.0 and 0.0 <= m["coarse_covered_by_fine"] <= 1.0
    assert m["fine_inside_coarse"] > 0.5   # cụm rõ ràng phải trùng nhau giữa hai độ phân giải


# T24 ---------------------------------------------------------------------------------------
def test_T24_run_specs_and_summary():
    cx, cy, ntl, area = hot_field()
    kw = base_kwargs(cx, cy, ntl, area)
    base_hh = rob.hh_mask(run_lisa(**kw))
    assert base_hh.sum() >= 30     # không rỗng, nếu không Jaccard = 1 một cách vô nghĩa
    specs = rob.default_specs(kw)
    assert {s["group"] for s in specs} >= {"weights", "threshold", "transform", "inference"}
    table, mat = rob.run_specs(kw, specs, base_hh)
    assert mat.shape == (cx.size, len(specs) + 1) and len(table) == len(specs) + 1
    assert table.loc[0, "Jaccard"] == 1.0 and table.loc[0, "Nhóm"] == "base"
    assert ((table["Jaccard"] >= 0) & (table["Jaccard"] <= 1)).all()
    s = rob.summarize(table, mat, area)
    assert s["n_specs"] == len(specs) and s["min_jaccard"] <= s["median_jaccard"]
    assert 0.0 <= s["robust_core_share"] <= base_hh.sum() * area[0] / area.sum() + 1e-12
    assert s["median_jaccard"] >= rob.STABLE_JACCARD and s["verdict"] == "vững"  # cụm rõ ràng nên phải vững

    # biến thể không đổi gì thì Jaccard đúng bằng 1 và lõi vững = toàn bộ HH
    same, mat2 = rob.run_specs(kw, [{"name": "y hệt", "group": "x", "overrides": {}}], base_hh)
    assert same.loc[1, "Jaccard"] == 1.0
    s2 = rob.summarize(same, mat2, area)
    assert math.isclose(s2["robust_core_share"], base_hh.sum() * area[0] / area.sum())

    # nhiễu thuần: kết quả phải bị đánh giá yếu hơn cụm rõ ràng
    rng = np.random.default_rng(3)
    noise = rng.gamma(2.0, 3.0, cx.size) + 1.0
    kn = base_kwargs(cx, cy, noise, area, fdr=False)
    hh_n = rob.hh_mask(run_lisa(**kn))
    assert hh_n.sum() > 0
    tn, mn = rob.run_specs(kn, rob.default_specs(kn), hh_n)
    assert rob.summarize(tn, mn, area)["median_jaccard"] < s["median_jaccard"]

    # kết quả gốc rỗng thì không có gì để kiểm tra độ vững: không được báo "vững"
    empty = np.zeros(cx.size, bool)
    te, me = rob.run_specs(kw, specs[:1], empty)
    assert rob.summarize(te, me, area)["verdict"] == "không có HH"
    assert rob.summarize(table.iloc[:1], mat[:, :1], area)["verdict"] == "n/a"
    assert rob.work_units(100, 199, 9) == 100 * 8 * 199 * 10


def test_T24b_asinh_and_log_do_not_stack():
    cx, cy, ntl, area = hot_field()
    kw = base_kwargs(cx, cy, ntl, area, log_transform=True)
    names = {s["name"]: s for s in rob.default_specs(kw)}
    assert names["asinh(NTL)"]["overrides"]["log_transform"] is False
    assert names["Cắt P99 trước z-score"]["overrides"]["log_transform"] is False
    assert "Thô (không ln)" in names and names["Thô (không ln)"]["overrides"]["log_transform"] is False


# T25 ---------------------------------------------------------------------------------------
def test_T25_adjacent_years():
    cx, cy, ntl, area = hot_field()
    kw = base_kwargs(cx, cy, ntl, area)
    base_hh = rob.hh_mask(run_lisa(**kw))
    assert base_hh.sum() >= 30
    moved = np.roll(ntl.reshape(30, 30), 8, axis=1).ravel()   # cụm dịch sang phải 8 ô
    t = rob.adjacent_years(kw, base_hh, {2023: ntl.copy(), 2025: moved})
    assert list(t["Năm"]) == [2023, 2025]
    assert t.loc[0, "Jaccard so với năm gốc"] == 1.0
    assert t.loc[1, "Jaccard so với năm gốc"] < 0.3
    exp = rob.export_columns({}, None, t)
    assert math.isclose(exp["rob_adjacent_year_min_jaccard"], round(float(t.iloc[1, 3]), 4))


# T26 ---------------------------------------------------------------------------------------
def test_T26_validation_statistics():
    x = np.arange(100, dtype=float)
    assert math.isclose(val.spearman(x, x ** 3), 1.0)
    assert math.isclose(val.spearman(x, -x), -1.0)
    assert math.isnan(val.spearman(np.ones(10), np.arange(10)))
    assert math.isnan(val.spearman([1, 2], [1, 2]))

    proxy = np.r_[np.zeros(75), np.arange(1, 26)]
    ntl_sep = np.r_[np.zeros(75), 10 + np.arange(25)]
    assert math.isclose(val.auc_top_quartile(ntl_sep, proxy), 1.0)
    rng = np.random.default_rng(0)
    assert abs(val.auc_top_quartile(rng.normal(size=4000), rng.normal(size=4000)) - 0.5) < 0.05

    cx, cy, area = make_grid(30, 30)
    n = cx.size
    ntl = rng.gamma(2.0, 3.0, n)
    strong = val.proxy_agreement(ntl, area * (ntl ** 1.2) * rng.lognormal(0, 0.2, n), area, cx, cy, CELL, b=100)
    assert strong["rho"] > 0.8 and strong["level"] == "mạnh" and strong["ci_lo"] < strong["rho"] < strong["ci_hi"]
    weak = val.proxy_agreement(ntl, area * rng.gamma(2.0, 3.0, n), area, cx, cy, CELL, b=100)
    assert abs(weak["rho"]) < 0.2 and weak["level"] == "yếu"
    small = val.proxy_agreement(ntl[:10], ntl[:10], area[:10], cx[:10], cy[:10], CELL)
    assert small["level"] == "n/a" and small["n"] == 10 and val.export_columns(small, "built") == {}
    core = np.zeros(n, bool)
    core[:200] = True
    assert val.proxy_agreement(ntl, ntl, area, cx, cy, CELL, core=core, b=50)["n"] == 200
    ex = val.export_columns(strong, "pop")
    assert set(ex) == {"val_rho_pop", "val_rho_pop_ci_lo", "val_rho_pop_ci_hi", "val_auc_pop"}

    same = val.compare_clipping(ntl, ntl)
    assert same["rho"] == 1.0 and same["share_changed"] == 0.0 and same["max_abs_diff"] == 0.0
    noclip = ntl.copy()
    noclip[:90] = -0.3    # 90 ô bị cắt về 0 trong bản cắt
    clipped = np.clip(noclip, 0, None)
    cmp_ = val.compare_clipping(clipped, noclip)
    assert math.isclose(cmp_["share_changed"], 90 / n) and math.isclose(cmp_["max_abs_diff"], 0.3)


# T27 ---------------------------------------------------------------------------------------
def test_T27_ee_extra_pure_helpers():
    assert ee_extra.nearest_epoch(2025) == 2020 and ee_extra.nearest_epoch(2018) == 2020
    assert ee_extra.nearest_epoch(2012) == 2010 and ee_extra.nearest_epoch(1960) == 1975
    assert ee_extra.nearest_epoch(2030, last_observed=2025) == 2025
    px = ee_extra.estimate_pixels((16.50, 47.82, 16.56, 47.87), 100.0)
    assert 2e3 < px < 3e3          # khoảng 4.5 km x 5.5 km ở 100 m, tức ~45 x 55 pixel
    assert ee_extra.estimate_pixels((10, 10, 12, 12), 100.0) > ee_extra.MAX_PIXELS

    tif = b"II*\x00" + b"\x00" * 20
    assert ee_extra.extract_tif_bytes(tif) == tif
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("a.download.tif", tif)
    assert ee_extra.extract_tif_bytes(buf.getvalue()) == tif
    with pytest.raises(ValueError):
        ee_extra.extract_tif_bytes(b"<html>error</html>")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("readme.txt", "x")
    with pytest.raises(ValueError):
        ee_extra.extract_tif_bytes(buf.getvalue())

    with pytest.raises(ValueError):   # vùng quá lớn bị chặn trước khi gọi Earth Engine
        ee_extra.fetch_ghsl_raster(object(), "built", (10, 10, 12, 12), 2020)
    with pytest.raises(ValueError):
        ee_extra.fetch_ghsl_raster(object(), "gdp", (16.5, 47.8, 16.6, 47.9), 2020)
    with pytest.raises(ValueError):
        ee_extra.fetch_ntl_variant(MagicMock(), "X", (0, 0, 1, 1), 2020, 463.83, reducer="max")


def test_T27b_ee_extra_builds_expected_calls(monkeypatch):
    monkeypatch.setattr(ee_extra, "_download", lambda img, roi, scale, timeout=180: b"II*\x00")
    ee = MagicMock()
    img = MagicMock()
    col = ee.ImageCollection.return_value.filterDate.return_value.filterBounds.return_value
    col.size.return_value.getInfo.return_value = 12
    col.map.side_effect = lambda f: (f(img), col.map.return_value)[1]
    out = ee_extra.fetch_ntl_variant(ee, "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG", (16.5, 47.8, 16.6, 47.9),
                                     2025, 463.83, cf_min=3, reducer="mean")
    assert out == b"II*\x00"
    img.select.return_value.gte.assert_called_with(3)          # ngưỡng cf_cvg được truyền vào
    col.map.return_value.mean.assert_called_once()
    col.map.return_value.median.assert_not_called()
    ee_extra.fetch_obs_count_raster(ee, "X", (16.5, 47.8, 16.6, 47.9), 2025, 463.83)
    col.map.return_value.count.assert_called_once()

    col.size.return_value.getInfo.return_value = 0
    with pytest.raises(LookupError):
        ee_extra.fetch_ntl_variant(ee, "X", (16.5, 47.8, 16.6, 47.9), 2025, 463.83)

    ee2 = MagicMock()
    ghsl_col = ee2.ImageCollection.return_value.filter.return_value
    ghsl_col.size.return_value.getInfo.return_value = 1
    data, epoch = ee_extra.fetch_ghsl_raster(ee2, "pop", (16.5, 47.8, 16.6, 47.9), 2025)
    assert data == b"II*\x00" and epoch == 2020
    ee2.ImageCollection.assert_called_with("JRC/GHSL/P2023A/GHS_POP")
    ee2.Filter.calendarRange.assert_called_with(2020, 2020, "year")


def test_T28_pandas_roundtrip_of_export_columns():
    """Các cột export ghép được thành một dòng panel mà không trùng khóa."""
    cx, cy, ntl, area = hot_field()
    kw = base_kwargs(cx, cy, ntl, area)
    base_hh = rob.hh_mask(run_lisa(**kw))
    table, mat = rob.run_specs(kw, rob.default_specs(kw)[:2], base_hh)
    summ = rob.summarize(table, mat, area)
    row = {}
    for part in (dq.quality_export(dq.raster_report(ntl), dq.cell_report(len(ntl), 0, 0, ntl)),
                 rob.export_columns(summ), val.export_columns({"n": 50, "rho": 0.7, "ci_lo": 0.6, "ci_hi": 0.8, "auc": 0.8}, "built")):
        assert not set(part) & set(row)
        row.update(part)
    assert pd.DataFrame([row]).shape[0] == 1 and "rob_median_jaccard" in row and "val_rho_built" in row
