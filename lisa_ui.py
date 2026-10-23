from __future__ import annotations

import json
import re

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
import streamlit as st
import altair as alt
from branca.element import MacroElement
from jinja2 import Template
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
        "title": "🧭 LISA & Data bridge cho hồi quy panel",
        "intro": "Phát hiện cụm ánh sáng nóng/lạnh bằng Local Moran's I và xuất biến sẵn sàng cho hồi quy panel.",
        "params": "⚙️ Tham số kiểm định LISA",
        "p_stat": "Kiểm định thống kê", "p_data": "Xử lý dữ liệu", "p_cluster": "Điều kiện cụm",
        "perms": "Số hoán vị", "alpha": "Mức ý nghĩa α", "fdr": "Hiệu chỉnh FDR (Benjamini–Hochberg)",
        "log": "Dùng ln(NTL) trước khi chuẩn hóa", "thr": "Ngưỡng 'ô sáng' (nW/cm²/sr)",
        "clu": "Số ô tối thiểu của cụm HH", "nbr": "Số láng giềng tối thiểu để kiểm định",
        "submit": "🔄 Cập nhật tham số LISA",
        "h_perms": "Số lần xáo trộn ngẫu nhiên để tạo phân phối tham chiếu. Số càng cao (999) p-value càng chính xác nhưng chạy chậm hơn.",
        "h_alpha": "Ngưỡng ý nghĩa p-value để quyết định cụm không gian có thực sự tồn tại hay do ngẫu nhiên (thường dùng 0.05).",
        "h_fdr": "Cơ chế siêu khắt khe (FDR) chặn đứng việc máy tính báo động giả khi kiểm định hàng ngàn ô lưới cùng lúc.",
        "h_log": "Chuyển NTL sang dạng logarit tự nhiên (ln). Giúp giảm nhiễu cục bộ từ các ô siêu sáng (nhà máy, sân bay).",
        "h_thr": "Chỉ các ô có độ sáng lớn hơn ngưỡng này mới được đưa vào kiểm định (giúp loại bỏ hoàn toàn nhiễu vùng tối).",
        "h_clu": "Chỉ ghi nhận biến giả (Hotspot Dummy = 1) nếu phát hiện một cụm điểm nóng High-High liên tục lớn hơn số ô này.",
        "h_nbr": "Loại bỏ các ô cô lập (quá ít hàng xóm) khỏi phép kiểm định để tránh kết quả bị nhiễu do thiếu liên kết không gian.",
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
        "comp_t": "🧮 Cơ cấu trạng thái & Moran scatterplot",
        "comp": "Cơ cấu trạng thái không gian", "cls": "Trạng thái", "cells": "Số ô", "area": "% diện tích vùng",
        "scat": "Biểu đồ phân tán Moran (Moran scatterplot)",
        "scat_help": "Trục x: z-score của ô; trục y: trung bình z của láng giềng. Độ dốc đường xu hướng ≈ Moran's I toàn cục.",
        "sx": "Z-score NTL (bản thân)", "sy": "Spatial lag z-score (hàng xóm)", "slegend": "Trạng thái",
        "no_scat": "Không đủ dữ liệu ô sáng để vẽ biểu đồ.",
        "bridge_t": "📤 Data bridge: xuất dữ liệu cho hồi quy",
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
        "title": "🧭 LISA & Data bridge for panel regression",
        "intro": "Detect **light hot/cold spots** with Local Moran's I and export panel-regression-ready variables.",
        "params": "⚙️ LISA test parameters",
        "p_stat": "Statistical test", "p_data": "Data handling", "p_cluster": "Cluster rules",
        "perms": "Permutations", "alpha": "Significance α", "fdr": "FDR correction (Benjamini–Hochberg)",
        "log": "Use ln(NTL) before standardising", "thr": "'Lit' threshold (nW/cm²/sr)",
        "clu": "Min cells per HH cluster", "nbr": "Min neighbours to be tested",
        "submit": "🔄 Update LISA parameters",
        "h_perms": "Number of random permutations for pseudo p-value. 999 gives the most precise p-value but takes longer.",
        "h_alpha": "Significance level (p-value threshold) to determine if structural clusters exist.",
        "h_fdr": "Strict multiple testing correction (Benjamini-Hochberg) to minimize False Positives.",
        "h_log": "Apply natural log (ln) to NTL before standardizing. Mitigates outliers from ultra-bright pixels.",
        "h_thr": "Only cells strictly brighter than this threshold are tested (removes dark area noise).",
        "h_clu": "Hotspot Dummy = 1 only if a contiguous High-High cluster contains at least this many cells.",
        "h_nbr": "Exclude isolated cells (few neighbors) from testing to avoid spurious spatial association.",
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
        "bridge_t": "📤 Data bridge: export for regression",
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

