"""
NTL Data Extractor (Global Scale)
Trích xuất Ánh sáng ban đêm (VIIRS) theo lưới ô vuông cho Kinh tế lượng không gian.

Pipeline 4 trạm:
  1. Gridding  : UTM động -> lưới mét -> clip theo ranh giới
  2. Fetch     : Google Earth Engine -> GeoTIFF về máy chủ
  3. Compute   : exactextract (C/C++) -> zonal mean theo tỷ lệ phủ
  4. Visualize : folium dark map + tooltip song ngữ + phân tích + xuất dữ liệu
"""
import io
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
from folium.plugins import Fullscreen, MiniMap, MousePosition
from streamlit_folium import st_folium

try:
    import pycountry
except Exception:  # pragma: no cover
    pycountry = None

# ==========================================
# 0. CONFIG
# ==========================================
st.set_page_config(page_title="NTL Data Extractor", page_icon="🌙", layout="wide")

BASE_DATA_DIR = "data/gadm41_VNM_gpkg"
GEE_DATASET = "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"
GEE_SCALE_M = 463.83          # độ phân giải gốc VIIRS (~15 arc-sec)
MAX_CELLS = 150_000           # trần số ô lưới để tránh treo máy chủ
RENDER_CAP = 40_000           # trần số ô vẽ lên bản đồ (trình duyệt)
YEARS = list(range(2014, 2026))

TILE_DARK = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
TILE_SAT = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
TILE_LIGHT = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"

# Ngưỡng phân loại kinh tế (nW/cm²/sr) — dùng chung cho tooltip, bảng và CSV
THRESHOLDS = [40, 15, 5]  # >=40, >=15, >=5, >0, ==0

# ==========================================
# 1. TÊN HIỂN THỊ (BEGIN NAMES)
# ==========================================
ISO_NAMES = {"vi": {"VNM": "Việt Nam"}, "en": {"VNM": "Vietnam"}}


def _fold(s):
    """Bỏ dấu + viết thường để so sánh/sắp xếp."""
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").casefold()


def iso3_of(folder):
    m = re.match(r"^([A-Za-z]{3})(?=[_\W]|$)", folder)
    return m.group(1).upper() if m else None


def country_label(folder, lang="vi"):
    """'VNM_Curated_Provinces' -> 'Việt Nam' / 'Vietnam'."""
    iso = iso3_of(folder)
    if iso is None:
        return re.sub(r"\s+", " ", folder.replace("_", " ")).strip()
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
    return re.sub(r"\s+", " ", folder.replace("_", " ")).strip()


def clean_county(stem, state_name):
    """'VNM Hà Nội Hoàn Kiếm District' -> 'Hoàn Kiếm' (bỏ mã nước, tên tỉnh, hậu tố District)."""
    tokens = stem.replace("_", " ").split()
    if tokens and len(tokens[0]) == 3 and tokens[0].isalpha() and tokens[0].isupper():
        tokens = tokens[1:]
    st_tokens = state_name.split()
    n = len(st_tokens)
    if n and len(tokens) > n and [_fold(t) for t in tokens[:n]] == [_fold(t) for t in st_tokens]:
        tokens = tokens[n:]
    while len(tokens) > 1 and _fold(tokens[-1]) in {"district", "county"}:
        tokens = tokens[:-1]
    return " ".join(tokens) if tokens else stem
# END NAMES


def subdirs(path):
    if not os.path.isdir(path):
        return []
    return sorted(
        (d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))),
        key=_fold,
    )


def list_counties(country, state):
    """Trả về {tên_file: tên_hiển_thị} (đã sắp xếp, không trùng)."""
    p = os.path.join(BASE_DATA_DIR, country, state)
    if not os.path.isdir(p):
        return {}
    state_name = clean_state(state)
    files = sorted((f for f in os.listdir(p) if f.lower().endswith(".geojson")), key=_fold)
    out, used = {}, set()
    for f in files:
        stem = f[: -len(".geojson")]
        label = clean_county(stem, state_name)
        if label in used:
            label = f"{label} ({stem.replace('_', ' ')})"
        used.add(label)
        out[f] = label
    return dict(sorted(out.items(), key=lambda kv: _fold(kv[1])))


