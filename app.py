import streamlit as st
import ee
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
import folium
from streamlit_folium import st_folium
import math
import os
import requests
import tempfile

# ==========================================
# 0. PAGE CONFIGURATION & GEE INIT
# ==========================================
st.set_page_config(page_title="NTL Data Extractor (Global Scale)", layout="wide")

def init_gee():
    try:
        # Nếu đang chạy trên Streamlit Cloud
        if "ee_credentials" in st.secrets:
            # Lấy email và khóa trực tiếp từ Secrets
            service_account_email = st.secrets["ee_credentials"]["client_email"]
            private_key = st.secrets["ee_credentials"]["private_key"]
            
            # Xử lý ký tự xuống dòng (quan trọng trên Cloud)
            if '\\n' in private_key:
                private_key = private_key.replace('\\n', '\n')
            
            # Sử dụng chính hàm xác thực gốc của Earth Engine
            credentials = ee.ServiceAccountCredentials(service_account_email, key_data=private_key)
            
            # Truyền credentials và bắt buộc truyền tham số project (như tài liệu yêu cầu)
            project_id = st.secrets["ee_credentials"]["project_id"]
            ee.Initialize(credentials, project=project_id)
        else:
            # Nếu chạy trên máy tính cá nhân
            ee.Initialize()
        return True
    except Exception as e:
        st.error(f"Google Earth Engine initialization failed: {e}")
        return False

is_gee_ready = init_gee()

def get_dynamic_utm_crs(lon, lat):
    """Calculate the correct UTM Zone EPSG code based on global Longitude/Latitude."""
    utm_zone = math.floor((lon + 180) / 6) + 1
    return 32600 + utm_zone if lat >= 0 else 32700 + utm_zone

# ==========================================
# 1. DYNAMIC FOLDER SCANNING (CASCADING UX)
# ==========================================
# Định nghĩa đường dẫn gốc chứa dữ liệu đã tuyển chọn
BASE_DATA_DIR = "data/gadm41_VNM_gpkg"

def get_countries():
    """Quét thư mục gốc để lấy danh sách Quốc gia (VD: USA, VNM)"""
    if not os.path.exists(BASE_DATA_DIR):
        return []
    return [d for d in os.listdir(BASE_DATA_DIR) if os.path.isdir(os.path.join(BASE_DATA_DIR, d))]

def get_states(country):
    """Quét thư mục Quốc gia để lấy danh sách Bang/Tỉnh"""
    country_path = os.path.join(BASE_DATA_DIR, country)
    if not os.path.exists(country_path):
        return []
    return [d for d in os.listdir(country_path) if os.path.isdir(os.path.join(country_path, d))]

def get_counties(country, state):
    """Quét thư mục Bang để lấy danh sách file GeoJSON (Quận/Hạt)"""
    state_path = os.path.join(BASE_DATA_DIR, country, state)
    if not os.path.exists(state_path):
        return []
    # Chỉ lấy các file có đuôi .geojson
    files = [f for f in os.listdir(state_path) if f.endswith('.geojson')]
    # Làm đẹp tên hiển thị (Bỏ đuôi .geojson và các dấu gạch dưới)
    display_names = {f.replace(".geojson", "").replace("_", " "): f for f in files}
    return display_names


st.title("Nighttime Lights (NTL) Extraction Engine")
st.markdown("""
**Architecture:** Cloud-to-Local Raster Fetch + C/C++ Engine (`exactextract`).
Designed for Econometric Spatial Analysis (MAUP-resistant 1000m resolution).
""")

# ==========================================
# 2. SIDEBAR PARAMETERS (CASCADING DROPDOWNS)
# ==========================================
with st.sidebar:
    st.header("1. Spatial Parameters")
    
    # 2.1 Dropdown Quốc Gia
    available_countries = get_countries()
    if not available_countries:
        st.error(f"⚠️ No data found in `{BASE_DATA_DIR}`. Please create the folder structure.")
        st.stop()
        
    selected_country = st.selectbox("Select Country", available_countries)
    
    # 2.2 Dropdown Bang/Tỉnh (Tự động cập nhật theo Quốc gia)
    available_states = get_states(selected_country)
    selected_state = st.selectbox("Select State / Region", available_states)
    
    # 2.3 Dropdown Quận/Hạt (Tự động cập nhật theo Bang)
    available_counties_dict = get_counties(selected_country, selected_state)
    selected_county_display = st.selectbox("Select County / District", list(available_counties_dict.keys()))
    
    # Lấy đường dẫn file vật lý dựa trên lựa chọn
    selected_county_file = available_counties_dict.get(selected_county_display)
    full_file_path = os.path.join(BASE_DATA_DIR, selected_country, selected_state, selected_county_file)
    
    
    st.markdown("---")
    st.header("2. Analytical Parameters")
    cell_size = st.slider("Grid Resolution (meters)", min_value=500, max_value=5000, value=1000, step=500)
    year = st.selectbox("Select Year", list(range(2014, 2024)), index=8)
    
    run_btn = st.button("Execute Pipeline")

# ==========================================
# 3. CORE PIPELINE EXECUTION
# ==========================================
if run_btn:
    st.session_state['is_executed'] = True
    st.session_state['file_path'] = full_file_path
    st.session_state['display_name'] = selected_county_display
    st.session_state['size'] = cell_size
    st.session_state['year'] = year

