from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from . import ee_extra
from .performance import measured_call
from .data_quality import cell_report, obs_report, quality_export, quality_flags, raster_report  # noqa: F401
from .formatting import fmt_p  # noqa: F401
from .lisa_core import edge_cell_mask
from .validation import MIN_CELLS, compare_clipping, export_columns as val_export, proxy_agreement
from .zonal import zonal_stat

_ICON = {"ok": "✅", "warn": "⚠️", "info": "ℹ️"}
_PROXY_LABEL = {
    "built": ("Diện tích xây dựng (GHSL)", "Built-up surface (GHSL)"),
    "pop": ("Dân số (GHSL)", "Population (GHSL)"),
}
_KEEP = 8   # số kết quả giữ lại trong session cho mỗi loại


def _put(cache: dict, key, value) -> None:
    if key not in cache and len(cache) >= _KEEP:
        cache.pop(next(iter(cache)))
    cache[key] = value


def _bbox(grid_wgs) -> tuple:
    x0, y0, x1, y1 = grid_wgs.total_bounds
    pad = 0.005   # cùng khoảng đệm với pipeline chính
    return (round(x0 - pad, 5), round(y0 - pad, 5), round(x1 + pad, 5), round(y1 + pad, 5))


def _line(it: dict, vi: bool) -> str:
    k, v, ic = it["key"], it["vals"], _ICON[it["level"]]
    if k == "nodata":
        t = (f"**Pixel không có giá trị (NaN/inf):** {v['nodata_share'] * 100:.2f}% trong {v['n_pixels']:,} pixel. "
             "Pipeline đổi các pixel này thành 0." if vi else
             f"**Pixels without a value (NaN/inf):** {v['nodata_share'] * 100:.2f}% of {v['n_pixels']:,} pixels. "
             "The pipeline turns them into 0.")
    elif k == "neg":
        t = (f"**Bức xạ âm (nhiễu nền):** {v['neg_share'] * 100:.1f}% pixel, nhỏ nhất {v['min']:.2f}. "
             "Giá trị âm bị cắt về 0 trước khi lấy trung bình." if vi else
             f"**Negative radiance (background noise):** {v['neg_share'] * 100:.1f}% of pixels, minimum {v['min']:.2f}. "
             "Negatives are clipped to 0 before averaging.")
        if it["level"] == "warn":
            t += (" Tỷ lệ cao: hãy chạy 'So sánh không cắt giá trị âm' bên dưới." if vi
                  else " High share: run 'Compare without clipping negatives' below.")
    elif k == "missing":
        t = (f"**Ô không có kết quả trích xuất:** {v['cells_missing_stats']} trên {v['n_cells']:,} ô. "
             "Các ô này bị tính là 0 (tối)." if vi else
             f"**Cells without an extracted value:** {v['cells_missing_stats']} of {v['n_cells']:,}. "
             "They are counted as 0 (dark).")
    elif k == "zero":
        t = (f"**Ô bằng 0:** {v['zero_cell_share'] * 100:.0f}% số ô. Tỷ lệ cao làm ln(1+NTL) nhạy với đơn vị đo." if vi
             else f"**Zero cells:** {v['zero_cell_share'] * 100:.0f}% of cells. A high share makes ln(1+NTL) scale-sensitive.")
    else:   # obs
        t = (f"**Số tháng quan sát không mây:** trung vị {v['median_months']:.0f} tháng/pixel; "
             f"{v['no_obs_share'] * 100:.1f}% pixel không có tháng nào (đang bị tính là tối), "
             f"{v['low_obs_share'] * 100:.1f}% dưới {v['min_months']} tháng." if vi else
             f"**Cloud-free months:** median {v['median_months']:.0f} per pixel; "
             f"{v['no_obs_share'] * 100:.1f}% of pixels have none (counted as dark), "
             f"{v['low_obs_share'] * 100:.1f}% have fewer than {v['min_months']}.")
    return f"{ic} {t}"


def collect_quality_export(ts: str) -> dict:
    """Cột chất lượng và kiểm chứng đã tính cho lần chạy `ts`, để ghép vào dòng panel."""
    ss = st.session_state
    res_q = ss.get("_dq_base", {}).get(ts)
    if not res_q:
        return {}
    out = quality_export(res_q["raster"], res_q["cells"], ss.get("_dq_obs", {}).get(ts))
    clip = ss.get("_dq_clip", {}).get(ts)
    if clip:
        out["dq_clip_rho"] = round(clip["rho"], 4) if np.isfinite(clip["rho"]) else float("nan")
        out["dq_clip_share_changed"] = round(clip["share_changed"], 6)
    for tag in ("built", "pop"):
        v = ss.get("_dq_val", {}).get((ts, tag))
        if v:
            out.update(val_export(v["agree"], tag))
    return out