def slugify(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", _fold(s)).strip("_") or "area"


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
        "st1": "Trạm 1: Tạo lưới {s}m và cắt theo ranh giới...",
        "st2": "Trạm 2: Tải raster từ Google Earth Engine...",
        "st3": "Trạm 3: Tính phủ phân số điểm ảnh (C/C++)...",
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
        "scale": "Thang màu",
        "scale_names": {"linear": "Tuyến tính", "sqrt": "Căn bậc hai", "log": "Logarit"},
        "opacity": "Độ đậm ô lưới",
        "hide0": "Ẩn ô không sáng",
        "hl": "Viền Top 10",
        "tile_dark": "Nền tối",
        "tile_sat": "Vệ tinh",
        "tile_light": "Nền sáng",
        "layer_grid": "Lưới NTL",
        "layer_bound": "Ranh giới",
        "layer_top": "Top 10 điểm sáng",
        "render_cap": "Địa phương có {n:,} ô; bản đồ chỉ vẽ {c:,} ô sáng nhất để trình duyệt chạy mượt (CSV vẫn đầy đủ).",
        # --- đầu dò ---
        "aliases": ["🔢 ID ô lưới:", "📐 Diện tích đo lường:", "💡 Cường độ NTL (nW/cm²/sr):",
                    "⚖️ So với mức TB địa phương:", "🏆 Thứ hạng sáng:", "📈 Phân vị (0-100):",
                    "🔆 Tỷ trọng tổng ánh sáng:", "🏙️ Ước lượng Kinh tế (Global):", "📊 Vị thế Nội bộ (Local):"],
        "dev": ["Thương mại/Dịch vụ (Mật độ siêu cao)", "Đô thị lõi/Khu dân cư đông đúc",
                "Vành đai đô thị/Ngoại ô phát triển", "Khu vực ven đô/Hoạt động kinh tế thấp",
                "Không gian mở/Khu vực thiếu sáng"],
        "rank": ["Top 25% (Tâm điểm kinh tế của địa phương)", "Bottom 25% (Vùng trũng của địa phương)",
                 "Mức phát triển trung bình của địa phương", "Không có ánh sáng đáng kể"],
        # --- dữ liệu ---
        "sec_overview": "Thông tin chung",
        "sec_stats": "Thống kê phân bố ánh sáng",
        "sec_class": "Cơ cấu theo nhóm kinh tế (Global)",
        "sec_hist": "Phân bố số ô theo cường độ NTL",
        "sec_top": "Top 10 ô sáng nhất",
        "sec_full": "Xem bảng đầy đủ (tối đa 5.000 dòng sáng nhất)",
        "sec_meta": "Phương pháp & siêu dữ liệu",
        "sec_dl": "Tải dữ liệu",
        "ov_cols": ["Chỉ tiêu", "Giá trị"],
        "ov_rows": ["Địa phương", "Năm / Độ phân giải lưới", "Số ô lưới", "Tổng diện tích", "Thời điểm xử lý"],
        "stat_cols": ["Chỉ số", "Giá trị"],
        "stat_rows": ["Trung bình (theo diện tích)", "Trung bình (đơn giản)", "Trung vị", "Độ lệch chuẩn",
                      "Nhỏ nhất", "P25", "P75", "P90", "P99", "Lớn nhất",
                      "Hệ số Gini (bất bình đẳng ánh sáng)", "Tỷ lệ ô có ánh sáng",
                      "Tỷ trọng SOL của 10% ô sáng nhất"],
        "cls_cols": ["Nhóm", "Ngưỡng NTL", "Số ô", "% ô", "% diện tích", "% tổng ánh sáng"],
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
        "csv_note": "CSV gồm mã địa phương, tọa độ tâm ô (WGS84 & UTM), diện tích, NTL, SOL, hạng, phân vị, tỷ trọng và nhóm kinh tế (1 = sáng nhất, 5 = không sáng).",
        # --- hướng dẫn ---
        "guide_title": "### 📖 Hướng dẫn đọc dữ liệu (cho nhà phân tích / đầu tư)",
        "g_tab_cols": ["Nhóm", "Ngưỡng NTL (nW/cm²/sr)", "Diễn giải"],
        "g_code_title": "Ví dụ dùng CSV trong hồi quy",
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
        "st1": "Station 1: Building {s}m grid and clipping to boundary...",
        "st2": "Station 2: Fetching raster from Google Earth Engine...",
        "st3": "Station 3: Computing fractional pixel coverage (C/C++)...",
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
        "scale": "Color scale",
        "scale_names": {"linear": "Linear", "sqrt": "Square root", "log": "Logarithmic"},
        "opacity": "Cell opacity",
        "hide0": "Hide unlit cells",
        "hl": "Outline Top 10",
        "tile_dark": "Dark base",
        "tile_sat": "Satellite",
        "tile_light": "Light base",
        "layer_grid": "NTL grid",
        "layer_bound": "Boundary",
        "layer_top": "Top 10 hotspots",
        "render_cap": "This area has {n:,} cells; the map draws only the {c:,} brightest to keep the browser smooth (CSV stays complete).",
        "aliases": ["🔢 Grid ID:", "📐 Survey Area:", "💡 NTL Intensity (nW/cm²/sr):",
                    "⚖️ Versus area average:", "🏆 Brightness rank:", "📈 Percentile (0-100):",
                    "🔆 Share of total light:", "🏙️ Economic Proxy (Global):", "📊 Internal Status (Local):"],
        "dev": ["Commercial/Services (Ultra-high density)", "Urban Core/Dense Residential",
                "Urban Fringe/Developing Suburb", "Peri-urban/Low Economic Activity",
                "Open Space/Unlit Area"],
        "rank": ["Top 25% (Economic Hotspot of the area)", "Bottom 25% (Economic Coldspot)",
                 "Area-average development", "No significant light"],
        "sec_overview": "Overview",
        "sec_stats": "Light distribution statistics",
        "sec_class": "Breakdown by economic class (Global)",
        "sec_hist": "Number of cells by NTL intensity",
        "sec_top": "Top 10 brightest cells",
        "sec_full": "Show full table (up to 5,000 brightest rows)",
        "sec_meta": "Method & metadata",
        "sec_dl": "Downloads",
        "ov_cols": ["Item", "Value"],
        "ov_rows": ["Locality", "Year / Grid resolution", "Grid cells", "Total area", "Processed at"],
        "stat_cols": ["Statistic", "Value"],
        "stat_rows": ["Mean (area-weighted)", "Mean (simple)", "Median", "Std. deviation",
                      "Minimum", "P25", "P75", "P90", "P99", "Maximum",
                      "Gini coefficient (light inequality)", "Share of lit cells",
                      "SOL share of brightest 10% of cells"],
        "cls_cols": ["Class", "NTL threshold", "Cells", "% cells", "% area", "% of total light"],
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
        "csv_note": "CSV has locality codes, cell centroids (WGS84 & UTM), area, NTL, SOL, rank, percentile, share and economic class (1 = brightest, 5 = unlit).",
        "guide_title": "### 📖 Reading guide (for analysts / investors)",
        "g_tab_cols": ["Class", "NTL threshold (nW/cm²/sr)", "Interpretation"],
        "g_code_title": "Example: using the CSV in a regression",
    },
}

