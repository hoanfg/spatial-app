"""
lisa_diagnostics.py

"""
from __future__ import annotations

import math

import numpy as np

from .lisa_core import build_queen_neighbors, run_lisa

PERM_CHOICES = (199, 499, 999)
SEED_LIST = (42, 101, 202, 303, 404)
SEED_SD_LIMIT = 0.005
PRIMACY_LIMIT = 0.60
DARK_SHARE_LIMIT = 0.50


WORK_RATE = 1.5e7
HEAVY_WORK_LIMIT = 6e8



def jaccard(a, b) -> float:
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    u = int((a | b).sum())
    return 1.0 if u == 0 else float((a & b).sum() / u)


def winsorize_p99(ntl, q: float = 0.99):

    x = np.asarray(ntl, float)
    lit = x[np.isfinite(x) & (x > 0)]
    if lit.size == 0:
        return x.copy()
    return np.minimum(x, float(np.quantile(lit, q)))


def heavy_work_units(m_tests: int, perms: int, runs: int) -> float:
    return float(m_tests) * 8.0 * float(perms) * float(runs)


def estimate_seconds(m_tests: int, perms: int, runs: int) -> float:
    return heavy_work_units(m_tests, perms, runs) / WORK_RATE


def perm_power(m_tests: int, perms: int, alpha: float, fdr: bool = True,
               risky_ratio: float = 0.2) -> dict:
    """Assess whether the permutation floor gives BH enough resolving power.

    For a two-sided test, ``p_floor = 2/(perms+1)`` and the minimum rejected
    share is ``p_floor/alpha``. A share at or above one is infeasible.
    """
    p_floor = 2.0 / (perms + 1)
    out = {"p_floor": p_floor, "min_hits": 0, "ratio": 0.0, "infeasible": False,
           "risky": False, "suggested_perms": None, "applies": bool(fdr and m_tests > 0)}
    if not out["applies"]:
        return out
    ratio = p_floor / alpha
    out["ratio"] = float(ratio)
    out["min_hits"] = int(math.ceil(ratio * m_tests - 1e-9))
    out["infeasible"] = ratio >= 1.0 - 1e-9
    out["risky"] = (not out["infeasible"]) and ratio > risky_ratio + 1e-9
    for p in PERM_CHOICES:
        if p > perms and (2.0 / (p + 1)) / alpha <= risky_ratio + 1e-9:
            out["suggested_perms"] = p
            break
    if out["suggested_perms"] is None and perms < PERM_CHOICES[-1] and (out["infeasible"] or out["risky"]):
        out["suggested_perms"] = PERM_CHOICES[-1]
    return out


def ks_pareto(top_k, u_thr: float, alpha: float):
    """Compare ``top_k/u_thr`` with a Pareto CDF and return asymptotic KS results.

    Because alpha is estimated from the same sample, the p-value is approximate.
    """
    x = np.sort(np.asarray(top_k, float) / u_thr)
    k = x.size
    F = 1.0 - x ** (-alpha)
    D = float(max(np.max(np.arange(1, k + 1) / k - F), np.max(F - np.arange(0, k) / k)))
    lam = (math.sqrt(k) + 0.12 + 0.11 / math.sqrt(k)) * D
    p = 2.0 * sum((-1) ** (j - 1) * math.exp(-2.0 * j * j * lam * lam) for j in range(1, 101))
    return D, float(min(1.0, max(0.0, p)))


def hill_diagnostics(ntl, core, lit, tail_frac: float = 0.10) -> dict:

    ntl = np.asarray(ntl, float)
    vals = np.sort(ntl[np.asarray(core, bool) & np.asarray(lit, bool)])[::-1]
    nan = float("nan")
    res = {"alpha": nan, "se": nan, "ci_lo": nan, "ci_hi": nan, "k": 0, "ks_D": nan,
           "ks_p": nan, "power_law_ok": None, "tail_frac": tail_frac, "tied_threshold": False}
    if vals.size < 15:
        return res
    k = max(5, int(math.floor(tail_frac * vals.size)))
    u = float(max(vals[min(k, vals.size - 1)], 1e-9))
    top = vals[:k]
    xi = float(np.mean(np.log(np.maximum(top / u, 1.0))))
    res["k"] = k
    res["tied_threshold"] = bool(np.all(top <= u * (1 + 1e-12)))
    if xi <= 1e-6:
        return res
    a = 1.0 / xi
    se = a / math.sqrt(k)
    D, p = ks_pareto(top, u, a)
    res.update(alpha=a, se=se, ci_lo=a - 1.96 * se, ci_hi=a + 1.96 * se, ks_D=D, ks_p=p,
               power_law_ok=bool(p >= 0.05))
    return res