if st.session_state.get('is_executed', False):
    
    file_path = st.session_state['file_path']
    display_name = st.session_state['display_name']
    size = st.session_state['size']
    year = st.session_state['year']
    
    # Kích hoạt import muộn (Lazy Import) cho exact_extract để tối ưu thời gian khởi động app
    from exactextract import exact_extract
    
    # ---------------------------------------------------------
    # STATION 1: DATA LOADING & DYNAMIC GRIDDING
    # ---------------------------------------------------------
    with st.spinner(f"Station 1: Loading `{display_name}` and Generating {size}m Grid..."):
        try:
            boundary = gpd.read_file(file_path)
            boundary_union = gpd.GeoDataFrame(geometry=[boundary.unary_union], crs=boundary.crs)
            
            centroid_lon = boundary_union.geometry.centroid.x.iloc[0]
            centroid_lat = boundary_union.geometry.centroid.y.iloc[0]
            dynamic_epsg = get_dynamic_utm_crs(centroid_lon, centroid_lat)
            
            st.info(f"🌍 Auto-detected CRS: UTM Zone EPSG:{dynamic_epsg}")
            
            boundary_utm = boundary_union.to_crs(epsg=dynamic_epsg)
            minx, miny, maxx, maxy = boundary_utm.total_bounds
            x_coords = np.arange(minx, maxx, size)
            y_coords = np.arange(miny, maxy, size)
            
            grid_cells = [Polygon([(x, y), (x + size, y), (x + size, y + size), (x, y + size)]) 
                          for x in x_coords for y in y_coords]
                    
            raw_grid = gpd.GeoDataFrame({'geometry': grid_cells}, crs=boundary_utm.crs)
            clipped_grid = gpd.clip(raw_grid, boundary_utm)
            clipped_grid['area_km2'] = clipped_grid.geometry.area / 1e6
            
            st.success(f"✅ Generated {len(clipped_grid)} grid cells at {size}m resolution.")
            
        except Exception as e:
            st.error(f"Error at Station 1: {e}")
            st.stop()

    # ---------------------------------------------------------
    # STATION 2: CLOUD-TO-LOCAL RASTER FETCH
    # ---------------------------------------------------------
    with st.spinner("Station 2: Fetching NTL Raster from Google Earth Engine (1 Request Only)..."):
        try:
            bounds = boundary_union.geometry.bounds.iloc[0]
            ee_roi = ee.Geometry.Rectangle([bounds['minx'], bounds['miny'], bounds['maxx'], bounds['maxy']])
            
            dataset = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG") \
                        .filterDate(f"{year}-01-01", f"{year}-12-31") \
                        .select('avg_rad') \
                        .median() \
                        .clip(ee_roi)
            
            download_url = dataset.getDownloadUrl({
                'scale': 1000, 
                'crs': 'EPSG:4326',
                'region': ee_roi,
                'format': 'GEO_TIFF'
            })
            
            response = requests.get(download_url)
            temp_tif = tempfile.NamedTemporaryFile(delete=False, suffix='.tif')
            temp_tif.write(response.content)
            temp_tif.close()
            
            st.success("✅ Raster fetched successfully (Network API bypassed).")

        except Exception as e:
            st.error(f"Error at Station 2: {e}")
            st.stop()

    # ---------------------------------------------------------
    # STATION 3: LOCAL C/C++ COMPUTE (EXACTEXTRACT)
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # STATION 3: LOCAL C/C++ COMPUTE (EXACTEXTRACT)
    # ---------------------------------------------------------
    with st.spinner("Station 3: Calculating Fractional Pixel Coverage (C/C++ Engine)..."):
        try:
            grid_wgs84 = clipped_grid.to_crs(epsg=4326)
            
            # BƯỚC 1: BẮT BUỘC PHẢI CÓ DÒNG NÀY ĐỂ TẠO RA BIẾN 'stats'
            stats = exact_extract(temp_tif.name, grid_wgs84, ['mean'])
            
            # BƯỚC 2: Thuật toán dò tìm thông minh giá trị 'mean'
            mean_values = []
            for s in stats:
                val = 0
                if s and isinstance(s, dict):
                    for k, v in s.items():
                        if 'mean' in str(k).lower() and v is not None:
                            val = float(v)
                            break
                mean_values.append(val)
                
            # BƯỚC 3: Gắn dữ liệu vào bản đồ
            clipped_grid['ntl_mean'] = mean_values
            
            os.remove(temp_tif.name)
            st.success("✅ Econometric Data Extraction complete.")
            
        except Exception as e:
            st.error(f"Error at Station 3: {e}")
            st.stop()

    # ---------------------------------------------------------
    # STATION 4: VISUALIZATION & EXPORT
    # ---------------------------------------------------------
    with st.spinner("Station 4: Rendering Map..."):
        center_lat = boundary_union.geometry.centroid.y.iloc[0]
        center_lon = boundary_union.geometry.centroid.x.iloc[0]
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9, tiles="CartoDB positron")
        
        display_grid = clipped_grid.to_crs(epsg=4326)
        display_grid = display_grid[display_grid['ntl_mean'] > 0.1]
        
        folium.Choropleth(
            geo_data=display_grid,
            data=display_grid,
            columns=['geometry', 'ntl_mean'],
            key_on='feature.id',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.1,
            legend_name='NTL Mean'
        ).add_to(m)

        st_data = st_folium(m, width=900, height=500)
        
        csv_data = clipped_grid.drop(columns=['geometry']).to_csv(index=False)
        st.download_button(
            label="Download Data for Spatial Econometrics (CSV)",
            data=csv_data,
            file_name=f"{display_name.replace(' ', '_')}_NTL_{year}_{size}m.csv",
            mime="text/csv"
        )
