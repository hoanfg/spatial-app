import streamlit as st
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import folium
from streamlit_folium import st_folium
import os
import branca.colormap as cm

# 1. Cấu hình giao diện Streamlit
st.set_page_config(page_title="Spatial grid system", layout="wide")
st.title("Spatial grid cutter tool")

# 2. Đọc dữ liệu Shapefile Tĩnh từ thư mục data
file_path = "data/gadm41_VNM_1.shp"

# Kiểm tra xem file có tồn tại không trước khi đọc
if not os.path.exists(file_path):
    st.error(f"Data file not found at {file_path}. Please check the directory.")
    st.stop()

@st.cache_data # Lưu cache để không phải đọc lại file shp khi người dùng tương tác
def load_data():
    return gpd.read_file(file_path)

with st.spinner("Loading boundaries data..."):
    df_vietnam = load_data()

# 3. Thanh điều hướng (Sidebar)
with st.sidebar:
    st.header("Input parameters")
    list_provinces = df_vietnam['NAME_1'].sort_values().unique()
    selected_province = st.selectbox("Please choose City/Province", list_provinces)
    
    cell_size = st.slider("Grid size (meters)", min_value=1000, max_value=5000, value=2000, step=1000)
    run_btn = st.button("Generate grid")

# --- KỸ THUẬT SESSION STATE (LƯU TRẠNG THÁI) ---
# Nếu bấm nút, ta lưu yêu cầu vào bộ nhớ của trình duyệt
if run_btn:
    st.session_state['da_bam_nut'] = True
    st.session_state['tinh_dang_chon'] = selected_province
    st.session_state['kich_thuoc'] = cell_size