def tail_sensitivity(ntl, core, lit, fracs=(0.05, 0.10, 0.15)) -> dict:
    rows = [hill_diagnostics(ntl, core, lit, f) for f in fracs]
    al = [r["alpha"] for r in rows if np.isfinite(r["alpha"])]
    spread = float(max(al) - min(al)) if len(al) >= 2 else float("nan")
    return {"rows": rows, "spread": spread}


def cluster_primacy(region_metrics: dict) -> dict:
    n_cl = int(region_metrics.get("n_hh_clusters", 0))
    largest = float(region_metrics.get("largest_hh_cluster_km2", 0.0))
    tot = float(region_metrics.get("area_total_km2", 0.0))
    cl_area = float(region_metrics.get("hh_cluster_area_share", 0.0)) * tot
    primacy = float(largest / cl_area) if cl_area > 1e-12 else float("nan")
    return {"n_clusters": n_cl, "primacy": primacy,
            "multipolar": bool(n_cl >= 2 and np.isfinite(primacy) and primacy < PRIMACY_LIMIT)}


def resid_moran(cx, cy, ntl, area, dist_core_km, edge, cell_size_m: float,
                perms: int = 99, seed: int = 42, max_n_perm: int = 40_000) -> dict:
    """Compute Queen Moran's I for residuals from an area-weighted urban gradient.

    Permutations are skipped above ``max_n_perm``; large grids report I only.
    """
    cx, cy = np.asarray(cx, float), np.asarray(cy, float)
    ntl, area = np.asarray(ntl, float), np.asarray(area, float)
    d = np.asarray(dist_core_km, float)
    core = (~np.asarray(edge, bool)) & np.isfinite(ntl) & np.isfinite(d)
    nan = {"I": float("nan"), "p": float("nan"), "n": int(core.sum()), "flag": False, "perm_done": False}
    if core.sum() < 30:
        return nan
    y = np.log1p(np.maximum(ntl[core], 0.0))
    w = np.maximum(area[core], 1e-9)
    dd = d[core]
    if np.std(dd) < 1e-6 or np.std(y) < 1e-6:
        return nan
    X = np.column_stack([np.ones(dd.size), dd])
    sw = np.sqrt(w)
    beta = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]
    u = y - X @ beta
    u = u - u.mean()

    ci = np.flatnonzero(core)
    nbr = build_queen_neighbors(cx, cy, cell_size_m, core)
    valid = nbr >= 0
    k = valid.sum(axis=1)
    nb = np.maximum(nbr, 0)
    uf = np.zeros(cx.size)
    uf[ci] = u
    has = core & (k > 0)
    hi = np.flatnonzero(has)
    if hi.size < 10:
        return nan

    def _I(vec):
        lag = (vec[nb[hi]] * valid[hi]).sum(axis=1) / k[hi]
        den = float((vec[hi] ** 2).sum())
        return float((vec[hi] * lag).sum() / den) if den > 1e-12 else float("nan")

    I = _I(uf)
    out = {"I": I, "p": float("nan"), "n": int(core.sum()), "flag": False, "perm_done": False,
           "perms": int(perms), "descriptive_high_I": bool(np.isfinite(I) and I > 0.3)}
    if np.isfinite(I) and ci.size <= max_n_perm:
        rng = np.random.default_rng(seed)
        E = -1.0 / (hi.size - 1)
        ge = 0
        for _ in range(perms):
            up = np.zeros(cx.size)
            up[ci] = rng.permutation(u)
            ge += int(abs(_I(up) - E) >= abs(I - E) - 1e-12)
        out["p"] = (1 + ge) / (perms + 1)
        out["perm_done"] = True
        out["flag"] = bool(out["p"] < 0.05 and I > 0)
    # If permutation inference is skipped, I > 0.3 is a descriptive
    # threshold only. Never reuse the significance flag for this heuristic.
    return out



def dark_share(ntl, edge) -> dict:
    ntl = np.asarray(ntl, float)
    core = ~np.asarray(edge, bool)
    sh = float((ntl[core] <= 0).mean()) if core.any() else float("nan")
    return {"share": sh, "flag": bool(np.isfinite(sh) and sh > DARK_SHARE_LIMIT)}



