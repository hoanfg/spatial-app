"""
lisa_core.py — Revised & Mathematically Validated
=================================================
Lõi tính toán Kinh tế lượng Không gian độc lập (NumPy + Pandas).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

QUADRANTS = ("High-High", "Low-Low", "High-Low", "Low-High")   # mã 0..3
NS = "Not Significant"
DARK = "Dark (NTL=0)"
EDGE = "Edge-Masked"
ALL_LABELS = (*QUADRANTS, NS, DARK, EDGE)


def edge_cell_mask(area_km2, cell_size_m: float, tol: float = 0.99) -> np.ndarray:
    """True nếu diện tích thực của ô nhỏ hơn tol * (cell_size_m / 1000)^2."""
    return np.asarray(area_km2, dtype=float) < tol * (cell_size_m / 1000.0) ** 2


def zscore_lit_only(ntl, lit_threshold: float = 0.0, ref_mask=None,
                    log_transform: bool = False, ddof: int = 1,
                    include_zeros: bool = False, return_stats: bool = False):
    """Chuẩn hóa Z-score với ddof=1 (khớp Chương 3.1 Báo cáo kỹ thuật).

    - Nếu include_zeros=False (mặc định): chỉ chuẩn hóa trên các ô NTL > lit_threshold.
    - Nếu include_zeros=True: giữ cả các ô NTL <= lit_threshold (dùng log1p nếu log_transform=True).
    """
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
        # Cộng epsilon nhỏ tương đối để tránh lỗi làm tròn dấu phẩy động ở sát biên
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

    # m2 tính nhất quán trên tập pool (với z đã chuẩn hóa ddof=1 thì m2 = (m-1)/m)
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


@dataclass
class LisaResult:
    cell_df: pd.DataFrame
    region_metrics: dict
    sig_mask: np.ndarray


def run_lisa(cx, cy, ntl, area_km2, cell_size_m: float, *,
             lit_threshold: float = 0.0, edge_tol: float = 0.99, perms: int = 499,
             alpha: float = 0.05, fdr: bool = True, log_transform: bool = False,
             min_neighbors: int = 1, min_cluster_cells: int = 4, seed: int = 42,
             include_zeros: bool = False, meta: dict | None = None) -> LisaResult:
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

            # Lấy tâm có trọng số bức xạ của cụm HH có diện tích lớn nhất làm CBD
            best_comp = int(np.flatnonzero(big)[np.argmax(carea[big])])
            core_cells = hh_indices[inv == best_comp]
            w_core = np.maximum(ntl[core_cells] * area[core_cells], 1e-9)
            cbd_x = float(np.average(cx[core_cells], weights=w_core))
            cbd_y = float(np.average(cy[core_cells], weights=w_core))

    if n_clusters == 0:
        # Dự phòng khi không có cụm HH: lấy ô không biên có (NTL + spatial lag) cao nhất
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

    # ---- Biến tổng hợp cấp vùng cho Panel ----
    tot = max(float(area.sum()), 1e-12)
    core = ~edge
    ana = max(float(area[members].sum()), 1e-12)
    m_tests = int(f_idx.size)
    p_floor = 2.0 / (perms + 1)
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