# 4. Xử lý thuật toán cắt lưới và sinh dữ liệu giả lập (Mock Data)
if st.session_state.get('da_bam_nut', False):
    
    tinh = st.session_state['tinh_dang_chon']
    size = st.session_state['kich_thuoc']
    
    with st.spinner(f"Processing mathematical operations and generating simulated data of {size}m for {tinh}..."):
        # Lọc ranh giới và bẻ hệ tọa độ sang mét
        boundary = df_vietnam[df_vietnam['NAME_1'] == tinh]
        boundary_utm = boundary.to_crs(epsg=32648)
        
        # Tạo lưới thô
        minx, miny, maxx, maxy = boundary_utm.total_bounds
        x_coords = np.arange(minx, maxx, size)
        y_coords = np.arange(miny, maxy, size)
        
        grid_cells = []
        for x in x_coords:
            for y in y_coords:
                poly = Polygon([(x, y), (x + size, y), (x + size, y + size), (x, y + size)])
                grid_cells.append(poly)
                
        raw_grid = gpd.GeoDataFrame({'geometry': grid_cells}, crs=boundary_utm.crs)
        
        # Cắt gọt viền và tính diện tích
        clipped_grid = gpd.clip(raw_grid, boundary_utm)
        clipped_grid['area_km2'] = clipped_grid.geometry.area / 1e6
        
        # --- BƯỚC NÂNG CẤP: TẠO GIÁ TRỊ KINH TẾ (MOCK DATA) ---
        # 1. Nhận diện "Ô biên giới" (Border Cell) vs "Ô tiêu chuẩn" (Core Cell)
        # Nếu diện tích thực tế nhỏ hơn 95% diện tích lưới gốc -> Đánh dấu là Ô biên giới
        standard_area = (size / 1000) ** 2
        clipped_grid['cell_type'] = np.where(clipped_grid['area_km2'] < (standard_area * 0.95), 'Border', 'Standard (Core)')
        
        # 2. Tìm điểm trung tâm của toàn tỉnh (Central Business District proxy)
        prov_centroid = boundary_utm.geometry.centroid.iloc[0]
        
        # 3. Tính khoảng cách từ từng ô lưới đến trung tâm (mét)
        clipped_grid['dist_to_center'] = clipped_grid.geometry.centroid.distance(prov_centroid)
        
        # 4. Chuyển khoảng cách thành Điểm số Kinh tế (Điểm NTL mô phỏng 0-100)
        # Gần trung tâm -> Điểm cao. Xa trung tâm -> Điểm thấp. Áp dụng nhiễu ngẫu nhiên (noise) để trông thực tế.
        max_dist = clipped_grid['dist_to_center'].max()
        np.random.seed(42) # Cố định seed để bản đồ không bị giật khi xem
        noise = np.random.normal(0, 5, len(clipped_grid)) 
        
        # Công thức tính điểm nghịch đảo khoảng cách
        clipped_grid['mock_ntl_score'] = 100 * (1 - (clipped_grid['dist_to_center'] / max_dist)) + noise
        
        # Ép điểm số về dải 0-100 (tránh bị âm hoặc vượt 100 do nhiễu)
        clipped_grid['mock_ntl_score'] = clipped_grid['mock_ntl_score'].clip(0, 100).round(2)
        
        # Trả hệ tọa độ về WGS84 để hiển thị lên Folium
        clipped_grid_wgs84 = clipped_grid.to_crs(epsg=4326)
        
        st.success(f"Complete! Generated {len(clipped_grid)} spatial grid cells with simulated economic data.")

        # 5. Vẽ bản đồ Nhiệt (Heatmap)
        center_y = boundary.geometry.centroid.y.values[0]
        center_x = boundary.geometry.centroid.x.values[0]
        
        m = folium.Map(location=[center_y, center_x], zoom_start=10, tiles='OpenStreetMap')
        
        # Khởi tạo dải màu (Colormap) từ Xanh thẫm (Thấp) đến Vàng rực (Cao)
        colormap = cm.LinearColormap(
            colors=['#0d0887', '#7a0403', '#cb4621', '#f89441', '#f0f921'], 
            vmin=0, vmax=100,
            caption='Light intensity / Economic simulation (0-100)'
        )
        m.add_child(colormap)
        
        # Đưa ranh giới lưới và đổ màu lên bản đồ
        folium.GeoJson(
            clipped_grid_wgs84,
            style_function=lambda feature: {
                'fillColor': colormap(feature['properties']['mock_ntl_score']),
                'color': '#ffffff' if feature['properties']['cell_type'] == 'Standard (Core)' else '#ff0000', # Viền đỏ cho ô biên giới
                'weight': 0.5,
                'fillOpacity': 0.7
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['mock_ntl_score', 'area_km2', 'cell_type'], 
                aliases=['Economic score (Mock NTL):', 'Actual area (km2):', 'Grid classification:'],
                labels=True
            )
        ).add_to(m)
        
        # Khóa tín hiệu re-run của Folium
        st_folium(m, width=1000, height=600, returned_objects=[])

        st.markdown("### 📥 Data export")
        st.info("This spatial grid infrastructure is ready for download and integration into econometric models (Stata, R, QGIS) or merging with satellite data")
        
        # Tạo cột để đặt 2 nút tải xuống cạnh nhau
        col1, col2 = st.columns(2)
        
        # 1. Nút tải định dạng GeoJSON (Dành cho GIS)
        # GeoJSON giữ được hình dạng đa giác (Polygon) của lưới
        geojson_data = clipped_grid_wgs84.to_json()
        with col1:
            st.download_button(
                label="Download grid map (GeoJSON)",
                data=geojson_data,
                file_name=f"{tinh}_Grid_{size}m.geojson",
                mime="application/geo+json"
            )
        
        # 2. Nút tải định dạng CSV (Dành cho Thống kê/Stata)
        # CSV bỏ đi cột geometry phức tạp, giữ lại tọa độ điểm trung tâm (Centroid X, Y)
        df_export = clipped_grid_wgs84.copy()
        # Tạo cột tọa độ tâm (Centroid) để có thể vẽ lại lưới dưới dạng điểm (Point) trên Stata/Excel
        df_export['centroid_lon'] = df_export.geometry.centroid.x
        df_export['centroid_lat'] = df_export.geometry.centroid.y
        # Xóa cột geometry vì CSV không đọc được định dạng Polygon
        df_csv = df_export.drop(columns=['geometry']).to_csv(index=False).encode('utf-8')
        
        with col2:
            st.download_button(
                label="Download data table (CSV)",
                data=df_csv,
                file_name=f"{tinh}_Data_{size}m.csv",
                mime="text/csv"
            )
