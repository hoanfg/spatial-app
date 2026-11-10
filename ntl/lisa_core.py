"""
lisa_core.py

"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

try:
    from scipy.spatial import cKDTree as _cKDTree
except Exception:  # pragma: no cover
    _cKDTree = None

QUADRANTS = ("High-High", "Low-Low", "High-Low", "Low-High")   # mã 0..3
ROOK_DROP_COLS = (0, 2, 5, 7)   # các cột láng giềng chéo trong ma trận Queen (n, 8)
NS = "Not Significant"
DARK = "Dark (NTL=0)"
EDGE = "Edge-Masked"
ALL_LABELS = (*QUADRANTS, NS, DARK, EDGE)

SPILLOVER_RINGS = (
    "0_Treated_HH",
    "1_Spillover_0_2km",
    "2_Spillover_2_5km",
    "3_Spillover_5_10km",
    "4_Pure_Control_gt10km",
)

SPACETIME_REGIMES = (
    "1_Synergistic_Growth",
    "2_Agglomeration_Shadow",
    "3_Emergent_Pioneer",
    "4_Synchronized_Decline",
)


def edge_cell_mask(area_km2, cell_size_m: float, tol: float = 0.99) -> np.ndarray:
    """True nếu diện tích thực của ô nhỏ hơn tol * (cell_size_m / 1000)^2."""
    return np.asarray(area_km2, dtype=float) < tol * (cell_size_m / 1000.0) ** 2


def zscore_lit_only(ntl, lit_threshold: float = 0.0, ref_mask=None,
                    log_transform: bool = False, ddof: int = 1,
                    include_zeros: bool = False, return_stats: bool = False):
    """Chuẩn hóa Z-score với ddof=1"""
    x = np.asarray(ntl, dtype=float)
    valid = np.isfinite(x) & (x >= 0.0 if include_zeros else x > lit_threshold)
    with np.errstate(divide="ignore", invalid="ignore"):
        if log_transform:
            v = np.log1p(np.maximum(x, 0.0)) if include_zeros else np.log(x)
        else:
            v = x
    ref = valid if ref_mask is None else (valid & np.asarray(ref_mask, dtype=bool))
    z = np.full(x.shape, np.nan)
    mu = sd = float("nan")
    if ref.sum() >= 2:
        mu, sd = float(v[ref].mean()), float(v[ref].std(ddof=ddof))
        if sd > 1e-12:
            z[valid] = (v[valid] - mu) / sd
    return (z, mu, sd) if return_stats else z


def build_queen_neighbors(cx, cy, cell_size_m: float, active,
                          grid_ix=None, grid_iy=None) -> np.ndarray:
    """Ma trận (n, 8) chỉ số láng giềng Queen trên lưới đều cho các ô `active`."""
    cx, cy = np.asarray(cx, float), np.asarray(cy, float)
    active = np.asarray(active, dtype=bool)
    n = len(cx)
    nbr = np.full((n, 8), -1, dtype=np.int64)
    act = np.flatnonzero(active)
    if act.size == 0:
        return nbr

    if grid_ix is not None and grid_iy is not None:
        ix = np.asarray(grid_ix, dtype=np.int64)
        iy = np.asarray(grid_iy, dtype=np.int64)
    else:
        ix = np.floor((cx + 1e-6) / cell_size_m).astype(np.int64)
        iy = np.floor((cy + 1e-6) / cell_size_m).astype(np.int64)

    ix = ix - ix.min() + 1
    iy = iy - iy.min() + 1
    h = int(iy.max()) + 3
    key = ix * h + iy
    akey = key[act]
    order = np.argsort(akey)
    sk = akey[order]
    if np.any(sk[1:] == sk[:-1]):
        raise ValueError("Hai ô lưới trùng chỉ số (cell_size_m không khớp với lưới?).")

    col = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nk = akey + dx * h + dy
            pos = np.minimum(np.searchsorted(sk, nk), len(sk) - 1)
            ok = sk[pos] == nk
            nbr[act[ok], col] = act[order[pos[ok]]]
            col += 1
    return nbr


def local_moran(z, nbr, focal, members, perms: int = 499, seed: int = 42,
                two_sided: bool = True):
    """Tính Local Moran's I (row-standardized) và pseudo p-value qua hoán vị có điều kiện."""
    z = np.asarray(z, float)
    n = len(z)
    I = np.full(n, np.nan)
    lagz = np.full(n, np.nan)
    p = np.full(n, np.nan)
    q = np.full(n, -1, dtype=np.int8)
    f_idx = np.flatnonzero(focal)
    pool = np.flatnonzero(members)
    m = pool.size
    if f_idx.size == 0 or m < 3:
        return I, lagz, p, q

    valid = nbr >= 0
    k = valid.sum(axis=1)
    zn = np.where(valid, z[np.maximum(nbr, 0)], 0.0)
    lag = zn.sum(axis=1) / np.maximum(k, 1)

    m2 = float(np.mean(z[pool] ** 2))
    zf, kf = z[f_idx], k[f_idx]
    I_obs = zf * lag[f_idx] / m2
    I[f_idx], lagz[f_idx] = I_obs, lag[f_idx]

    cmask = np.arange(8)[None, :] < kf[:, None]
    pos_self = np.searchsorted(pool, f_idx)
    rng = np.random.default_rng(seed)
    ge = np.zeros(f_idx.size, dtype=np.int32)
    le = np.zeros(f_idx.size, dtype=np.int32)

    for _ in range(perms):
        r = rng.integers(0, m - 1, size=(f_idx.size, 8))
        r += (r >= pos_self[:, None])
        lp = (z[pool[r]] * cmask).sum(axis=1) / kf
        I_sim = zf * lp / m2
        ge += (I_sim >= I_obs - 1e-12)
        le += (I_sim <= I_obs + 1e-12)

    extreme = np.minimum(ge, le)
    p_one = (extreme + 1.0) / (perms + 1.0)
    p[f_idx] = np.minimum(1.0, 2.0 * p_one) if two_sided else p_one

    lf = lag[f_idx]
    qq = np.full(f_idx.size, -1, dtype=np.int8)
    qq[(zf > 0) & (lf > 0)] = 0
    qq[(zf < 0) & (lf < 0)] = 1
    qq[(zf > 0) & (lf < 0)] = 2
    qq[(zf < 0) & (lf > 0)] = 3
    q[f_idx] = qq
    return I, lagz, p, q


