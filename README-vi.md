# 🌐 Dự án Kinh tế lượng không gian

[ 🇬🇧 English ](README.md) | [ 🇻🇳 Tiếng Việt ](README-vi.md)

## 📌 Tổng quan dự án
Dự án này là một hệ thống thiết kế cho **Kinh tế lượng không gian**, kết hợp giữa hạ tầng lưới không gian và luồng trích xuất dữ liệu ánh sáng ban đêm (Nighttime Lights - NTL)

Ứng dụng giải quyết bài toán từ việc chuẩn hóa ranh giới hành chính bất quy tắc thành ma trận lưới vuông, kết nối trực tiếp với Google Earth Engine (GEE) để tải dữ liệu Raster (SNPP-VIIRS), cho đến việc tự động tính toán các chỉ số thống kê không gian vi mô (LISA) để xuất ra dữ liệu bảng (Panel Data) phục vụ các mô hình vĩ mô

---

## 🛠 Đặc tả kỹ thuật
* **Ngôn ngữ lập trình:** Python 3.x
 
* **Framework Giao diện:** Streamlit, quản lý Session State để chống hiện tượng re-run của hệ thống tĩnh

* **Lõi xử lý Không gian (GIS Core):** 
  * `GeoPandas` & `Shapely`: Xử lý hình học véc-tơ, phép toán đại số không gian
  * `NumPy`: Sinh ma trận tọa độ tối ưu hóa hiệu năng
  * `rasterio`, `exactextract`: Xử lý raster sub-pixel

* **Điện toán đám mây:** `earthengine-api` (Google Earth Engine) xác thực qua GCP Service Account và Streamlit Secrets

* **Trực quan hóa:** `Folium`, `Altair` (Bản đồ nhiệt tương tác động)

* **Nguồn dữ liệu ranh giới:** Sử dụng **dữ liệu tĩnh GADM v4.1 (Shapefiles)** thay vì API thời gian thực (GADM, 2022)

   * *Lý do: Giải quyết vấn đề "xung đột dữ liệu mảng" trong kinh tế lượng khi ranh giới hành chính có sự sáp nhập/chia tách qua các năm. Dữ liệu tĩnh đảm bảo mốc thời gian không gian được cố định theo năm nghiên cứu*

---

## ⚙️ Cơ chế thuật toán (4 trạm)
### Giai đoạn 1: Xây dựng Lưới Không gian

1. **Lưới hóa:** Chuyển đổi ranh giới gốc từ hệ tọa độ cầu `WGS84` (kinh độ/vĩ độ) sang hệ tọa độ phẳng `UTM EPSG:32648` (đo bằng mét) để đảm bảo các phép tính hình học không bị méo mó theo độ cong của Trái Đất. Sinh ma trận lưới vuông (500m, 1000m...) và dùng `gpd.clip()` để cắt gọt đa giác ranh giới.

2. **Tải raster đám mây:** Vượt qua giới hạn trích xuất của GEE bằng cách tải toàn bộ ảnh vệ tinh GeoTIFF thô về máy chủ nội bộ, giữ nguyên độ phân giải gốc cao nhất (~463m)

3. **Thống kê vùng chính xác:** Sử dụng C++ `exactextract` để tính trung bình NTL dựa trên tỷ lệ che phủ thực tế của điểm ảnh, hạn chế sai số sao cho thấp nhất của phương pháp đo theo tâm truyền thống

4. **LISA & Panel data bridge:** Chạy thuật toán Local Moran's I để phát hiện các cụm điểm nóng kinh tế, đồng thời tổng hợp các biến vĩ mô (Spillover lag, khoảng cách tới CBD, Gini ánh sáng) để xuất thẳng ra file CSV cho hồi quy panel.

---

## ⚠️ Phương pháp luận và giải pháp

1. **Bài toán MAUP và "Ô biên giới":**

Khi ép một ma trận lưới vuông (ví dụ 1x1 km = 1 km²) vào một ranh giới hành chính ngoằn ngoèo, thuật toán cắt sẽ sinh ra một loạt các **ô biên giới** có hình thù móp méo và diện tích bị hao hụt (ví dụ: chỉ còn $0.15 km^2$ hoặc $0.8 km^2$) (Openshaw, 1983)

