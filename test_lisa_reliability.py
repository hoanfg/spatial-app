"""
test_lisa_reliability.py

Bộ kiểm thử độ tin cậy cho lisa_core.py (T01-T08).
Chạy:  python test_lisa_reliability.py   hoặc   pytest -q test_lisa_reliability.py

Các test phản ánh hành vi MONG MUỐN. T04/T05 từng lộ lỗi thật của lisa_core.py (mục 2.3, 2.5) và đã được sửa.
"""
from __future__ import annotations

import math

import numpy as np

from lisa_core import (
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
    """Thêm viền: ô biên (diện tích nhỏ) để không phải mọi ô đều là ô lõi bị loại."""
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