def bh_reject(p, alpha: float = 0.05) -> np.ndarray:
    """Quy trình Benjamini–Hochberg (1995) kiểm soát FDR."""
    p = np.asarray(p, float)
    m = len(p)
    rej = np.zeros(m, dtype=bool)
    if m == 0:
        return rej
    order = np.argsort(p)
    ok = p[order] <= alpha * np.arange(1, m + 1) / m
    if ok.any():
        rej[order[: np.flatnonzero(ok).max() + 1]] = True
    return rej


def cluster_labels(mask, nbr, max_iter: int = 5000) -> np.ndarray:
    """Tìm các thành phần liên thông (Connected Components) trên đồ thị láng giềng Queen."""
    mask = np.asarray(mask, dtype=bool)
    n = len(mask)
    lab = np.where(mask, np.arange(n), n)
    nb = np.where((nbr >= 0) & mask[np.maximum(nbr, 0)], nbr, n)
    for _ in range(max_iter):
        new = np.minimum(lab, np.append(lab, n)[nb].min(axis=1))
        new = np.minimum(new, np.append(new, n)[new])
        if np.array_equal(new, lab):
            break
        lab = new
    return lab


def gini(x) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x) & (x >= 0.0)]
    if x.size == 0 or x.sum() <= 0:
        return 0.0
    x = np.sort(x)
    n = x.size
    return float(2 * np.sum(np.arange(1, n + 1) * x) / (n * x.sum()) - (n + 1) / n)


def _min_euclidean_dist_m(src_x, src_y, dst_x, dst_y) -> np.ndarray:
    """Khoảng cách Euclid ngắn nhất từ mỗi điểm (src_x, src_y) tới tập (dst_x, dst_y)."""
    if len(dst_x) == 0 or len(src_x) == 0:
        return np.full(len(src_x), np.nan)
    if _cKDTree is not None:
        tree = _cKDTree(np.column_stack([dst_x, dst_y]))
        d, _ = tree.query(np.column_stack([src_x, src_y]), k=1)
        return np.asarray(d, dtype=float)
    # Dự phòng thuần NumPy theo khối
    out = np.empty(len(src_x), dtype=float)
    chunk = 512
    for s in range(0, len(src_x), chunk):
        e = min(len(src_x), s + chunk)
        dx = src_x[s:e, None] - dst_x[None, :]
        dy = src_y[s:e, None] - dst_y[None, :]
        out[s:e] = np.sqrt(np.min(dx * dx + dy * dy, axis=1))
    return out


