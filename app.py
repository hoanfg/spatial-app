import streamlit as st
import ee
import geemap.foliumap as geemap
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
import folium
from streamlit_folium import st_folium
import math
import os
import requests
import rasterio
from exactextract import exact_extract
import tempfile
import pycountry

# ==========================================
# 0. PAGE CONFIGURATION & GEE INIT
# ==========================================
st.set_page_config(page_title="NTL Data Extractor (Global Scale)", layout="wide")

@st.cache_resource
def init_gee():
    try:
        ee.Initialize()
        return True
    except Exception as e:
        st.error("Google Earth Engine initialization failed. Check your authentication.")
        return False

is_gee_ready = init_gee()

def get_dynamic_utm_crs(lon, lat):
    """Calculate the correct UTM Zone EPSG code based on global Longitude/Latitude."""
    utm_zone = math.floor((lon + 180) / 6) + 1
    return 32600 + utm_zone if lat >= 0 else 32700 + utm_zone

# ==========================================
# 1. CURATED DATABASE CONFIGURATION
# ==========================================
# Danh sách các khu vực có sẵn trong "Kho dữ liệu tuyển chọn"
# Key là tên hiển thị, Value là đường dẫn file tĩnh trong thư mục dự án
CURATED_REGIONS = {
    "Vietnam - Binh Phuoc Province (ADM1)": "data/curated_boundaries/VNM_Binh_Phuoc.geojson",
    # Bạn tự tải và thêm các file GeoJSON khác vào thư mục này:
    # "USA - Harris County, Texas (ADM2)": "data/curated_boundaries/USA_Texas_Harris_County.geojson",
    # "France - Paris Region (ADM2)": "data/curated_boundaries/FRA_Ile_de_France.geojson"
}

st.title("Nighttime Lights (NTL) Extraction Engine")
st.markdown("""
**Architecture:** Cloud-to-Local Raster Fetch + C/C++ Engine (`exactextract`).
Designed for Econometric Spatial Analysis (MAUP-resistant 1000m resolution).
""")

# ==========================================
# 2. SIDEBAR PARAMETERS
# ==========================================
with st.sidebar:
    st.header("1. Spatial Parameters")
    
    # Lazy Loading: Chỉ nạp danh sách tên, không nạp dữ liệu
    selected_region_name = st.selectbox("Select Curated Region", list(CURATED_REGIONS.keys()))
    
    # Cho phép điều chỉnh lưới, nhưng khóa cứng mặc định ở 1000m chuẩn học thuật
    cell_size = st.slider("Grid Resolution (meters)", min_value=500, max_value=5000, value=1000, step=500)
    
    st.markdown("---")
    st.header("2. Temporal Parameters")
    year = st.selectbox("Select Year", list(range(2014, 2024)), index=8)
    
    run_btn = st.button("Execute Pipeline")

if run_btn:
    st.session_state['is_executed'] = True
    st.session_state['region_name'] = selected_region_name
    st.session_state['size'] = cell_size
    st.session_state['year'] = year

