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

T = {
    "vi": {
        "title": "🧭 LISA & Data Bridge cho hồi quy panel",
        "perms": "Số hoán vị", "alpha": "Mức ý nghĩa α", "fdr": "Hiệu chỉnh FDR (Benjamini–Hochberg)",
        "log": "Dùng ln(NTL) trước khi chuẩn hóa", "thr": "Ngưỡng 'ô sáng' (nW/cm²/sr)",
        "clu": "Số ô tối thiểu của cụm HH", "nbr": "Số láng giềng tối thiểu để kiểm định",
        "run": "Đang tính Local Moran's I...",
        "degrade": "⚠️ Lưới có {n:,} ô (> {c:,}). Bản đồ tự động ẨN các ô NTL = 0 để trình duyệt không tràn RAM. "
                   "CSV kết quả vẫn giữ 100% quan sát.",
        "degrade2": "Sau khi ẩn ô tối vẫn còn {m:,} ô > {c:,}: bản đồ chỉ vẽ {c:,} ô, ưu tiên ô có ý nghĩa LISA rồi NTL cao nhất. "
                    "CSV vẫn đầy đủ.",
        "hide0": "Ẩn ô không sáng (bắt buộc khi N lớn)", "hide_edge": "Ẩn ô biên bị loại",
        "k_hh": "Tỷ trọng diện tích HH", "k_gini": "Gini ánh sáng (ô đủ, gồm ô tối)", "k_dum": "Dummy cụm nóng",
        "k_mi": "Moran's I (ô sáng)", "yes": "Có", "no": "Không",
        "fdr_warn": "⚠️ Với {m:,} phép kiểm định và {p} hoán vị, p nhỏ nhất = {pf:.4f}. FDR chỉ bác bỏ được nếu có "
                    "≥ {k:,} ô đạt p tối thiểu. Hãy tăng số hoán vị nếu kết quả HH bằng 0.",
        "comp": "Cơ cấu trạng thái không gian", "cls": "Trạng thái", "cells": "Số ô", "area": "% diện tích vùng",
        "dl_cell": "⬇️ CSV theo ô (100% quan sát + LISA)", "dl_panel": "⬇️ CSV panel (1 dòng/vùng-năm)",
        "add": "➕ Thêm vùng-năm này vào bảng panel", "panel": "Bảng panel tích lũy",
        "note": "Ô tối không tham gia đồ thị láng giềng (listwise deletion); ô biên bị loại khỏi cả vai trò tâm lẫn láng giềng. "
                "Ô sáng cô lập (không có láng giềng sáng) không được kiểm định.",
        "tt": ["Ô", "NTL", "z (ô sáng)", "p giả", "Trạng thái", "Cách lõi (km)"],
    },
    "en": {
        "title": "🧭 LISA & Data Bridge for panel regression",
        "perms": "Permutations", "alpha": "Significance α", "fdr": "FDR correction (Benjamini–Hochberg)",
        "log": "Use ln(NTL) before standardising", "thr": "'Lit' threshold (nW/cm²/sr)",
        "clu": "Min cells per HH cluster", "nbr": "Min neighbours to be tested",
        "run": "Computing Local Moran's I...",
        "degrade": "⚠️ Grid has {n:,} cells (> {c:,}). The map automatically HIDES NTL = 0 cells to protect browser RAM. "
                   "The result CSV keeps 100% of observations.",
        "degrade2": "After hiding dark cells {m:,} cells remain (> {c:,}): the map draws {c:,}, LISA-significant cells first, "
                    "then highest NTL. CSV stays complete.",
        "hide0": "Hide unlit cells (forced for large N)", "hide_edge": "Hide masked edge cells",
        "k_hh": "HH area share", "k_gini": "Light Gini (core cells incl. dark)", "k_dum": "Hotspot dummy",
        "k_mi": "Moran's I (lit cells)", "yes": "Yes", "no": "No",
        "fdr_warn": "⚠️ With {m:,} tests and {p} permutations the minimum pseudo p is {pf:.4f}. BH can reject only if "
                    "≥ {k:,} cells reach that floor. Raise permutations if HH is empty.",
        "comp": "Spatial class composition", "cls": "Class", "cells": "Cells", "area": "% of region area",
        "dl_cell": "⬇️ Cell-level CSV (100% obs + LISA)", "dl_panel": "⬇️ Panel CSV (1 row / region-year)",
        "add": "➕ Add this region-year to the panel table", "panel": "Accumulated panel table",
        "note": "Dark cells are excluded from the neighbour graph (listwise deletion); edge cells are removed as both centres "
                "and neighbours. Isolated lit cells (no lit neighbour) are not tested.",
        "tt": ["Cell", "NTL", "z (lit)", "pseudo p", "Class", "Dist to core (km)"],
    },
}


