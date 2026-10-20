import geopandas as gpd
import streamlit as st
# (Các thư viện khác vẫn giữ nguyên)

# ---------------------------------------------------------
# BƯỚC 1 MỚI: ĐỌC DỮ LIỆU RANH GIỚI TĨNH
# ---------------------------------------------------------
st.write("1. Đang tải ranh giới từ file tĩnh...")

# Chỉ cần truyền đường dẫn tới file .shp, GeoPandas sẽ tự lo phần còn lại
file_path = "gadm41_VNM_1.shp" 
gdf_provinces = gpd.read_file(file_path)

# In thử danh sách 5 tỉnh đầu tiên để kiểm tra
print(gdf_provinces['NAME_1'].head())

try:
    # Đọc toàn bộ bản đồ 63 tỉnh thành
    map_vietnam = gpd.read_file(file_path)
    
    # Ở file GADM, cột chứa tên tỉnh thường là 'NAME_1'
    # Lọc lấy riêng tỉnh Bắc Ninh
    boundary = map_vietnam[map_vietnam['NAME_1'] == 'Bắc Ninh']
    
    if boundary.empty:
        st.error("Không tìm thấy Bắc Ninh trong dữ liệu. Vui lòng kiểm tra lại tên cột (NAME_1).")
        st.stop()
        
    # Ép hệ tọa độ sang UTM (EPSG:32648 là vùng UTM phổ biến của Bắc Việt Nam)
    # Lưu ý: Khi dùng GeoPandas thuần, ta không dùng ox.project_gdf nữa
    boundary_utm = boundary.to_crs(epsg=32648)
    
    st.success("Tải ranh giới thành công!")
    
    # ... (Các Bước 2, 3 tạo lưới và cắt lưới giữ nguyên như cũ) ...
    
except Exception as e:
    st.error(f"Lỗi khi đọc file: {e}")