def compute_pareto_top_lights(ntl: np.ndarray, area: np.ndarray, core: np.ndarray,
                              lit: np.ndarray, tail_frac: float = 0.10):
    """Mô-đun 1: Hill Tail Exponent (Pareto alpha) trên Top 10% ô sáng (Bluhm & Krause, 2022 JDE)."""
    n = len(ntl)
    top_dummy = np.zeros(n, dtype=int)
    sol = ntl * area
    lit_core_vals = np.sort(ntl[core & lit])[::-1]
    if lit_core_vals.size >= 15:
        k_tail = max(5, int(np.floor(tail_frac * lit_core_vals.size)))
        u_thr = float(max(lit_core_vals[min(k_tail, lit_core_vals.size - 1)], 1e-9))
        top_k = lit_core_vals[:k_tail]
        logs = np.log(np.maximum(top_k / u_thr, 1.0))
        hill_xi = float(np.mean(logs))
        pareto_alpha = float(1.0 / hill_xi) if hill_xi > 1e-6 else float("nan")
        top_dummy[core & (ntl >= u_thr)] = 1
        tot_core_sol = float(sol[core].sum())
        top_sol_share = float(sol[top_dummy == 1].sum() / tot_core_sol) if tot_core_sol > 1e-12 else 0.0
    else:
        pareto_alpha = float("nan")
        top_sol_share = float("nan")
    return top_dummy, pareto_alpha, top_sol_share


def compute_urban_density_gradient(ntl: np.ndarray, dist_core_km: np.ndarray,
                                   area: np.ndarray, core: np.ndarray):
    """Mô-đun 2: Độ dốc suy giảm mật độ đô thị WLS ln(1+NTL) = a - gamma*d (Duranton & Puga, 2023)."""
    d_c = dist_core_km[core]
    y_c = np.log1p(np.maximum(ntl[core], 0.0))
    w_c = np.maximum(area[core], 1e-9)
    if d_c.size >= 10 and np.std(d_c) > 1e-6 and np.std(y_c) > 1e-6:
        w_sum = float(w_c.sum())
        d_bar = float(np.sum(w_c * d_c) / w_sum)
        y_bar = float(np.sum(w_c * y_c) / w_sum)
        cov_dy = float(np.sum(w_c * (d_c - d_bar) * (y_c - y_bar)))
        var_d = float(np.sum(w_c * (d_c - d_bar) ** 2))
        var_y = float(np.sum(w_c * (y_c - y_bar) ** 2))
        gamma_decay = float(-cov_dy / max(var_d, 1e-12))
        r2 = float((cov_dy ** 2) / max(var_d * var_y, 1e-12))
        return gamma_decay, r2
    return float("nan"), float("nan")


def compute_spillover_rings_and_rdd(cx: np.ndarray, cy: np.ndarray, is_hh: np.ndarray,
                                    core: np.ndarray, edge: np.ndarray):
    """Mô-đun 3: Vành đai lan tỏa đồng tâm (Butts, 2024) & Khoảng cách có dấu (Spatial RDD)."""
    n = len(cx)
    hh_idx = np.flatnonzero(is_hh)
    non_hh_idx = np.flatnonzero(core & ~is_hh)
    if hh_idx.size > 0:
        d_out_m = _min_euclidean_dist_m(cx, cy, cx[hh_idx], cy[hh_idx])
        dist_to_hh_km = d_out_m / 1000.0
        signed_dist_hh_km = dist_to_hh_km.copy()
        if non_hh_idx.size > 0:
            d_in_m = _min_euclidean_dist_m(cx[hh_idx], cy[hh_idx], cx[non_hh_idx], cy[non_hh_idx])
            signed_dist_hh_km[hh_idx] = -d_in_m / 1000.0
        else:
            # Không có ô lõi non-HH => không tồn tại ranh giới nội bộ điều trị/đối chứng:
            # biến chạy có dấu của Spatial RDD không xác định (NaN, không phải 0.0).
            signed_dist_hh_km = np.full(n, np.nan)
        ring = np.select(
            [edge, is_hh, dist_to_hh_km <= 2.0, dist_to_hh_km <= 5.0, dist_to_hh_km <= 10.0],
            ["Edge_Masked", "0_Treated_HH", "1_Spillover_0_2km", "2_Spillover_2_5km", "3_Spillover_5_10km"],
            default="4_Pure_Control_gt10km",
        )
    else:
        dist_to_hh_km = np.full(n, np.nan)
        signed_dist_hh_km = np.full(n, np.nan)
        ring = np.where(edge, "Edge_Masked", "No_HH_Cluster")
    return dist_to_hh_km, signed_dist_hh_km, ring


