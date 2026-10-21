# 🌐 Dự án Kinh tế lượng không gian: Hạ tầng lưới & trích xuất dữ liệu ánh sáng đêm

[ 🇬🇧 English ](README.md) | [ 🇻🇳 Tiếng Việt ](README-vi.md)

## 📌 Tổng quan dự án
Dự án này tập trung xây dựng **hạ tầng lưới không gian và luồng trích xuất dữ liệu ánh sáng đêm (NTL)**, đóng vai trò là công cụ kỹ thuật dữ liệu cho phân tích Kinh tế lượng không gian

Ứng dụng giải quyết bài toán tiêu chuẩn hóa ranh giới hành chính phức tạp thành ma trận không gian đồng nhất, đồng thời kết nối trực tiếp với Cloud API để trích xuất dữ liệu Raster thực tế (vệ tinh SNPP-VIIRS) phục vụ phân tích kinh tế vi mô

---

## 🛠 Đặc tả kỹ thuật
* **Ngôn ngữ lập trình:** Python 3.x
 
* **Framework Giao diện:** Streamlit, quản lý Session State để chống hiện tượng re-run của hệ thống tĩnh

* **Lõi xử lý Không gian (GIS Core):** 
  * `GeoPandas` & `Shapely`: Xử lý hình học véc-tơ, phép toán đại số không gian
  * `NumPy`: Sinh ma trận tọa độ tối ưu hóa hiệu năng

* **Xử lý ảnh vệ tinh (Raster):** `rasterstats`, `rasterio` (Cho cơ chế dự phòng Local GeoTIFF)

* **Điện toán đám mây:** `earthengine-api` (Google Earth Engine) xác thực qua GCP Service Account và Streamlit Secrets

* **Trực quan hóa:** `Folium`, `branca.colormap` (Bản đồ nhiệt tương tác động)

* **Nguồn dữ liệu ranh giới:** Sử dụng **dữ liệu tĩnh GADM v4.1 (Shapefiles)** thay vì API thời gian thực (GADM, 2022)

   * *Lý do: Giải quyết triệt để vấn đề "xung đột dữ liệu mảng" trong kinh tế lượng khi ranh giới hành chính có sự sáp nhập/chia tách qua các năm. Dữ liệu tĩnh đảm bảo mốc thời gian không gian được cố định theo năm nghiên cứu*

---

## ⚙️ Cơ chế thuật toán
### Giai đoạn 1: Xây dựng Lưới Không gian

1. **Chuẩn hóa hệ tọa độ (CRS):** Chuyển đổi ranh giới gốc từ hệ tọa độ cầu `WGS84` (kinh độ/vĩ độ) sang hệ tọa độ phẳng `UTM EPSG:32648` (đo bằng mét) để đảm bảo các phép tính hình học không bị méo mó theo độ cong của Trái Đất

2. **Khởi tạo hộp bao quanh:** Tính toán tọa độ cực hạn (`minx, miny, maxx, maxy`) bao trọn toàn bộ tỉnh

3. **Sinh ma trận lưới thô:** Dùng `NumPy` duyệt qua các trục X, Y với bước nhảy `cell_size` (1000m, 2000m...), tạo ra các đa giác phủ kín bounding box

4. **Phép cắt không gian:** Sử dụng thuật toán `gpd.clip()` để dùng đa giác ranh giới hành chính phức tạp gọt đứt phần lưới thô thừa ra ngoài

5. **Đồng bộ hóa trực quan:** Trả hệ tọa độ về lại `WGS84` để render trên nền tảng bản đồ web của Leaflet/Folium

### Giai đoạn 2: Trích xuất Dữ liệu Đám mây

1. **Tích hợp Google Earth Engine:** Truy cập an toàn vào kho dữ liệu vệ tinh NOAA/VIIRS/DNB để lấy chỉ số bức xạ ánh sáng ban đêm thực tế

2. **Thuật toán Chunking:** Giải quyết triệt để lỗi HTTP 413 (Payload too large) của Google Cloud bằng cách chia nhỏ các yêu cầu MultiPolygon phức tạp thành các gói (100 ô lưới/lượt gửi)

3. **Cơ chế Dự phòng (Fallback):** Triển khai tính toán Zonal Statistics cục bộ, cho phép người dùng tải lên các file `.tif` tĩnh khi API Cloud vượt quá hạn mức