T["vi"].update({
    "flow": "**Quy trình:** ① chỉnh tham số → ② bấm *Cập nhật* → ③ đọc kết quả chính → ④ xem bản đồ cụm → ⑤ xuất dữ liệu cho hồi quy.",
    "verdict_t": "Nhận định nhanh:",
    "v_hot": "  Phát hiện **cụm điểm nóng (High-High)** liên thông từ {k} ô trở lên, chiếm **{hh:.2f}%** diện tích vùng.",
    "v_nohot": "  **Chưa có cụm điểm nóng đủ lớn** (cần ≥ {k} ô liên thông).",
    "v_frag": " Có {hh:.2f}% diện tích HH có ý nghĩa thống kê nhưng rời rạc.",
    "v_mi_pos": "  Moran's I (ô sáng) = **{mi:.3f}** > 0: các ô sáng có xu hướng **tụ cụm** trong không gian.",
    "v_mi_neg": "  Moran's I (ô sáng) = **{mi:.3f}** ≤ 0: chưa thấy xu hướng tụ cụm (ngẫu nhiên hoặc xen kẽ).",
    "v_gini": "  Gini ánh sáng = **{g:.3f}**, ánh sáng {gd}.",
    "gini_desc": ["phân bố tương đối đều", "tập trung ở mức vừa phải", "tập trung rất cao vào vài ô"],
    "guide_t": "📖 Cách đọc bản đồ LISA",
    "map_hint": "Rê chuột vào ô để xem NTL, z-score, p giả, trạng thái và khoảng cách tới lõi cụm. Ô không có ý nghĩa (NS) và ô tối được vẽ mờ.",
    "legend_desc": {
        "HH": "Sáng giữa vùng sáng: **điểm nóng** thật sự.",
        "LL": "Tối giữa vùng tối: **điểm lạnh**.",
        "HL": "Ô sáng nằm giữa các ô tối: điểm sáng cô lập (ngoại lệ).",
        "LH": "Ô tối nằm giữa các ô sáng: “lỗ hổng” trong vùng sáng.",
        "NS": "Không có ý nghĩa thống kê (không khác ngẫu nhiên).",
        "EDGE": "Ô biên bị cắt bởi ranh giới, loại khỏi phân tích.",
        "DARK": "Ô không sáng, không tham gia đồ thị láng giềng.",
    },
})
T["en"].update({
    "flow": "**Workflow:** ① adjust parameters → ② press *Update* → ③ read the key results → ④ inspect the cluster map → ⑤ export for regression.",
    "verdict_t": "Quick take:",
    "v_hot": "  Found **High-High hotspot clusters** of {k}+ connected cells, covering **{hh:.2f}%** of the region's area.",
    "v_nohot": "  **No hotspot cluster large enough** (needs ≥ {k} connected cells).",
    "v_frag": " {hh:.2f}% of the area is significant HH but fragmented.",
    "v_mi_pos": "  Moran's I (lit cells) = **{mi:.3f}** > 0: bright cells tend to **cluster** in space.",
    "v_mi_neg": "  Moran's I (lit cells) = **{mi:.3f}** ≤ 0: no clustering tendency (random or alternating).",
    "v_gini": "  Light Gini = **{g:.3f}**, light is {gd}.",
    "gini_desc": ["fairly evenly spread", "moderately concentrated", "highly concentrated in a few cells"],
    "guide_t": "📖 How to read the LISA map",
    "map_hint": "Hover a cell for NTL, z-score, pseudo p, class and distance to the cluster core. Non-significant (NS) and dark cells are drawn faint.",
    "legend_desc": {
        "HH": "Bright among bright: a true **hotspot**.",
        "LL": "Dark among dark: a **cold spot**.",
        "HL": "A bright cell surrounded by dark ones: isolated bright spot (outlier).",
        "LH": "A dark cell surrounded by bright ones: a “hole” in a lit area.",
        "NS": "Not statistically significant (indistinguishable from chance).",
        "EDGE": "Border cell clipped by the boundary: excluded from the analysis.",
        "DARK": "Unlit cell: not part of the neighbour graph.",
    },
})

