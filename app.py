import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os

# 1. Cấu hình trang
st.set_page_config(page_title="Mô phỏng Lưới Không gian", layout="wide")
st.title("Hệ thống Demo Lưới Không gian Kinh tế lượng")

# 2. Sidebar UI
with st.sidebar:
    st.header("Lựa chọn Dữ liệu Demo")
    
    # Giả sử bạn đã bỏ 2 file này vào thư mục data
    location_options = {
        "Bắc Ninh (Lưới 2x2km)": "data/bacninh_grid.geojson",
        "Đà Nẵng (Lưới 1x1km)": "data/danang_grid.geojson" 
    }
    
    selected_area = st.selectbox("Chọn khu vực đã xử lý:", list(location_options.keys()))
    file_path = location_options[selected_area]

# 3. Khu vực Bản đồ Chính
if os.path.exists(file_path):
    with st.spinner("Đang nạp dữ liệu không gian..."):
        # Đọc file GeoJSON đã xử lý sẵn
        gdf_grid = gpd.read_file(file_path)
        
        # Lấy tọa độ trung tâm để camera bản đồ chĩa vào đó
        center_y = gdf_grid.geometry.centroid.y.mean()
        center_x = gdf_grid.geometry.centroid.x.mean()
        
        # Khởi tạo bản đồ Folium (Nền bản đồ mặc định của OpenStreetMap)
        m = folium.Map(location=[center_y, center_x], zoom_start=10, tiles='CartoDB positron')
        
        # Vẽ lưới (GeoJSON) lên bản đồ
        folium.GeoJson(
            gdf_grid,
            style_function=lambda feature: {
                'fillColor': 'blue',
                'color': 'black',    # Màu viền lưới
                'weight': 1,         # Độ dày viền
                'fillOpacity': 0.1   # Độ trong suốt (để nhìn xuyên xuống nền đường phố)
            },
            # Hiển thị thông tin (tooltip) khi di chuột qua từng ô
            tooltip=folium.GeoJsonTooltip(fields=['area_km2'], aliases=['Diện tích (km2):'], labels=True)
        ).add_to(m)
        
        # Hiển thị bản đồ lên Streamlit
        st_folium(m, width=1200, height=600)
        
        st.info(f"Đã nạp thành công {len(gdf_grid)} ô lưới không gian.")
else:
    st.error("Chưa tìm thấy file dữ liệu. Vui lòng chạy code tạo lưới trước.")