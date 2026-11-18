"""
ntl_distribution.py

  lorenz_df      Đường cong Lorenz của SOL theo ô (khớp với gini() của app).
  ranksize_df    Rank-size log-log của ô sáng + đường Pareto theo Hill (cùng định nghĩa đuôi với lisa_core).
  radial_df      NTL trung bình (theo diện tích) theo vòng cách ô sáng nhất.
  hist_share_df  % số ô và % tổng ánh sáng theo từng khoảng NTL.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

MAX_POINTS = 400


def gini(values) -> float:
    """Return the Gini coefficient for a finite, nonnegative sample.

    Invalid values are rejected instead of being silently removed because
    dropping observations changes the population represented by the result.
    Empty and all-zero samples retain the application's documented value 0.
    """
    x = np.asarray(values, dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("Gini values must be finite")
    if np.any(x < 0.0):
        raise ValueError("Gini values must be nonnegative")
    total = float(x.sum())
    if x.size == 0 or total <= 0.0:
        return 0.0
    x = np.sort(x)
    n = x.size
    idx = np.arange(1, n + 1, dtype=float)
    return float(2.0 * np.sum(idx * x) / (n * total) - (n + 1.0) / n)

def _thin_indices(n: int, max_points: int = MAX_POINTS) -> np.ndarray:

    if n <= max_points:
        return np.arange(n)
    idx = np.unique(np.round(np.geomspace(1, n, max_points)).astype(int) - 1)
    return np.unique(np.concatenate([idx, [0, n - 1]]))


def lorenz_df(sol_cell) -> tuple[pd.DataFrame, float]:

    x = np.asarray(sol_cell, dtype=float)
    gini_v = gini(x)
    x = np.sort(x)
    n, total = x.size, float(x.sum())
    if n == 0 or total <= 0:
        return pd.DataFrame({"cum_cells": [0.0, 1.0], "cum_sol": [0.0, 1.0]}), 0.0
    cum = np.concatenate([[0.0], np.cumsum(x) / total])
    frac = np.arange(n + 1) / n
    keep = _thin_indices(n + 1)
    return pd.DataFrame({"cum_cells": frac[keep], "cum_sol": cum[keep]}), gini_v


def ranksize_df(ntl, core, tail_frac: float = 0.10):
    """Return thinned rank-size points, a Pareto fit, and fit metadata.

    Metadata is omitted when fewer than 15 lit core cells are available.
    """
    ntl = np.asarray(ntl, float)
    vals = np.sort(ntl[np.asarray(core, bool) & (ntl > 0)])[::-1]
    if vals.size == 0:
        return pd.DataFrame({"rank": [], "ntl": []}), pd.DataFrame({"rank": [], "fit": []}), None
    keep = _thin_indices(vals.size)
    pts = pd.DataFrame({"rank": keep + 1, "ntl": vals[keep]})
    if vals.size < 15:
        return pts, pd.DataFrame({"rank": [], "fit": []}), None
    k = max(5, int(math.floor(tail_frac * vals.size)))
    u = float(max(vals[min(k, vals.size - 1)], 1e-9))
    xi = float(np.mean(np.log(np.maximum(vals[:k] / u, 1.0))))
    if xi <= 1e-6:
        return pts, pd.DataFrame({"rank": [], "fit": []}), None
    alpha = 1.0 / xi
    r = np.arange(1, k + 1, dtype=float)
    fit = pd.DataFrame({"rank": r, "fit": u * (r / k) ** (-1.0 / alpha)})
    return pts, fit, {"alpha": alpha, "k": k, "u": u, "n_lit": int(vals.size)}


def radial_df(cx, cy, ntl, area, width_km: float = 1.0) -> pd.DataFrame:

    cx, cy = np.asarray(cx, float), np.asarray(cy, float)
    ntl, area = np.asarray(ntl, float), np.asarray(area, float)
    if ntl.size == 0 or not np.isfinite(ntl).any():
        return pd.DataFrame({"dist_km": [], "mean_ntl": [], "cells": []})
    c = int(np.argmax(ntl))
    d = np.hypot(cx - cx[c], cy - cy[c]) / 1000.0
    ring = np.floor(d / width_km).astype(int)
    df = pd.DataFrame({"ring": ring, "w": area, "wx": area * ntl})
    g = df.groupby("ring").agg(w=("w", "sum"), wx=("wx", "sum"), cells=("w", "size"))
    out = pd.DataFrame({
        "dist_km": (g.index.to_numpy() + 0.5) * width_km,
        "mean_ntl": np.where(g["w"].to_numpy() > 0, g["wx"].to_numpy() / np.maximum(g["w"].to_numpy(), 1e-12), 0.0),
        "cells": g["cells"].to_numpy(),
    })
    return out.reset_index(drop=True)


def hist_share_df(ntl, area, edges, labels) -> pd.DataFrame:

    ntl, area = np.asarray(ntl, float), np.asarray(area, float)
    cats = pd.cut(ntl, bins=edges, labels=list(labels))
    sol_cell = ntl * area
    n, sol = ntl.size, float(sol_cell.sum())
    cells = pd.Series(1.0, index=range(n)).groupby(cats, observed=False).sum().reindex(list(labels), fill_value=0.0)
    sols = pd.Series(sol_cell).groupby(cats, observed=False).sum().reindex(list(labels), fill_value=0.0)
    rows = []
    for lb in labels:
        rows.append({"bin": lb, "series": "cells", "pct": float(cells[lb]) / n * 100 if n else 0.0})
        rows.append({"bin": lb, "series": "sol", "pct": float(sols[lb]) / sol * 100 if sol > 0 else 0.0})
    return pd.DataFrame(rows)