_CSS = """
<style>
@keyframes lisaUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.lisa-hero{padding:2px 0 4px;color:#9aa0aa;font-size:.95rem;animation:lisaUp .5s both}
div[data-testid="stMetric"]{background:rgba(127,127,140,.07);border:1px solid rgba(127,127,140,.22);
  border-radius:12px;padding:10px 14px;transition:transform .18s ease,border-color .18s ease;animation:lisaUp .5s both}
div[data-testid="stMetric"]:hover{transform:translateY(-3px);border-color:rgba(255,183,3,.6)}
div[data-testid="stMetricValue"]{font-weight:700}
.lisa-leg{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px}
.lisa-li{display:flex;gap:10px;align-items:flex-start;border:1px solid rgba(127,127,140,.22);border-radius:12px;
  padding:9px 12px;background:rgba(127,127,140,.06);transition:transform .18s ease,border-color .18s ease;animation:lisaUp .5s both}
.lisa-li:hover{transform:translateY(-2px);border-color:rgba(255,183,3,.55)}
.lisa-li i{width:16px;height:16px;border-radius:4px;flex:none;margin-top:2px;border:1px solid rgba(127,127,140,.6)}
.lisa-li b{display:block;font-size:.88rem}.lisa-li span{font-size:.8rem;opacity:.8;line-height:1.4}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
"""

LISA_MAP_CSS = """
<style>
@keyframes ntFadeIn{from{opacity:0}to{opacity:1}}
@keyframes ntSlideUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
.leaflet-container{animation:ntFadeIn .8s both}
.lisa-legend{position:fixed;bottom:24px;left:12px;z-index:9999;background:rgba(10,10,14,.86);color:#fff;padding:8px 11px;
  border-radius:10px;border:1px solid rgba(255,255,255,.18);font:12px Inter,Arial,sans-serif;animation:ntSlideUp .7s .5s both}
.lisa-legend div{margin-top:3px;white-space:nowrap}
.lisa-legend span{width:12px;height:12px;display:inline-block;margin-right:7px;border:1px solid rgba(255,255,255,.4);
  vertical-align:-2px;border-radius:3px}
@media (prefers-reduced-motion:reduce){.leaflet-container,.lisa-legend{animation:none!important}}
</style>
"""

_CLS_KEY = {"High-High": "HH", "Low-Low": "LL", "High-Low": "HL", "Low-High": "LH", NS: "NS", EDGE: "EDGE", DARK: "DARK"}


def _legend(lang):
    items = "".join(f'<div><span style="background:{COLORS[k]}"></span>{k}</div>' for k in ALL_LABELS)
    return f'<div class="lisa-legend">{items}</div>'


def _legend_guide_html(L):
    def _b(t):  # khối này là HTML thô nên đổi **đậm** của Markdown sang <b>
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    cards = "".join(
        f'<div class="lisa-li" style="animation-delay:{0.05 * i:.2f}s"><i style="background:{COLORS[k]}"></i>'
        f'<div><b>{k}</b><span>{_b(L["legend_desc"].get(_CLS_KEY.get(k, ""), ""))}</span></div></div>'
        for i, k in enumerate(ALL_LABELS))
    return f'<div class="lisa-leg">{cards}</div>'