GUIDE = {
    "vi": [
        ("1. NTL là gì và đo bằng gì?",
         """
* **NTL (Nighttime Lights)** là ánh sáng phát ra ban đêm, vệ tinh **VIIRS/DNB** (NOAA) đo hằng tháng.
* **Đơn vị:** nW/cm²/sr (nano-watt trên cm² trên steradian) — là *bức xạ*, không phải số bóng đèn.
* **Dữ liệu dùng:** `avg_rad` của sản phẩm đã hiệu chỉnh ánh sáng tạp. Với năm **{y}**, công cụ lấy **trung vị** các ảnh tháng để giảm nhiễu mây, trăng, cháy rừng.
* **Vì sao liên quan kinh tế?** Đô thị sáng hơn thường có mật độ dân cư, thương mại, công nghiệp và hạ tầng cao hơn, nên NTL là *biến đại diện (proxy)* cho hoạt động kinh tế, đặc biệt ở nơi thiếu số liệu GDP chi tiết.
"""),
        ("2. Cách đọc bản đồ",
         """
* **Màu:** đen/nâu = tối; cam/vàng = sáng vừa; trắng = rất sáng. Ô gần như không sáng được làm mờ để nổi bật vùng có hoạt động.
* **Thang màu:** *Tuyến tính* giữ đúng tỷ lệ nhưng vùng ven đô dễ bị tối; *Căn bậc hai* và *Logarit* kéo sáng vùng thấp để thấy cấu trúc đô thị. Chú ý chú giải: vị trí các mốc màu thay đổi theo thang.
* **Độ đậm / Ẩn ô không sáng:** điều chỉnh để nhìn nền bản đồ bên dưới.
* **Viền Top 10:** viền xanh lơ quanh 10 ô sáng nhất (điểm nóng).
* **Nút lớp (góc phải):** đổi nền *Tối / Vệ tinh / Sáng*, bật/tắt lưới, ranh giới. Có nút toàn màn hình, tọa độ chuột và bản đồ nhỏ.
"""),
        ("3. Cách đọc Đầu dò (tooltip)",
         """
Rê chuột vào một ô để xem:
* **ID ô lưới / Diện tích:** ô sát ranh giới bị cắt nên nhỏ hơn ô đầy đủ — khi hồi quy nên dùng diện tích làm trọng số.
* **Cường độ NTL:** trung bình có trọng số theo tỷ lệ phủ điểm ảnh.
* **So với mức TB địa phương:** 2.0× nghĩa là sáng gấp đôi trung bình (theo diện tích) của địa phương.
* **Thứ hạng / Phân vị:** #1 là ô sáng nhất; P90 nghĩa là sáng hơn 90% số ô.
* **Tỷ trọng tổng ánh sáng:** phần trăm tổng SOL của địa phương nằm trong ô này.
* **Ước lượng Kinh tế (Global):** phân nhóm theo ngưỡng bức xạ chung toàn cầu (bảng bên dưới).
* **Vị thế Nội bộ (Local):** Top 25% / trung bình / Bottom 25% so với các ô còn lại **trong cùng địa phương**.
"""),
        ("4. Bảng ngưỡng phân loại (Global)", "__TABLE__"),
        ("5. MAUP và vì sao dùng lưới",
         """
* **MAUP** (Modifiable Areal Unit Problem): kết quả thống kê đổi khi đổi cách vẽ ranh giới. Phường/xã to nhỏ rất khác nhau nên dễ gây thiên lệch.
* **Lưới đều {s}×{s} m** cho đơn vị không gian thống nhất; lưới căn theo bội số {s} m nên **ghép được giữa các địa phương**.
* **Đánh đổi:** lưới càng mịn thì càng nhiều ô nhưng thông tin gốc không tăng thêm (VIIRS ~463 m). Lưới ≥ 1000 m thường ổn hơn cho hồi quy; thử nhiều độ phân giải để kiểm tra độ vững (robustness).
"""),
        ("6. Dùng CSV trong nghiên cứu", "__CODE__"),
        ("7. Hạn chế cần biết",
         """
* NTL là **proxy**, không phải GDP: khu công nghiệp nặng, đèn chiếu sáng công cộng dày, sân bay, cảng có thể sáng hơn mức hoạt động kinh tế thực.
* Nông thôn/khu thương mại ít đèn (hoặc dùng điện ít) có thể bị **đánh giá thấp**.
* **Hiệu ứng lan sáng (blooming):** ánh sáng tràn sang mặt nước/ô lân cận.
* **Giá trị âm** do nhiễu cảm biến đã đưa về 0. Ngưỡng phân loại là **tham khảo**, không phải chuẩn chính thức.
* Ô biên nhỏ hơn ô đầy đủ → dùng `area_km2` để lọc hoặc đặt trọng số.
"""),
    ],
    "en": [
        ("1. What is NTL and how is it measured?",
         """
* **NTL (Nighttime Lights)** is light emitted at night, measured monthly by the NOAA **VIIRS/DNB** satellite sensor.
* **Unit:** nW/cm²/sr (nanowatts per cm² per steradian) — a *radiance*, not a count of lamps.
* **Data used:** `avg_rad` from the stray-light-corrected product. For **{y}** the tool takes the **median** of monthly images to damp clouds, moonlight and fires.
* **Why economics?** Brighter places usually have more people, commerce, industry and infrastructure, so NTL is a *proxy* for economic activity, especially where granular GDP data are missing.
"""),
        ("2. Reading the map",
         """
* **Color:** black/brown = dark; orange/yellow = moderate; white = very bright. Nearly unlit cells are faded so active areas stand out.
* **Color scale:** *Linear* keeps true proportions but peri-urban areas look dark; *Square root* and *Logarithmic* lift low values to reveal urban structure. Check the legend: color stops move with the scale.
* **Opacity / Hide unlit cells:** adjust to see the base map underneath.
* **Outline Top 10:** cyan outlines around the 10 brightest cells (hotspots).
* **Layer control (top right):** switch *Dark / Satellite / Light* base maps, toggle grid and boundary. Fullscreen, mouse coordinates and a mini-map are included.
"""),
        ("3. Reading the tooltip",
         """
Hover over a cell to see:
* **Grid ID / Area:** cells on the border are clipped and smaller than full cells — use area as a weight in regressions.
* **NTL intensity:** mean weighted by fractional pixel coverage.
* **Versus area average:** 2.0× means twice the (area-weighted) average of the locality.
* **Rank / Percentile:** #1 is the brightest cell; P90 means brighter than 90% of cells.
* **Share of total light:** percent of the locality's total SOL located in this cell.
* **Economic Proxy (Global):** class from global radiance thresholds (table below).
* **Internal Status (Local):** Top 25% / average / Bottom 25% relative to other cells **in the same locality**.
"""),
        ("4. Classification thresholds (Global)", "__TABLE__"),
        ("5. MAUP and why a grid",
         """
* **MAUP** (Modifiable Areal Unit Problem): statistical results change when boundaries are redrawn. Wards/communes vary wildly in size, creating bias.
* A **{s}×{s} m grid** gives uniform spatial units; it is snapped to multiples of {s} m so it **can be merged across localities**.
* **Trade-off:** a finer grid has more cells but no extra information (VIIRS ~463 m). Grids ≥ 1000 m are usually safer for regressions; test several resolutions for robustness.
"""),
        ("6. Using the CSV in research", "__CODE__"),
        ("7. Limitations to keep in mind",
         """
* NTL is a **proxy**, not GDP: heavy industry, dense public lighting, airports and ports can be brighter than their economic activity.
* Rural or low-light commercial areas can be **under-estimated**.
* **Blooming:** light spills onto water or neighbouring cells.
* **Negative values** from sensor noise are set to 0. Class thresholds are **indicative**, not an official standard.
* Border cells are smaller than full cells → filter or weight with `area_km2`.
"""),
    ],
}