def _legend(lang):
    items = "".join(
        f'<div><span style="background:{COLORS[k]};width:12px;height:12px;display:inline-block;'
        f'margin-right:6px;border:1px solid #666"></span>{k}</div>' for k in ALL_LABELS)
    return ('<div style="position:fixed;bottom:24px;left:12px;z-index:9999;background:rgba(255,255,255,.92);'
            f'padding:8px 10px;border-radius:6px;font:12px sans-serif;color:#222">{items}</div>')


def render_lisa_tab(res, grid_utm, export_df, *, lang="vi", region_id="region", region_label="",
                    render_cap=30_000, basemap="CartoDB positron"):
    L = T["en" if lang == "en" else "vi"]
    size, yr = int(res["size"]), int(res["year"])
    n = len(grid_utm)
    st.subheader(L["title"])

    # ---------- tham số ----------
    with st.form(key="lisa_params_form"):
        c1, c2, c3, c4 = st.columns(4)
        perms = c1.selectbox(L["perms"], [199, 499, 999], index=1)
        alpha = c2.selectbox(L["alpha"], [0.05, 0.01], index=0)
        fdr = c3.toggle(L["fdr"], value=True)
        use_log = c4.toggle(L["log"], value=False)
        
        c5, c6, c7 = st.columns(3)
        thr = c5.number_input(L["thr"], min_value=0.0, max_value=5.0, value=0.0, step=0.1)
        min_clu = c6.slider(L["clu"], 1, 30, 4) # Đổi giá trị min thành 1
        min_nbr = c7.slider(L["nbr"], 1, 4, 1)
        
        # Nút submit của Form
        submit_lisa = st.form_submit_button("🔄 Cập nhật tham số LISA", type="primary")

    # ---------- tính (cache trong session theo kết quả + tham số) ----------
    ckey = (res["ts"], size, perms, alpha, fdr, use_log, thr, min_clu, min_nbr)
    cache = st.session_state.setdefault("_lisa_cache", {})
    if ckey not in cache:
        cache.clear()
        cent = grid_utm.geometry.centroid
        meta = {"iso3": res["iso3"], "region_id": region_id, "region_label": region_label, "year": yr}
        with st.spinner(L["run"]):
            cache[ckey] = run_lisa(
                cent.x.to_numpy(), cent.y.to_numpy(), grid_utm["ntl_mean"].to_numpy(float),
                grid_utm["area_km2"].to_numpy(float), size, lit_threshold=thr, edge_tol=0.99,
                perms=perms, alpha=alpha, fdr=fdr, log_transform=use_log, min_neighbors=min_nbr,
                min_cluster_cells=min_clu, meta=meta)
    out = cache[ckey]
    cdf, rm = out.cell_df, out.region_metrics

    # ---------- KPI ----------
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(L["k_hh"], f"{rm['hh_area_share'] * 100:.2f}%")
    k2.metric(L["k_gini"], f"{rm['gini_ntl_core_all']:.3f}")
    k3.metric(L["k_dum"], L["yes"] if rm["hotspot_dummy"] else L["no"])
    k4.metric(L["k_mi"], f"{rm['moran_I_lit']:.3f}")
    if fdr and rm["n_cells_tested"] and rm["hh_area_share"] == 0:
        st.warning(L["fdr_warn"].format(m=rm["n_cells_tested"], p=perms, pf=rm["p_floor"], k=rm["fdr_min_hits_needed"]))
    st.caption(L["note"])

    # ---------- Graceful degradation (chỉ ảnh hưởng hiển thị, KHÔNG ảnh hưởng CSV) ----------
    forced = n > render_cap
    h1, h2 = st.columns(2)
    hide0 = h1.toggle(L["hide0"], value=False, key="lisa_hide0", disabled=forced) or forced
    hide_edge = h2.toggle(L["hide_edge"], value=False, key="lisa_hide_edge")
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

    # ---------- Bản đồ 2D ----------
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
        zoom_start=13, # Tự động zoom vừa phải vào tâm
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        control_scale=True, 
        prefer_canvas=True,
        no_wrap=True,  # Chặn duplicate bản đồ thế giới
        max_zoom=16    # Esri Dark chỉ hỗ trợ tối đa zoom 16
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
    area = grid_utm["area_km2"].to_numpy(float)
    labs = cdf["lisa_class"].to_numpy()
    comp = pd.DataFrame({
        L["cls"]: list(ALL_LABELS),
        L["cells"]: [int((labs == k).sum()) for k in ALL_LABELS],
        L["area"]: [round(float(area[labs == k].sum() / area.sum() * 100), 2) for k in ALL_LABELS],
    })
    
    # Chia giao diện làm 2 cột
    col_tab, col_chart = st.columns([1, 1.5])
    
    with col_tab:
        st.markdown(f"**{L['comp']}**")
        st.dataframe(comp, hide_index=True, use_container_width=True)
        
    with col_chart:
        st.markdown("**Biểu đồ phân tán Moran (Moran Scatterplot)**")
        # Chỉ lấy các ô có dữ liệu hợp lệ (Bỏ ô tối và ô biên bị NaN)
        plot_df = cdf[cdf['ntl_z_lit'].notna() & cdf['lisa_lag_z'].notna()].copy()
        
        if not plot_df.empty:
            # Vẽ các điểm scatter
            scatter = alt.Chart(plot_df).mark_circle(size=45, opacity=0.7).encode(
                x=alt.X('ntl_z_lit:Q', title='Z-score NTL (Bản thân)'),
                y=alt.Y('lisa_lag_z:Q', title='Spatial Lag Z-score (Hàng xóm)'),
                color=alt.Color('lisa_class:N', 
                                scale=alt.Scale(domain=list(COLORS.keys()), range=list(COLORS.values())),
                                legend=alt.Legend(title="Trạng thái")),
                tooltip=[
                    alt.Tooltip('lisa_class:N', title='LISA'),
                    alt.Tooltip('ntl_z_lit:Q', title='Z-score'),
                    alt.Tooltip('lisa_lag_z:Q', title='Lag Z-score')
                ]
            )
            # Vẽ 2 đường ngắt tọa độ (0,0) đứt nét mờ
            hline = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(color='gray', strokeDash=[3,3], opacity=0.5).encode(y='y:Q')
            vline = alt.Chart(pd.DataFrame({'x': [0]})).mark_rule(color='gray', strokeDash=[3,3], opacity=0.5).encode(x='x:Q')
            
            # Vẽ đường xu hướng Hồi quy tuyến tính (Slope = Global Moran's I)
            trend = scatter.transform_regression('ntl_z_lit', 'lisa_lag_z').mark_line(color='#00e5ff', size=2)
            
            chart = (scatter + hline + vline + trend).interactive().properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Không có đủ dữ liệu ô sáng để vẽ đồ thị.")

    # ---------- Data Bridge: luôn 100% quan sát ----------
    full = pd.concat([export_df.reset_index(drop=True), cdf.reset_index(drop=True)], axis=1)
    panel_row = pd.DataFrame([rm])
    slug = f"{region_id}_{yr}_{size}m"
    d1, d2, d3 = st.columns(3)
    d1.download_button(L["dl_cell"], full.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"{slug}_lisa_cells.csv", mime="text/csv", type="primary")
    d2.download_button(L["dl_panel"], panel_row.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"{slug}_panel_row.csv", mime="text/csv")
    if d3.button(L["add"], key="lisa_add_panel"):
        rows = st.session_state.setdefault("panel_rows", [])
        key = tuple(rm[c] for c in KEY_COLS)
        rows[:] = [r for r in rows if tuple(r[c] for c in KEY_COLS) != key] + [dict(rm)]

    rows = st.session_state.get("panel_rows", [])
    if rows:
        pdf = pd.DataFrame(rows).sort_values(["iso3", "region_id", "year", "cell_size_m"])
        st.markdown(f"**{L['panel']}** ({len(pdf)})")
        st.dataframe(pdf, hide_index=True, use_container_width=True)
        st.download_button(L["dl_panel"] + " — all", pdf.to_csv(index=False).encode("utf-8-sig"),
                           file_name="ntl_lisa_panel.csv", mime="text/csv", key="lisa_dl_all")
    return out