@st.fragment if hasattr(st, "fragment") else (lambda f: f)
def render_quality_panel(*, res, grid_utm, lang, ee, dataset, scale_m):
    vi = lang != "en"
    ts, size, year = res["ts"], int(res["size"]), int(res["year"])
    dq = res.get("data_quality")
    ss = st.session_state
    ss.setdefault("_dq_base", {})[ts] = dq
    obs_cache = ss.setdefault("_dq_obs", {})
    clip_cache = ss.setdefault("_dq_clip", {})
    val_cache = ss.setdefault("_dq_val", {})

    items = quality_flags(dq["raster"], dq["cells"], obs_cache.get(ts)) if dq else []
    n_warn = sum(1 for i in items if i["level"] == "warn")
    schema = ((dq or {}).get("raster") or {}).get("quality_band_schema")
    if schema and not schema.get("supported"):
        n_warn += 1
    title = ("🛡️ Chất lượng dữ liệu & kiểm chứng ngoài" if vi else "🛡️ Data quality & external validation") + \
        (f"  ·  ⚠️ {n_warn}" if n_warn else "  ·  ✅")

    with st.expander(title, expanded=bool(n_warn)):
        if not dq:
            st.info("Lần chạy này chưa có báo cáo chất lượng. Bấm 'Chạy phân tích' lại để tạo." if vi
                    else "This run has no quality report yet. Press 'Run analysis' again to create it.")
            return
        if schema:
            if not schema.get("supported"):
                st.warning(("A02: Không đọc được schema raster chất lượng " if vi
                            else "A02: Unrecognized quality raster schema ")
                           + f"(status={schema['status']}, bands={schema['band_count']}, "
                           + f"descriptions={schema['descriptions']}).")
            elif schema["status"] == "validated_producer_order":
                st.info("A02: Đã xác minh thứ tự bands mặc dù GeoTIFF thiếu tên band."
                        if vi else "A02: Trusted producer band order was validated despite missing descriptions.")
        st.subheader("Báo cáo tự động" if vi else "Automatic report",
                     help=("Đo những chỗ pipeline đổi thầm lặng thành 0: pixel không có giá trị, bức xạ âm bị cắt, ô không trích xuất được. "
                           "Chỉ ghi nhận, không sửa giá trị NTL." if vi else
                           "Measures where the pipeline silently turns things into 0: pixels without a value, clipped negative radiance, "
                           "cells with no extracted value. It only records; it never changes NTL values."))
        st.markdown("\n\n".join(_line(i, vi) for i in items))

        # --- các kiểm tra theo nút -------------------------------------------------------------
        st.markdown("---")
        st.subheader("Kiểm tra sâu" if vi else "Deeper checks",
                     help=("Các nút này tải thêm dữ liệu từ Earth Engine hoặc trích xuất lại từ ảnh đã tải. "
                           "Kết quả được lưu đệm theo lần chạy; bấm lại chỉ hiện kết quả cũ." if vi else
                           "These buttons fetch more data from Earth Engine or re-extract from the downloaded image. "
                           "Results are cached per run; pressing again shows the stored result."))
        grid_wgs = grid_utm.to_crs(epsg=4326)
        bbox = _bbox(grid_wgs)
        b1, b2 = st.columns(2)
        run_obs = b1.button(("✅ " if ts in obs_cache else "▶ ") + ("Đếm số tháng quan sát không mây" if vi else "Count cloud-free months"),
                            key="dq_btn_obs", use_container_width=True,
                            help=("Với mỗi pixel, đếm số tháng có quan sát không mây trong năm. Pixel 0 tháng đang bị tính là tối." if vi
                                  else "Counts cloud-free months per pixel in the year. Pixels with 0 months are currently counted as dark."))
        run_clip = b2.button(("✅ " if ts in clip_cache else "▶ ") + ("So sánh không cắt giá trị âm" if vi else "Compare without clipping negatives"),
                             key="dq_btn_clip", use_container_width=True, disabled="tif_bytes" not in res,
                             help=("Trích xuất lại trung bình theo ô từ ảnh đã tải nhưng giữ giá trị âm, rồi so với bản đã cắt. Không cần Earth Engine." if vi
                                   else "Re-extracts cell means from the downloaded image keeping negatives, then compares with the clipped version. No Earth Engine needed."))

        def _done(msg_vi, msg_en):
            st.toast(msg_vi if vi else msg_en, icon="✅")

        if run_obs:
            if ts in obs_cache:
                _done("Đã có kết quả lưu đệm", "Cached result available")
            else:
                try:
                    with st.spinner("Đang tải số tháng quan sát từ Earth Engine..." if vi else "Fetching cloud-free month counts..."):
                        from rasterio.io import MemoryFile
                        raw = ee_extra.fetch_obs_count_raster(ee, dataset, bbox, year, scale_m)
                        with MemoryFile(raw) as mf:
                            with mf.open() as src:
                                arr = src.read(1)
                        _put(obs_cache, ts, obs_report(arr))
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"{'Lỗi' if vi else 'Error'}: {e}")
        if run_clip:
            if ts in clip_cache:
                _done("Đã có kết quả lưu đệm", "Cached result available")
            else:
                try:
                    with st.spinner("Đang trích xuất lại..." if vi else "Re-extracting..."):
                        raw_mean = zonal_stat(res["tif_bytes"], grid_wgs, "mean", clip_negative=False, fill_missing=0.0)
                        _put(clip_cache, ts, compare_clipping(grid_utm["ntl_mean"].to_numpy(float), raw_mean.to_numpy(float)))
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"{'Lỗi' if vi else 'Error'}: {e}")

        c = clip_cache.get(ts)
        if c:
            st.markdown("**" + ("Kết quả: cắt âm so với giữ âm" if vi else "Result: clipped vs unclipped negatives") + "**")
            m1, m2, m3 = st.columns(3)
            m1.metric("Spearman (thứ hạng ô)" if vi else "Spearman (cell ranking)", f"{c['rho']:.4f}",
                      help="1 nghĩa là cách xử lý âm không đổi thứ hạng các ô." if vi else "1 means negative handling does not change the cell ranking.")
            m2.metric("Ô đổi quá 10%" if vi else "Cells changed > 10%", f"{c['share_changed'] * 100:.1f}%")
            m3.metric("Lệch lớn nhất" if vi else "Max difference", f"{c['max_abs_diff']:.3f}")
            if c["rho"] < 0.98 or c["share_changed"] > 0.10:
                st.warning("Cách xử lý giá trị âm làm đổi đáng kể kết quả; nên báo cáo cả hai bản." if vi
                           else "Negative handling changes the results noticeably; report both versions.")
            else:
                st.success("Cách xử lý giá trị âm gần như không ảnh hưởng." if vi else "Negative handling has almost no effect.")

        # --- kiểm chứng ngoài ------------------------------------------------------------------
        st.markdown("---")
        st.subheader("Kiểm chứng ngoài" if vi else "External validation",
                     help=("So NTL với một đại lượng độc lập trên cùng các ô. Nếu hai thứ gần như không liên quan, NTL ở nơi này "
                           "không phản ánh hoạt động hay dân cư như bạn kỳ vọng. Ngưỡng 0,4/0,6 là quy ước thực hành, không phải ngưỡng thống kê." if vi else
                           "Compares NTL with an independent quantity on the same cells. If they are nearly unrelated, NTL here does not reflect "
                           "activity or settlement as expected. The 0.4/0.6 cut-offs are a rule of thumb, not a statistical threshold."))
        kind = st.radio("Đại lượng so sánh" if vi else "Compare with", ["built", "pop"], horizontal=True, key="dq_proxy_kind",
                        format_func=lambda k: _PROXY_LABEL[k][0 if vi else 1])
        vkey = (ts, kind)
        run_val = st.button(("✅ " if vkey in val_cache else "▶ ") + ("Tải và so sánh" if vi else "Fetch and compare"),
                            key="dq_btn_val",
                            help=("Tải raster GHSL 100 m từ Earth Engine, cộng theo ô rồi tính tương quan hạng Spearman với NTL (khoảng tin cậy bootstrap theo khối)." if vi
                                  else "Fetches the 100 m GHSL raster from Earth Engine, sums it per cell and computes the Spearman rank correlation with NTL (block-bootstrap CI)."))
        if run_val:
            if vkey in val_cache:
                _done("Đã có kết quả lưu đệm", "Cached result available")
            else:
                try:
                    with st.spinner("Đang tải GHSL và so sánh..." if vi else "Fetching GHSL and comparing..."):
                        raw, epoch = measured_call(res.get("perf_monitor"),
                                                   f"ghsl.{kind}.fetch_native",
                                                   ee_extra.fetch_ghsl_raster, ee, kind, bbox, year)
                        sums = measured_call(res.get("perf_monitor"),
                                             f"ghsl.{kind}.zonal_sum", zonal_stat, raw,
                                             grid_wgs, "sum", clip_negative=True,
                                             fill_missing=0.0).to_numpy(float)
                        area = grid_utm["area_km2"].to_numpy(float)
                        cent = grid_utm.geometry.centroid
                        core = ~edge_cell_mask(area, size, 0.99)
                        ntl = grid_utm["ntl_mean"].to_numpy(float)
                        agree = measured_call(res.get("perf_monitor"), f"ghsl.{kind}.agreement",
                                              proxy_agreement, ntl, sums, area, cent.x.to_numpy(),
                                              cent.y.to_numpy(), size, core=core)
                        _put(val_cache, vkey, {"agree": agree, "epoch": epoch, "sums": sums, "core": core})
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"{'Lỗi' if vi else 'Error'}: {e}")
        v = val_cache.get(vkey)
        if v:
            a = v["agree"]
            if a["n"] < MIN_CELLS:
                st.info(f"Chỉ có {a['n']} ô lõi, cần ít nhất {MIN_CELLS} để so sánh." if vi
                        else f"Only {a['n']} core cells; at least {MIN_CELLS} are needed.")
            else:
                m1, m2, m3 = st.columns(3)
                m1.metric("Spearman ρ", f"{a['rho']:.3f}", help=("Tương quan hạng giữa NTL và mật độ đại lượng so sánh." if vi
                                                                  else "Rank correlation between NTL and the density of the compared quantity."))
                m2.metric("CI 95% (theo khối)" if vi else "95% CI (block)", f"{a['ci_lo']:.2f} – {a['ci_hi']:.2f}",
                          help=("Lấy mẫu lại theo khối 5×5 ô để tôn trọng tự tương quan không gian." if vi
                                else "Resampled in 5×5-cell blocks to respect spatial autocorrelation."))
                m3.metric("AUC top 25%" if vi else "AUC top 25%", f"{a['auc']:.3f}",
                          help=("Xác suất một ô thuộc 25% mật độ cao nhất có NTL cao hơn một ô khác; 0,5 là ngẫu nhiên." if vi
                                else "Probability that a top-quartile cell has higher NTL than another cell; 0.5 is random."))
                lvl = a["level"]
                msg = (f"Mức đồng thuận **{lvl}** (ρ = {a['rho']:.2f}). " if vi else f"Agreement level **{lvl}** (ρ = {a['rho']:.2f}). ")
                msg += (f"Epoch GHSL dùng: {v['epoch']} (NTL năm {year})." if vi else f"GHSL epoch used: {v['epoch']} (NTL year {year}).")
                if a["proxy_zero_share"] > 0.5:
                    msg += (f" {a['proxy_zero_share'] * 100:.0f}% ô có giá trị 0: ρ chịu ảnh hưởng của nhiều giá trị trùng." if vi
                            else f" {a['proxy_zero_share'] * 100:.0f}% of cells are 0: ρ is affected by many ties.")
                (st.success if lvl == "mạnh" else (st.warning if lvl == "yếu" else st.info))(msg)
                ok = v["core"] & (grid_utm["area_km2"].to_numpy(float) > 0)
                dens = v["sums"][ok] / grid_utm["area_km2"].to_numpy(float)[ok]
                df = pd.DataFrame({"ntl": grid_utm["ntl_mean"].to_numpy(float)[ok], "dens": dens})
                df = df[(df["ntl"] > 0) & (df["dens"] > 0)]
                if len(df) > 2000:
                    df = df.sample(2000, random_state=0)
                if len(df) >= 5:
                    ch = alt.Chart(df).mark_circle(color="#ffaa00", size=34, opacity=0.65).encode(
                        x=alt.X("ntl:Q", title="NTL (nW/cm²/sr)", scale=alt.Scale(type="log")),
                        y=alt.Y("dens:Q", title=(_PROXY_LABEL[kind][0 if vi else 1] + " / km²"), scale=alt.Scale(type="log")),
                        tooltip=[alt.Tooltip("ntl:Q", format=".2f"), alt.Tooltip("dens:Q", format=".1f")],
                    ).properties(height=280)
                    st.altair_chart(ch, use_container_width=True)
                    st.caption("Chỉ vẽ ô có cả hai giá trị dương (trục log); tối đa 2.000 điểm." if vi
                               else "Only cells with both values positive are plotted (log axes); at most 2,000 points.")