# Hướng dẫn ngưỡng (diễn giải) — theo thứ tự nhóm 1..5
CLASS_NOTES = {
    "vi": ["Trung tâm thương mại/dịch vụ, khu công nghiệp sáng mạnh", "Lõi đô thị, dân cư đông đúc",
           "Vành đai đô thị, ngoại ô đang phát triển", "Ven đô, hoạt động kinh tế thấp", "Đất trống, nông-lâm nghiệp, mặt nước"],
    "en": ["Commercial/services hubs, brightly lit industry", "Urban core, dense residential",
           "Urban fringe, developing suburbs", "Peri-urban, low economic activity", "Open land, farm/forest, water"],
}
THRESH_TEXT = [">= 40", "15 - 40", "5 - 15", "> 0 - 5", "0"]

CODE_SNIPPET = '''# Python (pandas + statsmodels)
import pandas as pd
import statsmodels.formula.api as smf

df = pd.read_csv("your_file.csv")
# Bỏ/giảm trọng số ô biên nhỏ  |  drop small border cells
df = df[df["area_km2"] >= 0.5 * (df["cell_size_m"] / 1000) ** 2]

merged = df.merge(your_data, on="grid_id")      # hoặc ghép theo tọa độ tâm ô
res = smf.wls("ln_outcome ~ ntl_log", data=merged,
              weights=merged["area_km2"]).fit(cov_type="HC1")
print(res.summary())
# Kiểm tra tự tương quan không gian: esda.Moran(res.resid, w)  (cột centroid_x/y)

* Stata:  gen ln_ntl = ln(ntl_mean + 1)
*         reg ln_outcome ln_ntl [aweight = area_km2], vce(robust)
'''

