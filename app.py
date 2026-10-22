import io
import math
import os
import tempfile
import zipfile
import branca.colormap as cm
import ee
import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import requests
import shapely
import streamlit as st
from streamlit_folium import st_folium

try:
    import pycountry
except Exception:  # pragma: no cover
    pycountry = None

# ==========================================
# 0. CONFIG
# ==========================================
st.set_page_config(
    page_title="NTL Data Extractor",
    page_icon="🌙",
    layout="wide",
)

BASE_DATA_DIR = "data/gadm41_VNM_gpkg"
GEE_DATASET = "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"
GEE_SCALE_M = 463.83          # độ phân giải gốc VIIRS (~15 arc-sec)
MAX_CELLS = 150_000           # trần số ô lưới để tránh treo máy chủ
YEARS = list(range(2014, 2026))

# ==========================================
# 1. SONG NGỮ
# ==========================================
TEXT = {
    "vi": {
        "title": "🌙 Công cụ trích xuất Ánh sáng ban đêm (NTL)",
        "subtitle": "Kiến trúc: tải raster từ Cloud về máy chủ + động cơ C/C++ (`exactextract`). "
                    "Thiết kế cho Kinh tế lượng không gian (chống lỗi MAUP, độ phân giải gốc ~463m).",
        "lang_label": "🌐 Ngôn ngữ / Language",
        "sb_spatial": "1. Tham số không gian",
        "country": "Quốc gia",
        "state": "Tỉnh / Bang",
        "county": "Quận / Huyện",
        "sb_analytic": "2. Tham số phân tích",
        "cell": "Độ phân giải lưới (mét)",
        "year": "Năm phân tích",
        "run": "🚀 Chạy phân tích",
        "no_data": "⚠️ Không tìm thấy dữ liệu trong `{d}`. Hãy tạo cấu trúc: quốc gia/tỉnh/huyện.geojson.",
        "no_state": "Quốc gia này chưa có thư mục tỉnh/bang.",
        "no_county": "Tỉnh/bang này chưa có file .geojson.",
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
        "tab_map": "🗺️ Bản đồ",
        "tab_data": "📋 Dữ liệu",
        "tab_guide": "📖 Hướng dẫn đọc",
        "caption": "Cường độ ánh sáng ban đêm ({y}) - nW/cm²/sr",
        "aliases": ["🔢 ID Ô lưới:", "📐 Diện tích đo lường:", "💡 Cường độ NTL (nW/cm²/sr):",
                    "🏙️ Ước lượng Kinh tế (Global):", "📊 Vị thế Nội bộ (Local):"],
        "dev": ["Thương mại/Dịch vụ (Mật độ siêu cao)", "Đô thị lõi/Khu dân cư đông đúc",
                "Vành đai đô thị/Ngoại ô phát triển", "Khu vực ven đô/Hoạt động kinh tế thấp",
                "Không gian mở/Khu vực thiếu sáng"],
        "rank": ["Top 25% (Tâm điểm kinh tế của địa phương)", "Bottom 25% (Vùng trũng của địa phương)",
                 "Mức phát triển trung bình của địa phương", "Không có ánh sáng đáng kể"],
        "top10": "Top 10 ô sáng nhất",
        "download": "⬇️ Tải dữ liệu hồi quy không gian (CSV)",
        "guide_title": "### 📊 Hướng dẫn đọc dữ liệu (cho nhà phân tích / đầu tư)",
        "guide": """
Công cụ chuyển ảnh vệ tinh ban đêm thành chỉ báo kinh tế không gian.

* **Cường độ NTL:** đo ánh sáng từ đèn đường, tòa nhà... Là *biến đại diện* (proxy) đáng tin cậy cho mức tập trung GDP và hạ tầng.
* **Khắc phục lỗi MAUP:** ranh giới phường/xã không đều gây nhiễu mô hình. Lưới **{s}×{s} m** chuẩn hóa đơn vị không gian để so sánh công bằng.
* **Đầu dò (Tooltip):** rê chuột vào một ô:
    * *Ước lượng Kinh tế (Global):* phân loại theo ngưỡng bức xạ chung toàn cầu.
    * *Vị thế Nội bộ (Local):* xếp hạng phân vị so với các ô khác trong cùng địa phương.
* **SOL (Sum of Lights):** tổng (NTL × diện tích), thường dùng làm biến giải thích trong hồi quy.
* **Lưu ý:** giá trị âm do nhiễu VIIRS đã được đưa về 0.
""",
        "csv_note": "CSV gồm tọa độ tâm ô (WGS84 & UTM), diện tích, NTL và metadata để chạy hồi quy.",
    },
    "en": {
        "title": "🌙 Nighttime Lights (NTL) Extraction Engine",
        "subtitle": "Architecture: Cloud-to-Local raster fetch + C/C++ engine (`exactextract`). "
                    "Built for Spatial Econometrics (MAUP-resistant, native ~463m resolution).",
        "lang_label": "🌐 Language / Ngôn ngữ",
        "sb_spatial": "1. Spatial Parameters",
        "country": "Country",
        "state": "State / Region",
        "county": "County / District",
        "sb_analytic": "2. Analytical Parameters",
        "cell": "Grid Resolution (meters)",
        "year": "Analysis Year",
        "run": "🚀 Execute Pipeline",
        "no_data": "⚠️ No data found in `{d}`. Create the structure: country/state/county.geojson.",
        "no_state": "This country has no state/region folders.",
        "no_county": "This state has no .geojson files.",
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
        "tab_map": "🗺️ Map",
        "tab_data": "📋 Data",
        "tab_guide": "📖 Reading Guide",
        "caption": "Nighttime Lights Intensity ({y}) - nW/cm²/sr",
        "aliases": ["🔢 Grid ID:", "📐 Survey Area:", "💡 NTL Intensity (nW/cm²/sr):",
                    "🏙️ Economic Proxy (Global):", "📊 Internal Status (Local):"],
        "dev": ["Commercial/Services (Ultra-high density)", "Urban Core/Dense Residential",
                "Urban Fringe/Developing Suburb", "Peri-urban/Low Economic Activity",
                "Open Space/Unlit Area"],
        "rank": ["Top 25% (Economic Hotspot of the area)", "Bottom 25% (Economic Coldspot)",
                 "Area-average development", "No significant light"],
        "top10": "Top 10 brightest cells",
        "download": "⬇️ Download Data for Spatial Econometrics (CSV)",
        "guide_title": "### 📊 Spatial Econometrics Insights (for analysts / investors)",
        "guide": """
This tool converts nighttime satellite imagery into spatial economic indicators.

* **NTL Intensity:** light from streetlights and buildings. A reliable *proxy variable* for GDP concentration and infrastructure.
* **Solving MAUP:** administrative units have irregular sizes and bias statistics. A **{s}×{s} m** grid normalizes spatial units for unbiased regression.
* **Tooltip:** hover over a cell:
    * *Economic Proxy (Global):* class based on global radiance thresholds.
    * *Internal Status (Local):* quantile rank versus other cells in the same area.
* **SOL (Sum of Lights):** sum of (NTL × area), a common regressor.
* **Note:** negative values caused by VIIRS noise are floored at 0.
""",
        "csv_note": "CSV includes cell centroids (WGS84 & UTM), area, NTL and metadata for regression.",
    },
}

