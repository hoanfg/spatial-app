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
    year = st.selectbox("Select Year", list(range(2014, 2026)), index=9)
    
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
            
            boundary_utm = boundary_union.to_crs(epsg=dynamic_epsg)
            minx, miny, maxx, maxy = boundary_utm.total_bounds
            
            # SỬA LỖI MẤT LƯỚI: Nới rộng khung bao (Buffer) để đảm bảo quét sạch 100% lãnh thổ
            x_coords = np.arange(minx - size, maxx + 2*size, size)
            y_coords = np.arange(miny - size, maxy + 2*size, size)
            
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
    with st.spinner("Station 2: Fetching Raster from Cloud..."):
        try:
            bounds_wgs84 = clipped_grid.to_crs(epsg=4326).total_bounds
            minx, miny, maxx, maxy = bounds_wgs84
            ee_roi = ee.Geometry.Rectangle([minx, miny, maxx, maxy])
            
            dataset = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG") \
                .filterDate(f'{year}-01-01', f'{year}-12-31') \
                .filterBounds(ee_roi) \
                .select('avg_rad')
            
            # Ép unmask(0) để khắc phục lỗi NoData của Google
            ntl_image = dataset.median().unmask(0).clip(ee_roi)
            
            import requests
            import tempfile
            
            url = ntl_image.getDownloadUrl({
                'scale': 463,
                'crs': 'EPSG:4326', # Ép cứng tọa độ chuẩn để không bao giờ bị lệch
                'region': ee_roi,
                'format': 'GEO_TIFF'
            })
            
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"Failed to download raster: HTTP {response.status_code}")
                
            temp_tif = tempfile.NamedTemporaryFile(suffix='.tif', delete=False)
            temp_tif.write(response.content)
            temp_tif.close()
            
            st.success("✅ Raster fetched successfully (Network API bypassed).")
        except Exception as e:
            st.error(f"Error at Station 2: {e}")
            st.stop()
            
    # ---------------------------------------------------------
    # STATION 3: LOCAL C/C++ COMPUTE (EXACTEXTRACT)
    # ---------------------------------------------------------
    with st.spinner("Station 3: Calculating Fractional Pixel Coverage (C/C++ Engine)..."):
        try:
            grid_wgs84 = clipped_grid.to_crs(epsg=4326)
            
            # ÉP XUẤT RA DATAFRAME ĐỂ DỄ DÀNG LẤY DỮ LIỆU
            stats = exact_extract(temp_tif.name, grid_wgs84, ['mean'], output='pandas')
            
            # Lấy thẳng cột có chữ 'mean' (thường là 'mean' hoặc 'mean_1')
            mean_col = [c for c in stats.columns if 'mean' in str(c).lower()][0]
            
            # Gắn vào lưới
            clipped_grid['ntl_mean'] = stats[mean_col].fillna(0).tolist()
            
            os.remove(temp_tif.name)
            st.success("✅ Econometric Data Extraction complete.")
            
        except Exception as e:
            st.error(f"Error at Station 3: {e}")
            st.stop()

    # ---------------------------------------------------------
    # STATION 4: VISUALIZATION & EXPORT
    # ---------------------------------------------------------
    with st.spinner("Station 4: Rendering Aviation Map & Analytics..."):
        import branca.colormap as cm
        
        center_lat = boundary_union.geometry.centroid.y.iloc[0]
        center_lon = boundary_union.geometry.centroid.x.iloc[0]
        
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=12, 
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
            attr="Esri"
        )
        
        display_grid = clipped_grid.to_crs(epsg=4326)
        display_grid['grid_id'] = display_grid.index.astype(str)
        display_grid['ntl_mean'] = pd.to_numeric(display_grid['ntl_mean'], errors='coerce').fillna(0).round(2)
        
        # 1. Format lại diện tích để hiển thị chữ "km²"
        display_grid['area_km2_str'] = display_grid['area_km2'].round(2).astype(str) + " km²"
        
        # 2. PHÂN LỚP THÔNG MINH KẾT HỢP: Ngưỡng Tuyệt Đối (Global) + Tương Đối (Local)
        q75 = display_grid['ntl_mean'].quantile(0.75)
        q25 = display_grid['ntl_mean'].quantile(0.25)
        
        def get_smart_insights(val):
            # A. Phân loại theo mức độ phát triển chung (Ngưỡng tuyệt đối của VIIRS)
            if val >= 40:
                dev_level = "Thương mại/Dịch vụ sầm uất (Mật độ siêu cao)"
            elif val >= 15:
                dev_level = "Đô thị lõi/Khu dân cư đông đúc"
            elif val >= 5:
                dev_level = "Vành đai đô thị/Ngoại ô đang phát triển"
            elif val > 0:
                dev_level = "Khu vực ven đô/Hoạt động kinh tế thấp"
            else:
                dev_level = "Không gian mở/Khu vực thiếu sáng"
                
            # B. Đánh giá vị thế nội bộ (So với trung bình của chính Quận/Huyện này)
            if val >= q75:
                local_rank = "Nhóm dẫn đầu (Top 25% khu vực)"
            elif val <= q25:
                local_rank = "Nhóm thấp nhất (Bottom 25% khu vực)"
            else:
                local_rank = "Mức trung bình của khu vực"
                
            return dev_level, local_rank

        # Áp dụng hàm để tạo 2 cột thông tin mới
        display_grid[['dev_level', 'local_rank']] = display_grid['ntl_mean'].apply(get_smart_insights).apply(pd.Series)
        
        if not display_grid.empty:
            max_val = float(display_grid['ntl_mean'].max())
            vmax = max_val if max_val > 0.1 else 1.0
            
            colormap = cm.LinearColormap(
                colors=['#000000', '#804000', '#ffaa00', '#ffff00', '#ffffff'], 
                vmin=0, 
                vmax=vmax
            )
            colormap.caption = f'Nighttime Lights Intensity ({year}) - nW/cm²/sr'
            
            folium.GeoJson(
                display_grid,
                style_function=lambda feature: {
                    'fillColor': colormap(feature['properties']['ntl_mean']),
                    'color': '#555555',  
                    'weight': 0.3,       
                    'fillOpacity': 0.8 if feature['properties']['ntl_mean'] > (vmax * 0.1) else 0.25
                },
                tooltip=folium.features.GeoJsonTooltip(
                    # Truyền 5 trường thông tin chi tiết và dễ hiểu vào Tooltip
                    fields=['grid_id', 'area_km2_str', 'ntl_mean', 'dev_level', 'local_rank'],
                    aliases=[
                        '🔢 ID Ô lưới:', 
                        '📐 Diện tích đo lường:', 
                        '💡 Cường độ NTL (nW/cm²/sr):', 
                        '🏙️ Đặc điểm kinh tế ước lượng:', 
                        '📊 Vị thế so với toàn quận:'
                    ],
                    style="background-color: #111111; color: #ffffff; font-family: arial; font-size: 13px; padding: 12px; border-radius: 6px; border: 1px solid #777777; box-shadow: 2px 2px 8px rgba(0,0,0,0.5);"
                )
            ).add_to(m)
            
            boundary_wgs84 = boundary_union.to_crs(epsg=4326)
            folium.GeoJson(
                boundary_wgs84,
                style_function=lambda x: {
                    'fill': False,
                    'color': '#ffffff',  
                    'weight': 3          
                }
            ).add_to(m)
            
            colormap.add_to(m)

        # -----------------------------------------------------
        # HỘP GIẢI THÍCH TRỰC QUAN CHO NGƯỜI NGOÀI NGÀNH
        # -----------------------------------------------------
        st.markdown("### 📊 Hướng dẫn đọc dữ liệu (Dành cho nhà Phân tích / Đầu tư)")
        st.info(f'''
        Công cụ này chuyển đổi hình ảnh vệ tinh ban đêm thành các chỉ báo kinh tế không gian.
        
        * **Cường độ NTL (Nighttime Lights):** Đo lường ánh sáng phát ra từ đèn đường, tòa nhà, nhà máy. Đây là "biến đại diện" (Proxy) đáng tin cậy để đánh giá mức độ tập trung GDP, mật độ dân cư và cơ sở hạ tầng.
        * **Tại sao lại chia lưới {size}m?** Các ranh giới hành chính (phường/xã) thường có kích thước bất quy tắc, gây nhiễu cho các mô hình hồi quy. Mạng lưới ô vuông giúp chuẩn hóa không gian, cho phép so sánh công bằng giữa trung tâm và ngoại ô.
        * **Cách đọc Đầu dò (Tooltip):** Rê chuột vào một ô vuông bất kỳ để xem:
            * *Đặc điểm kinh tế:* Hệ thống đối chiếu mức sáng với thang đo toàn cầu để nhận diện khu vực đó là lõi đô thị sầm uất hay khu vực thưa thớt.
            * *Vị thế so với toàn quận:* Đánh giá xem ô lưới đó đang là tâm điểm phát triển (Top 25%) hay là vùng trũng (Bottom 25%) so với chính những ô xung quanh nó trong cùng quận.
        ''')

        st_data = st_folium(m, width=900, height=500, returned_objects=[])
        
        export_df = clipped_grid.drop(columns=['geometry', 'area_km2_str', 'dev_level', 'local_rank'], errors='ignore')
        csv_data = export_df.to_csv(index=False)
        st.download_button(
            label="⬇️ Tải Dữ Liệu Hồi Quy Không Gian (CSV)",
            data=csv_data,
            file_name=f"{display_name.replace(' ', '_')}_NTL_{year}_{size}m.csv",
            mime="text/csv",
            type="primary"
        )