LANG = "vi"  # được cập nhật ngay sau khi người dùng chọn ngôn ngữ

# Ngôn ngữ phải được chọn trước mọi widget khác
with st.sidebar:
    lang_choice = st.radio("🌐 Language / Ngôn ngữ", ["Tiếng Việt", "English"], key="lang_choice")
LANG = "vi" if lang_choice == "Tiếng Việt" else "en"
L = TEXT[LANG]


def fill(text, **kw):
    for k, v in kw.items():
        text = text.replace("{" + k + "}", str(v))
    return text


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


def local_labels(values: np.ndarray, q25: float, q75: float, lang_pack):
    r = lang_pack["rank"]
    return np.select(
        [values <= 0, values >= q75, values <= q25], [r[3], r[0], r[1]], default=r[2]
    )


def gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, dtype=float))
    n, total = len(x), x.sum()
    if n == 0 or total <= 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * np.sum(idx * x)) / (n * total) - (n + 1) / n)


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


# ==========================================
# 5. SIDEBAR (CASCADING, TÊN SẠCH)
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
        L["country"], countries, format_func=lambda c: country_label(c, LANG), key="country"
    )

    states = subdirs(os.path.join(BASE_DATA_DIR, sel_country))
    if not states:
        st.warning(L["no_state"])
        st.stop()
    sel_state = st.selectbox(L["state"], states, format_func=clean_state, key=f"state_{sel_country}")

    counties = list_counties(sel_country, sel_state)
    if not counties:
        st.warning(L["no_county"])
        st.stop()
    sel_county_file = st.selectbox(
        L["county"], list(counties.keys()), format_func=lambda f: counties[f],
        key=f"county_{sel_country}_{sel_state}",
    )
    sel_county = counties[sel_county_file]
    file_path = os.path.join(BASE_DATA_DIR, sel_country, sel_state, sel_county_file)
    st.caption(f"📍 {country_label(sel_country, LANG)} › {clean_state(sel_state)} › {sel_county}")

    st.markdown("---")
    st.header(L["sb_analytic"])
    cell_size = st.slider(L["cell"], min_value=500, max_value=5000, value=500, step=500)
    year = st.selectbox(L["year"], YEARS, index=len(YEARS) - 2)
    st.markdown("---")
    run_btn = st.button(L["run"], type="primary", use_container_width=True, disabled=not gee_ok)


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
place = f"{country_disp} › {state_disp} › {district}"

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
px_per_cell = round((size / GEE_SCALE_M) ** 2, 1)