# Ngôn ngữ phải được chọn trước mọi widget khác
with st.sidebar:
    lang_choice = st.radio("🌐 Language / Ngôn ngữ", ["Tiếng Việt", "English"], key="lang_choice")
L = TEXT["vi" if lang_choice == "Tiếng Việt" else "en"]

# ==========================================
# 2. GOOGLE EARTH ENGINE INIT
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
# 3. TIỆN ÍCH
# ==========================================
def get_dynamic_utm_crs(lon: float, lat: float) -> int:
    zone = min(60, max(1, math.floor((lon + 180) / 6) + 1))
    return (32600 if lat >= 0 else 32700) + zone


def subdirs(path):
    if not os.path.isdir(path):
        return []
    return sorted(d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)))


def country_label(code):
    if pycountry is not None:
        try:
            c = pycountry.countries.get(alpha_3=code.upper())
            if c:
                return f"{c.name} ({code})"
        except Exception:  # noqa: BLE001
            pass
    return code


def list_counties(country, state):
    p = os.path.join(BASE_DATA_DIR, country, state)
    if not os.path.isdir(p):
        return {}
    files = sorted(f for f in os.listdir(p) if f.lower().endswith(".geojson"))
    return {f[: -len(".geojson")].replace("_", " "): f for f in files}


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
    if n_est > MAX_CELLS * 4:  # trần thô trước khi clip (bounding box lớn hơn lãnh thổ)
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
    """Tải GeoTIFF NTL trung vị năm `year` trong bbox (WGS84). Kết quả được cache theo (bbox, năm)."""
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


