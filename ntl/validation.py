from __future__ import annotations

import numpy as np
import pandas as pd

RHO_STRONG = 0.60   # quy ước thực hành: từ mức này coi là tương quan mạnh
RHO_WEAK = 0.40     # dưới mức này coi là yếu
MIN_CELLS = 30
BLOCK_CELLS = 5     # cạnh khối (tính bằng ô) khi bootstrap theo khối


def _rank(x) -> np.ndarray:
    return pd.Series(np.asarray(x, float)).rank(method="average").to_numpy()


def spearman(x, y) -> float:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.size < 3:
        return float("nan")
    rx, ry = _rank(x), _rank(y)
    if rx.std() < 1e-12 or ry.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def auc_top_quartile(ntl, proxy) -> float:
    """Xác suất một ô thuộc 25% mật độ proxy cao nhất có NTL cao hơn một ô còn lại (Mann–Whitney)."""
    ntl, proxy = np.asarray(ntl, float), np.asarray(proxy, float)
    cut = np.quantile(proxy, 0.75)
    pos = proxy >= cut
    n1, n0 = int(pos.sum()), int((~pos).sum())
    if n1 == 0 or n0 == 0 or cut <= proxy.min():
        return float("nan")
    r = _rank(ntl)
    return float((r[pos].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def block_bootstrap_rho(ntl, proxy, cx, cy, cell_size_m: float, b: int = 200, seed: int = 42,
                        block_cells: int = BLOCK_CELLS) -> tuple[float, float]:
    """Khoảng 95% của Spearman khi lấy mẫu lại theo khối ô kề nhau (tôn trọng tự tương quan không gian)."""
    ntl, proxy = np.asarray(ntl, float), np.asarray(proxy, float)
    cx, cy = np.asarray(cx, float), np.asarray(cy, float)
    step = cell_size_m * block_cells
    key = (np.floor(cx / step).astype(np.int64) * 1_000_003 + np.floor(cy / step).astype(np.int64))
    ids, inv = np.unique(key, return_inverse=True)
    if ids.size < 5:
        return float("nan"), float("nan")
    members = [np.flatnonzero(inv == i) for i in range(ids.size)]
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(b):
        pick = rng.integers(0, ids.size, ids.size)
        idx = np.concatenate([members[i] for i in pick])
        out.append(spearman(ntl[idx], proxy[idx]))
    out = np.asarray([v for v in out if np.isfinite(v)])
    if out.size < max(10, b // 4):
        return float("nan"), float("nan")
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def proxy_agreement(ntl, proxy_sum, area_km2, cx, cy, cell_size_m: float, core=None, b: int = 200) -> dict:
    """Mức đồng thuận giữa NTL và mật độ của proxy (tổng proxy trong ô / diện tích ô)."""
    ntl, proxy_sum, area = (np.asarray(v, float) for v in (ntl, proxy_sum, area_km2))
    ok = np.isfinite(ntl) & np.isfinite(proxy_sum) & (area > 0)
    if core is not None:
        ok &= np.asarray(core, bool)
    n = int(ok.sum())
    out = {"n": n, "rho": float("nan"), "ci_lo": float("nan"), "ci_hi": float("nan"),
           "auc": float("nan"), "level": "n/a", "proxy_zero_share": float("nan")}
    if n < MIN_CELLS:
        return out
    dens = proxy_sum[ok] / area[ok]
    out["proxy_zero_share"] = float((dens <= 0).mean())
    out["rho"] = spearman(ntl[ok], dens)
    out["ci_lo"], out["ci_hi"] = block_bootstrap_rho(ntl[ok], dens, np.asarray(cx)[ok], np.asarray(cy)[ok],
                                                     cell_size_m, b=b)
    out["auc"] = auc_top_quartile(ntl[ok], dens)
    r = out["rho"]
    out["level"] = "n/a" if not np.isfinite(r) else ("mạnh" if r >= RHO_STRONG else ("vừa" if r >= RHO_WEAK else "yếu"))
    return out


def compare_clipping(ntl_clipped, ntl_unclipped, rel_tol: float = 0.10) -> dict:
    """So NTL khi cắt giá trị âm về 0 với khi giữ nguyên: mức lệch và thứ hạng ô có đổi không."""
    a, b = np.asarray(ntl_clipped, float), np.asarray(ntl_unclipped, float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return {"n": int(ok.sum()), "rho": float("nan"), "share_changed": float("nan"), "max_abs_diff": float("nan")}
    a, b = a[ok], b[ok]
    diff = np.abs(a - b)
    scale = np.maximum(np.abs(a), 1e-9)
    changed = (diff > 1e-9) & (diff / scale > rel_tol)
    return {"n": int(ok.sum()), "rho": spearman(a, b), "share_changed": float(changed.mean()),
            "max_abs_diff": float(diff.max())}


def export_columns(val: dict | None, tag: str) -> dict:
    """Cột đưa vào dòng panel; tag là 'built' hoặc 'pop'."""
    if not val or val.get("n", 0) < MIN_CELLS:
        return {}
    return {
        f"val_rho_{tag}": round(val["rho"], 4) if np.isfinite(val["rho"]) else float("nan"),
        f"val_rho_{tag}_ci_lo": round(val["ci_lo"], 4) if np.isfinite(val["ci_lo"]) else float("nan"),
        f"val_rho_{tag}_ci_hi": round(val["ci_hi"], 4) if np.isfinite(val["ci_hi"]) else float("nan"),
        f"val_auc_{tag}": round(val["auc"], 4) if np.isfinite(val["auc"]) else float("nan"),
    }