st.markdown(f"#### 📍 {place} &nbsp;·&nbsp; {yr} &nbsp;·&nbsp; {size} m")

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric(L["m_cells"], f"{n:,}")
c2.metric(L["m_mean"], f"{w_mean:.2f}")
c3.metric(L["m_max"], f"{ntl.max():.2f}")
c4.metric(L["m_sol"], f"{sol:,.1f}")
c5.metric(L["m_area"], f"{area.sum():,.1f} km²")
c6.metric(L["m_lit"], f"{(ntl > 0).mean() * 100:.0f}%")

tab_map, tab_data, tab_guide = st.tabs([L["tab_map"], L["tab_data"], L["tab_guide"]])

# ==========================================
# 8. TAB BẢN ĐỒ
# ==========================================
with tab_map:
    cA, cB, cC, cD = st.columns([2.2, 2, 1.3, 1.3])
    scale_mode = cA.radio(
        L["scale"], ["linear", "sqrt", "log"], index=1, horizontal=True,
        format_func=lambda k: L["scale_names"][k], key="scale_mode",
    )
    opacity = cB.slider(L["opacity"], 0.3, 1.0, 0.85, 0.05, key="opacity")
    hide0 = cC.toggle(L["hide0"], value=False, key="hide0")
    hl_top = cD.toggle(L["hl"], value=True, key="hl_top")

    disp = grid_utm.to_crs(epsg=4326)[["grid_id", "geometry"]].copy()
    disp["grid_id_str"] = disp["grid_id"].astype(str)
    disp["area_km2_str"] = [f"{a:.3f} km²" for a in area]
    disp["ntl_mean"] = np.round(ntl, 2)
    disp["ratio_str"] = [f"{r:.2f}×" for r in ratio]
    disp["rank_str"] = [f"#{r:,} / {n:,}" for r in rank]
    disp["pct_str"] = [f"P{p:.0f}" for p in pctile]
    disp["share_str"] = [f"{s:.3f}%" for s in share]
    disp["dev_level"] = np.array(L["dev"])[codes]
    disp["local_rank"] = local_labels(ntl, q25, q75, L)

    geo = disp.copy()
    if hide0:
        geo = geo[geo["ntl_mean"] > 0]
    if len(geo) > RENDER_CAP:
        st.warning(L["render_cap"].format(n=len(geo), c=RENDER_CAP))
        geo = geo.nlargest(RENDER_CAP, "ntl_mean")
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
    m.fit_bounds([[bminy, bminx], [bmaxy, bmaxx]])

    vmax = float(ntl.max())
    vmax = vmax if vmax > 0.1 else 1.0
    colormap = make_colormap(scale_mode, vmax, L["caption"].format(y=yr))

    def style_fn(feature):
        v = float(feature["properties"].get("ntl_mean") or 0.0)
        v = min(max(v, 0.0), vmax)
        if v <= 0:
            fo = 0.10
        elif v < vmax * 0.02:
            fo = opacity * 0.55
        else:
            fo = opacity
        return {"fillColor": colormap(v), "color": "#444444", "weight": 0.25, "fillOpacity": fo}

    folium.GeoJson(
        geo[["grid_id_str", "area_km2_str", "ntl_mean", "ratio_str", "rank_str", "pct_str",
             "share_str", "dev_level", "local_rank", "geometry"]],
        name=L["layer_grid"],
        style_function=style_fn,
        highlight_function=lambda f: {"weight": 2.2, "color": "#00e5ff", "fillOpacity": 0.97},
        tooltip=folium.GeoJsonTooltip(
            fields=["grid_id_str", "area_km2_str", "ntl_mean", "ratio_str", "rank_str", "pct_str",
                    "share_str", "dev_level", "local_rank"],
            aliases=L["aliases"],
            localize=True,
            sticky=True,
            style=(
                "background-color:rgba(12,12,16,0.94);color:#ffffff;font-family:Inter,Arial,sans-serif;"
                "font-size:12.5px;padding:12px 14px;border-radius:8px;border:1px solid #666666;"
                "box-shadow:0 4px 14px rgba(0,0,0,0.6);"
            ),
        ),
    ).add_to(m)

    if hl_top and ntl.max() > 0:
        top_geo = disp.nlargest(10, "ntl_mean")[["geometry"]]
        folium.GeoJson(
            top_geo, name=L["layer_top"], interactive=False,
            style_function=lambda _: {"fill": False, "color": "#00e5ff", "weight": 2.6},
        ).add_to(m)

    # Ranh giới: hào quang mờ + nét trắng sắc (chỉ Polygon, không Marker)
    bclean = bw[bw.geometry.type.isin(["Polygon", "MultiPolygon"])]
    bgroup = folium.FeatureGroup(name=L["layer_bound"], show=True)
    folium.GeoJson(bclean, interactive=False,
                   style_function=lambda _: {"fill": False, "color": "#ffffff", "weight": 8, "opacity": 0.14}).add_to(bgroup)
    folium.GeoJson(bclean, interactive=False,
                   style_function=lambda _: {"fill": False, "color": "#ffffff", "weight": 2.2, "opacity": 1}).add_to(bgroup)
    bgroup.add_to(m)

    colormap.add_to(m)
    Fullscreen(position="topleft").add_to(m)
    MousePosition(position="bottomleft", num_digits=5, prefix="Lat/Lon").add_to(m)
    MiniMap(toggle_display=True, minimized=True, position="bottomright", tile_layer="CartoDB dark_matter").add_to(m)
    folium.LayerControl(collapsed=True, position="topright").add_to(m)

    map_key = f"ntl_map_{LANG}_{scale_mode}_{opacity}_{hide0}_{hl_top}"
    st_folium(m, use_container_width=True, height=640, returned_objects=[], key=map_key)