# ==========================================
# 3. CORE PIPELINE EXECUTION
# ==========================================
if st.session_state.get('is_executed', False):
    
    region_name = st.session_state['region_name']
    size = st.session_state['size']
    year = st.session_state['year']
    file_path = CURATED_REGIONS[region_name]
    
    # ---------------------------------------------------------
    # STATION 1: DATA LOADING & DYNAMIC GRIDDING (RAM-SAFE)
    # ---------------------------------------------------------
    with st.spinner("Station 1: Loading Static Boundary and Generating 1000m Grid..."):
        try:
            # Tải lười (Lazy Load): Chỉ đọc file của khu vực được chọn
            boundary = gpd.read_file(file_path)
            # Gom toàn bộ ranh giới thành 1 Polygon duy nhất (để gọi GEE cho nhẹ)
            boundary_union = gpd.GeoDataFrame(geometry=[boundary.unary_union], crs=boundary.crs)
            
            centroid_lon = boundary_union.geometry.centroid.x.iloc[0]
            centroid_lat = boundary_union.geometry.centroid.y.iloc[0]
            dynamic_epsg = get_dynamic_utm_crs(centroid_lon, centroid_lat)
            
            st.info(f"🌍 Auto-detected CRS: UTM Zone EPSG:{dynamic_epsg}")
            
            # Cắt lưới 1000m
            boundary_utm = boundary_union.to_crs(epsg=dynamic_epsg)
            minx, miny, maxx, maxy = boundary_utm.total_bounds
            x_coords = np.arange(minx, maxx, size)
            y_coords = np.arange(miny, maxy, size)
            
            grid_cells = [Polygon([(x, y), (x + size, y), (x + size, y + size), (x, y + size)]) 
                          for x in x_coords for y in y_coords]
                    
            raw_grid = gpd.GeoDataFrame({'geometry': grid_cells}, crs=boundary_utm.crs)
            clipped_grid = gpd.clip(raw_grid, boundary_utm)
            
            # Tính diện tích thật (km2) để kiểm chứng MAUP
            clipped_grid['area_km2'] = clipped_grid.geometry.area / 1e6
            
            st.success(f"✅ Generated {len(clipped_grid)} grid cells at {size}m resolution.")
            
        except Exception as e:
            st.error(f"Error at Station 1 (Data Loading): {e}")
            st.stop()

    # ---------------------------------------------------------
    # STATION 2: CLOUD-TO-LOCAL RASTER FETCH (BYPASS API LIMITS)
    # ---------------------------------------------------------
    with st.spinner("Station 2: Fetching 1000m NTL Raster from Google Earth Engine (1 Request Only)..."):
        try:
            # Chuyển Bounding Box của ranh giới sang định dạng GEE
            bounds = boundary_union.geometry.bounds.iloc[0]
            ee_roi = ee.Geometry.Rectangle([bounds['minx'], bounds['miny'], bounds['maxx'], bounds['maxy']])
            
            # Khởi tạo Image Collection VIIRS
            dataset = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG") \
                        .filterDate(f"{year}-01-01", f"{year}-12-31") \
                        .select('avg_rad') \
                        .median() \
                        .clip(ee_roi)
            
            # Lấy URL tải trực tiếp file GeoTIFF (Khóa cứng scale=1000)
            download_url = dataset.getDownloadUrl({
                'scale': 1000, 
                'crs': 'EPSG:4326', # Giữ nguyên độ phân giải góc của vệ tinh lúc tải
                'region': ee_roi,
                'format': 'GEO_TIFF'
            })
            
            # Tải ảnh về RAM (Tempfile) thay vì lưu vào ổ cứng
            response = requests.get(download_url)
            temp_tif = tempfile.NamedTemporaryFile(delete=False, suffix='.tif')
            temp_tif.write(response.content)
            temp_tif.close()
            
            st.success("✅ Raster fetched successfully (Network API bypassed).")

        except Exception as e:
            st.error(f"Error at Station 2 (GEE Fetch): {e}. This might happen if the region is larger than 32MB GEE Limit.")
            st.stop()

    # ---------------------------------------------------------
    # STATION 3: LOCAL C/C++ COMPUTE (EXACTEXTRACT)
    # ---------------------------------------------------------
    with st.spinner("Station 3: Calculating Fractional Pixel Coverage (C/C++ Engine)..."):
        try:
            # Chuyển lưới từ UTM về lại EPSG:4326 để khớp với ảnh TIFF vừa tải
            grid_wgs84 = clipped_grid.to_crs(epsg=4326)
            
            # Sử dụng exactextract để tính NTL trung bình dựa trên fraction (tỷ lệ diện tích)
            stats = exact_extract(temp_tif.name, grid_wgs84, ['mean'])
            
            # Gắn kết quả vào GeoDataFrame gốc
            clipped_grid['ntl_mean'] = [s['mean'] if s['mean'] is not None else 0 for s in stats]
            
            # Xóa file rác
            os.remove(temp_tif.name)
            
            st.success("✅ Econometric Data Extraction complete (MAUP resistant).")
            
        except Exception as e:
            st.error(f"Error at Station 3 (Computation): {e}")
            st.stop()

    # ---------------------------------------------------------
    # STATION 4: VISUALIZATION & EXPORT
    # ---------------------------------------------------------
    with st.spinner("Station 4: Rendering Map..."):
        # Tính toán vĩ độ, kinh độ trung tâm cho Map
        center_lat = boundary_union.geometry.centroid.y.iloc[0]
        center_lon = boundary_union.geometry.centroid.x.iloc[0]
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9, tiles="CartoDB positron")
        
        # Thêm lưới Heatmap (Chuyển về EPSG 4326 để hiển thị trên web)
        display_grid = clipped_grid.to_crs(epsg=4326)
        
        # Chỉ vẽ các ô có ánh sáng (NTL > 0) để web đỡ lag
        display_grid = display_grid[display_grid['ntl_mean'] > 0.1]
        
        folium.Choropleth(
            geo_data=display_grid,
            data=display_grid,
            columns=['geometry', 'ntl_mean'],
            key_on='feature.id',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.1,
            legend_name='NTL Mean (Fractional Coverage)'
        ).add_to(m)

        st_data = st_folium(m, width=900, height=500)
        
        # Xuất file CSV cho phần mềm Stata/R
        csv_data = clipped_grid.drop(columns=['geometry']).to_csv(index=False)
        st.download_button(
            label="Download Data for Spatial Econometrics (CSV)",
            data=csv_data,
            file_name=f"{selected_region_name.split()[0]}_NTL_{year}_{size}m.csv",
            mime="text/csv"
        )