---

## ⚠️ Vấn đề "ô biên giới"

Khi ép một ma trận lưới vuông (ví dụ 1x1 km = 1 km²) vào một ranh giới hành chính ngoằn ngoèo, thuật toán cắt sẽ sinh ra một loạt các **ô biên giới** có hình thù móp méo và diện tích bị hao hụt (ví dụ: chỉ còn $0.15 km^2$ hoặc $0.8 km^2$) (Openshaw, 1983)

Trong kinh tế lượng, nếu ta thực hiện phép đếm tổng dữ liệu ánh sáng đêm hoặc dân số cho toàn bộ các ô lưới này, những ô biên giới sẽ có giá trị NTL rất thấp vì chúng quá nhỏ (Henderson et al., (2012). Mô hình hồi quy sẽ hiểu lầm rằng khu vực biên giới này là "vùng kinh tế kém phát triển", gây ra hiện tượng **phương sai sai số thay đổi (Heteroskedasticity)** và làm sai lệch nghiêm trọng trọng số (bias) của toàn bộ mô hình (Openshaw, 1983).

### 💡 Giải pháp chuẩn hóa kinh tế lượng tự đề xuất

Để giải quyết bài toán trên, Phase 1 đã chủ động tính toán và lưu trữ biến số diện tích thực (`area_km2`) cho từng ô lưới bị cắt gọt. Ở Phase 2, hệ thống sẽ áp dụng 2 chiến lược:

1. **Chuẩn hóa theo mật độ:** Thay vì sử dụng biến phụ thuộc là $Tổng NTL$, mô hình sẽ dùng $\frac{Tổng NTL}{area\_km2}$ (Cường độ kinh tế trên 1 km² thực tế)

2. **Lọc nhiễu biên:** Xóa bỏ hoàn toàn các ô lưới biên giới có tỷ lệ diện tích $< 10\%$ diện tích lưới tiêu chuẩn (ví dụ $< 0.1 km^2$ đối với lưới 1x1km) để loại bỏ các điểm dị thường khỏi tập dữ liệu

---

## 🚀 Ứng dụng: Lưới không gian này dùng để làm gì?
Mặc dù UI hiện tại mới chỉ là "trực quan hóa", nhưng **bảng dữ liệu ẩn** bên dưới bản đồ chính là cơ sở hạ tầng để thực hiện các phép **Spatial join (Gộp dữ liệu không gian)**. Cụ thể:

1. **Nội suy GDP vi mô:** Gắn dữ liệu pixel ánh sáng đêm (SNPP-VIIRS) vào lưới. Ô lưới nào sáng hơn phản ánh mức độ tập trung kinh tế cao hơn, cho phép ước lượng GDP tới cấp độ phường/xã hoặc từng khu phố (100 hecta) thay vì bị giới hạn ở số liệu GDP cấp tỉnh thô sơ (Elvidge et al., 2017)

2. **Đánh giá bất bình đẳng không gian:** Đếm số lượng Điểm quan tâm (POI) như Chi nhánh ngân hàng, ATM, hoặc Trường học rơi vào từng ô lưới. Từ đó chạy các mô hình hồi quy trọng số không gian (GWR) để xem xét mức độ tiếp cận tài chính/giáo dục

3. **Phân tích rủi ro khí hậu/bất động sản:** Gắn dữ liệu độ cao (DEM) hoặc bản đồ rủi ro ngập lụt vào lưới để định giá sự sụt giảm giá trị bất động sản ở những ô lưới có rủi ro cao

---

## 📚 Tài liệu tham khảo
Elvidge, C. D., Baugh, K., Zhizhin, M., Hsu, F. C., & Ghosh, T. (2017). VIIRS night-time lights. International Journal of Remote Sensing, 38(21), 5860-5879.

GADM. (2022). GADM database of Global Administrative Areas, version 4.1. Truy cập tại: https://gadm.org/

Henderson, J. V., Storeygard, A., & Weil, D. N. (2012). Measuring Economic Growth from Outer Space. American Economic Review, 102(2), 994-1028.

Openshaw, S. (1983). The Modifiable Areal Unit Problem. Concepts and Techniques in Modern Geography, 38.