# ==========================================
# 9. TAB DỮ LIỆU
# ==========================================
cent_utm = grid_utm.geometry.centroid
cent_wgs = gpd.GeoSeries(cent_utm, crs=grid_utm.crs).to_crs(epsg=4326)
export_df = pd.DataFrame(
    {
        "iso3": res["iso3"],
        "country": country_label(res["country_raw"], "en"),
        "province": state_disp,
        "district": district,
        "grid_id": grid_utm["grid_id"].to_numpy(dtype="int64"),
        "year": yr,
        "cell_size_m": size,
        "centroid_lon": np.round(cent_wgs.x.to_numpy(), 6),
        "centroid_lat": np.round(cent_wgs.y.to_numpy(), 6),
        f"centroid_x_epsg{epsg}": np.round(cent_utm.x.to_numpy(), 1),
        f"centroid_y_epsg{epsg}": np.round(cent_utm.y.to_numpy(), 1),
        "area_km2": np.round(area, 6),
        "ntl_mean": np.round(ntl, 4),
        "ntl_sol": np.round(sol_cell, 4),
        "ntl_log": np.round(np.log1p(ntl), 6),
        "ntl_rank": rank,
        "ntl_pctile": pctile,
        "ntl_vs_mean": np.round(ratio, 4),
        "sol_share_pct": np.round(share, 5),
        "ntl_class": codes + 1,
    }
)

