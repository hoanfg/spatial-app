from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from .lisa_diagnostics import HEAVY_WORK_LIMIT, estimate_seconds
from .robustness import (
    adjacent_years, default_specs, export_columns, hh_mask, maup_compare, run_specs, summarize, work_units,
)

_KEEP = 6
_VERDICT = {
    "vững": ("success", "Vững", "Robust"),
    "trung bình": ("info", "Trung bình", "Moderate"),
    "yếu": ("warning", "Yếu", "Fragile"),
    "không có HH": ("info", "Không có cụm HH để kiểm tra", "No HH cluster to test"),
    "n/a": ("info", "Không đủ dữ liệu", "Not enough data"),
}
_fragment = st.fragment if hasattr(st, "fragment") else (lambda f: f)


def _put(cache: dict, key, value) -> None:
    if key not in cache and len(cache) >= _KEEP:
        cache.pop(next(iter(cache)))
    cache[key] = value


def collect_robustness_export(ckey) -> dict:
    ss = st.session_state
    r = ss.get("_rob_cache", {}).get(ckey)
    if not r:
        return {}
    return export_columns(r["summary"], r.get("maup"), ss.get("_rob_years", {}).get(ckey))


@_fragment
def render_robustness(*, lang, ckey, out, grid_utm, size, perms, alpha, fdr, use_log, thr, min_clu, min_nbr,
                      year, fetch_year_ntl_fn=None, available_years=None):
    vi = lang != "en"
    rcache = st.session_state.setdefault("_rob_cache", {})
    ycache = st.session_state.setdefault("_rob_years", {})
    m = int(out.region_metrics["n_cells_tested"])
    cent = grid_utm.geometry.centroid
    area = grid_utm["area_km2"].to_numpy(float)
    base_kw = dict(
        cx=cent.x.to_numpy(), cy=cent.y.to_numpy(), ntl=grid_utm["ntl_mean"].to_numpy(float), area_km2=area,
        cell_size_m=size, lit_threshold=thr, edge_tol=0.99, perms=perms, alpha=alpha, fdr=fdr,
        log_transform=use_log, min_neighbors=min_nbr, min_cluster_cells=min_clu,
    )
    base_hh = hh_mask(out)
    specs = default_specs(base_kw)
    done = ckey in rcache
    verdict_tag = ""
    if done:
        verdict_tag = "  ·  " + _VERDICT.get(rcache[ckey]["summary"]["verdict"], _VERDICT["n/a"])[1 if vi else 2]
    title = ("🧪 Kiểm định độ vững" if vi else "🧪 Robustness checks") + verdict_tag

    with st.expander(title, expanded=False):
        st.caption(("Chạy lại LISA với nhiều đặc tả khác (trọng số, ngưỡng, biến đổi, α/FDR, lưới thô hơn, năm kề) rồi đo mức trùng của tập ô High-High "
                    "với bản gốc bằng hệ số Jaccard. Nếu kết luận đổi theo lựa chọn phân tích, nó không nên được báo cáo như một phát hiện chắc chắn."
                    if vi else
                    "Re-runs LISA under other specifications (weights, threshold, transforms, α/FDR, coarser grid, adjacent years) and measures "
                    "overlap of the High-High set with the baseline by Jaccard. If the conclusion changes with analytic choices, it should not "
                    "be reported as a firm finding."))
        w = work_units(m, perms, len(specs), True)
        too_big = w > HEAVY_WORK_LIMIT or m <= 0
        st.caption((f"{len(specs)} biến thể + lưới thô hơn 2×2; ước tính thô ≈ {estimate_seconds(m, perms, len(specs) + 1):.0f}s trên máy yếu. Kết quả được lưu đệm."
                    if vi else f"{len(specs)} variants + a 2×2 coarser grid; rough estimate ≈ {estimate_seconds(m, perms, len(specs) + 1):.0f}s on a weak machine. Cached."))
        if too_big:
            st.warning("Vùng quá lớn cho bộ kiểm định này: hãy tăng kích thước ô hoặc giảm số hoán vị." if vi
                       else "Area too large for this suite: use a coarser cell size or fewer permutations.")

        years_ok = []
        if fetch_year_ntl_fn and available_years:
            years_ok = [y for y in (year - 1, year + 1) if y in set(available_years)]
        with_years = False
        if years_ok:
            with_years = st.checkbox(
                ("Thêm so sánh với năm kề: " if vi else "Add adjacent years: ") + ", ".join(map(str, years_ok)),
                key="rob_years_chk",
                help=("Tải NTL của năm kề từ Earth Engine và chạy lại LISA cùng tham số. Chậm hơn." if vi
                      else "Fetches NTL for adjacent years from Earth Engine and re-runs LISA with the same parameters. Slower."))

        run = st.button(("✅ " if done else "▶ ") + ("Chạy kiểm định độ vững" if vi else "Run robustness checks"),
                        key="rob_btn_run", disabled=too_big, use_container_width=True)
        if run:
            if done and not (with_years and ckey not in ycache):
                st.toast("Đã có kết quả lưu đệm" if vi else "Cached result available", icon="✅")
            else:
                try:
                    if not done:
                        bar = st.progress(0.0, text="Kiểm định độ vững" if vi else "Robustness checks")
                        table, mat = run_specs(base_kw, specs, base_hh,
                                               progress=lambda f, t: bar.progress(min(1.0, f * 0.9), text=t))
                        summ = summarize(table, mat, area)
                        maup = maup_compare(base_kw, base_hh, 2)
                        bar.empty()
                        _put(rcache, ckey, {"table": table, "summary": summ, "maup": maup})
                    if with_years and ckey not in ycache:
                        with st.spinner("Đang tải NTL năm kề..." if vi else "Fetching adjacent-year NTL..."):
                            arrs = {}
                            for y in years_ok:
                                a = fetch_year_ntl_fn(y)
                                if a is not None and len(a) == len(area):
                                    arrs[y] = a
                            if arrs:
                                _put(ycache, ckey, adjacent_years(base_kw, base_hh, arrs))
                    st.toast("Hoàn tất kiểm định độ vững" if vi else "Robustness checks done", icon="✅")
                    st.rerun()  # để dòng panel/CSV nhận các cột rob_*
                except Exception as e:  # noqa: BLE001
                    st.error(f"{'Lỗi' if vi else 'Error'}: {e}")

        r = rcache.get(ckey)
        if not r:
            return
        s, table, maup = r["summary"], r["table"], r.get("maup")
        kind, lab_vi, lab_en = _VERDICT.get(s["verdict"], _VERDICT["n/a"])
        getattr(st, kind)((f"Kết luận độ vững: **{lab_vi}**" if vi else f"Robustness verdict: **{lab_en}**") +
                          ((f" (Jaccard trung vị {s['median_jaccard']:.2f}, nhỏ nhất {s['min_jaccard']:.2f})" if vi else
                            f" (median Jaccard {s['median_jaccard']:.2f}, min {s['min_jaccard']:.2f})")
                           if s["n_specs"] and np.isfinite(s["median_jaccard"]) and s["verdict"] != "không có HH" else ""))
        if s["verdict"] == "không có HH":
            st.caption("Bản gốc không có ô HH (thường do ít hoán vị so với FDR). Jaccard của hai tập rỗng bằng 1 nhưng không phải bằng chứng về độ vững."
                       if vi else "The baseline has no HH cells (often too few permutations for FDR). The Jaccard of two empty sets is 1, which is not evidence of robustness.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Biến thể Jaccard ≥ 0,70" if vi else "Variants with Jaccard ≥ 0.70", f"{s['n_stable']}/{s['n_specs']}",
                      help="Ngưỡng 0,70 và 0,50 là quy ước thực hành, không phải ngưỡng thống kê." if vi
                      else "The 0.70 and 0.50 cut-offs are rules of thumb, not statistical thresholds.")
            c2.metric("Lõi vững (diện tích)" if vi else "Robust core (area)", f"{s['robust_core_share'] * 100:.2f}%",
                      help="Phần diện tích vùng là HH ở bản gốc và ở ít nhất 80% số lần chạy." if vi
                      else "Share of area that is HH in the baseline and in at least 80% of runs.")
            c3.metric("Ô lõi vững" if vi else "Robust core cells", f"{s.get('robust_core_cells', 0):,}")
        show = table.copy()
        show["% diện tích HH"] = show["% diện tích HH"].round(2)
        show["Jaccard"] = show["Jaccard"].round(3)
        st.dataframe(show.drop(columns=["Nhóm"]), hide_index=True, use_container_width=True)
        if maup:
            st.markdown("**" + ("Lưới thô hơn (MAUP, 2×2)" if vi else "Coarser grid (MAUP, 2×2)") + "**")
            st.caption((f"HH ở lưới mịn: {maup['n_hh_fine']:,} ô ({maup['area_share_fine'] * 100:.2f}% diện tích); lưới thô: {maup['n_hh_coarse']:,} ô "
                        f"({maup['area_share_coarse'] * 100:.2f}%). Phần diện tích HH mịn nằm trong ô HH thô: "
                        f"{maup['fine_inside_coarse'] * 100:.0f}%." if vi and np.isfinite(maup["fine_inside_coarse"]) else
                        f"Fine-grid HH: {maup['n_hh_fine']:,} cells ({maup['area_share_fine'] * 100:.2f}% of area); coarse grid: "
                        f"{maup['n_hh_coarse']:,} cells ({maup['area_share_coarse'] * 100:.2f}%)."))
        y = ycache.get(ckey)
        if y is not None and len(y):
            st.markdown("**" + ("Năm kề" if vi else "Adjacent years") + "**")
            yy = y.copy()
            yy["% diện tích HH"] = yy["% diện tích HH"].round(2)
            yy["Jaccard so với năm gốc"] = yy["Jaccard so với năm gốc"].round(3)
            st.dataframe(yy, hide_index=True, use_container_width=True)
        csv = show.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ CSV" , csv, file_name=f"robustness_{year}.csv", mime="text/csv", key="rob_dl")
