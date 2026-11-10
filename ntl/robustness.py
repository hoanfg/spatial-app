"""Kiểm định độ vững: kết luận LISA có đổi khi đổi đặc tả hay không.

Mỗi biến thể chạy lại run_lisa với một thay đổi, rồi so tập ô High-High với bản gốc bằng hệ số Jaccard.
Chỉ dùng numpy và pandas, không import streamlit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .lisa_core import run_lisa
from .lisa_diagnostics import heavy_work_units, jaccard, winsorize_p99

STABLE_JACCARD = 0.70     # trung vị Jaccard từ mức này: kết quả vững
FRAGILE_JACCARD = 0.50    # dưới mức này: kết quả yếu
CORE_FRACTION = 0.80      # ô thuộc "lõi vững" nếu là HH trong ít nhất tỷ lệ này số lần chạy


def hh_mask(result) -> np.ndarray:
    return (result.cell_df["lisa_class"] == "High-High").to_numpy()


def default_specs(base: dict) -> list[dict]:
    """Danh sách biến thể. Mỗi biến thể: name, group, overrides (kwargs của run_lisa), transform (hàm trên ntl hoặc None)."""
    thr = float(base.get("lit_threshold", 0.0))
    alpha = float(base.get("alpha", 0.05))
    is_log = bool(base.get("log_transform", False))
    specs = [
        {"name": "Trọng số Rook (4 láng giềng)", "group": "weights", "overrides": {"weights": "rook"}},
        {"name": f"Ngưỡng ô sáng {thr + 0.5:g}", "group": "threshold",
         "overrides": {"lit_threshold": thr + 0.5}},
        {"name": f"Ngưỡng ô sáng {thr + 1.0:g}", "group": "threshold",
         "overrides": {"lit_threshold": thr + 1.0}},
        {"name": "Cắt P99 trước z-score", "group": "transform", "overrides": {"log_transform": False},
         "transform": "winsor"},
        {"name": "asinh(NTL)", "group": "transform",
         "overrides": {"lit_threshold": float(np.arcsinh(thr)), "log_transform": False}, "transform": "asinh"},
        {"name": "Thô (không ln)" if is_log else "ln(NTL)", "group": "transform",
         "overrides": {"log_transform": not is_log}},
        {"name": f"α = {alpha / 5:g}", "group": "inference", "overrides": {"alpha": alpha / 5}},
        {"name": f"α = {min(alpha * 2, 0.2):g}", "group": "inference", "overrides": {"alpha": min(alpha * 2, 0.2)}},
        {"name": "Không hiệu chỉnh FDR" if base.get("fdr", True) else "Có hiệu chỉnh FDR",
         "group": "inference", "overrides": {"fdr": not base.get("fdr", True)}},
    ]
    return specs


def _apply_transform(ntl, kind):
    if kind == "winsor":
        return winsorize_p99(ntl)
    if kind == "asinh":
        return np.arcsinh(np.asarray(ntl, float))
    return np.asarray(ntl, float)


def run_specs(base: dict, specs: list[dict], base_hh, progress=None) -> tuple[pd.DataFrame, np.ndarray]:
    """Chạy các biến thể. Trả (bảng kết quả, ma trận HH kích thước (số_ô, số_biến_thể + 1) với cột 0 là bản gốc)."""
    area = np.asarray(base["area_km2"], float)
    tot = max(float(area.sum()), 1e-12)
    base_hh = np.asarray(base_hh, bool)
    cols = [base_hh]
    rows = [{"Biến thể": "Bản gốc", "Nhóm": "base", "Số ô HH": int(base_hh.sum()),
             "% diện tích HH": float(area[base_hh].sum() / tot * 100), "Jaccard": 1.0}]
    for i, sp in enumerate(specs):
        kw = dict(base)
        kw.update(sp.get("overrides", {}))
        kw["ntl"] = _apply_transform(base["ntl"], sp.get("transform"))
        hh = hh_mask(run_lisa(**kw))
        cols.append(hh)
        rows.append({"Biến thể": sp["name"], "Nhóm": sp["group"], "Số ô HH": int(hh.sum()),
                     "% diện tích HH": float(area[hh].sum() / tot * 100), "Jaccard": jaccard(base_hh, hh)})
        if progress:
            progress((i + 1) / len(specs), sp["name"])
    return pd.DataFrame(rows), np.column_stack(cols)


def summarize(table: pd.DataFrame, hh_matrix: np.ndarray, area, core=None) -> dict:
    """Tóm tắt: Jaccard nhỏ nhất/trung vị, số biến thể vững, diện tích 'lõi vững' và nhãn kết luận."""
    area = np.asarray(area, float)
    var = table[table["Nhóm"] != "base"]
    if var.empty:
        return {"n_specs": 0, "min_jaccard": float("nan"), "median_jaccard": float("nan"),
                "n_stable": 0, "robust_core_share": float("nan"), "verdict": "n/a"}
    j = var["Jaccard"].to_numpy(float)
    med = float(np.median(j))
    base_col = hh_matrix[:, 0]
    freq = hh_matrix.mean(axis=1)
    core_cells = base_col & (freq >= CORE_FRACTION)
    tot = max(float(area.sum()), 1e-12)
    verdict = "vững" if med >= STABLE_JACCARD else ("trung bình" if med >= FRAGILE_JACCARD else "yếu")
    if not base_col.any():
        verdict = "không có HH"   # Jaccard của hai tập rỗng là 1, nhưng đó không phải bằng chứng về độ vững
    return {
        "n_specs": int(len(var)),
        "min_jaccard": float(j.min()),
        "median_jaccard": med,
        "n_stable": int((j >= STABLE_JACCARD).sum()),
        "robust_core_share": float(area[core_cells].sum() / tot),
        "robust_core_cells": int(core_cells.sum()),
        "verdict": verdict,
    }


def aggregate_blocks(cx, cy, ntl, area, cell_size_m: float, factor: int = 2) -> dict:
    """Gộp factor x factor ô thành một ô lớn: NTL trung bình theo diện tích, diện tích cộng dồn.

    Ô lớn nằm ở biên (tổng diện tích nhỏ hơn ô đầy đủ) sẽ bị run_lisa đánh dấu là ô biên như thường."""
    cx, cy = np.asarray(cx, float), np.asarray(cy, float)
    ntl, area = np.asarray(ntl, float), np.asarray(area, float)
    ix = np.floor((cx + 1e-6) / cell_size_m).astype(np.int64)
    iy = np.floor((cy + 1e-6) / cell_size_m).astype(np.int64)
    bx, by = ix // factor, iy // factor
    df = pd.DataFrame({"bx": bx, "by": by, "a": area, "wx": area * np.nan_to_num(ntl), "ax": area * cx, "ay": area * cy})
    g = df.groupby(["bx", "by"], sort=True).agg(a=("a", "sum"), wx=("wx", "sum"), ax=("ax", "sum"), ay=("ay", "sum"))
    big = float(cell_size_m * factor)
    # tâm lưới đều của ô lớn, không phải trọng tâm thật, để build_queen_neighbors dò đúng chỉ số
    bxs = g.index.get_level_values("bx").to_numpy()
    bys = g.index.get_level_values("by").to_numpy()
    return {
        "cx": (bxs + 0.5) * big, "cy": (bys + 0.5) * big,
        "ntl": (g["wx"] / g["a"]).to_numpy(), "area_km2": g["a"].to_numpy(),
        "cell_size_m": big, "block_of_cell": np.column_stack([bx, by]),
        "block_keys": np.column_stack([bxs, bys]),
    }


def maup_compare(base: dict, base_hh, factor: int = 2) -> dict:
    """So sánh với lưới thô hơn factor lần: diện tích HH hai bên và mức trùng không gian."""
    agg = aggregate_blocks(base["cx"], base["cy"], base["ntl"], base["area_km2"], base["cell_size_m"], factor)
    kw = {k: v for k, v in base.items() if k not in ("cx", "cy", "ntl", "area_km2", "cell_size_m")}
    kw.update(cx=agg["cx"], cy=agg["cy"], ntl=agg["ntl"], area_km2=agg["area_km2"], cell_size_m=agg["cell_size_m"])
    res = run_lisa(**kw)
    hh_big = hh_mask(res)
    base_hh = np.asarray(base_hh, bool)
    area = np.asarray(base["area_km2"], float)
    # ô nhỏ nằm trong ô lớn nào
    lookup = {(int(a), int(b)): i for i, (a, b) in enumerate(agg["block_keys"])}
    owner = np.array([lookup[(int(a), int(b))] for a, b in agg["block_of_cell"]])
    fine_in_hh_big = hh_big[owner]
    area_big = np.asarray(agg["area_km2"], float)
    hh_area = float(area[base_hh].sum())
    big_area = float(area_big[hh_big].sum())
    tot_fine = max(float(area.sum()), 1e-12)
    any_fine_hh = np.bincount(owner, weights=base_hh.astype(float), minlength=len(hh_big)) > 0
    return {
        "factor": int(factor),
        "n_hh_fine": int(base_hh.sum()), "n_hh_coarse": int(hh_big.sum()),
        "area_share_fine": hh_area / tot_fine,
        "area_share_coarse": big_area / max(float(area_big.sum()), 1e-12),
        # phần diện tích HH ở lưới mịn rơi vào ô HH của lưới thô, và ngược lại
        "fine_inside_coarse": float(area[base_hh & fine_in_hh_big].sum() / hh_area) if hh_area > 0 else float("nan"),
        "coarse_covered_by_fine": float(area_big[hh_big & any_fine_hh].sum() / big_area) if big_area > 0 else float("nan"),
    }


def adjacent_years(base: dict, base_hh, ntl_by_year: dict, progress=None) -> pd.DataFrame:
    """Chạy lại LISA với cùng tham số cho các năm kề, so tập HH với năm gốc."""
    area = np.asarray(base["area_km2"], float)
    tot = max(float(area.sum()), 1e-12)
    base_hh = np.asarray(base_hh, bool)
    rows = []
    items = sorted(ntl_by_year.items())
    for i, (year, ntl) in enumerate(items):
        kw = dict(base)
        kw["ntl"] = np.asarray(ntl, float)
        hh = hh_mask(run_lisa(**kw))
        rows.append({"Năm": int(year), "Số ô HH": int(hh.sum()),
                     "% diện tích HH": float(area[hh].sum() / tot * 100), "Jaccard so với năm gốc": jaccard(base_hh, hh)})
        if progress:
            progress((i + 1) / len(items), str(year))
    return pd.DataFrame(rows)


def work_units(m_tests: int, perms: int, n_specs: int, with_maup: bool = True) -> float:
    """Khối lượng tính ước lượng, cùng thang đo với lisa_diagnostics.heavy_work_units."""
    return heavy_work_units(m_tests, perms, n_specs + (1 if with_maup else 0))


def export_columns(summary: dict, maup: dict | None = None, years: pd.DataFrame | None = None) -> dict:
    out = {}
    if summary and summary.get("n_specs"):
        out.update({
            "rob_n_specs": summary["n_specs"],
            "rob_min_jaccard": round(summary["min_jaccard"], 4),
            "rob_median_jaccard": round(summary["median_jaccard"], 4),
            "rob_robust_core_share": round(summary["robust_core_share"], 6),
        })
    if maup:
        out["rob_maup_fine_inside_coarse"] = round(maup["fine_inside_coarse"], 4) if np.isfinite(maup["fine_inside_coarse"]) else float("nan")
    if years is not None and len(years):
        out["rob_adjacent_year_min_jaccard"] = round(float(years["Jaccard so với năm gốc"].min()), 4)
    return out