with tab_data:
    st.caption(L["csv_note"])
    if size < 1000:
        st.warning(L["quality_warn"].format(s=size, px=px_per_cell))

    col_l, col_r = st.columns(2)

    # --- Thông tin chung ---
    with col_l:
        st.subheader(L["sec_overview"])
        ov = pd.DataFrame(
            {
                L["ov_cols"][0]: L["ov_rows"],
                L["ov_cols"][1]: [place, f"{yr} / {size} m", f"{n:,}", f"{area.sum():,.2f} km²", res["ts"]],
            }
        )
        st.dataframe(ov, hide_index=True, use_container_width=True)

    # --- Thống kê ---
    with col_r:
        st.subheader(L["sec_stats"])
        top10_n = max(1, int(math.ceil(n * 0.10)))
        top10_share = float(np.sort(sol_cell)[::-1][:top10_n].sum() / sol * 100) if sol > 0 else 0.0
        stat_vals = [
            f"{w_mean:.3f}", f"{ntl.mean():.3f}", f"{np.median(ntl):.3f}", f"{ntl.std():.3f}",
            f"{ntl.min():.3f}", f"{q25:.3f}", f"{q75:.3f}",
            f"{np.quantile(ntl, 0.90):.3f}", f"{np.quantile(ntl, 0.99):.3f}", f"{ntl.max():.3f}",
            f"{gini(sol_cell):.3f}", f"{(ntl > 0).mean() * 100:.1f}%", f"{top10_share:.1f}%",
        ]
        st.dataframe(
            pd.DataFrame({L["stat_cols"][0]: L["stat_rows"], L["stat_cols"][1]: stat_vals}),
            hide_index=True, use_container_width=True, height=320,
        )

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
    st.dataframe(
        cls_tbl, hide_index=True, use_container_width=True,
        column_config={
            L["cls_cols"][3]: st.column_config.ProgressColumn(L["cls_cols"][3], min_value=0, max_value=100, format="%.1f%%"),
            L["cls_cols"][4]: st.column_config.ProgressColumn(L["cls_cols"][4], min_value=0, max_value=100, format="%.1f%%"),
            L["cls_cols"][5]: st.column_config.ProgressColumn(L["cls_cols"][5], min_value=0, max_value=100, format="%.1f%%"),
        },
    )

    # --- Histogram ---
    st.subheader(L["sec_hist"])
    edges = [-0.001, 0, 1, 2, 5, 10, 15, 25, 40, 80, np.inf]
    binned = pd.cut(ntl, bins=edges, labels=L["hist_bins"]).value_counts(sort=False)
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
    st.altair_chart(chart, use_container_width=True)

    # --- Top 10 ---
    st.subheader(L["sec_top"])
    top_cols = ["grid_id", "centroid_lon", "centroid_lat", "area_km2", "ntl_mean", "ntl_vs_mean",
                "sol_share_pct", "ntl_rank", "ntl_class"]
    st.dataframe(
        export_df.nlargest(10, "ntl_mean")[top_cols], hide_index=True, use_container_width=True,
        column_config={"ntl_mean": st.column_config.ProgressColumn("ntl_mean", min_value=0, max_value=float(vmax), format="%.2f")},
    )
    with st.expander(L["sec_full"]):
        st.dataframe(export_df.sort_values("ntl_mean", ascending=False).head(5000), hide_index=True, use_container_width=True)

    # --- Phương pháp ---
    st.subheader(L["sec_meta"])
    meta_vals = [
        fill(v, ds=GEE_DATASET, y=yr, s=size, e=epsg, px=px_per_cell) for v in L["meta_vals"]
    ]
    st.dataframe(
        pd.DataFrame({L["meta_cols"][0]: L["meta_rows"], L["meta_cols"][1]: meta_vals}),
        hide_index=True, use_container_width=True,
    )

    # --- Tải dữ liệu ---
    st.subheader(L["sec_dl"])
    slug = f"{slugify(district)}_NTL_{yr}_{size}m"
    d1, d2 = st.columns(2)
    d1.download_button(
        label=L["download"],
        data=export_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{slug}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True,
    )
    with d2:
        if st.toggle(L["prep_geo"], key="prep_geo"):
            geo_gdf = gpd.GeoDataFrame(
                export_df, geometry=gpd.GeoSeries(grid_utm.to_crs(epsg=4326).geometry.values, crs=4326)
            )
            st.download_button(
                label=L["download_geo"],
                data=geo_gdf.to_json().encode("utf-8"),
                file_name=f"{slug}.geojson",
                mime="application/geo+json",
                use_container_width=True,
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
                st.dataframe(gt, hide_index=True, use_container_width=True)
            elif body == "__CODE__":
                st.caption(L["g_code_title"])
                st.code(CODE_SNIPPET, language="python")
            else:
                st.markdown(fill(body, y=yr, s=size))
            if i == 4 and size < 1000:
                st.warning(L["quality_warn"].format(s=size, px=px_per_cell))
