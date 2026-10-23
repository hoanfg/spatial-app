"""
lisa_core.py — Phase 4 (Pragmatic & Academic)
==============================================
Lõi tính toán KHÔNG phụ thuộc Streamlit / libpysal (chỉ numpy + pandas) nên kiểm thử và
tái lập được ngoài giao diện.

Luồng chuẩn:
    res = run_lisa(cx, cy, ntl, area_km2, cell_size_m, ...)
    res.cell_df          -> 1 dòng / ô lưới (100% quan sát, không lọc)
    res.region_metrics   -> dict 1 dòng / (vùng, năm) để bơm vào hồi quy panel

Quyết định phương pháp luận (xem docstring từng hàm):
  * Ô biên (area < 0.99 * cell²) bị loại khỏi ĐỒ THỊ LÁNG GIỀNG (cả vai trò tâm lẫn láng giềng).
  * z-score chỉ trên ô sáng (NTL > ngưỡng) và ngoài ô biên; ô tối = NaN.
  * Hệ quả: ma trận W được dựng trên đồ thị con "chỉ ô sáng, không biên" (listwise deletion).
  * Local Moran's I: Queen, row-standardized, p-value bằng hoán vị có điều kiện (conditional
    permutation, quy ước GeoDa/esda), hiệu chỉnh Benjamini–Hochberg tùy chọn.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

QUADRANTS = ("High-High", "Low-Low", "High-Low", "Low-High")   # mã 0..3
NS = "Not Significant"
DARK = "Dark (NTL=0)"        # nhãn kỹ thuật (ngoài 5 trạng thái): ô không sáng
EDGE = "Edge-Masked"         # nhãn kỹ thuật (ngoài 5 trạng thái): ô biên bị loại
ALL_LABELS = (*QUADRANTS, NS, DARK, EDGE)


# ---------------------------------------------------------------------------
# 1. Edge-cell masking
# ---------------------------------------------------------------------------
def edge_cell_mask(area_km2, cell_size_m: float, tol: float = 0.99) -> np.ndarray:
    """True nếu ô bị cắt nhỏ: area_km2 < tol * (cell_size_m/1000)^2.

    Lưu ý đơn vị: area_km2 tính theo km² nên cạnh ô phải đổi từ mét sang km.
    """
    return np.asarray(area_km2, dtype=float) < tol * (cell_size_m / 1000.0) ** 2


# ---------------------------------------------------------------------------
# 2. Chuẩn hóa z-score cho dữ liệu zero-inflated
# ---------------------------------------------------------------------------
def zscore_lit_only(ntl, lit_threshold: float = 0.0, ref_mask=None,
                    log_transform: bool = False, ddof: int = 0,
                    return_stats: bool = False):
    """z-score với μ, σ chỉ tính trên các ô SÁNG (NTL > lit_threshold).

    - Ô tối (NTL <= ngưỡng) → NaN (không bị kéo về giá trị âm giả tạo, không làm sụt σ).
    - ref_mask (tùy chọn): chỉ dùng tập con này để ước lượng μ, σ (vd. ~is_edge), nhưng z vẫn
      được trả cho mọi ô sáng.
    - log_transform: lấy ln(NTL) trên ô sáng trước khi chuẩn hóa (khuyến nghị làm robustness,
      vì NTL ô sáng lệch phải rất mạnh nên z thô bị vài ô cực trị chi phối).
    """
    x = np.asarray(ntl, dtype=float)
    lit = np.isfinite(x) & (x > lit_threshold)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = np.log(x) if log_transform else x
    ref = lit if ref_mask is None else (lit & np.asarray(ref_mask, dtype=bool))
    z = np.full(x.shape, np.nan)
    mu = sd = float("nan")
    if ref.sum() >= 2:
        mu, sd = float(v[ref].mean()), float(v[ref].std(ddof=ddof))
        if sd > 1e-12:
            z[lit] = (v[lit] - mu) / sd
    return (z, mu, sd) if return_stats else z


# ---------------------------------------------------------------------------
# 3. Đồ thị láng giềng Queen trên lưới đều
# ---------------------------------------------------------------------------
def build_queen_neighbors(cx, cy, cell_size_m: float, active) -> np.ndarray:
    """Ma trận (n, 8) chỉ số láng giềng Queen, -1 = không có. Chỉ nối các ô `active`.

    Chỉ số hàng/cột nguyên suy từ tâm ô (tâm của phần ô bị cắt luôn nằm trong ô gốc vì ô lồi).
    Hàng của ô không active toàn -1.
    """
    cx, cy = np.asarray(cx, float), np.asarray(cy, float)
    active = np.asarray(active, dtype=bool)
    n = len(cx)
    nbr = np.full((n, 8), -1, dtype=np.int64)
    act = np.flatnonzero(active)
    if act.size == 0:
        return nbr
    ix = np.floor(cx / cell_size_m).astype(np.int64)
    iy = np.floor(cy / cell_size_m).astype(np.int64)
    ix -= ix.min() - 1
    iy -= iy.min() - 1
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


# ---------------------------------------------------------------------------
# 4. Local Moran's I (row-standardized) + hoán vị có điều kiện
# ---------------------------------------------------------------------------
def local_moran(z, nbr, focal, members, perms: int = 499, seed: int = 42):
    """Trả (I, lag_z, p_sim, quadrant_code); mã quadrant: 0 HH, 1 LL, 2 HL, 3 LH, -1 không xác định.

    I_i = z_i * Σ_j w_ij z_j / m2, với w_ij = 1/k_i (row-standardized), m2 = mean(z²) trên `members`.
    p_sim: pseudo p-value một phía theo quy ước GeoDa/esda, hoán vị có điều kiện (giữ z_i,
    rút ngẫu nhiên k_i giá trị từ các ô khác, có hoàn lại). Giá trị p nhỏ nhất = 1/(perms+1).
    """
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
    pos_self = np.searchsorted(pool, f_idx)          # f_idx ⊂ pool, cùng sắp xếp
    rng = np.random.default_rng(seed)
    ge = np.zeros(f_idx.size, dtype=np.int32)
    for _ in range(perms):
        r = rng.integers(0, m - 1, size=(f_idx.size, 8))
        r += (r >= pos_self[:, None])                # bỏ chính ô i khỏi tập rút
        lp = (z[pool[r]] * cmask).sum(axis=1) / kf
        ge += (zf * lp / m2 >= I_obs)
    ge = np.minimum(ge, perms - ge)                  # quy ước esda: đuôi gần hơn
    p[f_idx] = (ge + 1.0) / (perms + 1.0)

    lf = lag[f_idx]
    qq = np.full(f_idx.size, -1, dtype=np.int8)
    qq[(zf > 0) & (lf > 0)] = 0
    qq[(zf < 0) & (lf < 0)] = 1
    qq[(zf > 0) & (lf < 0)] = 2
    qq[(zf < 0) & (lf > 0)] = 3
    q[f_idx] = qq
    return I, lagz, p, q


def bh_reject(p, alpha: float = 0.05) -> np.ndarray:
    """Benjamini–Hochberg FDR: True = bác bỏ H0 (ô có ý nghĩa)."""
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


# ---------------------------------------------------------------------------
# 5. Cụm HH liên thông + Gini
# ---------------------------------------------------------------------------
def cluster_labels(mask, nbr, max_iter: int = 5000) -> np.ndarray:
    """Nhãn thành phần liên thông (Queen) của các ô mask=True; ô ngoài mask = n (sentinel)."""
    mask = np.asarray(mask, dtype=bool)
    n = len(mask)
    lab = np.where(mask, np.arange(n), n)
    nb = np.where((nbr >= 0) & mask[np.maximum(nbr, 0)], nbr, n)
    for _ in range(max_iter):
        new = np.minimum(lab, np.append(lab, n)[nb].min(axis=1))
        new = np.minimum(new, np.append(new, n)[new])      # pointer jumping
        if np.array_equal(new, lab):
            break
        lab = new
    return lab


def gini(x) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0 or x.sum() <= 0:
        return 0.0
    x = np.sort(x)
    n = x.size
    return float(2 * np.sum(np.arange(1, n + 1) * x) / (n * x.sum()) - (n + 1) / n)


# ---------------------------------------------------------------------------
# 6. Orchestrator + Data Bridge
# ---------------------------------------------------------------------------
@dataclass
class LisaResult:
    cell_df: pd.DataFrame        # 1 dòng / ô, 100% quan sát
    region_metrics: dict         # 1 dòng / (vùng, năm) cho panel
    sig_mask: np.ndarray         # ô có ý nghĩa (HH/LL/HL/LH), dùng cho ưu tiên hiển thị


def run_lisa(cx, cy, ntl, area_km2, cell_size_m: float, *,
             lit_threshold: float = 0.0, edge_tol: float = 0.99, perms: int = 499,
             alpha: float = 0.05, fdr: bool = True, log_transform: bool = False,
             min_neighbors: int = 1, min_cluster_cells: int = 4, seed: int = 42,
             meta: dict | None = None) -> LisaResult:
    ntl = np.asarray(ntl, dtype=float)
    area = np.asarray(area_km2, dtype=float)
    n = len(ntl)

    edge = edge_cell_mask(area, cell_size_m, edge_tol)
    lit = np.isfinite(ntl) & (ntl > lit_threshold)
    z = zscore_lit_only(ntl, lit_threshold, ref_mask=~edge, log_transform=log_transform)
    members = lit & ~edge & np.isfinite(z)
    nbr = build_queen_neighbors(cx, cy, cell_size_m, members)
    k = (nbr >= 0).sum(axis=1)
    focal = members & (k >= max(1, min_neighbors))

    I, lagz, p, q = local_moran(z, nbr, focal, members, perms, seed)
    
    valid_nbr = nbr >= 0  # Lọc các hàng xóm hợp lệ
    # Lấy cường độ NTL thực tế của các hàng xóm (nếu không hợp lệ thì gán 0)
    ntl_nbrs = np.where(valid_nbr, ntl[np.maximum(nbr, 0)], 0.0)
    # Tính trung bình cộng (Tổng NTL hàng xóm / số lượng hàng xóm k)
    # Nếu ô nào bị cô lập (k=0), gán cho nó giá trị NaN
    raw_lag = np.where(k > 0, ntl_nbrs.sum(axis=1) / k, np.nan)
                 
    sig = np.zeros(n, dtype=bool)
    f_idx = np.flatnonzero(focal)
    if f_idx.size:
        sig[f_idx] = bh_reject(p[f_idx], alpha) if fdr else (p[f_idx] < alpha)
    sig &= (q >= 0)

    label = np.full(n, NS, dtype=object)
    label[~lit & ~edge] = DARK
    label[edge] = EDGE
    for code, name in enumerate(QUADRANTS):
        label[sig & (q == code)] = name

    # ---- cụm HH liên thông ----
    is_hh = label == "High-High"
    cluster_id = np.full(n, -1, dtype=np.int64)
    n_clusters, largest_km2, cl_area = 0, 0.0, 0.0
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
            cluster_id[np.flatnonzero(is_hh)[big[inv]]] = ids[inv][big[inv]]

    # ---- biến cho panel ----
    tot = max(float(area.sum()), 1e-12)
    core = ~edge
    ana = max(float(area[members].sum()), 1e-12)
    m_tests = int(f_idx.size)
    p_floor = 1.0 / (perms + 1)
    row = dict(meta or {})
    row.update({
        "cell_size_m": cell_size_m,
        "n_cells": n, "n_cells_edge_masked": int(edge.sum()),
        "n_cells_lit": int(lit.sum()), "n_cells_tested": m_tests,
        "area_total_km2": round(tot, 4),
        "hh_area_share": float((area[is_hh]).sum() / tot),                 # ÷ tổng diện tích vùng
        "hh_area_share_of_tested": float(area[is_hh].sum() / ana),         # ÷ diện tích ô sáng đã kiểm định
        "hh_cluster_area_share": cl_area / tot,                            # chỉ cụm ≥ min_cluster_cells
        "ll_area_share": float(area[label == "Low-Low"].sum() / tot),
        "hl_area_share": float(area[label == "High-Low"].sum() / tot),
        "lh_area_share": float(area[label == "Low-High"].sum() / tot),
        "n_hh_clusters": n_clusters, "largest_hh_cluster_km2": largest_km2,
        "hotspot_dummy": int(n_clusters > 0),
        "gini_ntl_core_all": gini(ntl[core]),                              # ô đủ, gồm ô tối (cùng diện tích)
        "gini_ntl_core_lit": gini(ntl[core & lit]),                        # chỉ cường độ trong ô sáng
        "gini_sol_all": gini(ntl * area),                                  # tương thích Gini cũ của app
        "moran_I_lit": float(np.nanmean(I)) if np.isfinite(I).any() else float("nan"),
        "lit_area_share": float(area[lit].sum() / tot),
        # tham số để tái lập / pre-register
        "p_cfg_perms": perms, "p_cfg_alpha": alpha, "p_cfg_fdr": int(fdr),
        "p_cfg_log": int(log_transform), "p_cfg_lit_thr": lit_threshold,
        "p_cfg_edge_tol": edge_tol, "p_cfg_min_nbr": min_neighbors,
        "p_cfg_min_cluster": min_cluster_cells,
        "p_floor": p_floor,
        # cần ≥ số ô này đạt p tối thiểu thì BH mới có thể bác bỏ bất kỳ ô nào
        "fdr_min_hits_needed": int(math.ceil(p_floor * m_tests / alpha)) if (fdr and m_tests) else 0,
    })

    quad = np.array([QUADRANTS[c] if c >= 0 else "" for c in range(-1, 4)], dtype=object)[q.astype(int) + 1]
    cell_df = pd.DataFrame({
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
