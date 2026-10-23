"""
NTL Data Extractor (Global Scale) - v3
Trích xuất Ánh sáng ban đêm (VIIRS) theo lưới ô vuông cho Kinh tế lượng không gian.

Pipeline 4 trạm:
  1. Gridding  : UTM động -> lưới mét -> clip theo ranh giới (nới biên 1 ô)
  2. Fetch     : Google Earth Engine -> GeoTIFF về máy chủ (requests + tempfile)
  3. Compute   : exactextract (C/C++) -> zonal mean theo tỷ lệ phủ + Moran's I
  4. Visualize : folium Aviation Dark Mode + đầu dò song ngữ + phân tích + xuất CSV/GeoJSON
"""
import html as html_lib
import inspect  # noqa: F401  (giữ để tương thích mở rộng)
import io
import json
import math
import os
import re
import tempfile
import unicodedata
import zipfile
from datetime import datetime, timezone

import altair as alt
import branca.colormap as cm
import ee
import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import shapely
import streamlit as st
from branca.element import MacroElement
from folium.plugins import Fullscreen, MiniMap, MousePosition
from jinja2 import Template
from streamlit_folium import st_folium

try:
    import pycountry
except Exception:  # pragma: no cover
    pycountry = None

# ==========================================
# 0. CONFIG
# ==========================================
st.set_page_config(page_title="NTL Data Extractor", page_icon="🌙", layout="wide")

BASE_DATA_DIR = "data/gadm41_VNM_gpkg/VNM_Curated_provinces"
GEE_DATASET = "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"
GEE_SCALE_M = 463.83          # độ phân giải gốc VIIRS (~15 arc-sec)
MAX_CELLS = 150_000           # trần số ô lưới để tránh treo máy chủ
RENDER_CAP = 30_000           # trần số ô vẽ lên bản đồ (trình duyệt)
MORAN_MIN_CELLS = 30
MORAN_PERMS = 199
YEARS = list(range(2014, 2026))

TILE_DARK = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
TILE_SAT = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
TILE_LIGHT = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
TILE_STREET = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"

# Ngưỡng phân loại kinh tế (nW/cm²/sr) — dùng chung cho đầu dò, bảng và CSV
THRESHOLDS = [40, 15, 5]  # >=40, >=15, >=5, >0, ==0

# Màu nhóm kinh tế (0 = sáng nhất ... 4 = không sáng) và vị thế nội bộ (0 top, 1 giữa, 2 đáy, 3 không sáng)
CLASS_COLORS = ["#ffffff", "#ffe14d", "#ff9f1a", "#b34700", "#3d3d46"]
CLASS_TEXT_COLORS = ["#111111", "#111111", "#111111", "#ffffff", "#ffffff"]
LOCAL_COLORS = ["#ffb703", "#6c7a89", "#2b6cb0", "#2a2a33"]


# ==========================================
# 1. TÊN HIỂN THỊ (BEGIN NAMES) — Việt Nam / Hà Nội / Hoàn Kiếm
# ==========================================
ISO_NAMES = {"vi": {"VNM": "Việt Nam"}, "en": {"VNM": "Vietnam"}}
COUNTY_SUFFIXES = {"district", "county", "town", "city", "municipality", "urban", "rural"}


def _nfc(s):
    """Chuẩn hóa Unicode NFC (tên file Linux/macOS hay ở dạng NFD -> hiển thị lỗi dấu)."""
    return unicodedata.normalize("NFC", str(s))


def _fold(s):
    """Bỏ dấu + viết thường để so sánh."""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").casefold()


def _natkey(s):
    """Sắp xếp tự nhiên, bỏ dấu: 'Quận 2' < 'Quận 10'."""
    parts = re.split(r"(\d+)", _fold(s))
    return [int(p) if i % 2 else p for i, p in enumerate(parts)]


def iso3_of(folder):
    m = re.match(r"^([A-Za-z]{3})(?=[_\W]|$)", folder)
    return m.group(1).upper() if m else None


def country_label(folder, lang="vi"):
    """'VNM_Curated_Provinces' -> 'Việt Nam' / 'Vietnam'."""
    iso = iso3_of(folder)
    if iso is None:
        return _nfc(re.sub(r"\s+", " ", folder.replace("_", " ")).strip())
    if iso in ISO_NAMES.get(lang, {}):
        return ISO_NAMES[lang][iso]
    if pycountry is not None:
        try:
            c = pycountry.countries.get(alpha_3=iso)
            if c:
                return getattr(c, "common_name", None) or c.name
        except Exception:  # noqa: BLE001
            pass
    return iso


def clean_state(folder):
    """'Hà_Nội' -> 'Hà Nội'."""
    return _nfc(re.sub(r"\s+", " ", folder.replace("_", " ")).strip())


def split_county(stem, state_name):
    """'VNM Hà Nội Hoàn Kiếm District' -> ('Hoàn Kiếm', 'District')."""
    tokens = _nfc(stem).replace("_", " ").split()
    if tokens and len(tokens[0]) == 3 and tokens[0].isalpha() and tokens[0].isupper():
        tokens = tokens[1:]
    st_tokens = state_name.split()
    n = len(st_tokens)
    if n and len(tokens) > n and [_fold(t) for t in tokens[:n]] == [_fold(t) for t in st_tokens]:
        tokens = tokens[n:]
    removed = []
    while len(tokens) > 1 and _fold(tokens[-1]) in COUNTY_SUFFIXES:
        removed.insert(0, tokens.pop())
    name = " ".join(tokens) if tokens else _nfc(stem).replace("_", " ")
    return name, " ".join(removed)


def subdirs(path):
    if not os.path.isdir(path):
        return []
    return sorted((d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))), key=_natkey)


@st.cache_data(show_spinner=False)
def list_counties(country, state):
    """Trả về {tên_file: tên_hiển_thị} (sắp xếp tự nhiên, không trùng nhãn)."""
    p = os.path.join(BASE_DATA_DIR, country, state)
    if not os.path.isdir(p):
        return {}
    state_name = clean_state(state)
    ext = ".geojson"
    base = []
    for f in os.listdir(p):
        if f.lower().endswith(ext):
            stem = f[: -len(ext)]
            name, removed = split_county(stem, state_name)
            base.append((f, stem, name, removed))
    counts = {}
    for _, _, name, _ in base:
        counts[_fold(name)] = counts.get(_fold(name), 0) + 1
    out = {}
    for f, stem, name, removed in base:
        label = name
        if counts[_fold(name)] > 1:  # trùng tên -> thêm loại đơn vị để phân biệt
            label = f"{name} ({removed})" if removed else f"{name} ({_nfc(stem).replace('_', ' ')})"
        while label in out.values():
            label += " ·"
        out[f] = label
    return dict(sorted(out.items(), key=lambda kv: _natkey(kv[1])))