def compute_recentered_market_access(cx: np.ndarray, cy: np.ndarray, sol: np.ndarray,
                                     core: np.ndarray, cell_size_m: float,
                                     radius_steps: int = 5, tau_km: float = 0.5,
                                     dense_limit: int = 1_200_000):
    """Mô-đun 4: Tiếp cận thị trường đã khử thiên lệch vị trí trung tâm (Borusyak & Hull, 2023 Econometrica).

    Tính MA_i = Σ_{j != i} exp(-tau * d_ij) * SOL_j trong bán kính `radius_steps` ô lưới,
    và kỳ vọng giải tích dưới hoán vị không gian E_pi[MA_i] = mean(SOL_core) * Σ_{j != i} exp(-tau * d_ij).
    """
    n = len(cx)
    raw_ma = np.full(n, np.nan)
    exp_ma = np.full(n, np.nan)
    rec_ma = np.full(n, np.nan)
    if int(core.sum()) < 3:
        return raw_ma, exp_ma, rec_ma

    ix0 = np.floor((cx + 1e-6) / cell_size_m).astype(np.int64)
    iy0 = np.floor((cy + 1e-6) / cell_size_m).astype(np.int64)
    ix0 -= ix0.min()
    iy0 -= iy0.min()

    R = max(2, int(radius_steps))
    W = int(ix0.max()) + 1 + 2 * R
    H = int(iy0.max()) + 1 + 2 * R

    if W * H <= dense_limit:
        sol_grid = np.zeros((W, H), dtype=np.float64)
        core_grid = np.zeros((W, H), dtype=np.float64)
        gx = ix0 + R
        gy = iy0 + R
        sol_grid[gx[core], gy[core]] = sol[core]
        core_grid[gx[core], gy[core]] = 1.0

        ma_acc = np.zeros(n, dtype=np.float64)
        om_acc = np.zeros(n, dtype=np.float64)
        cell_km = cell_size_m / 1000.0

        for dx in range(-R, R + 1):
            for dy in range(-R, R + 1):
                if dx == 0 and dy == 0:
                    continue
                dist_steps = math.hypot(dx, dy)
                if dist_steps > R + 0.01:
                    continue
                w_d = math.exp(-tau_km * (dist_steps * cell_km))
                ma_acc += w_d * sol_grid[gx + dx, gy + dy]
                om_acc += w_d * core_grid[gx + dx, gy + dy]

        mean_sol_core = float(np.mean(sol[core]))
        raw_ma[core] = ma_acc[core]
        exp_ma[core] = om_acc[core] * mean_sol_core
        rec_ma[core] = raw_ma[core] - exp_ma[core]
    elif _cKDTree is not None:
        # Dự phòng cho hộp bao thưa (đảo xa bờ, địa phương kéo dài): không cấp phát lưới W*H,
        # dùng cKDTree với cùng bán kính (R + 0.01 bước lưới) và cùng trọng số exp(-tau * d_km).
        c_idx = np.flatnonzero(core)
        pts = np.column_stack([cx[c_idx], cy[c_idx]])
        tree = _cKDTree(pts)
        max_d = (R + 0.01) * cell_size_m
        coo = tree.sparse_distance_matrix(tree, max_d, output_type="coo_matrix")
        keep = coo.row != coo.col
        rows, cols, d_m = coo.row[keep], coo.col[keep], coo.data[keep]
        w_d = np.exp(-tau_km * d_m / 1000.0)
        m = c_idx.size
        ma_c = np.bincount(rows, weights=w_d * sol[c_idx][cols], minlength=m)
        om_c = np.bincount(rows, weights=w_d, minlength=m)
        mean_sol_core = float(np.mean(sol[core]))
        raw_ma[c_idx] = ma_c
        exp_ma[c_idx] = om_c * mean_sol_core
        rec_ma[c_idx] = raw_ma[c_idx] - exp_ma[c_idx]
    return raw_ma, exp_ma, rec_ma


@dataclass
class LisaResult:
    cell_df: pd.DataFrame
    region_metrics: dict
    sig_mask: np.ndarray


