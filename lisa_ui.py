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

from lisa_core import ALL_LABELS, DARK, EDGE, NS, SPILLOVER_RINGS, run_lisa, run_spacetime_lisa
from lisa_diagnostics import (
    HEAVY_WORK_LIMIT, SEED_LIST, auto_diagnostics, estimate_seconds, heavy_work_units,
    method_sensitivity, perm_power, seed_stability, tail_sensitivity,
)

COLORS = {  # quy ước màu GeoDa
    "High-High": "#d7191c", "Low-Low": "#2c7bb6", "High-Low": "#fdae61", "Low-High": "#abd9e9",
    NS: "#d9d9d9", EDGE: "#8c8c8c", DARK: "#2a2a33",
}
KEY_COLS = ("iso3", "region_id", "year", "cell_size_m")

# =====================================================================
# VĂN BẢN
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
            "- **p nhỏ nhất** = 2/(số hoán vị + 1) (kiểm định 2 phía). Nếu FDR bật mà không có ô HH nào, hãy tăng số hoán vị.\n"
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
            "- **Minimum p** = 2/(permutations + 1) (two-sided). If FDR is on and HH is empty, raise permutations.\n"
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
        "HH": "Ô sáng cao nằm giữa các ô sáng cao: **điểm nóng (Hotspot)** thực sự.",
        "LL": "Ô sáng yếu (< TB vùng sáng) nằm giữa các ô sáng yếu: **điểm lạnh (Coldspot)** của vùng sáng.",
        "HL": "Ô sáng cao nằm giữa các ô sáng yếu: **điểm sáng nổi bật cục bộ** (Spatial Outlier).",
        "LH": "Ô sáng yếu nằm giữa các ô sáng cao: **vùng trũng ánh sáng** giữa khu vực phát triển.",
        "NS": "Không có ý nghĩa thống kê (không khác biệt so với phân bố ngẫu nhiên).",
        "EDGE": "Ô biên bị cắt bởi ranh giới (< 99% diện tích chuẩn), loại khỏi kiểm định.",
        "DARK": "Ô không sáng (NTL ≤ ngưỡng), tách riêng khỏi đồ thị láng giềng vùng sáng.",
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
        "HH": "High-radiance cell surrounded by high-radiance cells: a true **hotspot**.",
        "LL": "Low-lit cell (< lit-area mean) surrounded by low-lit cells: a **cold spot** within the lit area.",
        "HL": "High-radiance cell surrounded by low-lit cells: **local bright outlier** (Spatial Outlier).",
        "LH": "Low-lit cell surrounded by high-radiance cells: **dim pocket** inside a developed zone.",
        "NS": "Not statistically significant (indistinguishable from spatial randomness).",
        "EDGE": "Border cell clipped by the boundary (< 99% standard area), excluded from testing.",
        "DARK": "Unlit cell (NTL ≤ threshold), excluded from the lit-area neighbour graph.",
    },
})

RING_COLORS = {
    "0_Treated_HH": "#d7191c",
    "1_Spillover_0_2km": "#fdae61",
    "2_Spillover_2_5km": "#fee08b",
    "3_Spillover_5_10km": "#abdda4",
    "4_Pure_Control_gt10km": "#2b83ba",
    "Edge_Masked": "#8c8c8c",
    "No_HH_Cluster": "#4a4a55",
}

T["vi"].update({
    "h_kpi_title": "4 chỉ số tổng hợp cấp vùng–năm được trích xuất tự động từ kiểm định LISA để đưa vào bảng hồi quy Panel.",
    "h_map_t": "Bản đồ tương tác cấp ô lưới. Cho phép chuyển đổi trực tiếp giữa Cụm LISA, Vành đai lan tỏa (Spillover Rings) và Tiếp cận thị trường (Recentered MA).",
    "h_comp_t": "Phân bố tỷ trọng diện tích các trạng thái không gian và đồ thị phân tán Moran kiểm tra cấu trúc tự tương quan.",
    "h_comp": "Số lượng ô và tỷ lệ % diện tích của từng trạng thái LISA trên tổng diện tích tự nhiên của địa phương.",
    "h_fq_title": "4 nhóm chỉ số kinh tế lượng không gian biên (2022–2026) đo lường cấu trúc đô thị và nhận diện nhân quả.",
    "h_ring_tbl": "Phân tách địa phương thành 5 vành đai đồng tâm từ biên cụm điểm nóng (Butts, 2024) để bóc tách hiệu ứng tràn và cô lập nhóm đối chứng sạch (>10km).",
    "h_rdd_chart": "Đồ thị gián đoạn không gian (Spatial RDD) theo khoảng cách có dấu tới biên cụm nóng (d < 0: trong lõi, d > 0: ngoài lõi).",
    "donut_rdd": "Khuyết biên Donut RDD (bỏ |d| < 0.5 km chống nhiễu tràn sáng VIIRS)",
    "h_donut_rdd": "Loại bỏ các ô nằm trong bán kính 500m quanh ranh giới cụm nóng để khử tự tương quan cơ học do độ phân giải gốc ~463m của vệ tinh VIIRS (Barreca et al., 2011; Gibson et al., 2021).",
    "h_st_year_t0": "Chọn năm gốc đối chiếu (t₀) để tính sai phân không–thời gian Δz và ma trận chuyển dịch Markov tới năm hiện tại.",
    "h_st_run_btn": "Tải ảnh vệ tinh VIIRS năm t₀ trên đúng lưới UTM hiện tại và tính vector dịch chuyển không gian 2 kỳ.",
    "h_st_shorrocks": "Chỉ số dịch chuyển Shorrocks (0 = thứ hạng không gian đóng băng hoàn toàn; càng cao = mức độ xáo trộn giữa các phân vị càng mạnh).",
    "h_st_synergy": "Tỷ lệ diện tích vùng lõi có cả ô tâm và các ô láng giềng cùng tăng trưởng bức xạ tương đối (Δz ≥ 0, ΔLag z ≥ 0).",
    "h_st_shadow": "Tỷ lệ diện tích vùng lõi bị suy giảm tương đối khi vùng lân cận tăng trưởng nóng (Δz < 0, ΔLag z ≥ 0: hiệu ứng hút nguồn lực).",
    "h_markov_hi": "Xác suất chuyển dịch giữa 4 phân vị ánh sáng (Q1→Q4) khi ô nằm cạnh các láng giềng ban đầu có độ sáng CAO (trên trung vị Lag z năm t₀).",
    "h_markov_lo": "Xác suất chuyển dịch giữa 4 phân vị ánh sáng (Q1→Q4) khi ô nằm cạnh các láng giềng ban đầu có độ sáng THẤP (dưới trung vị Lag z năm t₀).",
    "h_bridge_t": "Xuất dữ liệu vi mô (100% quan sát cấp ô) và dữ liệu vĩ mô (1 dòng/vùng-năm) phục vụ hồi quy trên Stata, R, Python.",
    "h_panel_tbl": "Bảng dữ liệu Panel tích lũy qua các lần bấm 'Thêm vùng-năm'. Khóa chính: (iso3, region_id, year, cell_size_m).",
    "map_mode_lbl": "Lớp hiển thị bản đồ",
    "map_modes": {"lisa": "Cụm LISA", "ring": "Vành đai lan tỏa (Spillover)", "ma": "Recentered MA"},
    "h_map_mode": "Đổi lớp tô màu trên bản đồ để kiểm tra trực quan các biến kinh tế lượng Q1.",
    "tt_full": ["Ô", "NTL", "z (ô sáng)", "p giả", "Trạng thái LISA", "Cách tâm CBD (km)", "Cách biên HH (km)", "Vành đai lan tỏa", "Recentered MA"],
})

