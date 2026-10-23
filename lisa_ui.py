from __future__ import annotations

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
import streamlit as st
import altair as alt
from streamlit_folium import st_folium

from lisa_core import ALL_LABELS, DARK, EDGE, NS, run_lisa

COLORS = {  # quy ước màu GeoDa
    "High-High": "#d7191c", "Low-Low": "#2c7bb6", "High-Low": "#fdae61", "Low-High": "#abd9e9",
    NS: "#d9d9d9", EDGE: "#8c8c8c", DARK: "#2a2a33",
}
KEY_COLS = ("iso3", "region_id", "year", "cell_size_m")

# =====================================================================
# VĂN BẢN (song ngữ). Chỉ là chuỗi hiển thị — không ảnh hưởng tính toán.
# =====================================================================
T = {
    "vi": {
        "title": "🧭 LISA & Data Bridge cho hồi quy panel",
        "intro": "Phát hiện **cụm ánh sáng nóng/lạnh** bằng Local Moran's I và xuất biến sẵn sàng cho hồi quy panel.",
        "params": "⚙️ Tham số kiểm định LISA",
        "p_stat": "Kiểm định thống kê", "p_data": "Xử lý dữ liệu", "p_cluster": "Điều kiện cụm",
        "perms": "Số hoán vị", "alpha": "Mức ý nghĩa α", "fdr": "Hiệu chỉnh FDR (Benjamini–Hochberg)",
        "log": "Dùng ln(NTL) trước khi chuẩn hóa", "thr": "Ngưỡng 'ô sáng' (nW/cm²/sr)",
        "clu": "Số ô tối thiểu của cụm HH", "nbr": "Số láng giềng tối thiểu để kiểm định",
        "submit": "🔄 Cập nhật tham số LISA",
        "h_perms": "Số lần xáo trộn ngẫu nhiên để tính p-value giả (pseudo p). Càng nhiều càng chính xác nhưng chạy chậm hơn.",
        "h_alpha": "Ngưỡng bác bỏ giả thuyết 'không có cụm'. 0,05 = chấp nhận 5% rủi ro báo nhầm.",
        "h_fdr": "Kiểm soát tỷ lệ phát hiện sai khi kiểm định hàng nghìn ô cùng lúc. Bật để kết quả thận trọng hơn.",
        "h_log": "Lấy logarit để giảm ảnh hưởng của vài ô sáng cực đoan (NTL lệch phải mạnh). Khuyến nghị cho kiểm tra độ vững.",
        "h_thr": "Ô có NTL ≤ ngưỡng được coi là 'tối' và bị loại khỏi đồ thị láng giềng. Mặc định 0.",
        "h_clu": "Cụm HH liên thông có ít ô hơn mức này không được tính vào biến 'hotspot_dummy'.",
        "h_nbr": "Ô sáng có ít láng giềng sáng hơn mức này sẽ không được kiểm định.",
        "h_submit": "Áp dụng các tham số ở trên. Kết quả được lưu đệm nên đổi qua lại không tính lại nếu tham số đã chạy.",
        "pop_params": "Hướng dẫn tham số LISA",
        "pop_params_brief": "Bấm để xem giải thích chi tiết từng tham số",
        "pop_params_body": (
            "**Local Moran's I** so sánh giá trị NTL của từng ô với trung bình của các ô láng giềng (Queen, 8 hướng).\n\n"
            "- **Z-score:** NTL được chuẩn hóa chỉ trên ô sáng (μ, σ tính trên ô sáng, không biên).\n"
            "- **Hoán vị có điều kiện:** giữ nguyên giá trị ô i, rút ngẫu nhiên giá trị láng giềng để dựng phân phối null.\n"
            "- **p nhỏ nhất** = 1/(số hoán vị + 1). Nếu FDR bật mà không có ô HH nào, hãy tăng số hoán vị.\n"
            "- **FDR (BH):** điều chỉnh p-value cho nhiều phép kiểm định; thận trọng hơn nhưng ít dương tính giả.\n"
            "- **HH / LL / HL / LH:** sáng-sáng (điểm nóng), tối-tối, sáng giữa vùng tối, tối giữa vùng sáng."),
        "run": "Đang tính Local Moran's I...",
        "st_title": "Đang chạy LISA ({n:,} ô, {p} hoán vị)...",
        "st_s1": "Dựng đồ thị láng giềng Queen trên các ô sáng",
        "st_s2": "Chuẩn hóa z-score (chỉ ô sáng, loại ô biên)",
        "st_s3": "Chạy {p} hoán vị có điều kiện cho từng ô",
        "st_s4": "Hiệu chỉnh đa kiểm định và gom cụm HH",
        "st_done": "Hoàn tất LISA ✅",
        "degrade": "Lưới có {n:,} ô (> {c:,}). Bản đồ tự ẩn các ô NTL = 0 để tránh tràn RAM trình duyệt. "
                   "CSV vẫn giữ 100% quan sát.",
        "degrade2": "Sau khi ẩn ô tối còn {m:,} ô (> {c:,}): bản đồ chỉ vẽ {c:,} ô, ưu tiên ô có ý nghĩa LISA rồi NTL cao nhất. "
                    "CSV vẫn đầy đủ.",
        "hide0": "Ẩn ô không sáng", "hide_edge": "Ẩn ô biên bị loại",
        "h_hide0": "Chỉ ảnh hưởng bản đồ, không ảnh hưởng CSV. Bị khóa khi lưới quá lớn.",
        "h_hide_edge": "Ẩn các ô bị cắt bởi ranh giới (đã bị loại khỏi phân tích).",
        "k_hh": "Tỷ trọng diện tích HH", "k_gini": "Gini ánh sáng", "k_dum": "Dummy cụm nóng",
        "k_mi": "Moran's I (ô sáng)", "yes": "Có", "no": "Không",
        "h_k_hh": "Phần diện tích vùng nằm trong ô High-High có ý nghĩa thống kê.",
        "h_k_gini": "Bất bình đẳng ánh sáng giữa các ô đủ (gồm ô tối). 0 = đều, gần 1 = tập trung.",
        "h_k_dum": "1 nếu có ít nhất một cụm HH liên thông đạt số ô tối thiểu.",
        "h_k_mi": "Trung bình Local I của các ô được kiểm định; > 0 nghĩa là có xu hướng tụ cụm.",
        "kpi_title": "📊 Kết quả chính",
        "fdr_warn": "Với {m:,} phép kiểm định và {p} hoán vị, p nhỏ nhất = {pf:.4f}. FDR chỉ bác bỏ được nếu có "
                    "≥ {k:,} ô đạt p tối thiểu. Hãy tăng số hoán vị nếu kết quả HH bằng 0.",
        "note_t": "Lưu ý phương pháp",
        "map_t": "🗺️ Bản đồ cụm LISA",
        "comp_t": "🧮 Cơ cấu trạng thái & Moran Scatterplot",
        "comp": "Cơ cấu trạng thái không gian", "cls": "Trạng thái", "cells": "Số ô", "area": "% diện tích vùng",
        "scat": "Biểu đồ phân tán Moran (Moran Scatterplot)",
        "scat_help": "Trục x: z-score của ô; trục y: trung bình z của láng giềng. Độ dốc đường xu hướng ≈ Moran's I toàn cục.",
        "sx": "Z-score NTL (bản thân)", "sy": "Spatial lag z-score (hàng xóm)", "slegend": "Trạng thái",
        "no_scat": "Không đủ dữ liệu ô sáng để vẽ biểu đồ.",
        "bridge_t": "📤 Data Bridge — xuất dữ liệu cho hồi quy",
        "bridge_cap": "CSV theo ô giữ 100% quan sát. CSV panel gồm 1 dòng cho mỗi (vùng, năm, độ phân giải).",
        "dl_cell": "⬇️ CSV theo ô (100% quan sát + LISA)", "dl_panel": "⬇️ CSV panel (1 dòng/vùng-năm)",
        "h_dl_cell": "Mỗi dòng là một ô lưới, gồm biến NTL gốc và kết quả LISA.",
        "h_dl_panel": "Một dòng tổng hợp cho vùng-năm hiện tại, dùng làm quan sát trong hồi quy panel.",
        "add": "➕ Thêm vùng-năm này vào bảng panel",
        "h_add": "Nếu trùng (iso3, vùng, năm, độ phân giải) thì dòng cũ sẽ được thay bằng dòng mới.",
        "added": "Đã thêm vào bảng panel.",
        "panel": "Bảng panel tích lũy", "panel_empty": "Chưa có dòng nào. Bấm “Thêm vùng-năm” để bắt đầu tích lũy.",
        "dl_all": " — toàn bộ",
        "note": "Ô tối không tham gia đồ thị láng giềng (listwise deletion); ô biên bị loại khỏi cả vai trò tâm lẫn láng giềng. "
                "Ô sáng cô lập (không có láng giềng sáng) không được kiểm định.",
        "tt": ["Ô", "NTL", "z (ô sáng)", "p giả", "Trạng thái", "Cách lõi (km)"],
    },
    "en": {
        "title": "🧭 LISA & Data Bridge for panel regression",
        "intro": "Detect **light hot/cold spots** with Local Moran's I and export panel-regression-ready variables.",
        "params": "⚙️ LISA test parameters",
        "p_stat": "Statistical test", "p_data": "Data handling", "p_cluster": "Cluster rules",
        "perms": "Permutations", "alpha": "Significance α", "fdr": "FDR correction (Benjamini–Hochberg)",
        "log": "Use ln(NTL) before standardising", "thr": "'Lit' threshold (nW/cm²/sr)",
        "clu": "Min cells per HH cluster", "nbr": "Min neighbours to be tested",
        "submit": "🔄 Update LISA parameters",
        "h_perms": "Number of random shuffles used to compute the pseudo p-value. More = more precise but slower.",
        "h_alpha": "Rejection threshold for 'no clustering'. 0.05 = accept a 5% false-alarm risk.",
        "h_fdr": "Controls the false discovery rate when testing thousands of cells at once. Turn on for more conservative results.",
        "h_log": "Log-transform to damp a few extreme bright cells (NTL is strongly right-skewed). Good for robustness checks.",
        "h_thr": "Cells with NTL ≤ threshold are 'dark' and dropped from the neighbour graph. Default 0.",
        "h_clu": "Connected HH clusters smaller than this do not count towards 'hotspot_dummy'.",
        "h_nbr": "Lit cells with fewer lit neighbours than this are not tested.",
        "h_submit": "Apply the parameters above. Results are cached, so revisiting a parameter set does not recompute.",
        "pop_params": "LISA parameter guide",
        "pop_params_brief": "Click for a detailed explanation of each parameter",
        "pop_params_body": (
            "**Local Moran's I** compares each cell's NTL with the mean of its Queen (8-direction) neighbours.\n\n"
            "- **Z-score:** NTL is standardised on lit, non-edge cells only.\n"
            "- **Conditional permutation:** cell i is held fixed; neighbour values are drawn at random to build the null.\n"
            "- **Minimum p** = 1/(permutations + 1). If FDR is on and HH is empty, raise permutations.\n"
            "- **FDR (BH):** adjusts for multiple testing; more conservative, fewer false positives.\n"
            "- **HH / LL / HL / LH:** bright-bright (hotspot), dark-dark, bright among dark, dark among bright."),
        "run": "Computing Local Moran's I...",
        "st_title": "Running LISA ({n:,} cells, {p} permutations)...",
        "st_s1": "Building Queen neighbour graph on lit cells",
        "st_s2": "Standardising z-scores (lit cells only, edge cells removed)",
        "st_s3": "Running {p} conditional permutations per cell",
        "st_s4": "Multiple-testing correction and HH clustering",
        "st_done": "LISA complete ✅",
        "degrade": "Grid has {n:,} cells (> {c:,}). The map hides NTL = 0 cells to protect browser RAM. "
                   "The CSV keeps 100% of observations.",
        "degrade2": "After hiding dark cells {m:,} remain (> {c:,}): the map draws {c:,}, LISA-significant first, "
                    "then highest NTL. CSV stays complete.",
        "hide0": "Hide unlit cells", "hide_edge": "Hide masked edge cells",
        "h_hide0": "Map only; the CSV is unaffected. Locked for very large grids.",
        "h_hide_edge": "Hide cells clipped by the boundary (already excluded from the analysis).",
        "k_hh": "HH area share", "k_gini": "Light Gini", "k_dum": "Hotspot dummy",
        "k_mi": "Moran's I (lit cells)", "yes": "Yes", "no": "No",
        "h_k_hh": "Share of region area inside statistically significant High-High cells.",
        "h_k_gini": "Light inequality across core cells (incl. dark). 0 = even, near 1 = concentrated.",
        "h_k_dum": "1 if at least one connected HH cluster reaches the minimum cell count.",
        "h_k_mi": "Mean Local I over tested cells; > 0 indicates clustering.",
        "kpi_title": "📊 Key results",
        "fdr_warn": "With {m:,} tests and {p} permutations the minimum pseudo p is {pf:.4f}. BH can reject only if "
                    "≥ {k:,} cells reach that floor. Raise permutations if HH is empty.",
        "note_t": "Methodology note",
        "map_t": "🗺️ LISA cluster map",
        "comp_t": "🧮 Class composition & Moran scatterplot",
        "comp": "Spatial class composition", "cls": "Class", "cells": "Cells", "area": "% of region area",
        "scat": "Moran scatterplot",
        "scat_help": "x: cell z-score; y: mean z-score of neighbours. The trend-line slope ≈ global Moran's I.",
        "sx": "NTL z-score (self)", "sy": "Spatial lag z-score (neighbours)", "slegend": "Class",
        "no_scat": "Not enough lit-cell data to draw the chart.",
        "bridge_t": "📤 Data Bridge — export for regression",
        "bridge_cap": "The cell CSV keeps 100% of observations. The panel CSV has one row per (region, year, resolution).",
        "dl_cell": "⬇️ Cell-level CSV (100% obs + LISA)", "dl_panel": "⬇️ Panel CSV (1 row / region-year)",
        "h_dl_cell": "One row per grid cell: raw NTL variables plus LISA results.",
        "h_dl_panel": "One summary row for the current region-year, ready to use as a panel observation.",
        "add": "➕ Add this region-year to the panel table",
        "h_add": "If (iso3, region, year, resolution) already exists, the old row is replaced.",
        "added": "Added to the panel table.",
        "panel": "Accumulated panel table", "panel_empty": "No rows yet. Click “Add region-year” to start accumulating.",
        "dl_all": " — all",
        "note": "Dark cells are excluded from the neighbour graph (listwise deletion); edge cells are removed as both centres "
                "and neighbours. Isolated lit cells (no lit neighbour) are not tested.",
        "tt": ["Cell", "NTL", "z (lit)", "pseudo p", "Class", "Dist to core (km)"],
    },
}