def run_lisa(cx, cy, ntl, area_km2, cell_size_m: float, *,
             lit_threshold: float = 0.0, edge_tol: float = 0.99, perms: int = 499,
             alpha: float = 0.05, fdr: bool = True, log_transform: bool = False,
             min_neighbors: int = 1, min_cluster_cells: int = 4, seed: int = 42,
             include_zeros: bool = False, meta: dict | None = None,
             weights: str = "queen") -> LisaResult:
    cx, cy = np.asarray(cx, dtype=float), np.asarray(cy, dtype=float)
    ntl = np.asarray(ntl, dtype=float)
    area = np.asarray(area_km2, dtype=float)
    n = len(ntl)

    edge = edge_cell_mask(area, cell_size_m, edge_tol)
    lit = np.isfinite(ntl) & (ntl > lit_threshold)
    z = zscore_lit_only(
        ntl, lit_threshold, ref_mask=~edge,
        log_transform=log_transform, ddof=1, include_zeros=include_zeros
    )
    members = (~edge) & np.isfinite(z) & (np.isfinite(ntl) if include_zeros else lit)
    nbr = build_queen_neighbors(cx, cy, cell_size_m, members)
    if weights == "rook":
        # chỉ giữ 4 láng giềng chung cạnh (cột 1, 3, 4, 6 trong thứ tự dx, dy của build_queen_neighbors)
        nbr = nbr.copy()
        nbr[:, ROOK_DROP_COLS] = -1
    elif weights != "queen":
        raise ValueError(f"weights phải là 'queen' hoặc 'rook', nhận {weights!r}")
    k = (nbr >= 0).sum(axis=1)
    focal = members & (k >= max(1, min_neighbors))

    I, lagz, p, q = local_moran(z, nbr, focal, members, perms, seed, two_sided=True)

    valid_nbr = nbr >= 0
    ntl_nbrs = np.where(valid_nbr, ntl[np.maximum(nbr, 0)], 0.0)
    raw_lag = np.where(k > 0, ntl_nbrs.sum(axis=1) / np.maximum(k, 1), np.nan)

    sig = np.zeros(n, dtype=bool)
    f_idx = np.flatnonzero(focal)
    if f_idx.size:
        sig[f_idx] = bh_reject(p[f_idx], alpha) if fdr else (p[f_idx] < alpha)
    sig &= (q >= 0)

    label = np.full(n, NS, dtype=object)
    if not include_zeros:
        label[~lit & ~edge] = DARK
    label[edge] = EDGE
    for code, name in enumerate(QUADRANTS):
        label[sig & (q == code)] = name

    # ---- Cụm HH liên thông & xác định tâm CBD vững (Robust CBD Centroid) ----
    is_hh = label == "High-High"
    cluster_id = np.full(n, -1, dtype=np.int64)
    n_clusters, largest_km2, cl_area = 0, 0.0, 0.0
    cbd_x, cbd_y = float(np.mean(cx)), float(np.mean(cy))

    if is_hh.any():
        cc = cluster_labels(is_hh, nbr)[is_hh]
        _, inv, cnt = np.unique(cc, return_inverse=True, return_counts=True)
        carea = np.bincount(inv, weights=area[is_hh])
        big = cnt >= min_cluster_cells
        n_clusters = int(big.sum())
        if n_clusters:
            largest_km2 = float(carea[big].max())
            cl_area = float(carea[big].sum())
            ids = np.cumsum(big) - 1
            hh_indices = np.flatnonzero(is_hh)
            cluster_id[hh_indices[big[inv]]] = ids[inv][big[inv]]

            best_comp = int(np.flatnonzero(big)[np.argmax(carea[big])])
            core_cells = hh_indices[inv == best_comp]
            w_core = np.maximum(ntl[core_cells] * area[core_cells], 1e-9)
            cbd_x = float(np.average(cx[core_cells], weights=w_core))
            cbd_y = float(np.average(cy[core_cells], weights=w_core))

    if n_clusters == 0:
        core_valid = ~edge & np.isfinite(ntl)
        if core_valid.any():
            composite_score = np.where(
                core_valid,
                0.5 * ntl + 0.5 * np.nan_to_num(raw_lag, nan=0.0),
                -np.inf,
            )
            cbd_idx = int(np.argmax(composite_score))
            cbd_x, cbd_y = float(cx[cbd_idx]), float(cy[cbd_idx])

    dist_to_core_km = np.sqrt((cx - cbd_x) ** 2 + (cy - cbd_y) ** 2) / 1000.0

    core = ~edge
    sol = ntl * area
    top_dummy, pareto_alpha, top10_sol_share = compute_pareto_top_lights(ntl, area, core, lit)
    urban_gradient_decay, monocentric_r2 = compute_urban_density_gradient(ntl, dist_to_core_km, area, core)
    # Ưu tiên cụm HH (FDR/alpha); nếu rỗng do FDR khắt khe thì lùi về HH (p < alpha) hoặc Top 10% Lights
    unadj_hh = (q == 0) & np.isfinite(p) & (p < alpha)
    if is_hh.any():
        core_treat_mask = is_hh
        treat_source = "LISA_HH_Active"
    elif unadj_hh.any():
        core_treat_mask = unadj_hh
        treat_source = "LISA_HH_Unadjusted"
    else:
        core_treat_mask = top_dummy.astype(bool)
        treat_source = "Top10_Bright_Core"
    dist_to_hh_km, signed_dist_hh_km, spillover_ring = compute_spillover_rings_and_rdd(
        cx, cy, core_treat_mask, core, edge
    )
    raw_ma, exp_ma, rec_ma = compute_recentered_market_access(cx, cy, sol, core, cell_size_m)

    # Hệ số tự hồi quy không gian bậc 1 (Spatial Unit Root / Persistence diagnostic - Müller & Watson, 2024)
    valid_ar = focal & np.isfinite(z) & np.isfinite(lagz)
    if int(valid_ar.sum()) >= 10 and float(np.std(z[valid_ar])) > 1e-6:
        spatial_ar1_rho = float(np.corrcoef(z[valid_ar], lagz[valid_ar])[0, 1])
    else:
        spatial_ar1_rho = float("nan")

    # ---- Biến tổng hợp cấp vùng cho Panel ----
    tot = max(float(area.sum()), 1e-12)
    core_area = max(float(area[core].sum()), 1e-12)
    ana = max(float(area[members].sum()), 1e-12)
    m_tests = int(f_idx.size)
    p_floor = 2.0 / (perms + 1)

    sp02_mask = spillover_ring == "1_Spillover_0_2km"
    ctrl_mask = spillover_ring == "4_Pure_Control_gt10km"

    row = dict(meta or {})
    row.update({
        "cell_size_m": cell_size_m,
        "n_cells": n, "n_cells_edge_masked": int(edge.sum()),
        "n_cells_lit": int(lit.sum()), "n_cells_tested": m_tests,
        "area_total_km2": round(tot, 4),
        "hh_area_share": float((area[is_hh]).sum() / tot),
        "hh_area_share_of_tested": float(area[is_hh].sum() / ana),
        "hh_cluster_area_share": cl_area / tot,
        "ll_area_share": float(area[label == "Low-Low"].sum() / tot),
        "hl_area_share": float(area[label == "High-Low"].sum() / tot),
        "lh_area_share": float(area[label == "Low-High"].sum() / tot),
        "n_hh_clusters": n_clusters, "largest_hh_cluster_km2": largest_km2,
        "hotspot_dummy": int(n_clusters > 0),
        "gini_ntl_core_all": gini(ntl[core]),
        "gini_ntl_core_lit": gini(ntl[core & lit]),
        "gini_sol_all": gini(ntl * area),
        "moran_I_lit": float(np.nanmean(I)) if np.isfinite(I).any() else float("nan"),
        "lit_area_share": float(area[lit].sum() / tot),
        "pareto_alpha_top10": round(pareto_alpha, 4) if np.isfinite(pareto_alpha) else float("nan"),
        "top10_lit_sol_share": round(top10_sol_share, 4) if np.isfinite(top10_sol_share) else float("nan"),
        "urban_gradient_decay": round(urban_gradient_decay, 5) if np.isfinite(urban_gradient_decay) else float("nan"),
        "monocentric_r2": round(monocentric_r2, 4) if np.isfinite(monocentric_r2) else float("nan"),
        "spatial_ar1_persistence": round(spatial_ar1_rho, 4) if np.isfinite(spatial_ar1_rho) else float("nan"),
        "spillover_0_2km_area_share": round(float(area[sp02_mask].sum() / core_area), 4),
        "pure_control_gt10km_area_share": round(float(area[ctrl_mask].sum() / core_area), 4),
        "spillover_core_source": treat_source,
        "mean_ntl_treated_hh": round(float(ntl[core_treat_mask].mean()), 3) if core_treat_mask.any() else float("nan"),
        "mean_ntl_spillover_0_2km": round(float(ntl[sp02_mask].mean()), 3) if sp02_mask.any() else float("nan"),
        "mean_ntl_pure_control": round(float(ntl[ctrl_mask].mean()), 3) if ctrl_mask.any() else float("nan"),
        # --- Hyperparameters ---
        "p_cfg_perms": perms, "p_cfg_alpha": alpha, "p_cfg_fdr": int(fdr),
        "p_cfg_log": int(log_transform), "p_cfg_lit_thr": lit_threshold,
        "p_cfg_edge_tol": edge_tol, "p_cfg_min_nbr": min_neighbors,
        "p_cfg_min_cluster": min_cluster_cells,
        "p_floor": p_floor,
        "fdr_min_hits_needed": int(math.ceil(p_floor * m_tests / alpha)) if (fdr and m_tests) else 0,
    })

    quad = np.array([QUADRANTS[c] if c >= 0 else "" for c in range(-1, 4)], dtype=object)[q.astype(int) + 1]
    cell_df = pd.DataFrame({
        "dist_to_core_km": np.round(dist_to_core_km, 3),
        "dist_to_hh_km": np.round(dist_to_hh_km, 3),
        "signed_dist_hh_km": np.round(signed_dist_hh_km, 3),
        "spillover_ring": spillover_ring,
        "raw_market_access": np.round(raw_ma, 4),
        "expected_ma_perm": np.round(exp_ma, 4),
        "recentered_market_access": np.round(rec_ma, 4),
        "top_lights_10pct_dummy": top_dummy,
        "ntl_raw_lag": np.round(raw_lag, 4),
        "ntl_z_lit": np.round(z, 4),
        "lisa_n_neighbors": k.astype(int),
        "lisa_I": np.round(I, 4),
        "lisa_lag_z": np.round(lagz, 4),
        "lisa_p_sim": np.round(p, 5),
        "lisa_quadrant_raw": quad,
        "lisa_class": label,
        "lisa_significant": sig.astype(int),
        "is_edge_masked": edge.astype(int),
        "is_dark": (~lit).astype(int),
        "hh_cluster_id": cluster_id,
    })
    return LisaResult(cell_df=cell_df, region_metrics=row, sig_mask=sig)