T["en"].update({
    "h_kpi_title": "4 region-year summary indicators extracted from LISA for macro panel regressions.",
    "h_map_t": "Interactive grid map. Switch between LISA Clusters, Causal Spillover Rings, and Recentered Market Access.",
    "h_comp_t": "Area share breakdown across spatial classes and Moran scatterplot diagnosing spatial autocorrelation.",
    "h_comp": "Cell count and area share (%) of each LISA class relative to total locality area.",
    "h_fq_title": "4 frontier spatial econometric indicator groups (2022–2026) for urban structure and causal inference.",
    "h_ring_tbl": "Partitions the locality into 5 concentric exposure rings from the hotspot boundary (Butts, 2024) to isolate pure controls (>10km).",
    "h_rdd_chart": "Spatial Regression Discontinuity (Spatial RDD) curve along signed distance to the hotspot boundary (d < 0: inside, d > 0: outside).",
    "donut_rdd": "Donut RDD (drop |d| < 0.5 km to purge VIIRS blooming)",
    "h_donut_rdd": "Excludes cells within 500m of the hotspot boundary to remove mechanical autocorrelation from native ~463m VIIRS pixels (Barreca et al., 2011; Gibson et al., 2021).",
    "h_st_year_t0": "Select comparison base year (t₀) to compute space-time first differences Δz and Spatial Markov transitions.",
    "h_st_run_btn": "Fetch base-year t₀ VIIRS raster on the current UTM grid and compute two-period spatial dynamics.",
    "h_st_shorrocks": "Shorrocks Mobility Index (0 = completely static spatial hierarchy; higher values indicate stronger rank mobility).",
    "h_st_synergy": "Share of core area where both the focal cell and its neighbors experienced positive relative growth (Δz ≥ 0, ΔLag z ≥ 0).",
    "h_st_shadow": "Share of core area experiencing relative decline while surrounding neighbors grow (Δz < 0, ΔLag z ≥ 0: resource siphoning effect).",
    "h_markov_hi": "Transition probability matrix across 4 light quartiles (Q1→Q4) conditioned on HIGH initial neighbor brightness (above median Lag z at t₀).",
    "h_markov_lo": "Transition probability matrix across 4 light quartiles (Q1→Q4) conditioned on LOW initial neighbor brightness (below median Lag z at t₀).",
    "h_bridge_t": "Export micro cell-level CSVs (100% observations) and macro region-year panel rows for Stata, R, and Python.",
    "h_panel_tbl": "Accumulated panel table across 'Add region-year' clicks. Primary key: (iso3, region_id, year, cell_size_m).",
    "map_mode_lbl": "Map display layer",
    "map_modes": {"lisa": "LISA Clusters", "ring": "Spillover Rings", "ma": "Recentered MA"},
    "h_map_mode": "Switch the active choropleth layer to visually inspect frontier Q1 spatial variables.",
    "tt_full": ["Cell", "NTL", "z (lit)", "pseudo p", "LISA Class", "Dist to CBD (km)", "Signed dist HH (km)", "Spillover Ring", "Recentered MA"],
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
    def _b(t):  
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    cards = "".join(
        f'<div class="lisa-li" style="animation-delay:{0.05 * i:.2f}s"><i style="background:{COLORS[k]}"></i>'
        f'<div><b>{k}</b><span>{_b(L["legend_desc"].get(_CLS_KEY.get(k, ""), ""))}</span></div></div>'
        for i, k in enumerate(ALL_LABELS))
    return f'<div class="lisa-leg">{cards}</div>'


class _LisaIntro(MacroElement):
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
    try:
        pop = st.popover("❓", help=brief)
    except TypeError:  
        pop = st.popover("❓")
    with pop:
        st.markdown(f"**{title}**")
        st.markdown(body)


def _pin(cfg_cls, **kw):
    try:
        return cfg_cls(pinned=True, **kw)
    except TypeError:
        return cfg_cls(**kw)


_LVL_ICON = {"ok": "✅", "warn": "⚠️", "info": "ℹ️"}
_DIAG_FIFO = 5


def _fifo_put(cache, key, value, cap):
    if key not in cache and len(cache) >= cap:
        cache.pop(next(iter(cache)))
    cache[key] = value


def _num(v, fmt="{:.3f}"):
    try:
        return fmt.format(v) if np.isfinite(v) else "N/A"
    except (TypeError, ValueError):
        return "N/A"


def _diag_line(it, vi):
    """Một dòng kết quả kiểm tra nhẹ (markdown)."""
    k, v = it["key"], it["vals"]
    ic = _LVL_ICON[it["level"]]
    if k == "perm":
        if not v["applies"]:
            return f"{ic} " + ("**Số hoán vị / FDR:** FDR đang tắt nên không áp dụng." if vi
                               else "**Permutations / FDR:** FDR is off, not applicable.")
        base = (f"**Số hoán vị / FDR:** {v['m']:,} ô kiểm định, p nhỏ nhất = {v['p_floor']:.4f}; FDR cần ≥ "
                f"{v['min_hits']:,} ô chạm mức sàn ({v['ratio'] * 100:.0f}% số ô kiểm định)." if vi else
                f"**Permutations / FDR:** {v['m']:,} tested cells, minimum p = {v['p_floor']:.4f}; BH needs ≥ "
                f"{v['min_hits']:,} cells at the floor ({v['ratio'] * 100:.0f}% of tested cells).")
        if v["auto_from"] is not None:
            base += (f" Đã tự nâng số hoán vị từ {v['auto_from']} lên {v['perms']} vì tổ hợp ban đầu bất khả thi."
                     if vi else f" Permutations auto-raised from {v['auto_from']} to {v['perms']}: the original setting was infeasible.")
        elif (v["infeasible"] or v["risky"]) and v["suggested_perms"]:
            base += (f" Hãy tăng số hoán vị lên {v['suggested_perms']} hoặc nới α." if vi
                     else f" Raise permutations to {v['suggested_perms']} or relax α.")
        elif v["infeasible"] or v["risky"]:
            base += (" Hãy nới α hoặc tắt FDR." if vi else " Relax α or turn FDR off.")
        return f"{ic} {base}"
    if k == "hill":
        if not np.isfinite(v["alpha"]):
            return f"{ic} " + ("**Đuôi Pareto:** không đủ ô sáng (cần ≥ 15) hoặc đuôi không phân tán để ước lượng." if vi
                               else "**Pareto tail:** not enough lit cells (≥ 15 needed) or no tail dispersion.")
        t = (f"**Đuôi Pareto:** α = {v['alpha']:.2f} ± {v['se']:.2f} (CI95 {v['ci_lo']:.2f}–{v['ci_hi']:.2f}, k = {v['k']}); "
             f"KS p = {v['ks_p']:.3f}." if vi else
             f"**Pareto tail:** α = {v['alpha']:.2f} ± {v['se']:.2f} (95% CI {v['ci_lo']:.2f}–{v['ci_hi']:.2f}, k = {v['k']}); "
             f"KS p = {v['ks_p']:.3f}.")
        if v["power_law_ok"] is False:
            t += " Đuôi không giống luật lũy thừa, hãy diễn giải α thận trọng." if vi else " The tail does not look like a power law; interpret α with care."
        if v["k"] < 20:
            t += " Mẫu đuôi nhỏ (k < 20), sai số rất lớn." if vi else " Small tail sample (k < 20), very wide error."
        return f"{ic} {t}"
    if k == "primacy":
        if not np.isfinite(v["primacy"]):
            return f"{ic} " + ("**Thống trị cụm đầu:** chưa có cụm HH đủ lớn." if vi else "**Cluster primacy:** no sufficiently large HH cluster.")
        t = (f"**Thống trị cụm đầu:** {v['n_clusters']} cụm HH, tỷ số = {v['primacy']:.2f}." if vi
             else f"**Cluster primacy:** {v['n_clusters']} HH clusters, ratio = {v['primacy']:.2f}.")
        if v["multipolar"]:
            t += (" Địa phương đa cực: tâm CBD có thể nhảy giữa các lần chạy; hãy cố định tâm theo năm gốc t₀ khi phân tích chuỗi thời gian."
                  if vi else " Multipolar locality: the CBD centre may jump between runs; fix it at base year t₀ for time series.")
        return f"{ic} {t}"
    if k == "resid":
        if not np.isfinite(v["I"]):
            return f"{ic} " + ("**Phần dư độ dốc đô thị:** không đủ dữ liệu." if vi else "**Urban-gradient residuals:** not enough data.")
        pt = f"p = {v['p']:.3f}" if v["perm_done"] else ("(không tính p-value vì lưới lớn)" if vi else "(no p-value: large grid)")
        t = f"**Phần dư độ dốc đô thị:** Moran's I = {v['I']:.3f}, {pt}." if vi else f"**Urban-gradient residuals:** Moran's I = {v['I']:.3f}, {pt}."
        if v["flag"]:
            t += (" Phần dư còn tự tương quan không gian: R² của độ dốc có thể bị thổi phồng." if vi
                  else " Residuals are still spatially autocorrelated: the gradient R² may be inflated.")
        return f"{ic} {t}"
    # dark
    t = (f"**Ô tối:** {v['share'] * 100:.0f}% số ô lõi có NTL = 0." if vi else f"**Dark cells:** {v['share'] * 100:.0f}% of core cells have NTL = 0.")
    if v["flag"]:
        t += (" Tỷ lệ cao: ln(1+NTL) nhạy với đơn vị đo; nên chạy thêm PPML (Chen & Roth, 2024)." if vi
              else " High share: ln(1+NTL) is scale-sensitive; also run PPML (Chen & Roth, 2024).")
    return f"{ic} {t}"


def _render_diagnostics(*, lang, ckey, out, grid_utm, size, perms, alpha, fdr, use_log, thr,
                        min_clu, min_nbr, perm_auto_from):
    """Expander kiểm định độ tin cậy. Trả về dict biến xuất thêm vào dòng panel."""
    vi = lang != "en"
    cdf, rm = out.cell_df, out.region_metrics

    acache = st.session_state.setdefault("_diag_cache", {})
    if ckey not in acache:
        cent = grid_utm.geometry.centroid
        _fifo_put(acache, ckey, auto_diagnostics(
            cent.x.to_numpy(), cent.y.to_numpy(), grid_utm["ntl_mean"].to_numpy(float),
            grid_utm["area_km2"].to_numpy(float), size, cdf, rm, perms, alpha, fdr, perm_auto_from), _DIAG_FIFO)
    auto = acache[ckey]
    n_warn = auto["n_warn"]
    title = ("🔬 Kiểm định độ tin cậy" if vi else "🔬 Reliability diagnostics") + \
        (f"  ·  ⚠️ {n_warn}" if n_warn else "  ·  ✅")
    export = dict(auto["export"])

    with st.expander(title, expanded=bool(n_warn)):
        st.caption("Các kiểm tra nhẹ chạy tự động theo từng lần cập nhật LISA; kiểm định nặng chỉ chạy khi bạn bấm nút."
                   if vi else "Light checks run automatically on every LISA update; heavy tests run only when you press a button.")
        st.markdown("\n\n".join(_diag_line(it, vi) for it in auto["items"]))

        st.markdown("---")
        st.markdown("**" + ("Kiểm định nặng (chạy khi bấm nút)" if vi else "Heavy tests (on demand)") + "**")
        m = int(rm["n_cells_tested"])
        n_seed = len(SEED_LIST)
        base_kw = dict(
            cx=grid_utm.geometry.centroid.x.to_numpy(), cy=grid_utm.geometry.centroid.y.to_numpy(),
            ntl=grid_utm["ntl_mean"].to_numpy(float), area_km2=grid_utm["area_km2"].to_numpy(float),
            cell_size_m=size, lit_threshold=thr, edge_tol=0.99, perms=perms, alpha=alpha, fdr=fdr,
            log_transform=use_log, min_neighbors=min_nbr, min_cluster_cells=min_clu,
        ) if m > 0 else None
        hcache = st.session_state.setdefault("_diag_heavy", {})

        w_seed, w_meth = heavy_work_units(m, perms, n_seed), heavy_work_units(m, perms, 2)
        too_big = max(w_seed, w_meth) > HEAVY_WORK_LIMIT
        st.caption((f"Ước tính thô trên máy yếu: seed ≈ {estimate_seconds(m, perms, n_seed):.0f}s, "
                    f"so sánh phương pháp ≈ {estimate_seconds(m, perms, 2):.0f}s. Kết quả được lưu đệm."
                    if vi else f"Rough estimate on a weak machine: seeds ≈ {estimate_seconds(m, perms, n_seed):.0f}s, "
                    f"method comparison ≈ {estimate_seconds(m, perms, 2):.0f}s. Results are cached."))
        if too_big:
            st.warning("Vùng quá lớn cho kiểm định nặng: hãy tăng kích thước ô hoặc giảm số hoán vị." if vi
                       else "Area too large for heavy tests: use a coarser cell size or fewer permutations.")

        b1, b2, b3 = st.columns(3)
        run_seed = b1.button((f"▶ Ổn định theo seed ({n_seed} lần)" if vi else f"▶ Seed stability ({n_seed} runs)"),
                             key="dg_btn_seed", disabled=too_big or base_kw is None, use_container_width=True)
        run_meth = b2.button("▶ So sánh thô / P99 / ln" if vi else "▶ Raw vs P99 vs ln", key="dg_btn_meth",
                             disabled=too_big or base_kw is None, use_container_width=True)
        run_tail = b3.button("▶ Độ nhạy tail_frac" if vi else "▶ tail_frac sensitivity", key="dg_btn_tail",
                             use_container_width=True)

        def _progress(label):
            bar = st.progress(0.0, text=label)
            return lambda f, txt: bar.progress(min(1.0, f), text=f"{label}: {txt}")

        if run_seed and (ckey, "seed") not in hcache:
            _fifo_put(hcache, (ckey, "seed"), seed_stability(base_kw, progress=_progress("seed")), 12)
        if run_meth and (ckey, "meth") not in hcache:
            base_hh = (cdf["lisa_class"] == "High-High").to_numpy()
            _fifo_put(hcache, (ckey, "meth"), method_sensitivity(base_kw, base_hh, use_log,
                                                                 progress=_progress("method")), 12)
        if run_tail and (ckey, "tail") not in hcache:
            lit = cdf["is_dark"].to_numpy() == 0
            _fifo_put(hcache, (ckey, "tail"), tail_sensitivity(
                grid_utm["ntl_mean"].to_numpy(float), ~cdf["is_edge_masked"].to_numpy().astype(bool), lit), 12)

        r = hcache.get((ckey, "seed"))
        if r:
            c1, c2 = st.columns(2)
            c1.metric("sd(hh_area_share) qua các seed" if vi else "sd(hh_area_share) across seeds", f"{r['sd'] * 100:.3f}%",
                      help="Ngưỡng ổn định: 0,5%." if vi else "Stability threshold: 0.5%.")
            c2.metric("hh_area_share trung bình" if vi else "Mean hh_area_share", f"{r['mean'] * 100:.2f}%")
            if r["unstable"]:
                st.warning("Kết quả đổi nhãn theo seed" + (": hãy tăng số hoán vị lên 999." if r["recommend_999"] else ".")
                           if vi else "Labels change with the seed" + (": raise permutations to 999." if r["recommend_999"] else "."))
            else:
                st.success("Ổn định theo seed (sd ≤ 0,5%)." if vi else "Stable across seeds (sd ≤ 0.5%).")
            export["hh_share_seed_sd"] = round(r["sd"], 6)
        r = hcache.get((ckey, "meth"))
        if r:
            c1, c2, c3 = st.columns(3)
            c1.metric("Jaccard thô ↔ P99" if vi else "Jaccard raw ↔ P99", f"{r['jaccard_raw_winsor']:.3f}")
            c2.metric("Jaccard thô ↔ ln" if vi else "Jaccard raw ↔ ln", f"{r['jaccard_raw_log']:.3f}")
            c3.metric("Jaccard P99 ↔ ln" if vi else "Jaccard P99 ↔ ln", f"{r['jaccard_winsor_log']:.3f}")
            st.caption((f"Số ô HH: thô {r['n_hh']['raw']:,} · P99 {r['n_hh']['winsor']:,} · ln {r['n_hh']['log']:,}. "
                        "Jaccard thấp nghĩa là cụm HH nhạy với ô dị thường."
                        if vi else f"HH cells: raw {r['n_hh']['raw']:,} · P99 {r['n_hh']['winsor']:,} · ln {r['n_hh']['log']:,}. "
                        "Low Jaccard means the HH set is sensitive to outliers."))
            export["hh_jaccard_raw_winsor"] = round(r["jaccard_raw_winsor"], 4)
            export["hh_jaccard_raw_log"] = round(r["jaccard_raw_log"], 4)
        r = hcache.get((ckey, "tail"))
        if r:
            rows = [{"tail_frac": f"{x['tail_frac']:.0%}", "k": x["k"], "α": _num(x["alpha"], "{:.2f}"),
                     "SE": _num(x["se"], "{:.2f}"), "KS p": _num(x["ks_p"], "{:.3f}")} for x in r["rows"]]
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            st.caption((f"Biên độ α giữa các ngưỡng cắt: {_num(r['spread'], '{:.2f}')} (nhỏ = đuôi ổn định)."
                        if vi else f"α range across tail fractions: {_num(r['spread'], '{:.2f}')} (small = stable tail)."))
            export["pareto_alpha_tail_spread"] = round(r["spread"], 4) if np.isfinite(r["spread"]) else float("nan")
    return export



def render_lisa_tab(res, grid_utm, export_df, *, lang="vi", region_id="region", region_label="",
                    render_cap=30_000, basemap="CartoDB positron",
                    fetch_year_ntl_fn=None, available_years=None):
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
    # Kiểm tra điều kiện đủ của số hoán vị TRƯỚC khi tính: tổ hợp bất khả thi (FDR không thể bác bỏ gì) bị tự nâng lên 999
    perm_auto_from = None
    _ar0 = grid_utm["area_km2"].to_numpy(float)
    _nt0 = grid_utm["ntl_mean"].to_numpy(float)
    _m_est = int(((_nt0 > thr) & ~(_ar0 < 0.99 * (size / 1000.0) ** 2)).sum())
    _pw0 = perm_power(_m_est, int(perms), float(alpha), bool(fdr))
    if _pw0["infeasible"] and perms < 999:
        perm_auto_from, perms = int(perms), 999
        st.info((f"Tổ hợp {perm_auto_from} hoán vị với α = {alpha} khiến FDR không thể bác bỏ ô nào; đã tự nâng lên 999 hoán vị."
                 if lang != "en" else
                 f"{perm_auto_from} permutations with α = {alpha} make BH unable to reject anything; auto-raised to 999."))
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

    out = cache[ckey]
    cdf, rm = out.cell_df, out.region_metrics
                        
    # ---------- KPI ----------
    st.divider()
    st.markdown(f"#### {L['kpi_title']}", help=L["h_kpi_title"])
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

    _diag_export = _render_diagnostics(
        lang=lang, ckey=ckey, out=out, grid_utm=grid_utm, size=size, perms=perms, alpha=alpha, fdr=fdr,
        use_log=use_log, thr=thr, min_clu=min_clu, min_nbr=min_nbr, perm_auto_from=perm_auto_from)
    rm_full = {**rm, **_diag_export}

    # ---------- Bản đồ ----------
    st.divider()
    st.markdown(f"#### {L['map_t']}", help=L["h_map_t"])
    forced = n > render_cap
    h0, h1, h2 = st.columns([2.2, 1.1, 1.1])
    map_mode = h0.radio(
        L["map_mode_lbl"], ["lisa", "ring", "ma"], horizontal=True,
        format_func=lambda k: L["map_modes"][k], key="lisa_map_mode", help=L["h_map_mode"],
    )
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
    sdist_arr = cdf.get("signed_dist_hh_km", pd.Series(np.zeros(len(cdf)))).to_numpy(float)
    ring_arr_map = cdf.get("spillover_ring", pd.Series(["N/A"] * len(cdf))).to_numpy()
    rma_arr_map = cdf.get("recentered_market_access", pd.Series(np.zeros(len(cdf)))).to_numpy(float)

    if map_mode == "ring":
        col_list = [RING_COLORS.get(str(x), "#8c8c8c") for x in ring_arr_map[idx]]
    elif map_mode == "ma":
        sub_ma = rma_arr_map[idx]
        lim = float(np.nanpercentile(np.abs(sub_ma), 95)) if np.isfinite(sub_ma).any() else 1.0
        lim = max(lim, 1e-6)
        col_list = [
            "#8c8c8c" if not np.isfinite(v) else (
                "#d7191c" if v > 0.35 * lim else ("#fdae61" if v > 0.05 * lim else (
                    "#f7f7f7" if v >= -0.05 * lim else ("#abd9e9" if v >= -0.35 * lim else "#2c7bb6")
                ))
            )
            for v in sub_ma
        ]
    else:
        col_list = [COLORS[x] for x in lab]

    gj = gpd.GeoDataFrame({
        "c": [f"#{int(i)}" for i in grid_utm["grid_id"].to_numpy()[idx]],
        "v": np.round(grid_utm["ntl_mean"].to_numpy()[idx], 2),
        "z": np.round(cdf["ntl_z_lit"].to_numpy()[idx], 2),
        "p": np.round(cdf["lisa_p_sim"].to_numpy()[idx], 4),
        "k": lab,
        "d": np.round(dist_arr[idx], 2),
        "sd": np.round(sdist_arr[idx], 2),
        "rg": ring_arr_map[idx],
        "ma": np.round(rma_arr_map[idx], 2),
        "col": col_list,
    }, geometry=sub.values, crs=4326)

    minx, miny, maxx, maxy = res["boundary_wgs"].total_bounds

    m = folium.Map(
        location=[(miny + maxy) / 2, (minx + maxx) / 2],
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri",
        control_scale=True,
        prefer_canvas=True,
        no_wrap=True,
        max_zoom=16,
    )
    m.fit_bounds([[miny, minx], [maxy, maxx]])

    lisa_layer = folium.GeoJson(
        gj, name="LISA",
        style_function=lambda f: {
            "fillColor": f["properties"]["col"], "color": f["properties"]["col"],
            "weight": 0.4, "fillOpacity": 0.15 if (map_mode == "lisa" and f["properties"]["k"] in (NS, DARK)) else 0.82
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["c", "v", "z", "p", "k", "d", "sd", "rg", "ma"],
            aliases=L["tt_full"],
            sticky=False,
        ),
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
    st.markdown(f"#### {L['comp_t']}", help=L["h_comp_t"])
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
            st.markdown(f"**{L['comp']}**", help=L["h_comp"])
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

    st.divider()
    is_vi = (lang != "en")
    st.markdown(
        "#### 🚀 Chỉ số kinh tế lượng Không gian biên"
        if is_vi else
        "#### 🚀 Frontier spatial econometric indicators",
        help=L["h_fq_title"],
    )
                        
    fq1, fq2, fq3, fq4 = st.columns(4)
    _pa = rm.get("pareto_alpha_top10", float("nan"))
    _ug = rm.get("urban_gradient_decay", float("nan"))
    _mr2 = rm.get("monocentric_r2", float("nan"))
    _ar1 = rm.get("spatial_ar1_persistence", float("nan"))

    fq1.metric(
        "Pareto α (Top 10% Lights)" if is_vi else "Pareto α (Top 10% Tail)",
        f"{_pa:.2f}" if np.isfinite(_pa) else "N/A",
        help=("Số mũ Hill trên Top 10% ô sáng (Bluhm & Krause, 2022). Càng gần 1.0 nghĩa là đuôi cực trị càng dày (siêu tập trung ở lõi đỉnh)."
              if is_vi else "Hill tail exponent on top 10% lit cells (Bluhm & Krause, 2022). Closer to 1.0 indicates extreme upper-tail concentration."),
    )
    fq2.metric(
        "Độ dốc đô thị γ (km⁻¹)" if is_vi else "Urban Decay Gradient γ (km⁻¹)",
        f"{_ug:.4f}" if np.isfinite(_ug) else "N/A",
        help=("Hệ số suy giảm mật độ kinh tế WLS ln(1+NTL) theo khoảng cách tới tâm CBD (Duranton & Puga, 2023)."
              if is_vi else "Area-weighted WLS decay rate of ln(1+NTL) per km from the CBD (Duranton & Puga, 2023)."),
    )
    fq3.metric(
        "Độ khớp đơn tâm (R²)" if is_vi else "Monocentricity Fit (R²)",
        f"{_mr2 * 100:.1f}%" if np.isfinite(_mr2) else "N/A",
        help=("Tỷ lệ phương sai ln(1+NTL) giải thích bởi khoảng cách tới 1 tâm CBD duy nhất. R² thấp + nhiều cụm HH = Đô thị đa cực (Polycentric)."
              if is_vi else "Share of ln(1+NTL) variance explained by distance to a single CBD. Low R² with multiple HH clusters indicates polycentricity."),
    )
    fq4.metric(
        "Độ bền AR(1) không gian" if is_vi else "Spatial AR(1) Persistence",
        f"{_ar1:.3f}" if np.isfinite(_ar1) else "N/A",
        help=("Hệ số tự tương quan bậc 1 (Müller & Watson, 2024 Econometrica). Nếu > 0.70, dữ liệu tiệm cận nghiệm đơn vị không gian (cần lấy sai phân hoặc kiểm soát chặt)."
              if is_vi else "First-order spatial autoregression coefficient (Müller & Watson, 2024 Econometrica). Values > 0.70 warn of near-unit-root spatial persistence."),
    )

    col_ring, col_rdd = st.columns([1.05, 1.45])
    with col_ring:
        with st.container(border=True):
            st.markdown(
                "**🎯 Vành đai lan tỏa nhân quả**"
                if is_vi else
                "**🎯 Causal spillover rings**",
                help=L["h_ring_tbl"],
            )
            ring_arr = cdf["spillover_ring"].to_numpy()
            ntl_arr = grid_utm["ntl_mean"].to_numpy(float)
            rec_ma_arr = cdf["recentered_market_access"].to_numpy(float)
            ring_rows = []
            for rg_code in SPILLOVER_RINGS:
                m_r = ring_arr == rg_code
                ring_rows.append({
                    ("Vành đai tiếp xúc" if is_vi else "Exposure Ring"): rg_code,
                    ("Số ô" if is_vi else "Cells"): int(m_r.sum()),
                    ("% Diện tích" if is_vi else "% Area"): round(float(area[m_r].sum() / max(area.sum(), 1e-12) * 100), 1),
                    ("NTL TB" if is_vi else "Mean NTL"): round(float(ntl_arr[m_r].mean()), 2) if m_r.any() else 0.0,
                    ("MA khử lệch" if is_vi else "Recentered MA"): round(float(np.nanmean(rec_ma_arr[m_r])), 2) if m_r.any() and np.isfinite(rec_ma_arr[m_r]).any() else 0.0,
                })
            st.dataframe(pd.DataFrame(ring_rows), hide_index=True, use_container_width=True)

    with col_rdd:
        with st.container(border=True):
            st.markdown(
                "**📉 Đường cong suy giảm & Gián đoạn ranh giới đô thị**"
                if is_vi else
                "**📉 Urban boundary discontinuity & Spillover decay (Spatial RDD)**",
                help=L["h_rdd_chart"],
            )
            donut_on = st.toggle(L["donut_rdd"], value=False, key="lisa_donut_rdd", help=L["h_donut_rdd"])
            rdd_df = pd.DataFrame({
                "signed_d": cdf["signed_dist_hh_km"].to_numpy(float),
                "ln_ntl": np.log1p(np.maximum(grid_utm["ntl_mean"].to_numpy(float), 0.0)),
                "ring": cdf["spillover_ring"].to_numpy(),
            }).dropna()
            rdd_df = rdd_df[rdd_df["ring"] != "Edge_Masked"]
            if donut_on:
                rdd_df = rdd_df[rdd_df["signed_d"].abs() >= 0.5]
            if not rdd_df.empty and len(rdd_df) >= 10:
                rdd_df["bin_d"] = (np.round(rdd_df["signed_d"] * 2.0) / 2.0)
                binned_rdd = (
                    rdd_df.groupby("bin_d", as_index=False)
                    .agg(mean_ln_ntl=("ln_ntl", "mean"), cells=("ln_ntl", "size"))
                    .query("cells >= 2 and bin_d >= -10 and bin_d <= 15")
                )
                pts_chart = alt.Chart(binned_rdd).mark_line(point=True, color="#ffb703", strokeWidth=2.2).encode(
                    x=alt.X("bin_d:Q", title=("Khoảng cách có dấu tới biên cụm nóng (km) [ <0: Trong lõi | >0: Ngoài lõi ]"
                                              if is_vi else "Signed distance to hotspot boundary (km) [ <0: Inside | >0: Outside ]")),
                    y=alt.Y("mean_ln_ntl:Q", title="Mean ln(1 + NTL)"),
                    tooltip=[
                        alt.Tooltip("bin_d:Q", title="Signed Dist (km)", format=".1f"),
                        alt.Tooltip("mean_ln_ntl:Q", title="Mean ln(1+NTL)", format=".3f"),
                        alt.Tooltip("cells:Q", title="Cells"),
                    ],
                )
                zero_rule = alt.Chart(pd.DataFrame({"x": [0.0]})).mark_rule(
                    color="#d7191c", strokeDash=[5, 4], strokeWidth=2
                ).encode(x="x:Q")
                st.altair_chart((pts_chart + zero_rule).interactive().properties(height=265), use_container_width=True)
            else:
                st.info("Chưa đủ quan sát để vẽ đường cong Spatial RDD." if is_vi else "Not enough observations for Spatial RDD curve.")

    # ---------- MODULE 5: DYNAMIC SPACE-TIME LISA & SPATIAL MARKOV (t0 -> t1) ----------
    if fetch_year_ntl_fn is not None and available_years:
        other_years = [int(y) for y in available_years if int(y) != yr]
        if other_years:
            with st.expander(
                f"⚡ Động học Không – Thời gian & Ma trận Spatial Markov (So sánh năm đối chiếu t₀ → {yr})"
                if is_vi else
                f"⚡ Dynamic Space-Time LISA & Spatial Markov Matrix (Compare base year t₀ → {yr})",
                expanded=False,
            ):
                st.caption(
                    "Phân tích vector dịch chuyển (Δz, ΔLag z), phát hiện hiệu ứng 'Bóng tối tích tụ' (Agglomeration Shadow) "
                    "và tính ma trận xác suất chuyển dịch Markov có điều kiện không gian (Rey, Arribas-Bel, & Wolf, 2023; Borusyak et al., 2024)."
                    if is_vi else
                    "Computes directional movement vectors (Δz, ΔLag z), detects 'Agglomeration Shadow' effects, "
                    "and estimates conditional Spatial Markov transition matrices (Rey, Arribas-Bel, & Wolf, 2023; Borusyak et al., 2024)."
                )
                sc1, sc2 = st.columns([2, 1])
                default_idx = 0
                year_t0 = sc1.selectbox(
                    "Chọn năm gốc đối chiếu (t₀)" if is_vi else "Select comparison base year (t₀)",
                    other_years, index=default_idx, key="st_lisa_year_t0", help=L["h_st_year_t0"],
                )
                run_st_btn = sc2.button(
                    f"⚡ Chạy Động học ({year_t0} → {yr})" if is_vi else f"⚡ Run Dynamics ({year_t0} → {yr})",
                    type="primary", use_container_width=True, key="btn_run_spacetime", help=L["h_st_run_btn"],
                )
                st_cache = st.session_state.setdefault("_spacetime_cache", {})
                st_key = (res["ts"], size, int(year_t0), int(yr))
                if run_st_btn and st_key not in st_cache:
                    with st.spinner(f"Đang tải ảnh VIIRS năm {year_t0} và tính Space-Time LISA..." if is_vi
                                    else f"Fetching {year_t0} VIIRS raster and computing Space-Time LISA..."):
                        ntl_t0_arr = fetch_year_ntl_fn(int(year_t0))
                        cent_xy = grid_utm.geometry.centroid
                        st_cache[st_key] = run_spacetime_lisa(
                            cent_xy.x.to_numpy(), cent_xy.y.to_numpy(),
                            ntl_t0_arr, grid_utm["ntl_mean"].to_numpy(float),
                            grid_utm["area_km2"].to_numpy(float), size,
                            year_t0=int(year_t0), year_t1=int(yr),
                        )
                if st_key in st_cache:
                    st_out = st_cache[st_key]
                    sm = st_out.metrics
                    m1, m2, m3 = st.columns(3)
                    m1.metric(
                        "Chỉ số dịch chuyển Shorrocks" if is_vi else "Shorrocks Mobility Index",
                        f"{sm['shorrocks_mobility']:.3f}" if np.isfinite(sm["shorrocks_mobility"]) else "N/A",
                        help=L["h_st_shorrocks"],
                    )
                    m2.metric(
                        "Tăng trưởng cộng hưởng (Δz+, ΔLag+)" if is_vi else "Synergistic Growth Share",
                        f"{sm['synergistic_growth_pct']:.1f}%",
                        help=L["h_st_synergy"],
                    )
                    m3.metric(
                        "Bóng tối tích tụ (Δz-, ΔLag+)" if is_vi else "Agglomeration Shadow Share",
                        f"{sm['agglomeration_shadow_pct']:.1f}%",
                        help=L["h_st_shadow"],
                    )
                    n1, n2, n3 = st.columns(3)
                    n1.metric("Extensive: tối → sáng" if is_vi else "Extensive: dark → lit",
                              _num(sm["extensive_entry_pct"], "{:.1f}%"),
                              help=("Tỷ lệ ô tối ở t₀ trở nên sáng ở t₁ (biên độ rộng)." if is_vi
                                    else "Share of cells dark at t₀ that are lit at t₁ (extensive margin)."))
                    n2.metric("Extensive: sáng → tối" if is_vi else "Extensive: lit → dark",
                              _num(sm["extensive_exit_pct"], "{:.1f}%"),
                              help=("Tỷ lệ ô sáng ở t₀ trở nên tối ở t₁." if is_vi
                                    else "Share of cells lit at t₀ that are dark at t₁."))
                    n3.metric("Intensive: Δln NTL (sáng cả 2 kỳ)" if is_vi else "Intensive: Δln NTL (lit both periods)",
                              _num(sm["intensive_mean_dln_ntl"]),
                              help=(f"Tăng trưởng trung bình của ln(NTL) trên {sm['n_both_lit']:,} ô sáng ở cả hai kỳ (biên độ sâu)." if is_vi
                                    else f"Mean ln(NTL) growth over {sm['n_both_lit']:,} cells lit in both periods (intensive margin)."))
                    st.dataframe(st_out.regime_summary, hide_index=True, use_container_width=True)
                    mc1, mc2 = st.columns(2)
                    with mc1:
                        st.markdown(
                            "**Spatial Markov: Khi láng giềng ban đầu SÁNG CAO (High-Lag Context, %)**"
                            if is_vi else "**Spatial Markov: High-Lag Neighbor Context (%)**",
                            help=L["h_markov_hi"],
                        )
                        st.dataframe(st_out.markov_high_lag, use_container_width=True)
                    with mc2:
                        st.markdown(
                            "**Spatial Markov: Khi láng giềng ban đầu SÁNG THẤP (Low-Lag Context, %)**"
                            if is_vi else "**Spatial Markov: Low-Lag Neighbor Context (%)**",
                            help=L["h_markov_lo"],
                        )
                        st.dataframe(st_out.markov_low_lag, use_container_width=True)

                    _bad_rows = [nm for nm in ("markov_all", "markov_high_lag", "markov_low_lag")
                                 if np.any((getattr(st_out, nm).sum(axis=1) > 0) &
                                           (np.abs(getattr(st_out, nm).sum(axis=1) - 100.0) > 0.2))]
                    if _bad_rows:
                        st.warning(("Tổng hàng ma trận Markov lệch 100% quá 0,2%: " if is_vi else
                                    "Markov matrix row sums deviate from 100% by more than 0.2%: ") + ", ".join(_bad_rows))
                    st_full_csv = pd.concat([export_df.reset_index(drop=True), cdf.reset_index(drop=True), st_out.st_cell_df.reset_index(drop=True)], axis=1)
                    st.download_button(
                        f"⬇️ Tải CSV Sai phân Không – Thời gian ({year_t0}_{yr}_spacetime_cells.csv)"
                        if is_vi else f"⬇️ Download Space-Time First-Difference CSV ({year_t0}_{yr})",
                        st_full_csv.to_csv(index=False).encode("utf-8-sig"),
                        file_name=f"{region_id}_{year_t0}_{yr}_{size}m_spacetime_cells.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                        
    # ---------- Data Bridge ----------
    st.divider()
    st.markdown(f"#### {L['bridge_t']}", help=L["h_bridge_t"])
    st.caption(L["bridge_cap"])
    full = pd.concat([export_df.reset_index(drop=True), cdf.reset_index(drop=True)], axis=1)
    panel_row = pd.DataFrame([rm_full])
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
        rows[:] = [r for r in rows if tuple(r[c] for c in KEY_COLS) != key] + [dict(rm_full)]
        st.toast(L["added"], icon="✅")

    rows = st.session_state.get("panel_rows", [])
    with st.container(border=True):
        if rows:
            pdf = pd.DataFrame(rows).sort_values(["iso3", "region_id", "year", "cell_size_m"])
            st.markdown(f"**{L['panel']}** ({len(pdf)})", help=L["h_panel_tbl"])
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
            st.markdown(f"**{L['panel']}**", help=L["h_panel_tbl"])
            st.caption(L["panel_empty"])
    return out