class _LisaIntro(MacroElement):
    """Hoạt cảnh mở đầu cho bản đồ LISA (chỉ đổi style hiển thị, không đụng dữ liệu)."""
    _template = Template(
        """
        {% macro script(this, kwargs) %}
        (function () {
            var map = {{ this._parent.get_name() }};
            var layer = {{ this.layer.get_name() }};
            var C = {{ this.cfg }};
            if (!C.on) { return; }
            if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) { return; }
            var items = [];
            layer.eachLayer(function (l) { if (l.getBounds) { items.push(l); } });
            var N = items.length;
            var ripple = !!C.ripple && N > 0 && N <= C.max;
            var c0 = map.getCenter(), z0 = map.getZoom();
            if (C.fly) { map.setView(c0, Math.max(z0 - 2, 1), {animate: false}); }
            var base = [], dist = [], last = [], i, d, o, ctr, dx, dy, dmax = 1e-12;
            if (ripple) {
                for (i = 0; i < N; i++) {
                    o = items[i].options;
                    ctr = items[i].getBounds().getCenter();
                    dx = ctr.lng - C.cx; dy = ctr.lat - C.cy;
                    d = Math.sqrt(dx * dx + dy * dy);
                    base.push([o.fillOpacity == null ? 0.2 : o.fillOpacity, o.opacity == null ? 1 : o.opacity]);
                    dist.push(d); last.push(0);
                    if (d > dmax) { dmax = d; }
                }
                for (i = 0; i < N; i++) {
                    dist[i] = dist[i] / dmax;
                    items[i].setStyle({fillOpacity: 0, opacity: 0});
                }
            }
            setTimeout(function () {
                if (C.fly) { map.flyTo(c0, z0, {duration: 1.7, easeLinearity: 0.25}); }
                if (!ripple) { return; }
                var t0 = null;
                function step(ts) {
                    if (t0 === null) { t0 = ts; }
                    var t = Math.min(1, (ts - t0) / C.dur), j, p;
                    for (j = 0; j < N; j++) {
                        p = (t - 0.55 * dist[j]) / 0.45;
                        p = p < 0 ? 0 : (p > 1 ? 1 : p);
                        p = p * p * (3 - 2 * p);
                        if (t >= 1) { p = 1; }
                        if (p !== last[j]) {
                            last[j] = p;
                            items[j].setStyle({fillOpacity: base[j][0] * p, opacity: base[j][1] * p});
                        }
                    }
                    if (t < 1) { requestAnimationFrame(step); }
                }
                requestAnimationFrame(step);
            }, 350);
        })();
        {% endmacro %}
        """
    )

    def __init__(self, layer, cfg):
        super().__init__()
        self._name = "LisaIntro"
        self.layer = layer
        self.cfg = json.dumps(cfg)


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
    st.caption(L["flow"])

    # ---------- tham số ----------
    with st.expander(L["params"], expanded=True):
        with st.form(key="lisa_params_form"):
            c1, c2, c3, c4 = st.columns(4)
            perms = c1.selectbox(L["perms"], [199, 499, 999], index=1, help=L["h_perms"])
            alpha = c2.selectbox(L["alpha"], [0.05, 0.01], index=0, help=L["h_alpha"])
            fdr = c3.toggle(L["fdr"], value=True, help=L["h_fdr"])
            use_log = c4.toggle(L["log"], value=False, help=L["h_log"])
            
            c5, c6, c7 = st.columns(3)
            thr = c5.number_input(L["thr"], min_value=0.0, max_value=5.0, value=0.0, step=0.1, help=L["h_thr"])
            min_clu = c6.slider(L["clu"], 1, 30, 4, help=L["h_clu"]) 
            min_nbr = c7.slider(L["nbr"], 1, 4, 1, help=L["h_nbr"])
            
            submit_lisa = st.form_submit_button(L["submit"], type="primary", help=L["h_submit"])

    # ---------- tính (cache trong session theo kết quả + tham số) ----------
    ckey = (res["ts"], size, perms, alpha, fdr, use_log, thr, min_clu, min_nbr)
    cache = st.session_state.setdefault("_lisa_cache", {})
    just_computed = ckey not in cache
    if ckey not in cache:
        if len(cache) >= 5:  # Giới hạn tối đa 5 bộ tham số trong RAM
            cache.pop(next(iter(cache)))
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
    _hh_pct = float(rm["hh_area_share"]) * 100
    _mi = float(rm["moran_I_lit"])
    _g = float(rm["gini_ntl_core_all"])
    _lines = []
    if rm["hotspot_dummy"]:
        _lines.append(L["v_hot"].format(k=min_clu, hh=_hh_pct))
    else:
        _lines.append(L["v_nohot"].format(k=min_clu) + (L["v_frag"].format(hh=_hh_pct) if _hh_pct > 0 else ""))
    if np.isfinite(_mi):
        _lines.append((L["v_mi_pos"] if _mi > 0 else L["v_mi_neg"]).format(mi=_mi))
    if np.isfinite(_g):
        _lines.append(L["v_gini"].format(g=_g, gd=L["gini_desc"][0 if _g < 0.4 else (1 if _g < 0.6 else 2)]))
    with st.container(border=True):
        st.markdown(f"**{L['verdict_t']}**")
        st.markdown("\n\n".join(_lines))
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
    st.caption(L["map_hint"])

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

    lisa_layer = folium.GeoJson(
        gj, name="LISA",
        style_function=lambda f: {"fillColor": f["properties"]["col"], "color": f["properties"]["col"],
                                  "weight": 0.4, "fillOpacity": 0.15 if f["properties"]["k"] in (NS, DARK) else 0.8},
        tooltip=folium.GeoJsonTooltip(fields=["c", "v", "z", "p", "k", "d"], aliases=L["tt"], sticky=False),
    )
    lisa_layer.add_to(m)
    folium.GeoJson(res["boundary_wgs"], interactive=False,
                   style_function=lambda _: {"fill": False, "color": "#222", "weight": 1.5}).add_to(m)
    m.get_root().header.add_child(folium.Element(LISA_MAP_CSS))
    _LisaIntro(lisa_layer, {
        "on": True, "fly": bool(just_computed), "ripple": bool(just_computed), "max": 9000, "dur": 1500,
        "cx": float((minx + maxx) / 2), "cy": float((miny + maxy) / 2),
    }).add_to(m)
    m.get_root().html.add_child(folium.Element(_legend(lang)))
    import streamlit.components.v1 as components
    components.html(m.get_root().render(), height=640)
    with st.expander(L["guide_t"], expanded=False):
        st.markdown(_legend_guide_html(L), unsafe_allow_html=True)

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