# ===========================================================================
# DYNAMIC SPACE-TIME LISA & SPATIAL MARKOV (Rey et al., 2023)
# ===========================================================================
@dataclass
class SpaceTimeResult:
    st_cell_df: pd.DataFrame
    regime_summary: pd.DataFrame
    markov_all: pd.DataFrame
    markov_high_lag: pd.DataFrame
    markov_low_lag: pd.DataFrame
    metrics: dict


def run_spacetime_lisa(cx, cy, ntl_t0, ntl_t1, area_km2, cell_size_m: float, *,
                       year_t0: int, year_t1: int, edge_tol: float = 0.99) -> SpaceTimeResult:
    """Phân tích Động học Không – Thời gian (Directional LISA & Spatial Markov Matrix t0 -> t1)."""
    cx, cy = np.asarray(cx, dtype=float), np.asarray(cy, dtype=float)
    ntl0 = np.asarray(ntl_t0, dtype=float)
    ntl1 = np.asarray(ntl_t1, dtype=float)
    area = np.asarray(area_km2, dtype=float)
    n = len(ntl1)

    edge = edge_cell_mask(area, cell_size_m, edge_tol)
    core = ~edge & np.isfinite(ntl0) & np.isfinite(ntl1)

    v0 = np.log1p(np.maximum(ntl0, 0.0))
    v1 = np.log1p(np.maximum(ntl1, 0.0))

    z0 = np.full(n, np.nan)
    z1 = np.full(n, np.nan)
    if int(core.sum()) >= 3:
        sd0 = float(v0[core].std(ddof=1))
        sd1 = float(v1[core].std(ddof=1))
        if sd0 > 1e-12:
            z0[core] = (v0[core] - float(v0[core].mean())) / sd0
        if sd1 > 1e-12:
            z1[core] = (v1[core] - float(v1[core].mean())) / sd1

    nbr = build_queen_neighbors(cx, cy, cell_size_m, core)
    valid = nbr >= 0
    k = valid.sum(axis=1)
    ok = core & (k > 0) & np.isfinite(z0) & np.isfinite(z1)

    lag0 = np.where(ok, np.where(valid, z0[np.maximum(nbr, 0)], 0.0).sum(axis=1) / np.maximum(k, 1), np.nan)
    lag1 = np.where(ok, np.where(valid, z1[np.maximum(nbr, 0)], 0.0).sum(axis=1) / np.maximum(k, 1), np.nan)

    dz = z1 - z0
    dlag = lag1 - lag0
    vec_mag = np.sqrt(dz ** 2 + dlag ** 2)
    moved = ok & (vec_mag >= 0.05)

    regime = np.full(n, "Excluded_or_Static", dtype=object)
    regime[moved & (dz >= 0) & (dlag >= 0)] = SPACETIME_REGIMES[0]
    regime[moved & (dz < 0) & (dlag >= 0)] = SPACETIME_REGIMES[1]
    regime[moved & (dz >= 0) & (dlag < 0)] = SPACETIME_REGIMES[2]
    regime[moved & (dz < 0) & (dlag < 0)] = SPACETIME_REGIMES[3]

    # Tính Recentered Market Access cho cả t0 và t1 để xuất biến sai phân chuẩn Borusyak & Hull (2023)
    _, _, rec_ma0 = compute_recentered_market_access(cx, cy, ntl0 * area, core, cell_size_m)
    _, _, rec_ma1 = compute_recentered_market_access(cx, cy, ntl1 * area, core, cell_size_m)

    # Spatial Markov Transition Matrix trên 4 Quartiles (Q1..Q4)
    q_labels = ["Q1 (Lowest)", "Q2 (Low-Mid)", "Q3 (High-Mid)", "Q4 (Highest)"]
    if int(ok.sum()) >= 12:
        r0 = pd.Series(v0[ok]).rank(pct=True, method="average").to_numpy()
        r1 = pd.Series(v1[ok]).rank(pct=True, method="average").to_numpy()
        c0 = np.clip(np.ceil(r0 * 4).astype(int) - 1, 0, 3)
        c1 = np.clip(np.ceil(r1 * 4).astype(int) - 1, 0, 3)
        lag0_ok = lag0[ok]
        hi_ctx = lag0_ok >= float(np.median(lag0_ok))

        def _build_mat(sub_mask):
            mat = np.zeros((4, 4), dtype=float)
            s0, s1 = c0[sub_mask], c1[sub_mask]
            for iq in range(4):
                rm = s0 == iq
                if rm.sum() > 0:
                    for jq in range(4):
                        mat[iq, jq] = round(float(np.mean(s1[rm] == jq) * 100.0), 1)
            return pd.DataFrame(mat, index=q_labels, columns=[f"→ {x.split()[0]}" for x in q_labels])

        df_m_all = _build_mat(np.ones(int(ok.sum()), dtype=bool))
        df_m_hi = _build_mat(hi_ctx)
        df_m_lo = _build_mat(~hi_ctx)
        trace_p = float(np.trace(df_m_all.to_numpy()) / 100.0)
        shorrocks_mobility = float((4.0 - trace_p) / 3.0)
    else:
        empty_m = pd.DataFrame(np.zeros((4, 4)), index=q_labels, columns=["→ Q1", "→ Q2", "→ Q3", "→ Q4"])
        df_m_all = df_m_hi = df_m_lo = empty_m
        shorrocks_mobility = float("nan")

    tot_core_area = max(float(area[ok].sum()), 1e-12)
    reg_rows = []
    for rg in SPACETIME_REGIMES:
        m_rg = regime == rg
        reg_rows.append({
            "regime": rg,
            "cells": int(m_rg.sum()),
            "area_share_pct": round(float(area[m_rg].sum() / tot_core_area * 100.0), 2),
            "mean_delta_ln_ntl": round(float((v1[m_rg] - v0[m_rg]).mean()), 4) if m_rg.any() else 0.0,
        })
    regime_summary = pd.DataFrame(reg_rows)

    st_cell_df = pd.DataFrame({
        f"ntl_{year_t0}": np.round(ntl0, 4),
        f"ntl_{year_t1}": np.round(ntl1, 4),
        "delta_ntl": np.round(ntl1 - ntl0, 4),
        "delta_ln_ntl": np.round(v1 - v0, 5),
        f"z_{year_t0}": np.round(z0, 4),
        f"z_{year_t1}": np.round(z1, 4),
        "delta_z": np.round(dz, 4),
        "delta_lag_z": np.round(dlag, 4),
        "movement_magnitude": np.round(vec_mag, 4),
        "delta_recentered_ma": np.round(rec_ma1 - rec_ma0, 4),
        "spacetime_regime": regime,
    })

    # Tách biên độ rộng / sâu (Chen & Roth, 2024): ln(1+NTL) trộn hai kênh này khi dữ liệu nhiều số 0
    lit0, lit1 = core & (ntl0 > 0), core & (ntl1 > 0)
    dark0 = core & ~(ntl0 > 0)
    both = lit0 & lit1
    entry = dark0 & lit1                      # tối -> sáng (extensive margin)
    exit_ = lit0 & ~lit1                      # sáng -> tối
    margin = np.full(n, "excluded", dtype=object)
    margin[core & ~lit0 & ~lit1] = "dark_both"
    margin[both] = "intensive"
    margin[entry] = "extensive_entry"
    margin[exit_] = "extensive_exit"
    with np.errstate(divide="ignore", invalid="ignore"):
        dln_int = np.where(both, np.log(np.where(both, ntl1, 1.0)) - np.log(np.where(both, ntl0, 1.0)), np.nan)
    st_cell_df["delta_ln_ntl_intensive"] = np.round(dln_int, 5)
    st_cell_df["margin_type"] = margin

    shadow_share = float(area[regime == "2_Agglomeration_Shadow"].sum() / tot_core_area * 100.0)
    synergy_share = float(area[regime == "1_Synergistic_Growth"].sum() / tot_core_area * 100.0)

    metrics = {
        "year_t0": year_t0,
        "year_t1": year_t1,
        "shorrocks_mobility": round(shorrocks_mobility, 4) if np.isfinite(shorrocks_mobility) else float("nan"),
        "synergistic_growth_pct": round(synergy_share, 2),
        "agglomeration_shadow_pct": round(shadow_share, 2),
        "mean_delta_ln_ntl": round(float((v1[core] - v0[core]).mean()), 4) if core.any() else 0.0,
        "extensive_entry_pct": round(float(entry.sum() / dark0.sum() * 100.0), 2) if dark0.any() else float("nan"),
        "extensive_exit_pct": round(float(exit_.sum() / lit0.sum() * 100.0), 2) if lit0.any() else float("nan"),
        "intensive_mean_dln_ntl": round(float(np.nanmean(dln_int[both])), 4) if both.any() else float("nan"),
        "n_both_lit": int(both.sum()),
    }
    return SpaceTimeResult(
        st_cell_df=st_cell_df,
        regime_summary=regime_summary,
        markov_all=df_m_all,
        markov_high_lag=df_m_hi,
        markov_low_lag=df_m_lo,
        metrics=metrics,
    )