def classify(values: np.ndarray, q25: float, q75: float, lang_pack):
    dev_lbl, rank_lbl = lang_pack["dev"], lang_pack["rank"]
    dev = np.select(
        [values >= 40, values >= 15, values >= 5, values > 0],
        dev_lbl[:4],
        default=dev_lbl[4],
    )
    rank = np.select(
        [values <= 0, values >= q75, values <= q25],
        [rank_lbl[3], rank_lbl[0], rank_lbl[1]],
        default=rank_lbl[2],
    )
    return dev, rank


# ==========================================
# 4. SIDEBAR (CASCADING)
# ==========================================
st.title(L["title"])
st.markdown(L["subtitle"])

with st.sidebar:
    st.header(L["sb_spatial"])
    countries = subdirs(BASE_DATA_DIR)
    if not countries:
        st.error(L["no_data"].format(d=BASE_DATA_DIR))
        st.stop()

    sel_country = st.selectbox(L["country"], countries, format_func=country_label, key="country")

    states = subdirs(os.path.join(BASE_DATA_DIR, sel_country))
    if not states:
        st.warning(L["no_state"])
        st.stop()
    sel_state = st.selectbox(L["state"], states, key=f"state_{sel_country}")

    counties = list_counties(sel_country, sel_state)
    if not counties:
        st.warning(L["no_county"])
        st.stop()
    sel_county = st.selectbox(L["county"], list(counties.keys()), key=f"county_{sel_country}_{sel_state}")
    file_path = os.path.join(BASE_DATA_DIR, sel_country, sel_state, counties[sel_county])

    st.markdown("---")
    st.header(L["sb_analytic"])
    cell_size = st.slider(L["cell"], min_value=500, max_value=5000, value=500, step=500)
    year = st.selectbox(L["year"], YEARS, index=len(YEARS) - 2)
    st.markdown("---")
    run_btn = st.button(L["run"], type="primary", use_container_width=True, disabled=not gee_ok)

# ==========================================
# 5. PIPELINE (chỉ chạy khi bấm nút; kết quả lưu session_state)
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

            grid = grid.merge(stats, on="grid_id", how="left")
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
        "name": sel_county,
        "size": cell_size,
        "year": int(year),
    }


if run_btn:
    st.session_state["result"] = run_pipeline()

res = st.session_state.get("result")
if not res:
    st.info(L["idle"])
    st.stop()

# ==========================================
# 6. HIỂN THỊ KẾT QUẢ
# ==========================================
grid_utm = res["grid_utm"]
size, yr, name, epsg = res["size"], res["year"], res["name"], res["epsg"]

disp = grid_utm.to_crs(epsg=4326).copy()
disp["ntl_mean"] = pd.to_numeric(disp["ntl_mean"], errors="coerce").fillna(0.0).round(2)

vals = disp["ntl_mean"].to_numpy(dtype=float)
q25, q75 = float(np.quantile(vals, 0.25)), float(np.quantile(vals, 0.75))
disp["dev_level"], disp["local_rank"] = classify(vals, q25, q75, L)
disp["grid_id_str"] = disp["grid_id"].astype(str)
disp["area_km2_str"] = disp["area_km2"].round(3).map(lambda v: f"{v:.3f} km²")

# --- Chỉ số tổng hợp ---
area = grid_utm["area_km2"].to_numpy(dtype=float)
ntl = grid_utm["ntl_mean"].to_numpy(dtype=float)
sol = float(np.sum(ntl * area))
w_mean = float(np.average(ntl, weights=area)) if area.sum() > 0 else 0.0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(L["m_cells"], f"{len(grid_utm):,}")
c2.metric(L["m_mean"], f"{w_mean:.2f}")
c3.metric(L["m_max"], f"{ntl.max():.2f}")
c4.metric(L["m_sol"], f"{sol:,.1f}")
c5.metric(L["m_area"], f"{area.sum():,.1f} km²")

