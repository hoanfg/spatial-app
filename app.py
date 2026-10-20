import streamlit as st
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon
import folium
from streamlit_folium import st_folium
import os

# 1. Cấu hình giao diện Streamlit
st.set_page_config(page_title="Hệ thống Lưới Không gian", layout="wide")
st.title("Công cụ Cắt Lưới Không Gian (Spatial Grid Generator)")

# 2. Đọc dữ liệu Shapefile Tĩnh từ thư mục data
file_path = "data/gadm41_VNM_1.shp"

# Kiểm tra xem file có tồn tại không trước khi đọc
if not os.path.exists(file_path):
    st.error(f"Không tìm thấy file dữ liệu tại {file_path}. Vui lòng kiểm tra lại thư mục.")
    st.stop()

@st.cache_data # Lưu cache để không phải đọc lại file shp khi người dùng tương tác
def load_data():
    return gpd.read_file(file_path)

with st.spinner("Đang tải dữ liệu ranh giới 63 tỉnh thành..."):
    df_vietnam = load_data()

# 3. Thanh điều hướng (Sidebar)
with st.sidebar:
    st.header("Thông số đầu vào")
    # Lấy danh sách tên tỉnh từ cột NAME_1 của GADM
    list_provinces = df_vietnam['NAME_1'].sort_values().unique()
    selected_province = st.selectbox("Chọn Tỉnh/Thành phố", list_provinces)
    
    cell_size = st.slider("Kích thước lưới (mét)", min_value=1000, max_value=5000, value=2000, step=1000)
    run_btn = st.button("Tiến hành tạo lưới")

# 4. Xử lý thuật toán cắt lưới khi bấm nút
if run_btn:
    with st.spinner(f"Đang xử lý toán học tạo lưới {cell_size}m cho {selected_province}..."):
        # Lọc ranh giới tỉnh được chọn
        boundary = df_vietnam[df_vietnam['NAME_1'] == selected_province]
        
        # Ép tọa độ sang UTM (EPSG:32648 là vùng chuẩn cho Việt Nam) để tính bằng mét
        boundary_utm = boundary.to_crs(epsg=32648)
        
        # Tạo lưới thô
        minx, miny, maxx, maxy = boundary_utm.total_bounds
        x_coords = np.arange(minx, maxx, cell_size)
        y_coords = np.arange(miny, maxy, cell_size)
        
        grid_cells = []
        for x in x_coords:
            for y in y_coords:
                poly = Polygon([(x, y), (x + cell_size, y), (x + cell_size, y + cell_size), (x, y + cell_size)])
                grid_cells.append(poly)
                
        raw_grid = gpd.GeoDataFrame({'geometry': grid_cells}, crs=boundary_utm.crs)
        
        # Cắt gọt viền và tính diện tích
        clipped_grid = gpd.clip(raw_grid, boundary_utm)
        clipped_grid['area_km2'] = clipped_grid.geometry.area / 1e6
        
        # Chuyển ngược lại hệ WGS84 (Kinh độ/Vĩ độ) để vẽ lên bản đồ Web
        clipped_grid_wgs84 = clipped_grid.to_crs(epsg=4326)
        
        st.success(f"Hoàn thành! Đã tạo ra {len(clipped_grid)} ô lưới không gian.")

        # 5. Vẽ bản đồ tương tác bằng Folium
        center_y = boundary.geometry.centroid.y.values[0]
        center_x = boundary.geometry.centroid.x.values[0]
        
        m = folium.Map(location=[center_y, center_x], zoom_start=10, tiles='CartoDB positron')
        
        # Đưa ranh giới lưới lên bản đồ
        folium.GeoJson(
            clipped_grid_wgs84,
            style_function=lambda feature: {
                'fillColor': '#0000ff',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.2
            },
            tooltip=folium.GeoJsonTooltip(fields=['area_km2'], aliases=['Diện tích (km2):'])
        ).add_to(m)
        
        # Hiển thị trên Streamlit
        st_folium(m, width=1000, height=600)