def auto_diagnostics(cx, cy, ntl, area, cell_size_m, cell_df, region_metrics,
                     perms: int, alpha: float, fdr: bool, perm_auto_from=None) -> dict:

    ntl = np.asarray(ntl, float)
    area = np.asarray(area, float)
    edge = cell_df["is_edge_masked"].to_numpy().astype(bool)
    core = ~edge
    lit = (cell_df["is_dark"].to_numpy() == 0)

    pw = perm_power(int(region_metrics["n_cells_tested"]), perms, alpha, fdr)
    hd = hill_diagnostics(ntl, core, lit)
    pr = cluster_primacy(region_metrics)
    rm_ = resid_moran(cx, cy, ntl, area, cell_df["dist_to_core_km"].to_numpy(float), edge, cell_size_m)
    dk = dark_share(ntl, edge)

    items = []
    items.append({"key": "perm", "level": "warn" if (pw["infeasible"] or pw["risky"]) else "ok",
                  "vals": {**pw, "perms": perms, "alpha": alpha, "m": int(region_metrics["n_cells_tested"]),
                           "auto_from": perm_auto_from}})
    if not np.isfinite(hd["alpha"]):
        lvl = "info"
    elif hd["power_law_ok"] is False or hd["k"] < 20:
        lvl = "warn"
    else:
        lvl = "ok"
    items.append({"key": "hill", "level": lvl, "vals": hd})
    items.append({"key": "primacy", "level": "warn" if pr["multipolar"] else "ok", "vals": pr})
    items.append({"key": "resid", "level": ("info" if not np.isfinite(rm_["I"]) or not rm_["perm_done"]
                                              else ("warn" if rm_["flag"] else "ok")),
                  "vals": rm_})
    items.append({"key": "dark", "level": "warn" if dk["flag"] else "ok", "vals": dk})

    export = {
        "pareto_se": round(hd["se"], 4) if np.isfinite(hd["se"]) else float("nan"),
        "pareto_ks_p": round(hd["ks_p"], 4) if np.isfinite(hd["ks_p"]) else float("nan"),
        "pareto_k_tail": hd["k"],
        "cluster_primacy": round(pr["primacy"], 4) if np.isfinite(pr["primacy"]) else float("nan"),
        "resid_moran_I": round(rm_["I"], 4) if np.isfinite(rm_["I"]) else float("nan"),
        "resid_moran_p": round(rm_["p"], 4) if np.isfinite(rm_["p"]) else float("nan"),
        "resid_moran_inference_performed": int(rm_["perm_done"]),
        "resid_moran_descriptive_high_I": int(rm_.get("descriptive_high_I", False)),
        "dark_cell_share": round(dk["share"], 4) if np.isfinite(dk["share"]) else float("nan"),
        "perm_min_hits_ratio": round(pw["ratio"], 4),
        "perm_auto_raised": int(perm_auto_from is not None),
    }
    return {"items": items, "export": export, "n_warn": sum(1 for it in items if it["level"] == "warn")}



def seed_stability(run_kwargs: dict, seeds=SEED_LIST, progress=None) -> dict:

    shares = []
    for i, s in enumerate(seeds):
        kw = dict(run_kwargs)
        kw["seed"] = int(s)
        shares.append(float(run_lisa(**kw).region_metrics["hh_area_share"]))
        if progress:
            progress((i + 1) / len(seeds), f"seed {s}")
    sd = float(np.std(shares))
    return {"seeds": list(seeds), "shares": shares, "sd": sd, "mean": float(np.mean(shares)),
            "unstable": bool(sd > SEED_SD_LIMIT),
            "recommend_999": bool(sd > SEED_SD_LIMIT and run_kwargs.get("perms", 499) < 999)}


def method_sensitivity(run_kwargs: dict, base_hh, base_log: bool, progress=None) -> dict:

    ntl = np.asarray(run_kwargs["ntl"], float)
    hh = {}
    steps = [("raw", ntl, False), ("winsor", winsorize_p99(ntl), False), ("log", ntl, True)]
    for i, (name, x, lg) in enumerate(steps):
        if base_hh is not None and ((name == "raw" and not base_log) or (name == "log" and base_log)):
            hh[name] = np.asarray(base_hh, bool)
        else:
            kw = dict(run_kwargs)
            kw["ntl"] = x
            kw["log_transform"] = lg
            out = run_lisa(**kw)
            hh[name] = (out.cell_df["lisa_class"] == "High-High").to_numpy()
        if progress:
            progress((i + 1) / len(steps), name)
    area = np.asarray(run_kwargs["area_km2"], float)
    tot = max(float(area.sum()), 1e-12)
    return {
        "n_hh": {k: int(v.sum()) for k, v in hh.items()},
        "area_share": {k: float(area[v].sum() / tot) for k, v in hh.items()},
        "jaccard_raw_winsor": jaccard(hh["raw"], hh["winsor"]),
        "jaccard_raw_log": jaccard(hh["raw"], hh["log"]),
        "jaccard_winsor_log": jaccard(hh["winsor"], hh["log"]),
    }