def slugify(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", _fold(s)).strip("_") or "area"
# END NAMES


# ==========================================
# 2. SONG NGỮ
# ==========================================
TEXT = {
    "vi": {
        "title": "🌙 Công cụ trích xuất Ánh sáng ban đêm (NTL)",
        "subtitle": "Kiến trúc: tải raster từ Cloud về máy chủ + động cơ C/C++ (`exactextract`). "
                    "Thiết kế cho Kinh tế lượng không gian (chống lỗi MAUP, độ phân giải gốc ~463m).",
        "sb_spatial": "1. Tham số không gian",
        "country": "Quốc gia",
        "state": "Tỉnh / Thành phố",
        "county": "Quận / Huyện",
        "sb_analytic": "2. Tham số phân tích",
        "cell": "Độ phân giải lưới (mét)",
        "year": "Năm phân tích",
        "run": "🚀 Chạy phân tích",
        "no_data": "⚠️ Không tìm thấy dữ liệu trong `{d}`. Hãy tạo cấu trúc: quốc gia/tỉnh/huyện.geojson.",
        "no_state": "Quốc gia này chưa có thư mục tỉnh/thành.",
        "no_county": "Tỉnh/thành này chưa có file .geojson.",
        "gee_fail": "Khởi tạo Google Earth Engine thất bại",
        "idle": "👈 Chọn địa phương, độ phân giải, năm ở thanh bên rồi bấm **Chạy phân tích**.",
        "st1": "Trạm 1/3 · Đang dựng lưới {s} m và cắt theo ranh giới...",
        "st2": "Trạm 2/3 · Đang tải ảnh vệ tinh VIIRS từ Google Earth Engine (có thể mất vài chục giây)...",
        "st3": "Trạm 3/3 · Đang tính NTL trung bình theo tỷ lệ phủ điểm ảnh cho từng ô...",
        "st4": "Hoàn tất ✅",
        "ok1": "Đã tạo {n:,} ô lưới ({s}m), UTM EPSG:{e}.",
        "ok2": "Đã tải raster NTL năm {y}.",
        "ok3": "Hoàn tất trích xuất thống kê vùng.",
        "err_cells": "Lưới có ~{n:,} ô, vượt trần {m:,}. Hãy chọn độ phân giải thô hơn hoặc địa phương nhỏ hơn.",
        "err_empty": "Không có ảnh VIIRS nào cho khu vực/năm {y}.",
        "err_http": "Tải raster thất bại (HTTP {c}). Vùng có thể quá lớn (giới hạn ~50MB); thử địa phương nhỏ hơn.",
        "err_stage": "Lỗi tại {s}",
        "m_cells": "Số ô lưới",
        "m_mean": "NTL trung bình",
        "m_max": "NTL cao nhất",
        "m_sol": "Tổng ánh sáng (SOL)",
        "m_area": "Tổng diện tích",
        "m_lit": "Ô có ánh sáng",
        "tab_map": "🗺️ Bản đồ",
        "tab_data": "📋 Dữ liệu",
        "tab_guide": "📖 Hướng dẫn đọc",
        "caption": "Cường độ ánh sáng ban đêm ({y}) - nW/cm²/sr",
        # --- bản đồ ---
        "color_mode": "Chế độ màu",
        "color_names": {"ntl": "Cường độ NTL", "class": "Nhóm kinh tế", "local": "Vị thế nội bộ"},
        "scale": "Thang màu (chế độ NTL)",
        "scale_names": {"linear": "Tuyến tính", "sqrt": "Căn bậc hai", "log": "Logarit"},
        "opacity": "Độ đậm ô lưới",
        "hide0": "Ẩn ô không sáng",
        "hl": "Viền Top 10",
        "borders": "Viền ô lưới",
        "mask": "Làm tối ngoài ranh giới",
        "tile_dark": "Nền tối",
        "tile_sat": "Vệ tinh",
        "tile_light": "Nền sáng",
        "tile_street": "Đường phố",
        "layer_grid": "Lưới NTL",
        "layer_bound": "Ranh giới",
        "layer_top": "Top 10 điểm sáng",
        "layer_mask": "Vùng ngoài ranh giới",
        "render_cap": "Địa phương có {n:,} ô; bản đồ chỉ vẽ {c:,} ô sáng nhất để trình duyệt chạy mượt (CSV vẫn đầy đủ).",
        "legend_class": "Nhóm kinh tế (Global)",
        "legend_local": "Vị thế nội bộ (Local)",
        "p_mean": "TB",
        "p_max": "Cao nhất",
        "p_lit": "Ô sáng",
        # --- đầu dò ---
        "tt": {"cell": "Ô", "area": "📐 Diện tích đo lường", "ratio": "⚖️ So với TB địa phương",
               "rank": "🏆 Thứ hạng sáng", "pct": "📈 Phân vị", "share": "🔆 Tỷ trọng tổng ánh sáng",
               "z": "📊 Độ lệch chuẩn (z)", "sol": "💠 Tổng ánh sáng ô (SOL)", "xy": "📍 Tâm ô (lat, lon)",
               "econ": "Ước lượng kinh tế (Global)", "local": "Vị thế nội bộ (Local)"},
        "short": ["Thương mại", "Đô thị lõi", "Vành đai", "Ven đô", "Không sáng"],
        "dev": ["Thương mại/Dịch vụ (Mật độ siêu cao)", "Đô thị lõi/Khu dân cư đông đúc",
                "Vành đai đô thị/Ngoại ô phát triển", "Khu vực ven đô/Hoạt động kinh tế thấp",
                "Không gian mở/Khu vực thiếu sáng"],
        # thứ tự: 0 = Top 25%, 1 = Giữa, 2 = Bottom 25%, 3 = Không sáng
        "rank": ["Top 25% (Tâm điểm kinh tế của địa phương)", "Mức phát triển trung bình của địa phương",
                 "Bottom 25% (Vùng trũng của địa phương)", "Không có ánh sáng đáng kể"],
        # --- dữ liệu ---
        "sec_take": "💡 Nhận định nhanh",
        "take": [
            "🔆 **Điểm sáng nhất:** ô **#{gid}** (lat {lat:.4f}, lon {lon:.4f}) có NTL = **{mx:.2f}**, "
            "gấp **{ratio:.1f}×** mức trung bình (theo diện tích) của địa phương.",
            "🏙️ **Độ tập trung:** 10% ô sáng nhất chứa **{top10:.1f}%** tổng ánh sáng; Gini = **{gini:.2f}** — {gdesc}.",
            "🌑 **Không gian tối:** {lit:.0f}% số ô có ánh sáng; {dark:.1f}% diện tích không có tín hiệu NTL.",
            "🧭 **Tự tương quan không gian:** Moran's I = **{mi:.3f}** (p ≈ {mp:.3f}) — {mdesc}.",
            "🧩 **Chất lượng mẫu:** {border:,}/{n:,} ô là ô biên (bị cắt theo ranh giới) — nên dùng `area_km2` làm "
            "trọng số hoặc lọc bằng `is_border_cell`.",
        ],
        "gdesc": ["ánh sáng phân bố khá đồng đều", "mức tập trung vừa phải", "ánh sáng tập trung rất cao vào vài ô lõi"],
        "mdesc": ["ánh sáng tụ thành cụm có ý nghĩa thống kê → cần mô hình không gian (SAR/SEM/SDM) hoặc sai số chuẩn Conley/cụm",
                  "chưa thấy cụm không gian có ý nghĩa thống kê",
                  "có dấu hiệu phân bố xen kẽ (tự tương quan âm) có ý nghĩa thống kê"],
        "sec_overview": "Thông tin chung",
        "sec_stats": "Thống kê phân bố ánh sáng",
        "sec_spatial": "🧭 Tự tương quan không gian (Moran's I)",
        "mi_I": "Moran's I",
        "mi_E": "Kỳ vọng E[I]",
        "mi_p": "p-value (hoán vị)",
        "mi_k": "Láng giềng TB (queen)",
        "mi_note": "Trọng số kề nhau kiểu Queen (8 hướng) trên lưới đều, kiểm định giả thuyết bằng {k} hoán vị ngẫu nhiên. "
                   "I > 0: ô sáng nằm cạnh ô sáng (cụm); I ≈ 0: ngẫu nhiên; I < 0: xen kẽ.",
        "mi_na": f"Chưa đủ dữ liệu để tính Moran's I (cần ≥ {MORAN_MIN_CELLS} ô và NTL có biến thiên).",
        "sec_class": "Cơ cấu theo nhóm kinh tế (Global)",
        "sec_hist": "Phân bố số ô theo cường độ NTL",
        "sec_top": "Top 10 ô sáng nhất",
        "sec_full": "Xem bảng đầy đủ (tối đa 5.000 dòng sáng nhất)",
        "sec_meta": "Phương pháp & siêu dữ liệu",
        "sec_dict": "📚 Từ điển dữ liệu (các cột trong CSV)",
        "sec_dl": "Tải dữ liệu",
        "ov_cols": ["Chỉ tiêu", "Giá trị"],
        "ov_rows": ["Địa phương", "Mã quốc gia (ISO3)", "Năm / Độ phân giải lưới", "Số ô lưới (ô đủ / ô biên)",
                    "Tổng diện tích", "Tâm địa phương (lat, lon)", "Hệ tọa độ lưới", "Thời điểm xử lý"],
        "stat_cols": ["Chỉ số", "Giá trị"],
        "stat_rows": ["Trung bình (theo diện tích)", "Trung bình (đơn giản)", "Trung vị", "Độ lệch chuẩn",
                      "Hệ số biến thiên (CV)", "Độ lệch phân phối (skewness)",
                      "Nhỏ nhất", "P25", "P75", "P90", "P99", "Lớn nhất",
                      "Hệ số Gini (bất bình đẳng ánh sáng)", "Tỷ lệ ô có ánh sáng",
                      "Tỷ trọng SOL của 10% ô sáng nhất"],
        "cls_cols": ["Nhóm", "Ngưỡng NTL", "Số ô", "% ô", "% diện tích", "% tổng ánh sáng"],
        "dict_cols": ["Cột", "Ý nghĩa"],
        "hist_x": "Khoảng NTL (nW/cm²/sr)",
        "hist_y": "Số ô",
        "hist_bins": ["0 (không sáng)", "0-1", "1-2", "2-5", "5-10", "10-15", "15-25", "25-40", "40-80", "80+"],
        "meta_cols": ["Mục", "Mô tả"],
        "meta_rows": ["Nguồn ảnh", "Chỉ số (band)", "Cách tổng hợp", "Độ phân giải gốc", "Lưới phân tích",
                      "Hệ tọa độ lưới", "Điểm ảnh VIIRS mỗi ô", "Ranh giới hành chính", "Phương pháp zonal"],
        "meta_vals": [
            "NOAA VIIRS DNB hàng tháng, hiệu chỉnh ánh sáng tạp (`{ds}`)",
            "`avg_rad` (bức xạ trung bình, nW/cm²/sr)",
            "Trung vị các ảnh tháng của năm {y}; giá trị rỗng = 0; giá trị âm = 0",
            "~463 m (15 arc-giây)",
            "{s} × {s} m, căn theo bội số {s} m trong hệ UTM",
            "EPSG:{e} (UTM)",
            "~{px} điểm ảnh/ô",
            "GADM 4.1",
            "`exactextract`: trung bình có trọng số theo tỷ lệ phủ điểm ảnh",
        ],
        "quality_warn": "⚠️ Lưới {s} m xấp xỉ 1-2 điểm ảnh VIIRS (~{px}/ô): các ô liền kề không độc lập về mặt thông tin. "
                        "Với hồi quy, nên dùng lưới ≥ 1000 m hoặc kiểm soát tự tương quan không gian.",
        "download": "⬇️ Tải CSV (hồi quy không gian)",
        "prep_geo": "Chuẩn bị tệp GeoJSON (cho QGIS/GeoPandas)",
        "download_geo": "⬇️ Tải GeoJSON",
        "csv_note": "CSV gồm mã địa phương, tọa độ tâm ô (WGS84 & UTM), diện tích, NTL, SOL, hạng, phân vị, z-score, "
                    "tỷ trọng, nhóm kinh tế (1 = sáng nhất, 5 = không sáng) và cờ ô biên.",
        "guide_title": "### 📖 Hướng dẫn đọc dữ liệu (cho nhà phân tích / đầu tư / nhà nghiên cứu)",
        "g_tab_cols": ["Nhóm", "Ngưỡng NTL (nW/cm²/sr)", "Diễn giải"],
        "g_code_title": "Ví dụ dùng CSV trong hồi quy và kiểm tra tự tương quan không gian",
    },
    "en": {
        "title": "🌙 Nighttime Lights (NTL) Extraction Engine",
        "subtitle": "Architecture: Cloud-to-Local raster fetch + C/C++ engine (`exactextract`). "
                    "Built for Spatial Econometrics (MAUP-resistant, native ~463m resolution).",
        "sb_spatial": "1. Spatial Parameters",
        "country": "Country",
        "state": "Province / City",
        "county": "District",
        "sb_analytic": "2. Analytical Parameters",
        "cell": "Grid Resolution (meters)",
        "year": "Analysis Year",
        "run": "🚀 Execute Pipeline",
        "no_data": "⚠️ No data found in `{d}`. Create the structure: country/state/county.geojson.",
        "no_state": "This country has no province/city folders.",
        "no_county": "This province/city has no .geojson files.",
        "gee_fail": "Google Earth Engine initialization failed",
        "idle": "👈 Pick a locality, resolution and year in the sidebar, then press **Execute Pipeline**.",
        "st1": "Station 1/3 · Building {s} m grid and clipping to boundary...",
        "st2": "Station 2/3 · Downloading VIIRS imagery from Google Earth Engine (may take a while)...",
        "st3": "Station 3/3 · Computing coverage-weighted NTL for every cell...",
        "st4": "Done ✅",
        "ok1": "Generated {n:,} grid cells ({s}m), UTM EPSG:{e}.",
        "ok2": "NTL raster for {y} fetched.",
        "ok3": "Zonal statistics extraction complete.",
        "err_cells": "Grid has ~{n:,} cells, above the {m:,} cap. Use a coarser resolution or a smaller area.",
        "err_empty": "No VIIRS imagery for this area/year {y}.",
        "err_http": "Raster download failed (HTTP {c}). Area may be too large (~50MB limit); try a smaller district.",
        "err_stage": "Error at {s}",
        "m_cells": "Grid cells",
        "m_mean": "Mean NTL",
        "m_max": "Max NTL",
        "m_sol": "Sum of Lights (SOL)",
        "m_area": "Total area",
        "m_lit": "Lit cells",
        "tab_map": "🗺️ Map",
        "tab_data": "📋 Data",
        "tab_guide": "📖 Reading Guide",
        "caption": "Nighttime Lights Intensity ({y}) - nW/cm²/sr",
        "color_mode": "Color mode",
        "color_names": {"ntl": "NTL intensity", "class": "Economic class", "local": "Local standing"},
        "scale": "Color scale (NTL mode)",
        "scale_names": {"linear": "Linear", "sqrt": "Square root", "log": "Logarithmic"},
        "opacity": "Cell opacity",
        "hide0": "Hide unlit cells",
        "hl": "Outline Top 10",
        "borders": "Cell borders",
        "mask": "Dim outside boundary",
        "tile_dark": "Dark base",
        "tile_sat": "Satellite",
        "tile_light": "Light base",
        "tile_street": "Streets",
        "layer_grid": "NTL grid",
        "layer_bound": "Boundary",
        "layer_top": "Top 10 hotspots",
        "layer_mask": "Outside boundary",
        "render_cap": "This area has {n:,} cells; the map draws only the {c:,} brightest to keep the browser smooth (CSV stays complete).",
        "legend_class": "Economic class (Global)",
        "legend_local": "Local standing",
        "p_mean": "Mean",
        "p_max": "Max",
        "p_lit": "Lit",
        "tt": {"cell": "Cell", "area": "📐 Survey area", "ratio": "⚖️ Versus area average",
               "rank": "🏆 Brightness rank", "pct": "📈 Percentile", "share": "🔆 Share of total light",
               "z": "📊 Std. deviations (z)", "sol": "💠 Cell sum of lights (SOL)", "xy": "📍 Centroid (lat, lon)",
               "econ": "Economic proxy (Global)", "local": "Internal status (Local)"},
        "short": ["Commercial", "Urban core", "Fringe", "Peri-urban", "Unlit"],
        "dev": ["Commercial/Services (Ultra-high density)", "Urban Core/Dense Residential",
                "Urban Fringe/Developing Suburb", "Peri-urban/Low Economic Activity",
                "Open Space/Unlit Area"],
        "rank": ["Top 25% (Economic Hotspot of the area)", "Area-average development",
                 "Bottom 25% (Economic Coldspot)", "No significant light"],
        "sec_take": "💡 Quick takeaways",
        "take": [
            "🔆 **Brightest spot:** cell **#{gid}** (lat {lat:.4f}, lon {lon:.4f}) has NTL = **{mx:.2f}**, "
            "**{ratio:.1f}×** the (area-weighted) locality average.",
            "🏙️ **Concentration:** the brightest 10% of cells hold **{top10:.1f}%** of all light; Gini = **{gini:.2f}** — {gdesc}.",
            "🌑 **Dark space:** {lit:.0f}% of cells are lit; {dark:.1f}% of the area has no NTL signal.",
            "🧭 **Spatial autocorrelation:** Moran's I = **{mi:.3f}** (p ≈ {mp:.3f}) — {mdesc}.",
            "🧩 **Sample quality:** {border:,}/{n:,} cells are border cells (clipped by the boundary) — use `area_km2` "
            "as a weight or filter with `is_border_cell`.",
        ],
        "gdesc": ["fairly even light distribution", "moderate concentration", "light is extremely concentrated in a few core cells"],
        "mdesc": ["light is significantly clustered → use spatial models (SAR/SEM/SDM) or Conley/clustered standard errors",
                  "no statistically significant spatial clustering",
                  "significant alternating pattern (negative autocorrelation)"],
        "sec_overview": "Overview",
        "sec_stats": "Light distribution statistics",
        "sec_spatial": "🧭 Spatial autocorrelation (Moran's I)",
        "mi_I": "Moran's I",
        "mi_E": "Expected E[I]",
        "mi_p": "p-value (permutation)",
        "mi_k": "Avg. neighbours (queen)",
        "mi_note": "Queen contiguity (8 directions) on the regular grid; significance from {k} random permutations. "
                   "I > 0: bright cells sit next to bright cells (clusters); I ≈ 0: random; I < 0: alternating.",
        "mi_na": f"Not enough data for Moran's I (needs ≥ {MORAN_MIN_CELLS} cells and variation in NTL).",
        "sec_class": "Breakdown by economic class (Global)",
        "sec_hist": "Number of cells by NTL intensity",
        "sec_top": "Top 10 brightest cells",
        "sec_full": "Show full table (up to 5,000 brightest rows)",
        "sec_meta": "Method & metadata",
        "sec_dict": "📚 Data dictionary (CSV columns)",
        "sec_dl": "Downloads",
        "ov_cols": ["Item", "Value"],
        "ov_rows": ["Locality", "Country code (ISO3)", "Year / Grid resolution", "Grid cells (full / border)",
                    "Total area", "Locality centre (lat, lon)", "Grid CRS", "Processed at"],
        "stat_cols": ["Statistic", "Value"],
        "stat_rows": ["Mean (area-weighted)", "Mean (simple)", "Median", "Std. deviation",
                      "Coefficient of variation (CV)", "Skewness",
                      "Minimum", "P25", "P75", "P90", "P99", "Maximum",
                      "Gini coefficient (light inequality)", "Share of lit cells",
                      "SOL share of brightest 10% of cells"],
        "cls_cols": ["Class", "NTL threshold", "Cells", "% cells", "% area", "% of total light"],
        "dict_cols": ["Column", "Meaning"],
        "hist_x": "NTL range (nW/cm²/sr)",
        "hist_y": "Cells",
        "hist_bins": ["0 (unlit)", "0-1", "1-2", "2-5", "5-10", "10-15", "15-25", "25-40", "40-80", "80+"],
        "meta_cols": ["Item", "Description"],
        "meta_rows": ["Imagery source", "Band", "Aggregation", "Native resolution", "Analysis grid",
                      "Grid CRS", "VIIRS pixels per cell", "Administrative boundary", "Zonal method"],
        "meta_vals": [
            "NOAA VIIRS DNB monthly, stray-light corrected (`{ds}`)",
            "`avg_rad` (mean radiance, nW/cm²/sr)",
            "Median of the monthly composites of {y}; nodata = 0; negatives = 0",
            "~463 m (15 arc-seconds)",
            "{s} × {s} m, snapped to multiples of {s} m in UTM",
            "EPSG:{e} (UTM)",
            "~{px} pixels/cell",
            "GADM 4.1",
            "`exactextract`: mean weighted by fractional pixel coverage",
        ],
        "quality_warn": "⚠️ A {s} m grid is about 1-2 VIIRS pixels (~{px}/cell): neighbouring cells are not informationally independent. "
                        "For regressions prefer a grid ≥ 1000 m or control for spatial autocorrelation.",
        "download": "⬇️ Download CSV (spatial econometrics)",
        "prep_geo": "Prepare GeoJSON file (for QGIS/GeoPandas)",
        "download_geo": "⬇️ Download GeoJSON",
        "csv_note": "CSV has locality codes, cell centroids (WGS84 & UTM), area, NTL, SOL, rank, percentile, z-score, "
                    "share, economic class (1 = brightest, 5 = unlit) and a border-cell flag.",
        "guide_title": "### 📖 Reading guide (for analysts / investors / researchers)",
        "g_tab_cols": ["Class", "NTL threshold (nW/cm²/sr)", "Interpretation"],
        "g_code_title": "Example: using the CSV in a regression and testing spatial autocorrelation",
    },
}

DATA_DICT = [
    ("country", "Tên quốc gia (tiếng Anh)", "Country name (English)"),
    ("iso3", "Mã quốc gia ISO 3 ký tự", "3-letter ISO country code"),
    ("province", "Tỉnh / Thành phố", "Province / City"),
    ("district", "Quận / Huyện", "District"),
    ("grid_id", "ID ô lưới, duy nhất trong tệp và trùng với số hiển thị ở đầu dò bản đồ",
     "Grid cell ID, unique in the file and identical to the map tooltip"),
    ("year", "Năm phân tích (trung vị 12 tháng)", "Analysis year (median of monthly composites)"),
    ("cell_size_m", "Cạnh ô lưới (mét)", "Grid cell side (metres)"),
    ("centroid_lon / centroid_lat", "Tọa độ tâm ô, WGS84 (độ)", "Cell centroid, WGS84 (degrees)"),
    ("centroid_x_epsg{E} / centroid_y_epsg{E}", "Tọa độ tâm ô trong UTM (mét) — dùng tính khoảng cách/ma trận trọng số",
     "Cell centroid in UTM (metres) — use for distances / spatial weights"),
    ("area_km2", "Diện tích thực của ô sau khi cắt theo ranh giới (km²)", "True cell area after clipping (km²)"),
    ("is_border_cell", "1 = ô biên bị cắt nhỏ hơn ô đầy đủ; 0 = ô đầy đủ", "1 = clipped border cell; 0 = full cell"),
    ("ntl_mean", "NTL trung bình, trọng số theo tỷ lệ phủ điểm ảnh (nW/cm²/sr)",
     "Mean NTL weighted by fractional pixel coverage (nW/cm²/sr)"),
    ("ntl_sol", "Tổng ánh sáng của ô = ntl_mean × area_km2", "Sum of lights of the cell = ntl_mean × area_km2"),
    ("ntl_log", "ln(1 + ntl_mean) — biến thường dùng trong hồi quy", "ln(1 + ntl_mean) — common regression variable"),
    ("ntl_zscore", "Điểm chuẩn hóa z so với các ô cùng địa phương", "Z-score relative to cells in the same locality"),
    ("ntl_rank", "Thứ hạng sáng (1 = sáng nhất)", "Brightness rank (1 = brightest)"),
    ("ntl_pctile", "Phân vị 0-100", "Percentile 0-100"),
    ("ntl_vs_mean", "Tỷ lệ so với trung bình (theo diện tích) của địa phương", "Ratio to the locality's area-weighted mean"),
    ("sol_share_pct", "% tổng ánh sáng (SOL) của địa phương nằm trong ô", "% of the locality's total SOL located in the cell"),
    ("ntl_class", "Nhóm kinh tế toàn cầu 1-5 (1 = sáng nhất, 5 = không sáng)", "Global economic class 1-5 (1 = brightest, 5 = unlit)"),
    ("ntl_class_label", "Nhãn nhóm kinh tế (tiếng Anh)", "Economic class label (English)"),
    ("ntl_local_grp", "Vị thế nội bộ: 1 = Top 25%, 2 = giữa, 3 = Bottom 25%, 4 = không sáng",
     "Local standing: 1 = Top 25%, 2 = middle, 3 = Bottom 25%, 4 = unlit"),
]

GUIDE = {
    "vi": [
        ("1. NTL là gì và đo bằng gì?",
         "*\t**NTL (Nighttime Lights)** là ánh sáng phát ra ban đêm, vệ tinh **VIIRS/DNB** (NOAA) đo hằng tháng.\n"
         "*\t**Đơn vị:** nW/cm²/sr (nano-watt trên cm² trên steradian) — là *bức xạ*, không phải số bóng đèn.\n"
         "*\t**Dữ liệu dùng:** `avg_rad` của sản phẩm đã hiệu chỉnh ánh sáng tạp. Với năm **{y}**, công cụ lấy **trung vị** các ảnh tháng để giảm nhiễu mây, trăng, cháy rừng.\n"
         "*\t**Vì sao liên quan kinh tế?** Đô thị sáng hơn thường có mật độ dân cư, thương mại, công nghiệp và hạ tầng cao hơn, nên NTL là *biến đại diện (proxy)* cho hoạt động kinh tế, đặc biệt ở nơi thiếu số liệu GDP chi tiết.\n"
         "*\t**Mốc tham khảo:** < 1 gần như tối; 5-15 khu dân cư/ven đô; 15-40 đô thị đông đúc; > 40 trung tâm thương mại, khu công nghiệp sáng mạnh."),
        ("2. Cách đọc bản đồ",
         "*\t**Chế độ màu (3 loại):**\n"
         "  *\t*Cường độ NTL* — thang liên tục từ đen → nâu → cam → vàng → trắng. Càng sáng càng nhiều ánh sáng.\n"
         "  *\t*Nhóm kinh tế* — tô 5 màu rời rạc theo ngưỡng toàn cầu (trắng = thương mại/dịch vụ, vàng = đô thị lõi, cam = vành đai, nâu = ven đô, xám = không sáng). Phù hợp để so sánh **giữa các địa phương**.\n"
         "  *\t*Vị thế nội bộ* — Top 25% (vàng cam), giữa (xám), Bottom 25% (xanh), không sáng (đen). Phù hợp để thấy **điểm nóng/vùng trũng trong cùng địa phương**.\n"
         "*\t**Thang màu (chỉ cho chế độ NTL):** *Tuyến tính* giữ đúng tỷ lệ nhưng vùng ven đô dễ tối; *Căn bậc hai* và *Logarit* kéo sáng vùng thấp để thấy cấu trúc đô thị. Chú ý chú giải: mốc màu thay đổi theo thang.\n"
         "*\t**Độ đậm / Ẩn ô không sáng / Viền ô lưới:** chỉnh để nhìn rõ nền bản đồ bên dưới hoặc nhìn rõ từng ô vuông.\n"
         "*\t**Làm tối ngoài ranh giới:** phủ lớp tối lên vùng ngoài địa phương để mắt tập trung vào khu vực phân tích.\n"
         "*\t**Viền Top 10:** viền xanh lơ quanh 10 ô sáng nhất (điểm nóng).\n"
         "*\t**Bảng thông tin góc trái trên:** tên địa phương, năm, độ phân giải, NTL trung bình/cao nhất, tỷ lệ ô sáng.\n"
         "*\t**Nút lớp (góc phải):** đổi nền *Tối / Vệ tinh / Sáng / Đường phố*, bật/tắt lưới, ranh giới, lớp làm tối. Có nút toàn màn hình, tọa độ chuột và bản đồ nhỏ."),
        ("3. Cách đọc Đầu dò (tooltip)",
         "Rê chuột vào một ô, đầu dò hiện theo thứ tự từ trên xuống:\n"
         "*\t**Tiêu đề:** `Ô #ID` và **huy hiệu nhóm kinh tế** (màu tương ứng bảng ngưỡng). Dòng nhỏ bên dưới là địa phương và năm.\n"
         "*\t**Số lớn + thanh màu:** cường độ NTL của ô; độ dài thanh = tỷ lệ so với ô sáng nhất của địa phương.\n"
         "*\t**Diện tích đo lường:** ô sát ranh giới bị cắt nên nhỏ hơn ô đầy đủ — khi hồi quy nên dùng diện tích làm trọng số.\n"
         "*\t**So với TB địa phương:** 2.0× nghĩa là sáng gấp đôi trung bình (theo diện tích) của địa phương.\n"
         "*\t**Thứ hạng / Phân vị:** #1 là ô sáng nhất; P90 nghĩa là sáng hơn 90% số ô.\n"
         "*\t**Tỷ trọng tổng ánh sáng:** phần trăm tổng SOL của địa phương nằm trong ô này.\n"
         "*\t**Độ lệch chuẩn (z):** +2 σ nghĩa là cao hơn trung bình ô 2 độ lệch chuẩn (dễ so sánh giữa các vùng).\n"
         "*\t**Tổng ánh sáng ô (SOL):** NTL × diện tích, dùng khi cộng gộp ô để tính cho cả vùng.\n"
         "*\t**Tâm ô (lat, lon):** tọa độ để tra cứu trên Google Maps hoặc ghép dữ liệu khác.\n"
         "*\t**Hai dòng cuối:** *Ước lượng kinh tế (Global)* — nhóm theo ngưỡng bức xạ chung toàn cầu; *Vị thế nội bộ (Local)* — Top 25% / trung bình / Bottom 25% so với các ô còn lại **trong cùng địa phương**."),
        ("4. Bảng ngưỡng phân loại (Global)", "__TABLE__"),
        ("5. Cách đọc tab Dữ liệu",
         "*\t**Nhận định nhanh:** tóm tắt tự động ô sáng nhất, độ tập trung ánh sáng, vùng tối và tự tương quan không gian.\n"
         "*\t**Hệ số Gini:** 0 = ánh sáng phân bố đều; gần 1 = tập trung vào vài ô. Đô thị đơn cực thường có Gini cao.\n"
         "*\t**Tỷ trọng SOL của 10% ô sáng nhất:** càng cao càng tập trung vào lõi đô thị.\n"
         "*\t**CV và skewness:** CV lớn = chênh lệch mạnh giữa các ô; skewness dương lớn = đuôi phải dài (vài ô cực sáng) → cân nhắc dùng `ntl_log`.\n"
         "*\t**Moran's I:** đo ánh sáng có **tụ thành cụm** hay không. I dương và p < 0,05 → có phụ thuộc không gian; hồi quy OLS thường sẽ có sai số tương quan → cần mô hình không gian hoặc sai số chuẩn Conley.\n"
         "*\t**Cơ cấu nhóm / Histogram / Top 10:** cho biết bao nhiêu % ô, diện tích và ánh sáng thuộc từng nhóm kinh tế.\n"
         "*\t**Từ điển dữ liệu:** giải thích từng cột trong CSV tải về."),
        ("6. MAUP và vì sao dùng lưới",
         "*\t**MAUP** (Modifiable Areal Unit Problem): kết quả thống kê đổi khi đổi cách vẽ ranh giới. Phường/xã to nhỏ rất khác nhau nên dễ gây thiên lệch.\n"
         "*\t**Lưới đều {s}×{s} m** cho đơn vị không gian thống nhất; lưới căn theo bội số {s} m nên **ghép được giữa các địa phương**.\n"
         "*\t**Đánh đổi:** lưới càng mịn thì càng nhiều ô nhưng thông tin gốc không tăng thêm (VIIRS ~463 m). Lưới ≥ 1000 m thường ổn hơn cho hồi quy; thử nhiều độ phân giải để kiểm tra độ vững (robustness)."),
        ("7. Dùng CSV trong nghiên cứu", "__CODE__"),
        ("8. Hạn chế cần biết",
         "*\tNTL là **proxy**, không phải GDP: khu công nghiệp nặng, đèn chiếu sáng công cộng dày, sân bay, cảng có thể sáng hơn mức hoạt động kinh tế thực.\n"
         "*\tNông thôn/khu thương mại ít đèn (hoặc dùng điện ít) có thể bị **đánh giá thấp**.\n"
         "*\t**Hiệu ứng lan sáng (blooming):** ánh sáng tràn sang mặt nước/ô lân cận.\n"
         "*\t**Giá trị âm** do nhiễu cảm biến đã đưa về 0. Ngưỡng phân loại là **tham khảo**, không phải chuẩn chính thức.\n"
         "*\tÔ biên nhỏ hơn ô đầy đủ → dùng `area_km2` để lọc hoặc đặt trọng số, hoặc lọc `is_border_cell == 0`.\n"
         "*\tKhi so sánh nhiều năm, nhớ rằng ảnh VIIRS đổi hiệu chuẩn/phiên bản theo thời gian; nên dùng sai phân hoặc hiệu ứng cố định theo năm.")
    ],
    "en": [
        ("1. What is NTL and how is it measured?",
         "*\t**NTL (Nighttime Lights)** is light emitted at night, measured monthly by the NOAA **VIIRS/DNB** satellite sensor.\n"
         "*\t**Unit:** nW/cm²/sr (nanowatts per cm² per steradian) — a *radiance*, not a count of lamps.\n"
         "*\t**Data used:** `avg_rad` from the stray-light-corrected product. For **{y}** the tool takes the **median** of monthly images to damp clouds, moonlight and fires.\n"
         "*\t**Why economics?** Brighter places usually have more people, commerce, industry and infrastructure, so NTL is a *proxy* for economic activity, especially where granular GDP data are missing.\n"
         "*\t**Rules of thumb:** < 1 almost dark; 5-15 residential/peri-urban; 15-40 dense urban; > 40 commercial hubs and brightly lit industry."),
        ("2. Reading the map",
         "*\t**Color modes (3):**\n"
         "  *\t*NTL intensity* — continuous scale black → brown → orange → yellow → white. Brighter = more light.\n"
         "  *\t*Economic class* — 5 discrete colors from global thresholds (white = commercial/services, yellow = urban core, orange = fringe, brown = peri-urban, grey = unlit). Best for comparing **across localities**.\n"
         "  *\t*Local standing* — Top 25% (amber), middle (grey), Bottom 25% (blue), unlit (black). Best for spotting **hotspots/coldspots within one locality**.\n"
         "*\t**Color scale (NTL mode only):** *Linear* keeps true proportions but peri-urban areas look dark; *Square root* and *Logarithmic* lift low values to reveal urban structure. Check the legend: color stops move with the scale.\n"
         "*\t**Opacity / Hide unlit cells / Cell borders:** adjust to see the base map or to see each square.\n"
         "*\t**Dim outside boundary:** darkens everything outside the locality so the eye stays on the study area.\n"
         "*\t**Outline Top 10:** cyan outlines around the 10 brightest cells (hotspots).\n"
         "*\t**Top-left info panel:** locality, year, resolution, mean/max NTL and share of lit cells.\n"
         "*\t**Layer control (top right):** switch *Dark / Satellite / Light / Streets* base maps, toggle grid, boundary and the dim layer. Fullscreen, mouse coordinates and a mini-map are included."),
        ("3. Reading the tooltip",
         "Hover over a cell; the tooltip shows, top to bottom:\n"
         "*\t**Header:** `Cell #ID` and an **economic-class badge** (color matches the threshold table). The small line below is locality and year.\n"
         "*\t**Big number + color bar:** the cell's NTL; bar length = ratio to the locality's brightest cell.\n"
         "*\t**Survey area:** cells on the border are clipped and smaller than full cells — use area as a weight in regressions.\n"
         "*\t**Versus area average:** 2.0× means twice the (area-weighted) average of the locality.\n"
         "*\t**Rank / Percentile:** #1 is the brightest cell; P90 means brighter than 90% of cells.\n"
         "*\t**Share of total light:** percent of the locality's total SOL located in this cell.\n"
         "*\t**Std. deviations (z):** +2 σ means two standard deviations above the cell mean (comparable across areas).\n"
         "*\t**Cell SOL:** NTL × area, used when summing cells up to larger regions.\n"
         "*\t**Centroid (lat, lon):** to look the place up or join other data.\n"
         "*\t**Last two lines:** *Economic proxy (Global)* — class from global radiance thresholds; *Internal status (Local)* — Top 25% / average / Bottom 25% relative to other cells **in the same locality**."),
        ("4. Classification thresholds (Global)", "__TABLE__"),
        ("5. Reading the Data tab",
         "*\t**Quick takeaways:** automatic summary of the brightest cell, light concentration, dark space and spatial autocorrelation.\n"
         "*\t**Gini coefficient:** 0 = evenly distributed light; near 1 = concentrated in a few cells. Monocentric cities usually have a high Gini.\n"
         "*\t**SOL share of the brightest 10% of cells:** the higher, the more concentrated in the urban core.\n"
         "*\t**CV and skewness:** large CV = strong differences between cells; large positive skewness = long right tail (a few extremely bright cells) → consider `ntl_log`.\n"
         "*\t**Moran's I:** tests whether light is **spatially clustered**. Positive I with p < 0.05 → spatial dependence; plain OLS will have correlated errors → use spatial models or Conley standard errors.\n"
         "*\t**Class breakdown / Histogram / Top 10:** show what % of cells, area and light fall in each economic class.\n"
         "*\t**Data dictionary:** explains every column of the downloadable CSV."),
        ("6. MAUP and why a grid",
         "*\t**MAUP** (Modifiable Areal Unit Problem): statistical results change when boundaries are redrawn. Wards/communes vary wildly in size, creating bias.\n"
         "*\tA **{s}×{s} m grid** gives uniform spatial units; it is snapped to multiples of {s} m so it **can be merged across localities**.\n"
         "*\t**Trade-off:** a finer grid has more cells but no extra information (VIIRS ~463 m). Grids ≥ 1000 m are usually safer for regressions; test several resolutions for robustness."),
        ("7. Using the CSV in research", "__CODE__"),
        ("8. Limitations to keep in mind",
         "*\tNTL is a **proxy**, not GDP: heavy industry, dense public lighting, airports and ports can be brighter than their economic activity.\n"
         "*\tRural or low-light commercial areas can be **under-estimated**.\n"
         "*\t**Blooming:** light spills onto water or neighbouring cells.\n"
         "*\t**Negative values** from sensor noise are set to 0. Class thresholds are **indicative**, not an official standard.\n"
         "*\tBorder cells are smaller than full cells → filter or weight with `area_km2`, or keep `is_border_cell == 0`.\n"
         "*\tWhen comparing years, remember VIIRS calibration/versions change over time; use first differences or year fixed effects.")
    ]
}

CLASS_NOTES = {
    "vi": ["Trung tâm thương mại/dịch vụ, khu công nghiệp sáng mạnh", "Lõi đô thị, dân cư đông đúc",
           "Vành đai đô thị, ngoại ô đang phát triển", "Ven đô, hoạt động kinh tế thấp", "Đất trống, nông-lâm nghiệp, mặt nước"],
    "en": ["Commercial/services hubs, brightly lit industry", "Urban core, dense residential",
           "Urban fringe, developing suburbs", "Peri-urban, low economic activity", "Open land, farm/forest, water"],
}
THRESH_TEXT = [">= 40", "15 - 40", "5 - 15", "> 0 - 5", "0"]

CODE_SNIPPET = '''# Python (pandas + statsmodels + libpysal/esda)
import pandas as pd
import statsmodels.formula.api as smf

df = pd.read_csv("your_file.csv")
# Bỏ ô biên nhỏ  |  drop small border cells
df = df[df["is_border_cell"] == 0]          # hoặc / or: area_km2 >= 0.5 * (cell_size_m/1000)**2

merged = df.merge(your_data, on="grid_id")   # hoặc ghép theo tọa độ tâm ô | or join on centroid
res = smf.wls("ln_outcome ~ ntl_log", data=merged,
              weights=merged["area_km2"]).fit(cov_type="HC1")
print(res.summary())

# Tự tương quan không gian của phần dư | spatial autocorrelation of residuals
import libpysal
from esda.moran import Moran
xy = merged[["centroid_x_epsg32648", "centroid_y_epsg32648"]].to_numpy()  # đổi EPSG | change EPSG
w = libpysal.weights.KNN.from_array(xy, k=8)
w.transform = "r"
print(Moran(res.resid.to_numpy(), w).I)

* Stata:  gen ln_ntl = ln(ntl_mean + 1)
*         reg ln_outcome ln_ntl [aweight = area_km2], vce(robust)
'''

LANG = "vi"  # được cập nhật ngay sau khi người dùng chọn ngôn ngữ

# Ngôn ngữ phải được chọn trước mọi widget khác
with st.sidebar:
    lang_choice = st.radio("🌐 Language / Ngôn ngữ", ["Tiếng Việt", "English"], key="lang_choice",
                       help="Đổi ngôn ngữ giao diện / Switch interface language")
LANG = "vi" if lang_choice == "Tiếng Việt" else "en"
L = TEXT[LANG]


def fill(text, **kw):
    for k, v in kw.items():
        text = text.replace("{" + k + "}", str(v))
    return text


def sx(fn, *args, **kwargs):
    """Tương thích Streamlit mới (width='stretch') và cũ (use_container_width=True)."""
    try:
        return fn(*args, width="stretch", **kwargs)
    except Exception:  # noqa: BLE001
        return fn(*args, use_container_width=True, **kwargs)

HELP = {
    "vi": {
        "country": "Quốc gia chứa dữ liệu ranh giới (thư mục trong data/gadm41_VNM_gpkg).",
        "state": "Tỉnh/Thành phố. Danh sách đổi theo quốc gia đã chọn.",
        "county": "Quận/Huyện cần phân tích. Mỗi file .geojson là một địa phương.",
        "cell": "Cạnh ô lưới vuông (m). Lưới mịn → nhiều ô hơn nhưng VIIRS gốc chỉ ~463 m, nên ô < 1000 m không độc lập thông tin.",
        "year": "Năm lấy trung vị 12 ảnh tháng VIIRS để giảm nhiễu mây, trăng, cháy.",
        "run": "Chạy 3 trạm: tạo lưới → tải ảnh vệ tinh → tính thống kê vùng. Kết quả được giữ lại khi bạn đổi tab.",
        "lang": "Đổi ngôn ngữ giao diện, không ảnh hưởng dữ liệu.",
        "color_mode": "NTL: thang liên tục. Nhóm kinh tế: ngưỡng toàn cầu. Vị thế nội bộ: so với các ô cùng địa phương.",
        "scale": "Tuyến tính giữ tỷ lệ thật; căn bậc hai/logarit kéo sáng vùng ánh sáng thấp. Chỉ dùng ở chế độ NTL.",
        "opacity": "Độ đậm màu của ô lưới trên nền bản đồ.",
        "hide0": "Ẩn ô NTL = 0 để thấy rõ nền bản đồ.",
        "hl": "Viền nét đứt quanh 10 ô sáng nhất (điểm nóng).",
        "borders": "Hiện đường viền từng ô vuông.",
        "mask": "Phủ tối vùng ngoài ranh giới để tập trung vào địa phương.",
    },
    "en": {
        "country": "Country holding the boundary data (folder in data/gadm41_VNM_gpkg).",
        "state": "Province/City. The list follows the selected country.",
        "county": "District to analyse. Each .geojson file is one locality.",
        "cell": "Square cell side (m). Finer grid = more cells, but native VIIRS is ~463 m, so cells < 1000 m are not informationally independent.",
        "year": "Year whose 12 monthly VIIRS composites are median-aggregated to damp clouds, moonlight and fires.",
        "run": "Runs 3 stations: grid → satellite download → zonal statistics. Results persist when you switch tabs.",
        "lang": "Switches the interface language only; data is unaffected.",
        "color_mode": "NTL: continuous scale. Economic class: global thresholds. Local standing: relative to cells in the same locality.",
        "scale": "Linear keeps true proportions; sqrt/log lift low-light areas. Only used in NTL mode.",
        "opacity": "Fill opacity of grid cells over the base map.",
        "hide0": "Hide NTL = 0 cells to see the base map.",
        "hl": "Dashed outline around the 10 brightest cells (hotspots).",
        "borders": "Show each square's outline.",
        "mask": "Darken everything outside the boundary to focus on the locality.",
    },
}
H = HELP[LANG]

APP_CSS = """
<style>
.block-container{padding-top:1.6rem}
div[data-testid="stMetric"]{background:rgba(127,127,140,.07);border:1px solid rgba(127,127,140,.22);
  border-radius:12px;padding:10px 14px}
div[data-testid="stMetricValue"]{font-weight:700}
section[data-testid="stSidebar"] hr{margin:.6rem 0}
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)

# ==========================================
# 3. GOOGLE EARTH ENGINE INIT
# ==========================================
@st.cache_resource(show_spinner=False)
def init_gee():
    """Trả về (ok, message). Chạy 1 lần cho mỗi phiên máy chủ."""
    try:
        if "ee_credentials" in st.secrets:
            sec = st.secrets["ee_credentials"]
            private_key = str(sec["private_key"])
            if "\\n" in private_key:
                private_key = private_key.replace("\\n", "\n")
            credentials = ee.ServiceAccountCredentials(sec["client_email"], key_data=private_key)
            ee.Initialize(credentials, project=sec["project_id"])
        else:
            ee.Initialize()
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, str(e)


gee_ok, gee_msg = init_gee()
if not gee_ok:
    st.error(f"{L['gee_fail']}: {gee_msg}")


# ==========================================
# 4. TIỆN ÍCH TÍNH TOÁN
# ==========================================
def get_dynamic_utm_crs(lon: float, lat: float) -> int:
    zone = min(60, max(1, math.floor((lon + 180) / 6) + 1))
    return (32600 if lat >= 0 else 32700) + zone


def union_geoms(gdf):
    geoms = gdf.geometry
    return geoms.union_all() if hasattr(geoms, "union_all") else geoms.unary_union


def build_grid(boundary_utm: gpd.GeoDataFrame, size: int):
    """Lưới căn theo bội số của `size` (nhất quán giữa các địa phương), nới biên 1 ô."""
    minx, miny, maxx, maxy = boundary_utm.total_bounds
    x0, y0 = math.floor(minx / size) * size - size, math.floor(miny / size) * size - size
    xs = np.arange(x0, maxx + 2 * size, size)
    ys = np.arange(y0, maxy + 2 * size, size)
    n_est = len(xs) * len(ys)
    if n_est > MAX_CELLS * 4:
        raise ValueError(L["err_cells"].format(n=n_est, m=MAX_CELLS * 4))
    xx, yy = np.meshgrid(xs, ys)
    xx, yy = xx.ravel(), yy.ravel()
    cells = shapely.box(xx, yy, xx + size, yy + size)
    raw = gpd.GeoDataFrame(geometry=cells, crs=boundary_utm.crs)
    clipped = gpd.clip(raw, boundary_utm, keep_geom_type=True).reset_index(drop=True)
    clipped = clipped[~clipped.geometry.is_empty & clipped.geometry.notna()].reset_index(drop=True)
    clipped["area_km2"] = clipped.geometry.area / 1e6
    clipped = clipped[clipped["area_km2"] > 0].reset_index(drop=True)
    clipped.insert(0, "grid_id", np.arange(len(clipped), dtype=np.int64))
    if len(clipped) > MAX_CELLS:
        raise ValueError(L["err_cells"].format(n=len(clipped), m=MAX_CELLS))
    return clipped


@st.cache_data(show_spinner=False, ttl=3600, max_entries=8)
def fetch_ntl_raster(bbox: tuple, year: int) -> bytes:
    """Tải GeoTIFF NTL trung vị năm `year` trong bbox (WGS84). Cache theo (bbox, năm)."""
    minx, miny, maxx, maxy = bbox
    roi = ee.Geometry.Rectangle([minx, miny, maxx, maxy])
    col = (
        ee.ImageCollection(GEE_DATASET)
        .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
        .filterBounds(roi)
        .select("avg_rad")
    )
    if col.size().getInfo() == 0:
        raise LookupError("EMPTY")
    img = col.median().unmask(0).clip(roi)
    url = img.getDownloadUrl(
        {"scale": GEE_SCALE_M, "crs": "EPSG:4326", "region": roi, "format": "GEO_TIFF"}
    )
    resp = requests.get(url, timeout=180)
    if resp.status_code != 200:
        raise ConnectionError(f"HTTP:{resp.status_code}")
    content = resp.content
    if content[:2] == b"PK":  # đôi khi GEE trả về zip
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            tif_names = [n for n in z.namelist() if n.lower().endswith(".tif")]
            if not tif_names:
                raise ValueError("ZIP without .tif")
            content = z.read(tif_names[0])
    return content


def class_codes(values: np.ndarray) -> np.ndarray:
    """0 = sáng nhất ... 4 = không sáng."""
    t1, t2, t3 = THRESHOLDS
    return np.select([values >= t1, values >= t2, values >= t3, values > 0], [0, 1, 2, 3], default=4)


def gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    n, total = len(x), x.sum()
    if n == 0 or total <= 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * x)) / (n * total) - (n + 1) / n)


def morans_i(grid: gpd.GeoDataFrame, values: np.ndarray, size: int, perms: int = MORAN_PERMS):
    """Moran's I (queen, nhị phân) trên lưới đều; p-value bằng hoán vị. Trả về dict hoặc None."""
    n = len(values)
    if n < MORAN_MIN_CELLS:
        return None
    x = np.asarray(values, dtype=float)
    z = x - x.mean()
    denom = float(z @ z)
    if denom <= 1e-12:
        return None
    cent = grid.geometry.centroid  # tâm của ô bị cắt vẫn nằm trong ô gốc (lồi)
    ix = np.floor(cent.x.to_numpy() / size).astype("int64")
    iy = np.floor(cent.y.to_numpy() / size).astype("int64")
    ix -= ix.min() - 1
    iy -= iy.min() - 1
    height = int(iy.max()) + 3
    key = ix * height + iy
    order = np.argsort(key)
    sk = key[order]
    src, dst = [], []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nk = key + dx * height + dy
            pos = np.minimum(np.searchsorted(sk, nk), len(sk) - 1)
            ok = sk[pos] == nk
            src.append(np.flatnonzero(ok))
            dst.append(order[pos[ok]])
    src, dst = np.concatenate(src), np.concatenate(dst)
    w_sum = len(src)
    if w_sum == 0:
        return None
    obs = (n / w_sum) * float(np.sum(z[src] * z[dst])) / denom
    rng = np.random.default_rng(42)
    sims = np.empty(perms)
    for b in range(perms):
        zp = rng.permutation(z)
        sims[b] = (n / w_sum) * float(np.sum(zp[src] * zp[dst])) / denom
    expected = -1.0 / (n - 1)
    p = (1 + int(np.sum(np.abs(sims - expected) >= abs(obs - expected)))) / (perms + 1)
    return {"I": float(obs), "E": float(expected), "p": float(p), "k": w_sum / n, "perms": perms}


def make_colormap(mode: str, vmax: float, caption: str):
    colors = ["#000000", "#4a1a00", "#b34700", "#ffaa00", "#ffee55", "#ffffff"]
    t = np.linspace(0, 1, len(colors))
    if mode == "linear":
        idx = vmax * t
    elif mode == "sqrt":
        idx = vmax * t ** 2
    else:
        idx = np.expm1(t * np.log1p(vmax))
    idx = np.maximum.accumulate(idx + np.arange(len(idx)) * 1e-9)
    idx[0], idx[-1] = 0.0, vmax
    cmap = cm.LinearColormap(colors=colors, index=[float(v) for v in idx], vmin=0.0, vmax=vmax)
    cmap.caption = caption
    return cmap


# ---- Đầu dò giàu thông tin: dựng bằng JS phía trình duyệt (nhẹ, không phình GeoJSON) ----
class RichTooltip(MacroElement):
    _template = Template(
        """
        {% macro script(this, kwargs) %}
        (function () {
            var layer = {{ this.layer.get_name() }};
            var T = {{ this.cfg }};
            var esc = function (s) {
                return String(s).replace(/[&<>"]/g, function (c) {
                    return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c];
                });
            };
            var row = function (k, v) {
                return '<div class="nt-r"><span>' + k + '</span><b>' + v + '</b></div>';
            };
            layer.bindTooltip(function (lyr) {
                var p = lyr.feature.properties;
                var col = T.cc[p.c], lcol = T.lc[p.l];
                var pct = Math.max(0, Math.min(100, p.v / T.vmax * 100));
                var z = (p.z >= 0 ? '+' : '') + p.z.toFixed(2) + ' \u03c3';
                return '<div class="nt">'
                    + '<div class="nt-h"><span>' + T.t.cell + ' #' + p.g + '</span>'
                    + '<span class="nt-badge" style="background:' + col + ';color:' + T.tc[p.c] + '">' + esc(T.short[p.c]) + '</span></div>'
                    + '<div class="nt-sub">' + esc(T.place) + ' \u00b7 ' + T.year + '</div>'
                    + '<div class="nt-v"><b>' + p.v.toFixed(2) + '</b><small>' + T.unit + '</small></div>'
                    + '<div class="nt-bar"><i style="width:' + pct.toFixed(1) + '%;background:' + col + '"></i></div>'
                    + row(T.t.area, p.a.toFixed(3) + ' km\u00b2')
                    + row(T.t.ratio, p.r.toFixed(2) + '\u00d7')
                    + row(T.t.rank, '#' + p.k + ' / ' + T.n)
                    + row(T.t.pct, 'P' + Math.round(p.p))
                    + row(T.t.share, p.s.toFixed(3) + '%')
                    + row(T.t.z, z)
                    + row(T.t.sol, p.o.toFixed(3))
                    + row(T.t.xy, p.y.toFixed(4) + ', ' + p.x.toFixed(4))
                    + '<div class="nt-sec">' + T.t.econ + '</div>'
                    + '<div class="nt-f"><i style="background:' + col + '"></i>' + esc(T.dev[p.c]) + '</div>'
                    + '<div class="nt-sec">' + T.t.local + '</div>'
                    + '<div class="nt-f"><i style="background:' + lcol + '"></i>' + esc(T.rank[p.l]) + '</div>'
                    + '</div>';
            }, {sticky: true, direction: 'auto', opacity: 1, className: 'nt-tip'});
        })();
        {% endmacro %}
        """
    )

    def __init__(self, layer, cfg):
        super().__init__()
        self._name = "RichTooltip"
        self.layer = layer
        self.cfg = json.dumps(cfg, ensure_ascii=False)


MAP_CSS = """
<style>
.leaflet-tooltip.nt-tip{background:rgba(10,10,14,.96);color:#fff;border:1px solid #5a5a66;border-radius:10px;
  padding:0;box-shadow:0 6px 22px rgba(0,0,0,.7);font-family:Inter,Arial,sans-serif;white-space:normal}
.leaflet-tooltip.nt-tip:before{display:none}
.nt{min-width:250px;padding:11px 13px 10px}
.nt-h{display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:12.5px;font-weight:700}
.nt-badge{font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:999px;letter-spacing:.2px}
.nt-sub{font-size:11px;color:#9aa0aa;margin:3px 0 6px}
.nt-v{display:flex;align-items:baseline;gap:6px}
.nt-v b{font-size:27px;line-height:1.1;color:#ffd166}
.nt-v small{font-size:10.5px;color:#9aa0aa}
.nt-bar{height:5px;border-radius:3px;background:#2a2a33;margin:5px 0 8px;overflow:hidden}
.nt-bar i{display:block;height:100%;border-radius:3px}
.nt-r{display:flex;justify-content:space-between;gap:16px;font-size:12px;padding:2px 0;border-bottom:1px solid rgba(255,255,255,.07)}
.nt-r span{color:#aab0bb}
.nt-r b{font-weight:600;color:#fff;text-align:right}
.nt-sec{font-size:9.5px;letter-spacing:.8px;text-transform:uppercase;color:#7d8490;margin-top:9px}
.nt-f{display:flex;align-items:center;gap:7px;font-size:12px;margin-top:3px;color:#ececf2}
.nt-f i{width:9px;height:9px;border-radius:50%;flex:none;border:1px solid rgba(255,255,255,.35)}
.nt-panel{position:absolute;top:10px;left:56px;z-index:9998;pointer-events:none;background:rgba(10,10,14,.84);
  color:#fff;border:1px solid rgba(255,255,255,.18);border-radius:10px;padding:8px 13px;
  font:12px Inter,Arial,sans-serif;backdrop-filter:blur(4px);max-width:60%}
.nt-panel .t{font-size:13.5px;font-weight:700;margin-bottom:2px}
.nt-panel .s{color:#aab0bb}
.nt-panel b{color:#ffd166}
.nt-legend{position:absolute;bottom:34px;left:10px;z-index:9998;pointer-events:none;background:rgba(10,10,14,.84);
  color:#fff;border:1px solid rgba(255,255,255,.18);border-radius:10px;padding:8px 12px;font:12px Inter,Arial,sans-serif}
.nt-legend .t{font-weight:700;margin-bottom:5px}
.nt-legend div.i{margin-top:3px;white-space:nowrap}
.nt-legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:7px;vertical-align:-2px;
  border:1px solid rgba(255,255,255,.35)}
</style>
"""


def legend_html(title, items):
    rows = "".join(
        f'<div class="i"><i style="background:{c}"></i>{html_lib.escape(t)}</div>' for c, t in items
    )
    return f'<div class="nt-legend"><div class="t">{html_lib.escape(title)}</div>{rows}</div>'


# ==========================================
# 5. SIDEBAR (CASCADING, TÊN SẠCH: Việt Nam / Hà Nội / Hoàn Kiếm)
# ==========================================
st.title(L["title"])
st.markdown(L["subtitle"])

with st.sidebar:
    st.header(L["sb_spatial"])
    countries = subdirs(BASE_DATA_DIR)
    if not countries:
        st.error(L["no_data"].format(d=BASE_DATA_DIR))
        st.stop()

    sel_country = st.selectbox(
        L["country"], countries, format_func=lambda c: country_label(c, LANG),
        key="sb_opt_country", help=H["country"],
    )
    if sel_country not in countries:
        sel_country = countries[0]

    states = subdirs(os.path.join(BASE_DATA_DIR, sel_country))
    if not states:
        st.warning(L["no_state"])
        st.stop()

    sel_state = st.selectbox(L["state"], states, format_func=clean_state, key="sb_opt_state", help=H["state"])
    if sel_state not in states:
        sel_state = states[0]

    counties = list_counties(sel_country, sel_state)
    if not counties:
        st.warning(L["no_county"])
        st.stop()

    sel_county_file = st.selectbox(
        L["county"], list(counties.keys()), format_func=lambda f: counties[f],
        key="sb_opt_county", help=H["county"],
    )
    sel_county = counties[sel_county_file]
    file_path = os.path.join(BASE_DATA_DIR, sel_country, sel_state, sel_county_file)
    st.caption(f"📍 {country_label(sel_country, LANG)} / {clean_state(sel_state)} / {sel_county}")

    st.divider()
    st.header(L["sb_analytic"])
    cell_size = st.slider(L["cell"], min_value=500, max_value=5000, value=500, step=500, help=H["cell"])
    if cell_size < 1000:
        st.caption("⚠️ " + ("Lưới < 1000 m: các ô liền kề không độc lập." if LANG == "vi"
                           else "Grid < 1000 m: neighbouring cells are not independent."))
    year = st.selectbox(L["year"], YEARS, index=len(YEARS) - 2, help=H["year"])

    st.divider()
    run_btn = sx(st.button, L["run"], type="primary", disabled=not gee_ok, help=H["run"])
    if not gee_ok:
        st.caption("🔌 " + ("Chưa kết nối Google Earth Engine." if LANG == "vi" else "Google Earth Engine not connected."))

# ==========================================
# 6. PIPELINE (chỉ chạy khi bấm nút; kết quả lưu session_state)
# ==========================================
def run_pipeline():
    from exactextract import exact_extract  # lazy import

    stage = "Station 1"
    tmp_path = None
    with st.status(L["st1"].format(s=cell_size), expanded=True) as status:
        try:
            # ---------- Trạm 1 ----------
            boundary = gpd.read_file(file_path)
            if boundary.crs is None:
                boundary = boundary.set_crs(epsg=4326)
            boundary = boundary[boundary.geometry.notna() & ~boundary.geometry.is_empty]
            boundary["geometry"] = boundary.geometry.make_valid()
            boundary = boundary[boundary.geometry.type.isin(["Polygon", "MultiPolygon", "GeometryCollection"])]
            boundary = boundary.explode(index_parts=False)
            boundary = boundary[boundary.geometry.type.isin(["Polygon", "MultiPolygon"])]
            if boundary.empty:
                raise ValueError("Boundary has no polygon geometry.")
            boundary_wgs = gpd.GeoDataFrame(geometry=[union_geoms(boundary.to_crs(4326))], crs=4326)

            bx0, by0, bx1, by1 = boundary_wgs.total_bounds
            epsg = get_dynamic_utm_crs((bx0 + bx1) / 2, (by0 + by1) / 2)
            boundary_utm = boundary_wgs.to_crs(epsg=epsg)

            grid = build_grid(boundary_utm, cell_size)
            st.write("✅ " + L["ok1"].format(n=len(grid), s=cell_size, e=epsg))

            # ---------- Trạm 2 ----------
            stage = "Station 2"
            status.update(label=L["st2"])
            grid_wgs = grid.to_crs(epsg=4326)
            gx0, gy0, gx1, gy1 = grid_wgs.total_bounds
            pad = 0.005  # ~500m, đảm bảo raster phủ hết ô biên
            bbox = (round(gx0 - pad, 5), round(gy0 - pad, 5), round(gx1 + pad, 5), round(gy1 + pad, 5))
            tif_bytes = fetch_ntl_raster(bbox, int(year))
            st.write("✅ " + L["ok2"].format(y=year))

            # ---------- Trạm 3 ----------
            stage = "Station 3"
            status.update(label=L["st3"])
            with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
                tmp.write(tif_bytes)
                tmp_path = tmp.name

            stats = exact_extract(
                tmp_path,
                grid_wgs[["grid_id", "geometry"]],
                ["mean"],
                include_cols=["grid_id"],
                output="pandas",
            )
            mean_col = next(c for c in stats.columns if "mean" in str(c).lower())
            stats = stats[["grid_id", mean_col]].rename(columns={mean_col: "ntl_mean"})
            stats["grid_id"] = pd.to_numeric(stats["grid_id"], errors="coerce").astype("int64")
            stats["ntl_mean"] = pd.to_numeric(stats["ntl_mean"], errors="coerce").fillna(0.0).clip(lower=0.0)

            grid = grid.merge(stats, on="grid_id", how="left").reset_index(drop=True)
            grid["ntl_mean"] = grid["ntl_mean"].fillna(0.0).astype(float)

            status.update(label="Trạm 3/3 · Đang tính Moran's I toàn cục (hoán vị)..." if LANG == "vi"
                          else "Station 3/3 · Computing global Moran's I (permutations)...")
      
            try:  # Moran's I (không làm hỏng pipeline nếu lỗi)
                moran = morans_i(grid, grid["ntl_mean"].to_numpy(dtype=float), cell_size)
            except Exception:  # noqa: BLE001
                moran = None
            st.write("✅ " + L["ok3"])

            status.update(label=L["st4"], state="complete", expanded=False)
        except LookupError:
            status.update(state="error")
            st.error(L["err_empty"].format(y=year))
            return None
        except ConnectionError as e:
            status.update(state="error")
            st.error(L["err_http"].format(c=str(e).split(":")[-1]))
            return None
        except Exception as e:  # noqa: BLE001
            status.update(state="error")
            st.error(f"{L['err_stage'].format(s=stage)}: {e}")
            return None
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    return {
        "grid_utm": grid,
        "boundary_wgs": boundary_wgs,
        "epsg": epsg,
        "country_raw": sel_country,
        "state_name": clean_state(sel_state),
        "district": sel_county,
        "iso3": iso3_of(sel_country) or "",
        "size": cell_size,
        "year": int(year),
        "moran": moran,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


if run_btn:
    st.session_state["result"] = run_pipeline()

res = st.session_state.get("result")
if not res:
    st.info(L["idle"])
    st.stop()

# ==========================================
# 7. TÍNH CHỈ SỐ CHO KẾT QUẢ
# ==========================================
grid_utm = res["grid_utm"].reset_index(drop=True)
size, yr, epsg = res["size"], res["year"], res["epsg"]
country_disp = country_label(res["country_raw"], LANG)
state_disp, district = res["state_name"], res["district"]
place = f"{country_disp} / {state_disp} / {district}"

n = len(grid_utm)
ntl = grid_utm["ntl_mean"].to_numpy(dtype=float)
area = grid_utm["area_km2"].to_numpy(dtype=float)
sol_cell = ntl * area
sol = float(sol_cell.sum())
w_mean = float(np.average(ntl, weights=area)) if area.sum() > 0 else 0.0
ser = pd.Series(ntl)
rank = ser.rank(method="min", ascending=False).astype(int).to_numpy()
pctile = (ser.rank(pct=True, method="average") * 100).round(1).to_numpy()
ratio = ntl / w_mean if w_mean > 0 else np.zeros(n)
share = sol_cell / sol * 100 if sol > 0 else np.zeros(n)
codes = class_codes(ntl)
q25, q75 = float(np.quantile(ntl, 0.25)), float(np.quantile(ntl, 0.75))
std_ntl = float(ntl.std())
zscore = (ntl - ntl.mean()) / std_ntl if std_ntl > 0 else np.zeros(n)
local_codes = np.select([ntl <= 0, ntl >= q75, ntl <= q25], [3, 0, 2], default=1)
is_border = area < 0.999 * (size / 1000) ** 2
px_per_cell = round((size / GEE_SCALE_M) ** 2, 1)
vmax = float(ntl.max())
vmax = vmax if vmax > 0.1 else 1.0

cent_utm = grid_utm.geometry.centroid
cent_wgs = gpd.GeoSeries(cent_utm, crs=grid_utm.crs).to_crs(epsg=4326)
lon_c, lat_c = cent_wgs.x.to_numpy(), cent_wgs.y.to_numpy()

st.divider()
with st.container(border=True):
    st.markdown(f"#### 📍 {place}")
    st.caption(f"{yr} · {size} m · EPSG:{epsg}")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(L["m_cells"], f"{n:,}", help="Tổng số ô lưới sau khi cắt theo ranh giới." if LANG == "vi" else "Total grid cells after clipping.")
    c2.metric(L["m_mean"], f"{w_mean:.2f}", help="NTL trung bình có trọng số diện tích (nW/cm²/sr)." if LANG == "vi" else "Area-weighted mean NTL (nW/cm²/sr).")
    c3.metric(L["m_max"], f"{ntl.max():.2f}", help="Giá trị NTL của ô sáng nhất." if LANG == "vi" else "NTL of the brightest cell.")
    c4.metric(L["m_sol"], f"{sol:,.1f}", help="SOL = Σ(NTL × diện tích). Tổng ánh sáng của địa phương." if LANG == "vi" else "SOL = Σ(NTL × area). Total light of the locality.")
    c5.metric(L["m_area"], f"{area.sum():,.1f} km²", help="Tổng diện tích các ô sau khi cắt." if LANG == "vi" else "Total area of clipped cells.")
    c6.metric(L["m_lit"], f"{(ntl > 0).mean() * 100:.0f}%", help="Tỷ lệ ô có NTL > 0." if LANG == "vi" else "Share of cells with NTL > 0.")
st.write("")

tab_map, tab_data, tab_lisa, tab_guide = st.tabs([
    L["tab_map"], 
    L["tab_data"], 
    "🧭 LISA · Panel", 
    L["tab_guide"]
])

# ==========================================
# 8. TAB BẢN ĐỒ
# ==========================================
with tab_map:
    with st.expander("🎛️ " + ("Tùy chỉnh hiển thị bản đồ" if LANG == "vi" else "Map display options"), expanded=True):
        cA, cB, cC = st.columns([2.4, 2.4, 2])
        color_mode = cA.radio(
            L["color_mode"], ["ntl", "class", "local"], index=0, horizontal=True,
            format_func=lambda k: L["color_names"][k], key="color_mode", help=H["color_mode"],
        )
        scale_mode = cB.radio(
            L["scale"], ["linear", "sqrt", "log"], index=1, horizontal=True,
            format_func=lambda k: L["scale_names"][k], key="scale_mode",
            disabled=(color_mode != "ntl"), help=H["scale"],
        )
        opacity = cC.slider(L["opacity"], 0.3, 1.0, 0.85, 0.05, key="opacity", help=H["opacity"])

        st.divider()
        cD, cE, cF, cG = st.columns(4)
        hide0 = cD.toggle(L["hide0"], value=False, key="hide0", help=H["hide0"])
        hl_top = cE.toggle(L["hl"], value=True, key="hl_top", help=H["hl"])
        borders = cF.toggle(L["borders"], value=False, key="borders", help=H["borders"])
        mask_on = cG.toggle(L["mask"], value=True, key="mask_on", help=H["mask"])

    # Bảng thuộc tính gọn (khóa ngắn) cho GeoJSON; đầu dò dựng bằng JS
    disp = gpd.GeoDataFrame(
        {
            "g": grid_utm["grid_id"].to_numpy(dtype="int64"),
            "a": np.round(area, 4),
            "v": np.round(ntl, 3),
            "o": np.round(sol_cell, 3),
            "r": np.round(ratio, 2),
            "k": rank.astype("int64"),
            "p": np.round(pctile, 1),
            "s": np.round(share, 4),
            "z": np.round(zscore, 2),
            "c": codes.astype("int64"),
            "l": local_codes.astype("int64"),
            "y": np.round(lat_c, 5),
            "x": np.round(lon_c, 5),
        },
        geometry=grid_utm.to_crs(epsg=4326).geometry.values,
        crs=4326,
    )

    geo = disp.copy()
    if hide0:
        geo = geo[geo["v"] > 0]
    if len(geo) > RENDER_CAP:
        st.warning(L["render_cap"].format(n=len(geo), c=RENDER_CAP))
        geo = geo.nlargest(RENDER_CAP, "v")
    try:  # làm gọn tọa độ để GeoJSON nhẹ hơn
        arr = shapely.set_precision(np.asarray(geo.geometry.values), 1e-6)
        geo = geo.set_geometry(gpd.GeoSeries(arr, index=geo.index, crs=4326))
    except Exception:  # noqa: BLE001
        pass

    bw = res["boundary_wgs"]
    bminx, bminy, bmaxx, bmaxy = bw.total_bounds
    m = folium.Map(
        location=[(bminy + bmaxy) / 2, (bminx + bmaxx) / 2],
        zoom_start=12, tiles=None, control_scale=True, prefer_canvas=True,
    )
    folium.TileLayer(tiles=TILE_DARK, attr="Esri, HERE, Garmin", name=L["tile_dark"], show=True).add_to(m)
    folium.TileLayer(tiles=TILE_SAT, attr="Esri, Maxar, Earthstar Geographics", name=L["tile_sat"], show=False).add_to(m)
    folium.TileLayer(tiles=TILE_LIGHT, attr="Esri, HERE, Garmin", name=L["tile_light"], show=False).add_to(m)
    folium.TileLayer(tiles=TILE_STREET, attr="Esri, HERE, Garmin, OpenStreetMap contributors",
                     name=L["tile_street"], show=False).add_to(m)
    m.fit_bounds([[bminy, bminx], [bmaxy, bmaxx]])
    m.get_root().header.add_child(folium.Element(MAP_CSS))

    colormap = make_colormap(scale_mode, vmax, L["caption"].format(y=yr))

    def style_fn(feature):
        p = feature["properties"]
        v = min(max(float(p.get("v") or 0.0), 0.0), vmax)
        if color_mode == "class":
            fill_c = CLASS_COLORS[int(p.get("c", 4))]
            fo = 0.18 if v <= 0 else opacity
        elif color_mode == "local":
            fill_c = LOCAL_COLORS[int(p.get("l", 3))]
            fo = 0.18 if v <= 0 else opacity
        else:
            fill_c = colormap(v)
            if v <= 0:
                fo = 0.10
            elif v < vmax * 0.02:
                fo = opacity * 0.55
            else:
                fo = opacity
        if borders:
            return {"fillColor": fill_c, "color": "#3a3a44", "weight": 0.5, "opacity": 0.9, "fillOpacity": fo}
        # không viền: nét cùng màu nền để xóa khe hở giữa các ô, nhìn liền mạch như ảnh nhiệt
        return {"fillColor": fill_c, "color": fill_c, "weight": 0.6, "opacity": min(fo, 0.9), "fillOpacity": fo}

    # Lớp làm tối ngoài ranh giới (tập trung mắt vào vùng phân tích)
    bclean = bw[bw.geometry.type.isin(["Polygon", "MultiPolygon"])]
    if mask_on:
        try:
            outside = shapely.make_valid(shapely.box(-180, -85, 180, 85).difference(union_geoms(bclean)))
            mgroup = folium.FeatureGroup(name=L["layer_mask"], show=True)
            folium.GeoJson(
                gpd.GeoDataFrame(geometry=[outside], crs=4326), interactive=False,
                style_function=lambda _: {"fillColor": "#000000", "fillOpacity": 0.55, "weight": 0, "opacity": 0},
            ).add_to(mgroup)
            mgroup.add_to(m)
        except Exception:  # noqa: BLE001
            pass

    grid_layer = folium.GeoJson(
        geo[["g", "a", "v", "o", "r", "k", "p", "s", "z", "c", "l", "y", "x", "geometry"]],
        name=L["layer_grid"],
        style_function=style_fn,
        highlight_function=lambda f: {"weight": 2.4, "color": "#00e5ff", "opacity": 1, "fillOpacity": 0.97},
    )
    grid_layer.add_to(m)

    tooltip_cfg = {
        "t": L["tt"], "n": f"{n:,}", "vmax": vmax, "place": district, "year": yr, "unit": "nW/cm²/sr",
        "cc": CLASS_COLORS, "tc": CLASS_TEXT_COLORS, "lc": LOCAL_COLORS,
        "short": L["short"], "dev": L["dev"], "rank": L["rank"],
    }
    RichTooltip(grid_layer, tooltip_cfg).add_to(m)

    if hl_top and ntl.max() > 0:
        top_geo = disp.nlargest(10, "v")[["geometry"]]
        folium.GeoJson(
            top_geo, name=L["layer_top"], interactive=False,
            style_function=lambda _: {"fill": False, "color": "#00e5ff", "weight": 2.6, "dashArray": "5 4"},
        ).add_to(m)

    # Ranh giới: hào quang mờ + nét trắng sắc (chỉ Polygon, không Marker)
    bgroup = folium.FeatureGroup(name=L["layer_bound"], show=True)
    folium.GeoJson(bclean, interactive=False,
                   style_function=lambda _: {"fill": False, "color": "#ffffff", "weight": 9, "opacity": 0.12}).add_to(bgroup)
    folium.GeoJson(bclean, interactive=False,
                   style_function=lambda _: {"fill": False, "color": "#ffffff", "weight": 2.2, "opacity": 1}).add_to(bgroup)
    bgroup.add_to(m)

    # Chú giải
    if color_mode == "ntl":
        colormap.add_to(m)
    elif color_mode == "class":
        items = [(CLASS_COLORS[i], f"{THRESH_TEXT[i]} · {L['short'][i]}") for i in range(5)]
        m.get_root().html.add_child(folium.Element(legend_html(L["legend_class"], items)))
    else:
        order = [0, 1, 2, 3]
        items = [(LOCAL_COLORS[i], L["rank"][i].split(" (")[0]) for i in order]
        m.get_root().html.add_child(folium.Element(legend_html(L["legend_local"], items)))

    # Bảng thông tin góc trái
    panel = (
        f'<div class="nt-panel"><div class="t">{html_lib.escape(district)}</div>'
        f'<div class="s">{html_lib.escape(country_disp)} / {html_lib.escape(state_disp)}</div>'
        f'<div class="s">{yr} · {size} m · {n:,} {"ô" if LANG == "vi" else "cells"}</div>'
        f'<div>{L["p_mean"]} <b>{w_mean:.2f}</b> · {L["p_max"]} <b>{ntl.max():.2f}</b> · '
        f'{L["p_lit"]} <b>{(ntl > 0).mean() * 100:.0f}%</b></div></div>'
    )
    m.get_root().html.add_child(folium.Element(panel))

    Fullscreen(position="topleft").add_to(m)
    MousePosition(position="bottomleft", num_digits=5, prefix="Lat/Lon").add_to(m)
    MiniMap(toggle_display=True, minimized=True, position="bottomright", tile_layer="CartoDB dark_matter").add_to(m)
    folium.LayerControl(collapsed=True, position="topright").add_to(m)

    map_key = (f"ntl_map_{LANG}_{color_mode}_{scale_mode}_{opacity}_{hide0}_{hl_top}_{borders}_{mask_on}_"
               f"{res['ts']}")
    try:
        st_folium(m, use_container_width=True, height=680, returned_objects=[], key=map_key)
    except TypeError:
        st_folium(m, height=680, returned_objects=[], key=map_key)

# ==========================================
# 9. TAB DỮ LIỆU
# ==========================================
export_df = pd.DataFrame(
    {
        "iso3": res["iso3"],
        "country": country_label(res["country_raw"], "en"),
        "province": state_disp,
        "district": district,
        "grid_id": grid_utm["grid_id"].to_numpy(dtype="int64"),
        "year": yr,
        "cell_size_m": size,
        "centroid_lon": np.round(lon_c, 6),
        "centroid_lat": np.round(lat_c, 6),
        f"centroid_x_epsg{epsg}": np.round(cent_utm.x.to_numpy(), 1),
        f"centroid_y_epsg{epsg}": np.round(cent_utm.y.to_numpy(), 1),
        "area_km2": np.round(area, 6),
        "is_border_cell": is_border.astype(int),
        "ntl_mean": np.round(ntl, 4),
        "ntl_sol": np.round(sol_cell, 4),
        "ntl_log": np.round(np.log1p(ntl), 6),
        "ntl_zscore": np.round(zscore, 4),
        "ntl_rank": rank,
        "ntl_pctile": pctile,
        "ntl_vs_mean": np.round(ratio, 4),
        "sol_share_pct": np.round(share, 5),
        "ntl_class": codes + 1,
        "ntl_class_label": np.array(TEXT["en"]["dev"])[codes],
        "ntl_local_grp": local_codes + 1,
    }
)

top10_n = max(1, int(math.ceil(n * 0.10)))
top10_share = float(np.sort(sol_cell)[::-1][:top10_n].sum() / sol * 100) if sol > 0 else 0.0
gini_v = gini(sol_cell)
lit_share = float((ntl > 0).mean() * 100)
dark_area = float(area[ntl <= 0].sum() / max(area.sum(), 1e-12) * 100)
cv = std_ntl / ntl.mean() if ntl.mean() > 0 else 0.0
skew = float(ser.skew()) if n > 2 and std_ntl > 0 else 0.0
moran = res.get("moran")

with tab_data:
    st.caption(L["csv_note"])
    if size < 1000:
        st.warning(L["quality_warn"].format(s=size, px=px_per_cell))

    # --- Nhận định nhanh ---
    with st.container(border=True):  
        st.subheader(L["sec_take"])
        imax = int(np.argmax(ntl))
        gdesc = L["gdesc"][0 if gini_v < 0.4 else (1 if gini_v < 0.6 else 2)]
        take_lines = [
            L["take"][0].format(gid=int(grid_utm["grid_id"].iloc[imax]), lat=lat_c[imax], lon=lon_c[imax],
                                mx=float(ntl[imax]), ratio=float(ratio[imax])),
            L["take"][1].format(top10=top10_share, gini=gini_v, gdesc=gdesc),
            L["take"][2].format(lit=lit_share, dark=dark_area),
        ]
        if moran:
            if moran["p"] < 0.05 and moran["I"] > moran["E"]:
                mdesc = L["mdesc"][0]
            elif moran["p"] < 0.05:
                mdesc = L["mdesc"][2]
            else:
                mdesc = L["mdesc"][1]
            take_lines.append(L["take"][3].format(mi=moran["I"], mp=moran["p"], mdesc=mdesc))
        take_lines.append(L["take"][4].format(border=int(is_border.sum()), n=n))
        st.info("\n\n".join(take_lines))
 
        col_l, col_r = st.columns(2)

    # --- Thông tin chung ---
    with col_l:
        with st.expander("ℹ️ " + L["sec_overview"], expanded=False):
            bcx, bcy = (bminx + bmaxx) / 2, (bminy + bmaxy) / 2
            ov_vals = [
                place, res["iso3"] or "-", f"{yr} / {size} m",
                f"{n:,} ({n - int(is_border.sum()):,} / {int(is_border.sum()):,})",
                f"{area.sum():,.2f} km²", f"{bcy:.4f}, {bcx:.4f}", f"EPSG:{epsg} (UTM)", res["ts"],
            ]
            sx(st.dataframe, pd.DataFrame({L["ov_cols"][0]: L["ov_rows"], L["ov_cols"][1]: ov_vals}), hide_index=True)

    # --- Thống kê ---
    with col_r:
        st.subheader(L["sec_stats"])
        stat_vals = [
            f"{w_mean:.3f}", f"{ntl.mean():.3f}", f"{np.median(ntl):.3f}", f"{std_ntl:.3f}",
            f"{cv:.2f}", f"{skew:.2f}",
            f"{ntl.min():.3f}", f"{q25:.3f}", f"{q75:.3f}",
            f"{np.quantile(ntl, 0.90):.3f}", f"{np.quantile(ntl, 0.99):.3f}", f"{ntl.max():.3f}",
            f"{gini_v:.3f}", f"{lit_share:.1f}%", f"{top10_share:.1f}%",
        ]
        sx(st.dataframe,
           pd.DataFrame({L["stat_cols"][0]: L["stat_rows"], L["stat_cols"][1]: stat_vals}),
           hide_index=True, height=320)

    # --- Moran's I ---
    st.subheader(L["sec_spatial"])
    if moran:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric(L["mi_I"], f"{moran['I']:.3f}", help="Moran's I toàn cục: >0 tụ cụm, ≈0 ngẫu nhiên, <0 xen kẽ." if LANG == "vi" else "Global Moran's I: >0 clustered, ≈0 random, <0 alternating.")
        k2.metric(L["mi_E"], f"{moran['E']:.4f}", help="Giá trị kỳ vọng khi ngẫu nhiên hoàn toàn = −1/(n−1)." if LANG == "vi" else "Expected value under randomness = −1/(n−1).")
        k3.metric(L["mi_p"], f"{moran['p']:.3f}", help="p-value giả từ hoán vị; < 0,05 là có ý nghĩa." if LANG == "vi" else "Permutation pseudo p-value; < 0.05 is significant.")
        k4.metric(L["mi_k"], f"{moran['k']:.2f}", help="Số láng giềng Queen trung bình mỗi ô (tối đa 8)." if LANG == "vi" else "Average Queen neighbours per cell (max 8).")
        st.caption(L["mi_note"].format(k=moran["perms"]))
    else:
        st.caption(L["mi_na"])

    # --- Cơ cấu nhóm ---
    st.subheader(L["sec_class"])
    cls = (
        pd.DataFrame({"code": codes, "area": area, "sol": sol_cell})
        .groupby("code").agg(cells=("area", "size"), area=("area", "sum"), sol=("sol", "sum"))
        .reindex(range(5), fill_value=0)
    )
    tot_area = max(area.sum(), 1e-12)
    cls_tbl = pd.DataFrame(
        {
            L["cls_cols"][0]: L["dev"],
            L["cls_cols"][1]: THRESH_TEXT,
            L["cls_cols"][2]: cls["cells"].astype(int).to_numpy(),
            L["cls_cols"][3]: np.round(cls["cells"].to_numpy() / n * 100, 1),
            L["cls_cols"][4]: np.round(cls["area"].to_numpy() / tot_area * 100, 1),
            L["cls_cols"][5]: np.round(cls["sol"].to_numpy() / sol * 100 if sol > 0 else np.zeros(5), 1),
        }
    )
    sx(
        st.dataframe, cls_tbl, hide_index=True,
        column_config={
            L["cls_cols"][3]: st.column_config.ProgressColumn(L["cls_cols"][3], min_value=0, max_value=100, format="%.1f%%"),
            L["cls_cols"][4]: st.column_config.ProgressColumn(L["cls_cols"][4], min_value=0, max_value=100, format="%.1f%%"),
            L["cls_cols"][5]: st.column_config.ProgressColumn(L["cls_cols"][5], min_value=0, max_value=100, format="%.1f%%"),
        },
    )

    # --- Histogram ---
    st.subheader(L["sec_hist"])
    edges = [-0.001, 0, 1, 2, 5, 10, 15, 25, 40, 80, np.inf]
    binned = pd.cut(ntl, bins=edges, labels=L["hist_bins"]).value_counts()
    hist_df = pd.DataFrame({"bin": list(L["hist_bins"]), "cells": [int(binned.get(b, 0)) for b in L["hist_bins"]]})
    chart = (
        alt.Chart(hist_df)
        .mark_bar(color="#ffaa00", cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("bin:N", sort=list(L["hist_bins"]), title=L["hist_x"], axis=alt.Axis(labelAngle=0)),
            y=alt.Y("cells:Q", title=L["hist_y"]),
            tooltip=[alt.Tooltip("bin:N", title=L["hist_x"]), alt.Tooltip("cells:Q", title=L["hist_y"], format=",")],
        )
        .properties(height=280)
    )
    sx(st.altair_chart, chart)

    # --- Top 10 ---
    st.subheader(L["sec_top"])
    top_cols = ["grid_id", "centroid_lon", "centroid_lat", "area_km2", "ntl_mean", "ntl_vs_mean",
                "sol_share_pct", "ntl_rank", "ntl_class"]
    top_cfg = {
        "grid_id": st.column_config.NumberColumn("grid_id", format="%d", pinned=True),
        "centroid_lon": st.column_config.NumberColumn("lon", format="%.5f"),
        "centroid_lat": st.column_config.NumberColumn("lat", format="%.5f"),
        "area_km2": st.column_config.NumberColumn("area_km2", format="%.3f"),
        "ntl_mean": st.column_config.ProgressColumn("ntl_mean", min_value=0, max_value=float(vmax), format="%.2f"),
        "ntl_vs_mean": st.column_config.NumberColumn("× vs TB", format="%.2f×"),
        "sol_share_pct": st.column_config.ProgressColumn("sol_share_pct", min_value=0,
                              max_value=float(max(export_df["sol_share_pct"].max(), 1e-9)), format="%.3f%%"),
        "ntl_rank": st.column_config.NumberColumn("rank", format="#%d"),
        "ntl_class": st.column_config.NumberColumn("class", format="%d"),
    }
    sx(st.dataframe, export_df.nlargest(10, "ntl_mean")[top_cols], hide_index=True, column_config=top_cfg)
   
    with st.expander(L["sec_full"]):
        full_cfg = {
            "grid_id": st.column_config.NumberColumn("grid_id", format="%d", pinned=True),
            "ntl_mean": st.column_config.ProgressColumn("ntl_mean", min_value=0, max_value=float(vmax), format="%.2f"),
            "ntl_pctile": st.column_config.ProgressColumn("ntl_pctile", min_value=0, max_value=100, format="P%.0f"),
        }
        sx(st.dataframe, export_df.sort_values("ntl_mean", ascending=False).head(5000),
           hide_index=True, column_config=full_cfg)

    # --- Phương pháp ---
    with st.expander("🔬 " + L["sec_meta"]):
        meta_vals = [fill(v, ds=GEE_DATASET, y=yr, s=size, e=epsg, px=px_per_cell) for v in L["meta_vals"]]
        sx(st.dataframe, pd.DataFrame({L["meta_cols"][0]: L["meta_rows"], L["meta_cols"][1]: meta_vals}), hide_index=True)

    # --- Từ điển dữ liệu ---
    with st.expander(L["sec_dict"]):
        li = 1 if LANG == "vi" else 2
        dd = pd.DataFrame(
            {
                L["dict_cols"][0]: [fill(r[0], E=epsg) for r in DATA_DICT],
                L["dict_cols"][1]: [r[li] for r in DATA_DICT],
            }
        )
        sx(st.dataframe, dd, hide_index=True)

    # --- Tải dữ liệu ---
    st.subheader(L["sec_dl"])
    slug = f"{slugify(district)}_NTL_{yr}_{size}m"
    d1, d2 = st.columns(2)
    with d1:
        sx(
            st.download_button,
            label=L["download"],
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{slug}.csv",
            mime="text/csv",
            type="primary",
            help="CSV theo ô, đủ cột cho hồi quy không gian (xem Từ điển dữ liệu)." if LANG == "vi" else "Cell-level CSV with all regression-ready columns (see Data dictionary)."
        )
    with d2:
        if st.toggle(L["prep_geo"], key="prep_geo", help="Dựng GeoJSON mất vài giây nên chỉ làm khi bạn bật." if LANG == "vi" else "Building GeoJSON takes a few seconds, so it only runs when enabled."):
            geo_gdf = gpd.GeoDataFrame(export_df, geometry=gpd.GeoSeries(grid_utm.to_crs(epsg=4326).geometry.values, crs=4326))
            sx(
                st.download_button,
                label=L["download_geo"],
                data=geo_gdf.to_json().encode("utf-8"),
                file_name=f"{slug}.geojson",
                mime="application/geo+json",
            )

# ==========================================
# 10. TAB HƯỚNG DẪN
# ==========================================
with tab_guide:
    st.markdown(L["guide_title"])
    for i, (title, body) in enumerate(GUIDE[LANG]):
        with st.expander(title, expanded=(i == 0)):
            if body == "__TABLE__":
                gt = pd.DataFrame(
                    {
                        L["g_tab_cols"][0]: L["dev"],
                        L["g_tab_cols"][1]: THRESH_TEXT,
                        L["g_tab_cols"][2]: CLASS_NOTES[LANG],
                    }
                )
                sx(st.dataframe, gt, hide_index=True)
            elif body == "__CODE__":
                st.caption(L["g_code_title"])
                st.code(CODE_SNIPPET, language="python")
            else:
                st.markdown(fill(body, y=yr, s=size))
            if "MAUP" in title and size < 1000:
                st.warning(L["quality_warn"].format(s=size, px=px_per_cell))


# ==========================================
# 11. TAB LISA (DATA BRIDGE CHO PANEL REGRESSION)
# ==========================================
with tab_lisa:
    from lisa_ui import render_lisa_tab
    
    # Tạo mã định danh vùng duy nhất (Ví dụ: VNM_hoan_kiem)
    region_id = f"{res['iso3']}_{slugify(res['district'])}"
    
    # Truyền dữ liệu vào lõi LISA
    try:
        render_lisa_tab(
            res=res,
            grid_utm=grid_utm,
            export_df=export_df,
            lang=LANG,
            region_id=region_id,
            region_label=place,
            render_cap=RENDER_CAP,
            basemap="CartoDB dark_matter" 
        )
    except Exception as e:
        st.error(f"Không chạy được mô-đun LISA: {e}")