_CSS = """
<style>
.lisa-hero{padding:2px 0 4px;color:#9aa0aa;font-size:.95rem}
div[data-testid="stMetric"]{background:rgba(127,127,140,.07);border:1px solid rgba(127,127,140,.22);
  border-radius:12px;padding:10px 14px}
div[data-testid="stMetricValue"]{font-weight:700}
</style>
"""


def _legend(lang):
    items = "".join(
        f'<div><span style="background:{COLORS[k]};width:12px;height:12px;display:inline-block;'
        f'margin-right:6px;border:1px solid #666"></span>{k}</div>' for k in ALL_LABELS)
    return ('<div style="position:fixed;bottom:24px;left:12px;z-index:9999;background:rgba(255,255,255,.92);'
            f'padding:8px 10px;border-radius:6px;font:12px sans-serif;color:#222">{items}</div>')


def _popover(brief, title, body):
    """Nút (?) : rê chuột -> mô tả ngắn; bấm -> hộp chi tiết."""
    try:
        pop = st.popover("❓", help=brief)
    except TypeError:  # Streamlit cũ không có help cho popover
        pop = st.popover("❓")
    with pop:
        st.markdown(f"**{title}**")
        st.markdown(body)


def _pin(cfg_cls, **kw):
    """Khóa cột nếu phiên bản Streamlit hỗ trợ."""
    try:
        return cfg_cls(pinned=True, **kw)
    except TypeError:
        return cfg_cls(**kw)


