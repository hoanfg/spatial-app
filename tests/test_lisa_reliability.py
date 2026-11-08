"""
test_lisa_reliability.py

Bộ kiểm thử độ tin cậy cho ntl/lisa_core.py, ntl/lisa_diagnostics.py, ntl/ntl_distribution.py (T01-T19).
Chạy từ thư mục gốc repo:   pytest -q        hoặc     python tests/test_lisa_reliability.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # để `import ntl` khi chạy trực tiếp

from ntl.lisa_core import (
    DARK,
    build_queen_neighbors,
    compute_pareto_top_lights,
    compute_recentered_market_access,
    compute_spillover_rings_and_rdd,
    run_lisa,
    run_spacetime_lisa,
    zscore_lit_only,
    gini,
)

CELL = 500.0


def make_grid(nx: int, ny: int, size: float = CELL, x0: float = 500_000.0, y0: float = 2_000_000.0):
    xs = x0 + (np.arange(nx) + 0.5) * size
    ys = y0 + (np.arange(ny) + 0.5) * size
    xx, yy = np.meshgrid(xs, ys)
    cx, cy = xx.ravel(), yy.ravel()
    area = np.full(cx.size, (size / 1000.0) ** 2)
    return cx, cy, area


def _pad_area(area):
    return area


# ---------------------------------------------------------------- T01
def test_T01_fdr_impossible_combo():
    """p_floor >= alpha thì BH không thể bác bỏ gì: fdr_min_hits_needed phải == m_tests (hoặc lớn hơn)."""
    cx, cy, area = make_grid(40, 40)  # 1600 ô
    rng = np.random.default_rng(0)
    ntl = rng.gamma(2.0, 5.0, size=cx.size) + 1.0
    out = run_lisa(cx, cy, ntl, area, CELL, perms=199, alpha=0.01, fdr=True)
    rm = out.region_metrics
    assert math.isclose(rm["p_floor"], 0.01)
    m = rm["n_cells_tested"]
    assert m > 0
    # p_floor == alpha  ->  cần 100% số ô chạm sàn
    assert rm["fdr_min_hits_needed"] >= m, (
        "fdr_min_hits_needed phải >= m_tests khi p_floor >= alpha; "
        "UI nên cảnh báo/nâng perms"
    )
    # Hệ quả: không thể có ô HH nào nếu dữ liệu ngẫu nhiên
    assert rm["hh_area_share"] == 0.0


# ---------------------------------------------------------------- T02
def test_T02_all_dark():
    cx, cy, area = make_grid(25, 20)
    ntl = np.zeros(cx.size)
    out = run_lisa(cx, cy, ntl, area, CELL, perms=99)
    rm, cdf = out.region_metrics, out.cell_df
    assert rm["gini_ntl_core_all"] == 0.0
    assert rm["hh_area_share"] == 0.0
    assert math.isnan(rm["pareto_alpha_top10"])
    assert (cdf["lisa_class"] == DARK).all()


# ---------------------------------------------------------------- T03
def test_T03_constant_ntl():
    cx, cy, area = make_grid(25, 20)
    ntl = np.full(cx.size, 10.0)
    z = zscore_lit_only(ntl)
    assert np.isnan(z).all()  # sd = 0 -> NaN, không chia 0
    assert gini(ntl) == 0.0
    out = run_lisa(cx, cy, ntl, area, CELL, perms=99)
    assert out.region_metrics["hh_area_share"] == 0.0
    assert out.region_metrics["gini_ntl_core_all"] == 0.0


# ---------------------------------------------------------------- T04  (đã sửa, mục 2.3)
def test_T04_all_core_cells_are_hh_signed_dist_nan():
    cx, cy, area = make_grid(10, 10)
    n = cx.size
    is_hh = np.ones(n, dtype=bool)
    core = np.ones(n, dtype=bool)
    edge = np.zeros(n, dtype=bool)
    _, signed, _ = compute_spillover_rings_and_rdd(cx, cy, is_hh, core, edge)
    assert np.isnan(signed).all(), (
        "khi không có ô non-HH, signed_dist_hh_km phải là NaN (không phải 0.0)"
    )


# ---------------------------------------------------------------- T05  (đã sửa, mục 2.5)
def test_T05_remote_island_sparse_bbox():
    """2 cụm 100 ô cách nhau 800 km: bbox 500 m -> W*H >> 1.2e6."""
    ax, ay, _ = make_grid(10, 10)
    bx, by, _ = make_grid(10, 10, x0=500_000.0 + 800_000.0, y0=2_000_000.0 + 400_000.0)
    cx, cy = np.concatenate([ax, bx]), np.concatenate([ay, by])
    n = cx.size
    core = np.ones(n, dtype=bool)
    sol = np.full(n, 1.0)

    # Không được tràn RAM / lỗi khi dựng láng giềng
    nbr = build_queen_neighbors(cx, cy, CELL, core)
    assert nbr.shape == (n, 8)

    _, _, rec = compute_recentered_market_access(cx, cy, sol, core, CELL)
    assert np.isfinite(rec[core]).any(), (
        "nhánh W*H > 1.2e6 phải dùng fallback cKDTree, không trả toàn NaN"
    )


# ---------------------------------------------------------------- T05b
def test_T05b_kdtree_fallback_matches_grid_branch():
    """Nhánh cKDTree phải cho đúng kết quả của nhánh lưới đặc (cùng bán kính, cùng trọng số)."""
    cx, cy, _ = make_grid(20, 20)
    n = cx.size
    core = np.ones(n, dtype=bool)
    core[::17] = False  # lỗ thủng để kiểm tra mặt nạ core
    rng = np.random.default_rng(5)
    sol = rng.gamma(2.0, 3.0, n)
    grid_res = compute_recentered_market_access(cx, cy, sol, core, CELL)
    kd_res = compute_recentered_market_access(cx, cy, sol, core, CELL, dense_limit=0)  # ép dùng cKDTree
    for a, b in zip(grid_res, kd_res):
        assert np.allclose(a, b, equal_nan=True, atol=1e-9), np.nanmax(np.abs(a - b))


# ---------------------------------------------------------------- helpers cho T09
def _ks_pareto(top_k, u_thr, alpha):
    """KS của top_k/u_thr so với F(x) = 1 - x^-alpha (x >= 1). Trả (D, p xấp xỉ tiệm cận)."""
    x = np.sort(np.asarray(top_k, float) / u_thr)
    k = x.size
    F = 1.0 - x ** (-alpha)
    ecdf_hi = np.arange(1, k + 1) / k
    ecdf_lo = np.arange(0, k) / k
    D = float(max(np.max(ecdf_hi - F), np.max(F - ecdf_lo)))
    lam = (math.sqrt(k) + 0.12 + 0.11 / math.sqrt(k)) * D
    p = 2.0 * sum((-1) ** (j - 1) * math.exp(-2.0 * j * j * lam * lam) for j in range(1, 101))
    return D, float(min(1.0, max(0.0, p)))


def _tail(ntl, frac=0.10):
    v = np.sort(ntl[ntl > 0])[::-1]
    k = max(5, int(math.floor(frac * v.size)))
    return v[:k], float(v[min(k, v.size - 1)])


# ---------------------------------------------------------------- T09
def test_T09_pareto_tail_goodness_of_fit_and_se():
    """Hill: SE = alpha/sqrt(k). Đuôi Pareto thật -> KS không bác bỏ; đuôi bị chặn trên -> KS bác bỏ."""
    rng = np.random.default_rng(11)
    n, true_alpha = 4000, 2.0
    area = np.full(n, 0.25)
    core = np.ones(n, dtype=bool)

    pareto = 1.0 * (1.0 - rng.random(n)) ** (-1.0 / true_alpha)
    _, a_hat, _ = compute_pareto_top_lights(pareto, area, core, pareto > 0)
    top_k, u = _tail(pareto)
    k = top_k.size
    se = a_hat / math.sqrt(k)
    assert abs(a_hat - true_alpha) < 3.5 * se, (a_hat, se)
    _, p_ok = _ks_pareto(top_k, u, a_hat)
    assert p_ok > 0.05, p_ok

    bounded = rng.uniform(10.0, 20.0, n)  # đuôi bị chặn, không phải luật lũy thừa
    _, a_b, _ = compute_pareto_top_lights(bounded, area, core, bounded > 0)
    top_b, u_b = _tail(bounded)
    _, p_bad = _ks_pareto(top_b, u_b, a_b)
    assert p_bad < 0.05, p_bad


def test_T09b_pareto_tail_fraction_sensitivity():
    """Đuôi Pareto thật: alpha ổn định khi đổi tail_frac 5% / 10% / 15%."""
    rng = np.random.default_rng(12)
    n = 6000
    x = (1.0 - rng.random(n)) ** (-1.0 / 2.0)
    area, core = np.full(n, 0.25), np.ones(n, dtype=bool)
    alphas = [compute_pareto_top_lights(x, area, core, x > 0, tail_frac=f)[1] for f in (0.05, 0.10, 0.15)]
    assert max(alphas) - min(alphas) < 0.5, alphas


# ---------------------------------------------------------------- T10
def test_T10_monte_carlo_seed_stability():
    """5 seed khác nhau: sd(hh_area_share) <= 0.5% (nếu vượt, khuyến nghị tăng perms lên 999)."""
    nx = ny = 30
    cx, cy, area = make_grid(nx, ny)
    rng = np.random.default_rng(21)
    ntl = np.clip(rng.normal(20, 5, cx.size), 1, None)
    ix, iy = np.arange(cx.size) % nx, np.arange(cx.size) // nx
    hot = (abs(ix - 15) <= 3) & (abs(iy - 15) <= 3)
    ntl[hot] = rng.normal(45, 3, hot.sum())
    shares = [
        run_lisa(cx, cy, ntl, area, CELL, perms=499, seed=s, fdr=False).region_metrics["hh_area_share"]
        for s in (42, 101, 202, 303, 404)
    ]
    print("T10: hh_area_share =", [round(v, 4) for v in shares])
    assert max(shares) > 0.0, "test vô nghĩa nếu không phát hiện HH nào"
    assert float(np.std(shares)) <= 0.005, shares


# ---------------------------------------------------------------- T11
def _winsorize_p99(ntl):
    lit = ntl[ntl > 0]
    cap = float(np.quantile(lit, 0.99))
    return np.minimum(ntl, cap)


def _jaccard(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    u = (a | b).sum()
    return 1.0 if u == 0 else float((a & b).sum() / u)


def test_T11_winsorized_vs_raw_jaccard():
    """Cắt P99 trước z-score phải phục hồi cụm HH bị ô đốt khí che khuất; đo Jaccard raw vs winsorized."""
    nx = ny = 30
    cx, cy, area = make_grid(nx, ny)
    rng = np.random.default_rng(1)
    ntl = np.clip(rng.normal(20, 5, cx.size), 1, None)
    ix, iy = np.arange(cx.size) % nx, np.arange(cx.size) // nx
    hot = (abs(ix - 15) <= 2) & (abs(iy - 15) <= 2)
    ntl[hot] = rng.normal(40, 3, hot.sum())
    ntl[0] = 5000.0

    def hh(x):
        out = run_lisa(cx, cy, x, area, CELL, perms=499, fdr=False)
        return (out.cell_df["lisa_class"] == "High-High").to_numpy()

    h_raw, h_win = hh(ntl), hh(_winsorize_p99(ntl))
    j = _jaccard(h_raw, h_win)
    rec_raw, rec_win = (h_raw & hot).sum() / hot.sum(), (h_win & hot).sum() / hot.sum()
    print(f"T11: Jaccard(raw,win)={j:.3f}, recall raw={rec_raw:.2f}, win={rec_win:.2f}")
    assert 0.0 <= j <= 1.0
    assert rec_win >= rec_raw
    assert _jaccard(h_win, h_win) == 1.0


# ---------------------------------------------------------------- T06
def test_T06_outlier_masking():
    """Một ô cực trị 5000 làm sd phình to; log_transform phải phát hiện >= số ô HH so với bản thô."""
    nx = ny = 30
    cx, cy, area = make_grid(nx, ny)
    rng = np.random.default_rng(1)
    ntl = np.clip(rng.normal(20, 5, cx.size), 1, None)
    # đặt cụm nóng 5x5 ở giữa (35-45)
    ix = np.arange(cx.size) % nx
    iy = np.arange(cx.size) // nx
    hot = (abs(ix - 15) <= 2) & (abs(iy - 15) <= 2)
    ntl[hot] = rng.normal(40, 3, hot.sum())
    ntl[0] = 5000.0  # đốt khí

    raw = run_lisa(cx, cy, ntl, area, CELL, perms=499, fdr=False)
    log = run_lisa(cx, cy, ntl, area, CELL, perms=499, fdr=False, log_transform=True)
    n_raw = int((raw.cell_df["lisa_class"] == "High-High").sum())
    n_log = int((log.cell_df["lisa_class"] == "High-High").sum())
    print(f"T06: HH raw={n_raw}, HH log={n_log}")
    assert n_log >= n_raw


# ---------------------------------------------------------------- T07
def test_T07_recentered_ma_permutation_theorem():
    """Dưới hoán vị ngẫu nhiên SOL, E[MA_i] = expected_ma_perm  =>  E[recentered] ~ 0."""
    nx = ny = 15
    cx, cy, area = make_grid(nx, ny)
    n = cx.size
    core = np.ones(n, dtype=bool)
    rng = np.random.default_rng(7)
    sol0 = rng.gamma(2.0, 3.0, n)
    raw_acc = np.zeros(n)
    exp0 = None
    B = 1000
    for _ in range(B):
        sol = rng.permutation(sol0)
        raw, exp, _rec = compute_recentered_market_access(cx, cy, sol, core, CELL)
        raw_acc += raw
        exp0 = exp
    mean_raw = raw_acc / B
    # hội tụ Monte Carlo: sai số ~ sd/sqrt(B); dùng dung sai tương đối
    rel = np.abs(mean_raw - exp0) / np.maximum(exp0, 1e-9)
    assert rel.max() < 0.05, f"max rel err = {rel.max():.4f}"
    # recentered = raw - expected  =>  trung bình ~ 0
    assert abs(np.mean(mean_raw - exp0)) < 0.05 * np.mean(exp0)


# ---------------------------------------------------------------- T08
def test_T08_spatial_markov_invariants():
    cx, cy, area = make_grid(30, 30)
    rng = np.random.default_rng(3)
    t0 = rng.gamma(2.0, 4.0, cx.size)
    t1 = rng.gamma(2.0, 4.0, cx.size)
    res = run_spacetime_lisa(cx, cy, t0, t1, area, CELL, year_t0=2018, year_t1=2024)
    for name in ("markov_all", "markov_high_lag", "markov_low_lag"):
        mat = getattr(res, name).to_numpy()
        sums = mat.sum(axis=1)
        nonzero = sums > 0
        assert np.all(np.abs(sums[nonzero] - 100.0) <= 0.2), (name, sums)
    sh = res.metrics["shorrocks_mobility"]
    assert 0.0 <= sh <= 4.0 / 3.0 + 1e-9


# ================================================================ lisa_diagnostics
from ntl.lisa_diagnostics import (  # noqa: E402
    auto_diagnostics, cluster_primacy, dark_share, hill_diagnostics, jaccard,
    method_sensitivity, perm_power, resid_moran, seed_stability, tail_sensitivity,
    winsorize_p99,
)


def _hot_grid(seed=21, nx=30, hot_r=3, hot_mu=45.0):
    cx, cy, area = make_grid(nx, nx)
    rng = np.random.default_rng(seed)
    ntl = np.clip(rng.normal(20, 5, cx.size), 1, None)
    ix, iy = np.arange(cx.size) % nx, np.arange(cx.size) // nx
    hot = (abs(ix - nx // 2) <= hot_r) & (abs(iy - nx // 2) <= hot_r)
    ntl[hot] = rng.normal(hot_mu, 3, hot.sum())
    return cx, cy, area, ntl, hot


# ---------------------------------------------------------------- T12
def test_T12_perm_power_flags():
    bad = perm_power(1000, 199, 0.01, fdr=True)
    assert bad["infeasible"] and bad["min_hits"] == 1000 and bad["suggested_perms"] == 999
    risky = perm_power(1000, 499, 0.01, fdr=True)
    assert risky["risky"] and not risky["infeasible"]
    ok = perm_power(1000, 499, 0.05, fdr=True)
    assert not ok["infeasible"] and not ok["risky"]
    off = perm_power(1000, 199, 0.01, fdr=False)
    assert not off["applies"] and not off["infeasible"]


# ---------------------------------------------------------------- T13
def test_T13_hill_diagnostics_se_ks_and_edge_cases():
    rng = np.random.default_rng(31)
    n = 4000
    x = (1.0 - rng.random(n)) ** (-1.0 / 2.0)
    core = np.ones(n, bool)
    h = hill_diagnostics(x, core, x > 0)
    assert math.isclose(h["se"], h["alpha"] / math.sqrt(h["k"]))
    assert h["ci_lo"] < h["alpha"] < h["ci_hi"] and h["power_law_ok"] is True
    b = rng.uniform(10, 20, n)
    assert hill_diagnostics(b, core, b > 0)["power_law_ok"] is False
    # quá ít ô sáng và NTL đồng nhất: không lỗi, trả NaN
    assert np.isnan(hill_diagnostics(np.ones(10), np.ones(10, bool), np.ones(10, bool))["alpha"])
    assert np.isnan(hill_diagnostics(np.full(200, 7.0), np.ones(200, bool), np.ones(200, bool))["alpha"])
    ts = tail_sensitivity(x, core, x > 0)
    assert len(ts["rows"]) == 3 and np.isfinite(ts["spread"])


# ---------------------------------------------------------------- T14
def test_T14_cluster_primacy():
    rm = {"n_hh_clusters": 2, "largest_hh_cluster_km2": 12.2, "hh_cluster_area_share": 0.5, "area_total_km2": 48.4}
    pr = cluster_primacy(rm)
    assert math.isclose(pr["primacy"], 12.2 / 24.2) and pr["multipolar"]
    mono = cluster_primacy({"n_hh_clusters": 1, "largest_hh_cluster_km2": 5.0,
                            "hh_cluster_area_share": 0.1, "area_total_km2": 50.0})
    assert math.isclose(mono["primacy"], 1.0) and not mono["multipolar"]
    none = cluster_primacy({"n_hh_clusters": 0, "largest_hh_cluster_km2": 0.0,
                            "hh_cluster_area_share": 0.0, "area_total_km2": 50.0})
    assert np.isnan(none["primacy"]) and not none["multipolar"]


# ---------------------------------------------------------------- T15
def test_T15_resid_moran_detects_spatial_structure():
    nx = 30
    cx, cy, area = make_grid(nx, nx)
    dist = np.hypot(cx - cx.mean(), cy - cy.mean()) / 1000.0
    edge = np.zeros(cx.size, bool)
    rng = np.random.default_rng(2)
    white = np.expm1(3.0 - 0.2 * dist + rng.normal(0, 0.15, cx.size))  # đúng mô hình ln(1+NTL) = a - g*d + nhiễu trắng
    r_w = resid_moran(cx, cy, white, area, dist, edge, CELL)
    assert r_w["perm_done"] and abs(r_w["I"]) < 0.15 and not r_w["flag"], r_w
    # phần dư có cấu trúc không gian (sóng sin ngang) mà độ dốc theo khoảng cách không bắt được
    wave = np.clip(20 + 8 * np.sin(cx / 1500.0), 0.1, None)
    r_s = resid_moran(cx, cy, wave, area, dist, edge, CELL)
    assert r_s["I"] > 0.5 and r_s["flag"], r_s
    # quá ít ô: trả NaN, không lỗi
    assert np.isnan(resid_moran(cx[:10], cy[:10], white[:10], area[:10], dist[:10], edge[:10], CELL)["I"])


# ---------------------------------------------------------------- T16
def test_T16_auto_diagnostics_end_to_end_and_degenerate():
    cx, cy, area, ntl, _ = _hot_grid()
    out = run_lisa(cx, cy, ntl, area, CELL, perms=199, alpha=0.05, fdr=True)
    d = auto_diagnostics(cx, cy, ntl, area, CELL, out.cell_df, out.region_metrics, 199, 0.05, True)
    assert {it["key"] for it in d["items"]} == {"perm", "hill", "primacy", "resid", "dark"}
    assert all(np.isfinite(v) or isinstance(v, (int, float)) for v in d["export"].values())
    # toàn ô tối: không văng lỗi, cờ dark_share bật
    z = np.zeros(cx.size)
    out0 = run_lisa(cx, cy, z, area, CELL, perms=99)
    d0 = auto_diagnostics(cx, cy, z, area, CELL, out0.cell_df, out0.region_metrics, 99, 0.05, True)
    assert dict((it["key"], it["level"]) for it in d0["items"])["dark"] == "warn"
    assert dark_share(z, np.zeros(z.size, bool))["share"] == 1.0


# ---------------------------------------------------------------- T17
def test_T17_seed_stability_and_method_sensitivity_helpers():
    cx, cy, area, ntl, hot = _hot_grid(hot_r=2, hot_mu=40.0)
    ntl = ntl.copy()
    ntl[0] = 5000.0
    kw = dict(cx=cx, cy=cy, ntl=ntl, area_km2=area, cell_size_m=CELL, perms=199, fdr=False)
    ss = seed_stability(kw, seeds=(42, 101, 202))
    assert len(ss["shares"]) == 3 and ss["sd"] >= 0.0 and max(ss["shares"]) > 0
    base = run_lisa(**kw)
    base_hh = (base.cell_df["lisa_class"] == "High-High").to_numpy()
    ms = method_sensitivity(kw, base_hh, base_log=False)
    assert ms["n_hh"]["raw"] == int(base_hh.sum())           # tái dùng kết quả gốc
    for key in ("jaccard_raw_winsor", "jaccard_raw_log", "jaccard_winsor_log"):
        assert 0.0 <= ms[key] <= 1.0
    w = winsorize_p99(ntl)
    assert w.max() < 5000.0 and w[0] == w.max()
    assert jaccard(base_hh, base_hh) == 1.0 and jaccard(np.zeros(3, bool), np.zeros(3, bool)) == 1.0


# ---------------------------------------------------------------- T18
def test_T18_extensive_intensive_margins():
    cx, cy, area = make_grid(20, 20)
    n = cx.size
    rng = np.random.default_rng(9)
    t0 = rng.gamma(2.0, 4.0, n) + 1.0
    t1 = t0 * 1.5
    t0[:40] = 0.0       # 40 ô tối ở t0 ...
    t1[:40] = 0.0
    t1[:10] = 5.0       # ... 10 ô trong số đó sáng lên ở t1 (entry), 30 ô còn lại tối cả hai kỳ
    t1[40:50] = 0.0     # 10 ô sáng ở t0 tắt ở t1 (exit)
    r = run_spacetime_lisa(cx, cy, t0, t1, area, CELL, year_t0=2018, year_t1=2024)
    m = r.metrics
    assert math.isclose(m["extensive_entry_pct"], 10 / 40 * 100, abs_tol=0.01)
    assert math.isclose(m["extensive_exit_pct"], 10 / (n - 40) * 100, abs_tol=0.01)
    both = (t0 > 0) & (t1 > 0)
    assert m["n_both_lit"] == int(both.sum())
    assert math.isclose(m["intensive_mean_dln_ntl"], float(np.mean(np.log(t1[both]) - np.log(t0[both]))), abs_tol=1e-3)
    assert set(r.st_cell_df["margin_type"]) >= {"extensive_entry", "extensive_exit", "intensive"}


# ---------------------------------------------------------------- T19  (biểu đồ phân phối tab Dữ liệu)
def test_T19_distribution_charts_data():
    from ntl.ntl_distribution import hist_share_df, lorenz_df, radial_df, ranksize_df

    rng = np.random.default_rng(5)
    n = 900
    cx, cy, area = make_grid(30, 30)
    ntl = rng.gamma(1.5, 4.0, n)
    ntl[:60] = 0.0
    sol_cell = ntl * area

    # Lorenz: khớp gini() của app, đơn điệu, đi từ (0,0) tới (1,1), nằm dưới đường chéo
    lz, g = lorenz_df(sol_cell)
    assert math.isclose(g, gini(sol_cell), abs_tol=1e-9)
    assert lz["cum_cells"].iloc[0] == 0 and lz["cum_sol"].iloc[0] == 0
    assert math.isclose(lz["cum_cells"].iloc[-1], 1.0) and math.isclose(lz["cum_sol"].iloc[-1], 1.0)
    assert (np.diff(lz["cum_sol"]) >= -1e-12).all() and (lz["cum_sol"] <= lz["cum_cells"] + 1e-12).all()
    lz0, g0 = lorenz_df(np.zeros(10))
    assert g0 == 0.0 and len(lz0) == 2
    big, _ = lorenz_df(rng.gamma(2, 3, 200_000))
    assert len(big) <= 410  # thưa hóa: nhẹ cho lưới lớn

    # Rank-size: chuỗi Pareto thuần phải cho alpha gần đúng và đường fit đi qua đầu bảng
    core = np.ones(n, bool)
    pareto = (1.0 - rng.random(n)) ** (-1.0 / 2.5) * 3.0
    pts, fit, info = ranksize_df(pareto, core)
    assert info is not None and 1.5 < info["alpha"] < 4.0
    assert pts["rank"].iloc[0] == 1 and pts["ntl"].iloc[0] == pareto.max()
    assert len(fit) == info["k"] and fit["fit"].is_monotonic_decreasing
    _, _, none_info = ranksize_df(np.array([1.0] * 10), np.ones(10, bool))
    assert none_info is None  # < 15 ô sáng
    _, _, tied = ranksize_df(np.full(100, 7.0), np.ones(100, bool))
    assert tied is None  # đuôi đồng hạng: không ước lượng
    e, _, _ = ranksize_df(np.zeros(50), np.ones(50, bool))
    assert len(e) == 0

    # Radial: tâm = ô sáng nhất; vòng đầu chứa ô đó; suy giảm khi cách xa tâm
    d = np.hypot(cx - cx[435], cy - cy[435]) / 1000.0
    syn = 50.0 * np.exp(-d)
    rd = radial_df(cx, cy, syn, area, width_km=1.0)
    assert rd["cells"].sum() == syn.size
    assert rd["mean_ntl"].iloc[0] > rd["mean_ntl"].iloc[1] > rd["mean_ntl"].iloc[2]
    assert len(radial_df(np.array([]), np.array([]), np.array([]), np.array([]))) == 0

    # Histogram % ô và % SOL: mỗi chuỗi cộng đúng 100
    edges = [-0.001, 0, 1, 2, 5, 10, 15, 25, 40, 80, np.inf]
    labels = ["0", "0-1", "1-2", "2-5", "5-10", "10-15", "15-25", "25-40", "40-80", "80+"]
    h = hist_share_df(ntl, area, edges, labels)
    for ser in ("cells", "sol"):
        assert math.isclose(h.loc[h.series == ser, "pct"].sum(), 100.0, abs_tol=1e-6)
    assert h.loc[(h.series == "cells") & (h.bin == "0"), "pct"].iloc[0] == 60 / n * 100
    assert h.loc[(h.series == "sol") & (h.bin == "0"), "pct"].iloc[0] == 0.0


# ---------------------------------------------------------------- T20  (hiển thị p-value chạm mức sàn)
def test_T20_fmt_p_floor():
    from ntl.formatting import fmt_p

    assert fmt_p(0.005, 199) == "≤ 0.005"            # 1/(199+1): chạm sàn, không phải p chính xác
    assert fmt_p(0.005, 199, prefix=True) == "p ≤ 0.005"
    assert fmt_p(0.012, 199, prefix=True) == "p = 0.012"
    assert fmt_p(0.01, 99) == "≤ 0.010"
    assert fmt_p(0.2, None) == "0.200"
    assert fmt_p(float("nan"), 99) == "N/A"
    # p đo từ run thật phải khớp quy tắc: p >= 1/(R+1)
    rng = np.random.default_rng(0)
    assert fmt_p(1.0 / 500, 499) == "≤ 0.002"
    assert fmt_p(2.0 / 500, 499).startswith("0.004")


if __name__ == "__main__":
    import traceback

    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_T")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except Exception:  # noqa: BLE001
            failed += 1
            print(f"FAIL  {name}")
            traceback.print_exc(limit=2)
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    raise SystemExit(1 if failed else 0)