tab_map, tab_data, tab_guide = st.tabs([L["tab_map"], L["tab_data"], L["tab_guide"]])

# --- Bản đồ ---
with tab_map:
    bw = res["boundary_wgs"]
    bminx, bminy, bmaxx, bmaxy = bw.total_bounds
    m = folium.Map(
        location=[(bminy + bmaxy) / 2, (bminx + bmaxx) / 2],
        zoom_start=12,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, HERE, Garmin",
    )
    m.fit_bounds([[bminy, bminx], [bmaxy, bmaxx]])

    vmax = float(ntl.max())
    vmax = vmax if vmax > 0.1 else 1.0
    colormap = cm.LinearColormap(
        colors=["#000000", "#804000", "#ffaa00", "#ffff00", "#ffffff"], vmin=0, vmax=vmax
    )
    colormap.caption = L["caption"].format(y=yr)

    geo = disp[["grid_id_str", "area_km2_str", "ntl_mean", "dev_level", "local_rank", "geometry"]]

    def style_fn(feature):
        v = feature["properties"].get("ntl_mean") or 0.0
        v = min(max(float(v), 0.0), vmax)
        return {
            "fillColor": colormap(v),
            "color": "#555555",
            "weight": 0.3,
            "fillOpacity": 0.8 if v > vmax * 0.1 else 0.25,
        }

    folium.GeoJson(
        geo,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=["grid_id_str", "area_km2_str", "ntl_mean", "dev_level", "local_rank"],
            aliases=L["aliases"],
            localize=True,
            style=(
                "background-color:#111111;color:#ffffff;font-family:arial;font-size:13px;"
                "padding:12px;border-radius:6px;border:1px solid #777777;"
                "box-shadow:2px 2px 8px rgba(0,0,0,0.5);"
            ),
        ),
    ).add_to(m)

    # Ranh giới trắng trên cùng (chỉ Polygon, không có Marker)
    bclean = bw[bw.geometry.type.isin(["Polygon", "MultiPolygon"])]
    folium.GeoJson(
        bclean,
        style_function=lambda _: {"fill": False, "color": "#ffffff", "weight": 3},
        interactive=False,
    ).add_to(m)
    colormap.add_to(m)

    st_folium(m, use_container_width=True, height=620, returned_objects=[], key="ntl_map")

# --- Bảng dữ liệu + CSV ---
cent_utm = grid_utm.geometry.centroid
cent_wgs = gpd.GeoSeries(cent_utm, crs=grid_utm.crs).to_crs(epsg=4326)
export_df = pd.DataFrame(
    {
        "grid_id": grid_utm["grid_id"].astype("int64"),
        "district": name,
        "year": yr,
        "cell_size_m": size,
        "centroid_lon": cent_wgs.x.round(6),
        "centroid_lat": cent_wgs.y.round(6),
        f"centroid_x_epsg{epsg}": cent_utm.x.round(1),
        f"centroid_y_epsg{epsg}": cent_utm.y.round(1),
        "area_km2": grid_utm["area_km2"].round(6),
        "ntl_mean": grid_utm["ntl_mean"].round(4),
    }
)
export_df["ntl_sol"] = (export_df["ntl_mean"] * export_df["area_km2"]).round(4)
export_df["ntl_log"] = np.log1p(export_df["ntl_mean"]).round(6)  # tiện cho hồi quy log

with tab_data:
    st.caption(L["csv_note"])
    st.subheader(L["top10"])
    st.dataframe(export_df.nlargest(10, "ntl_mean"), use_container_width=True, hide_index=True)
    st.download_button(
        label=L["download"],
        data=export_df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{name.replace(' ', '_')}_NTL_{yr}_{size}m.csv",
        mime="text/csv",
        type="primary",
    )

with tab_guide:
    st.markdown(L["guide_title"])
    st.info(L["guide"].format(s=size))