def render_lisa_tab(res, grid_utm, export_df, *, lang="vi", region_id="region", region_label="",
                    render_cap=30_000, basemap="CartoDB positron"):
    L = T["en" if lang == "en" else "vi"]
    size, yr = int(res["size"]), int(res["year"])
    n = len(grid_utm)

    st.markdown(_CSS, unsafe_allow_html=True)
    h1c, h2c = st.columns([12, 1], vertical_alignment="center")
    h1c.subheader(L["title"])
    with h2c:
        _popover(L["pop_params_brief"], L["pop_params"], L["pop_params_body"])
    st.markdown(f'<div class="lisa-hero">{L["intro"]}</div>', unsafe_allow_html=True)

    # ---------- tham số ----------
    with st.expander(L["params"], expanded=True):
        with st.form(key="lisa_params_form", border=False):
            st.caption(f"**{L['p_stat']}**")
            c1, c2, c3 = st.columns(3)
            perms = c1.selectbox(L["perms"], [199, 499, 999], index=1, help=L["h_perms"])
            alpha = c2.selectbox(L["alpha"], [0.05, 0.01], index=0, help=L["h_alpha"])
            with c3:
                fdr = st.toggle(L["fdr"], value=True, help=L["h_fdr"])

            st.divider()
            st.caption(f"**{L['p_data']}**")
            c4, c5 = st.columns(2)
            with c4:
                use_log = st.toggle(L["log"], value=False, help=L["h_log"])
            thr = c5.number_input(L["thr"], min_value=0.0, max_value=5.0, value=0.0, step=0.1, help=L["h_thr"])

            st.divider()
            st.caption(f"**{L['p_cluster']}**")
            c6, c7 = st.columns(2)
            min_clu = c6.slider(L["clu"], 1, 30, 4, help=L["h_clu"])
            min_nbr = c7.slider(L["nbr"], 1, 4, 1, help=L["h_nbr"])

            submit_lisa = st.form_submit_button(L["submit"], type="primary", help=L["h_submit"])

    # ---------- tính (cache trong session theo kết quả + tham số) ----------
    ckey = (res["ts"], size, perms, alpha, fdr, use_log, thr, min_clu, min_nbr)
    cache = st.session_state.setdefault("_lisa_cache", {})
    if ckey not in cache:
        cache.clear()
        cent = grid_utm.geometry.centroid
        meta = {"iso3": res["iso3"], "region_id": region_id, "region_label": region_label, "year": yr}
        with st.status(L["st_title"].format(n=n, p=perms), expanded=True) as status:
            st.write("① " + L["st_s1"])
            st.write("② " + L["st_s2"])
            st.write("③ " + L["st_s3"].format(p=perms))
            st.write("④ " + L["st_s4"])
            cache[ckey] = run_lisa(
                cent.x.to_numpy(), cent.y.to_numpy(), grid_utm["ntl_mean"].to_numpy(float),
                grid_utm["area_km2"].to_numpy(float), size, lit_threshold=thr, edge_tol=0.99,
                perms=perms, alpha=alpha, fdr=fdr, log_transform=use_log, min_neighbors=min_nbr,
                min_cluster_cells=min_clu, meta=meta)
            status.update(label=L["st_done"], state="complete", expanded=False)
    out = cache[ckey]
    cdf, rm = out.cell_df, out.region_metrics

    # ---------- KPI ----------
    st.divider()
    st.markdown(f"#### {L['kpi_title']}")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(L["k_hh"], f"{rm['hh_area_share'] * 100:.2f}%", help=L["h_k_hh"])
    k2.metric(L["k_gini"], f"{rm['gini_ntl_core_all']:.3f}", help=L["h_k_gini"])
    k3.metric(L["k_dum"], L["yes"] if rm["hotspot_dummy"] else L["no"], help=L["h_k_dum"])
    k4.metric(L["k_mi"], f"{rm['moran_I_lit']:.3f}", help=L["h_k_mi"])
    if fdr and rm["n_cells_tested"] and rm["hh_area_share"] == 0:
        st.warning(L["fdr_warn"].format(m=rm["n_cells_tested"], p=perms, pf=rm["p_floor"], k=rm["fdr_min_hits_needed"]))
    with st.expander(L["note_t"]):
        st.caption(L["note"])

    # ---------- Bản đồ ----------
    st.divider()
    st.markdown(f"#### {L['map_t']}")
    forced = n > render_cap
    h1, h2 = st.columns(2)
    hide0 = h1.toggle(L["hide0"], value=False, key="lisa_hide0", disabled=forced, help=L["h_hide0"]) or forced
    hide_edge = h2.toggle(L["hide_edge"], value=False, key="lisa_hide_edge", help=L["h_hide_edge"])
    if forced:
        st.warning(L["degrade"].format(n=n, c=render_cap))

    show = np.ones(n, dtype=bool)
    if hide0:
        show &= cdf["is_dark"].to_numpy() == 0
    if hide_edge:
        show &= cdf["is_edge_masked"].to_numpy() == 0
    idx = np.flatnonzero(show)
    if idx.size > render_cap:
        st.info(L["degrade2"].format(m=idx.size, c=render_cap))
        prio = np.lexsort((-grid_utm["ntl_mean"].to_numpy()[idx], -out.sig_mask[idx].astype(int)))
        idx = idx[prio[:render_cap]]

    sub = gpd.GeoSeries(grid_utm.geometry.iloc[idx].values, crs=grid_utm.crs).to_crs(4326)
    try:
        sub = gpd.GeoSeries(shapely.set_precision(np.asarray(sub.values), 1e-6), crs=4326)
    except Exception:  # noqa: BLE001
        pass
    lab = cdf["lisa_class"].to_numpy()[idx]

    dist_arr = cdf.get("dist_to_core_km", pd.Series(np.zeros(len(cdf)))).to_numpy()

    gj = gpd.GeoDataFrame({
        "c": [f"#{int(i)}" for i in grid_utm["grid_id"].to_numpy()[idx]],
        "v": np.round(grid_utm["ntl_mean"].to_numpy()[idx], 2),
        "z": np.round(cdf["ntl_z_lit"].to_numpy()[idx], 2),
        "p": np.round(cdf["lisa_p_sim"].to_numpy()[idx], 4),
        "k": lab,
        "d": np.round(dist_arr[idx], 2),
        "col": [COLORS[x] for x in lab],
    }, geometry=sub.values, crs=4326)

    minx, miny, maxx, maxy = res["boundary_wgs"].total_bounds

    m = folium.Map(
        location=[(miny + maxy) / 2, (minx + maxx) / 2],
        zoom_start=13,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        control_scale=True,
        prefer_canvas=True,
        no_wrap=True,
        max_zoom=16,
    )

    folium.GeoJson(
        gj, name="LISA",
        style_function=lambda f: {"fillColor": f["properties"]["col"], "color": f["properties"]["col"],
                                  "weight": 0.4, "fillOpacity": 0.15 if f["properties"]["k"] in (NS, DARK) else 0.8},
        tooltip=folium.GeoJsonTooltip(fields=["c", "v", "z", "p", "k", "d"], aliases=L["tt"], sticky=False),
    ).add_to(m)
    folium.GeoJson(res["boundary_wgs"], interactive=False,
                   style_function=lambda _: {"fill": False, "color": "#222", "weight": 1.5}).add_to(m)
    m.get_root().html.add_child(folium.Element(_legend(lang)))
    import streamlit.components.v1 as components
    components.html(m.get_root().render(), height=640)

    # ---------- Cơ cấu trạng thái & Moran Scatterplot ----------
    st.divider()
    st.markdown(f"#### {L['comp_t']}")
    area = grid_utm["area_km2"].to_numpy(float)
    labs = cdf["lisa_class"].to_numpy()
    comp = pd.DataFrame({
        L["cls"]: list(ALL_LABELS),
        L["cells"]: [int((labs == k).sum()) for k in ALL_LABELS],
        L["area"]: [round(float(area[labs == k].sum() / area.sum() * 100), 2) for k in ALL_LABELS],
    })

    col_tab, col_chart = st.columns([1, 1.5])

    with col_tab:
        with st.container(border=True):
            st.markdown(f"**{L['comp']}**")
            st.dataframe(
                comp, hide_index=True, use_container_width=True,
                column_config={
                    L["cls"]: _pin(st.column_config.TextColumn, label=L["cls"]),
                    L["cells"]: st.column_config.NumberColumn(L["cells"], format="%d"),
                    L["area"]: st.column_config.ProgressColumn(L["area"], min_value=0, max_value=100, format="%.2f%%"),
                })

    with col_chart:
        with st.container(border=True):
            st.markdown(f"**{L['scat']}**", help=L["scat_help"])
            plot_df = cdf[cdf['ntl_z_lit'].notna() & cdf['lisa_lag_z'].notna()].copy()

            if not plot_df.empty:
                scatter = alt.Chart(plot_df).mark_circle(size=45, opacity=0.7).encode(
                    x=alt.X('ntl_z_lit:Q', title=L["sx"]),
                    y=alt.Y('lisa_lag_z:Q', title=L["sy"]),
                    color=alt.Color('lisa_class:N',
                                    scale=alt.Scale(domain=list(COLORS.keys()), range=list(COLORS.values())),
                                    legend=alt.Legend(title=L["slegend"])),
                    tooltip=[
                        alt.Tooltip('lisa_class:N', title='LISA'),
                        alt.Tooltip('ntl_z_lit:Q', title='Z-score'),
                        alt.Tooltip('lisa_lag_z:Q', title='Lag Z-score')
                    ]
                )
                hline = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='gray', strokeDash=[3, 3], opacity=0.5).encode(y='y:Q')
                vline = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(color='gray', strokeDash=[3, 3], opacity=0.5).encode(x='x:Q')
                trend = scatter.transform_regression('ntl_z_lit', 'lisa_lag_z').mark_line(color='#00e5ff', size=2)

                chart = (scatter + hline + vline + trend).interactive().properties(height=320)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info(L["no_scat"])

    # ---------- Data Bridge: luôn 100% quan sát ----------
    st.divider()
    st.markdown(f"#### {L['bridge_t']}")
    st.caption(L["bridge_cap"])
    full = pd.concat([export_df.reset_index(drop=True), cdf.reset_index(drop=True)], axis=1)
    panel_row = pd.DataFrame([rm])
    slug = f"{region_id}_{yr}_{size}m"
    d1, d2, d3 = st.columns(3)
    d1.download_button(L["dl_cell"], full.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"{slug}_lisa_cells.csv", mime="text/csv", type="primary",
                       help=L["h_dl_cell"], use_container_width=True)
    d2.download_button(L["dl_panel"], panel_row.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"{slug}_panel_row.csv", mime="text/csv",
                       help=L["h_dl_panel"], use_container_width=True)
    if d3.button(L["add"], key="lisa_add_panel", help=L["h_add"], use_container_width=True):
        rows = st.session_state.setdefault("panel_rows", [])
        key = tuple(rm[c] for c in KEY_COLS)
        rows[:] = [r for r in rows if tuple(r[c] for c in KEY_COLS) != key] + [dict(rm)]
        st.toast(L["added"], icon="✅")

    rows = st.session_state.get("panel_rows", [])
    with st.container(border=True):
        if rows:
            pdf = pd.DataFrame(rows).sort_values(["iso3", "region_id", "year", "cell_size_m"])
            st.markdown(f"**{L['panel']}** ({len(pdf)})")
            st.dataframe(
                pdf, hide_index=True, use_container_width=True,
                column_config={
                    "iso3": _pin(st.column_config.TextColumn, label="iso3"),
                    "region_id": _pin(st.column_config.TextColumn, label="region_id"),
                    "year": st.column_config.NumberColumn("year", format="%d"),
                    "hh_area_share": st.column_config.ProgressColumn("hh_area_share", min_value=0, max_value=1, format="%.3f"),
                    "lit_area_share": st.column_config.ProgressColumn("lit_area_share", min_value=0, max_value=1, format="%.3f"),
                })
            st.download_button(L["dl_panel"] + L["dl_all"], pdf.to_csv(index=False).encode("utf-8-sig"),
                               file_name="ntl_lisa_panel.csv", mime="text/csv", key="lisa_dl_all",
                               help=L["h_dl_panel"])
        else:
            st.markdown(f"**{L['panel']}**")
            st.caption(L["panel_empty"])
    return out