Trong kinh tế lượng, nếu ta thực hiện phép đếm tổng dữ liệu ánh sáng đêm hoặc dân số cho toàn bộ các ô lưới này, những ô biên giới sẽ có giá trị NTL rất thấp vì chúng quá nhỏ (Henderson et al., (2012). Mô hình hồi quy sẽ hiểu lầm rằng khu vực biên giới này là "vùng kinh tế kém phát triển", gây ra hiện tượng **phương sai sai số thay đổi (Heteroskedasticity)** và làm sai lệch nghiêm trọng trọng số (bias) của toàn bộ mô hình (Openshaw, 1983)

Dự án áp dụng phương pháp Listwise Deletion (Loại bỏ danh sách). Các ô bị cắt bởi ranh giới và ô tối bị xóa hoàn toàn khỏi đồ thị láng giềng để không làm méo mó ma trận trọng số không gian (W)

2. **Vấn đề đa kiểm định":**

Việc kiểm định hàng ngàn ô lưới cùng lúc để tìm điểm nóng sẽ sinh ra hiện tượng dương tính giả (false positives - cụm ngẫu nhiên)

Lõi LISA ép buộc sử dụng hiệu chỉnh FDR (Benjamini-Hochberg) trên giá trị p-value hoán vị có điều kiện (Caldas de Castro & Singer, 2006). Điều này đảm bảo các cụm bong bóng (High-High) được xác định là chính xác về mặt thống kê

**3. Cầu nối dữ liệu hồi quy (từ vi mô lên vĩ mô):**

Thay vì trả về dữ liệu lưới thô, công cụ xuất ra các biến kiểm soát cho mô hình kinh tế lượng:

`hh_area_share`: Thay thế cho giá nhà quốc gia, đo lường sự bành trướng vật lý của các bong bóng kinh tế đô thị

`ntl_raw_lag`: Đo lường hiệu ứng lan tỏa để bắt dòng tiền đầu cơ vùng ven

`dist_to_core_km`: Kiểm soát rủi ro theo quy luật suy giảm khoảng cách

---

## 🚀 Ứng dụng: Lưới không gian này dùng để làm gì?
Mặc dù UI hiện tại mới chỉ là "trực quan hóa", nhưng **bảng dữ liệu ẩn** bên dưới bản đồ chính là cơ sở hạ tầng để thực hiện các phép **Spatial join (Gộp dữ liệu không gian)**. Cụ thể:

1. **Nội suy GDP vi mô:** Gắn dữ liệu pixel ánh sáng đêm (SNPP-VIIRS) vào lưới. Ô lưới nào sáng hơn phản ánh mức độ tập trung kinh tế cao hơn, cho phép ước lượng GDP tới cấp độ phường/xã hoặc từng khu phố (100 hecta) thay vì bị giới hạn ở số liệu GDP cấp tỉnh thô sơ (Elvidge et al., 2017)

2. **Đánh giá bất bình đẳng không gian:** Đếm số lượng Điểm quan tâm (POI) như Chi nhánh ngân hàng, ATM, hoặc Trường học rơi vào từng ô lưới. Từ đó chạy các mô hình hồi quy trọng số không gian (GWR) để xem xét mức độ tiếp cận tài chính/giáo dục

3. **Phân tích rủi ro khí hậu/bất động sản:** Gắn dữ liệu độ cao (DEM) hoặc bản đồ rủi ro ngập lụt vào lưới để định giá sự sụt giảm giá trị bất động sản ở những ô lưới có rủi ro cao

---

## 📚 Tài liệu tham khảo
Anselin, L. (1995). Local Indicators of Spatial Association—LISA. Geographical Analysis, 27(2), 93-115. DOI: 10.1111/j.1538-4632.1995.tb00338.x

Caldas de Castro, M., & Singer, B. H. (2006). Controlling the false discovery rate: A new application to account for multiple and dependent tests in local statistics of spatial association. Geographical Analysis, 38(2), 180-208. DOI: 10.1111/j.0016-7363.2006.00682.x

Elvidge, C. D., Baugh, K., Zhizhin, M., Hsu, F. C., & Ghosh, T. (2017). VIIRS night-time lights. International Journal of Remote Sensing, 38(21), 5860-5879. DOI: 10.1080/01431161.2017.1342050

GADM. (2022). GADM database of Global Administrative Areas, version 4.1. Truy cập tại: https://gadm.org/

Henderson, J. V., Storeygard, A., & Weil, D. N. (2012). Measuring Economic Growth from Outer Space. American Economic Review, 102(2), 994-1028. DOI: 10.1257/aer.102.2.994

Openshaw, S. (1984). The Modifiable Areal Unit Problem. Concepts and Techniques in Modern Geography (CATMOG), 38. https://www.spatial-literacy.org/qmrg/catmog/catmog_38.pdf
