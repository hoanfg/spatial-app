<a id="top"></a>

# Spatial-app: Kiểm chứng và hồ sơ bằng chứng

| Mục | Nội dung |
|:---|:---|
| Dự án | Trích xuất ánh sáng ban đêm VIIRS và kinh tế lượng không gian |
| Repository | `hoanfg/spatial-app` |
| Tài liệu | Đặc tả kiểm chứng |
| Phiên bản | 1.0: 11/11/2026 |
| Phiên bản mã nguồn tham chiếu | Nhánh `main`, sau các PR #10, #11, #12 và #13 |
| Trường hợp thực nghiệm | Diên Khánh (Yanqing), Bắc Kinh, Trung Quốc; 2014–2020 |
| Phạm vi | Phương pháp, kết quả số, tiêu chí chấp nhận, giới hạn và kế hoạch kiểm chứng tiếp |
| Bảo trì | Các đợt kiểm chứng bổ sung được cập nhật vào chính tài liệu này bằng PR |

> **Phạm vi bảo đảm.** Các phép tính trích xuất raster và thống kê không gian chính đã được tái lập tại trường hợp Diên Khánh với dữ liệu thực. Kết quả này **không** chứng minh tính đúng đắn trên mọi địa phương, mọi năm hoặc tính phù hợp của NTL như chỉ báo kinh tế. Tài liệu ghi nhận cả những phép kiểm thành công lẫn các lựa chọn phương pháp có độ nhạy lớn.

## Mục lục

1. [Mục tiêu và tiêu chuẩn kiểm chứng](#s1)
2. [Bộ dữ liệu chuẩn và điều kiện tái lập](#s2)
3. [Kiểm chứng ranh giới GADM](#s3)
4. [Kiểm chứng Local Moran và suy luận thống kê](#s4)
5. [Kiểm chứng trích xuất VIIRS năm 2020](#s5)
6. [Kiểm chứng trích xuất VIIRS năm 2014](#s6)
7. [Độ nhạy theo phương pháp tổng hợp ảnh và dữ liệu thiếu](#s7)
8. [Độ nhạy theo phép biến đổi NTL](#s8)
9. [Độ vững theo cấu trúc không gian](#s9)
10. [Kiểm chứng động học không–thời gian và Spatial Markov](#s10)
11. [Đối chiếu hội tụ với GHSL](#s11)
12. [Kiểm thử hồi quy và các thay đổi đã sửa](#s12)
13. [Trạng thái toàn chương trình và công việc còn lại](#s13)
14. [Danh mục và bảo quản bằng chứng](#s14)
15. [Quy trình bổ sung kiểm chứng và lịch sử phiên bản](#s15)

---

<a id="s1"></a>
## 1. Mục tiêu và tiêu chuẩn kiểm chứng

### 1.1. Mục đích nghiên cứu

Ứng dụng tích hợp ranh giới hành chính GADM 4.1, bức xạ ánh sáng ban đêm VIIRS, lưới phân tích, thống kê theo vùng, tự tương quan không gian, Local Indicators of Spatial Association (LISA), dữ liệu đối chứng GHSL và phân tích động học hai thời điểm.

Kiểm chứng phải phân biệt bốn loại khẳng định:

- **Độ chính xác số học:** Kết quả có khớp với phép tính độc lập trên cùng đầu vào và cùng quy ước không?
- **Độ nhạy phương pháp:** Kết quả thay đổi thế nào khi đổi phép tổng hợp ảnh, biến đổi dữ liệu, định nghĩa láng giềng, kích thước ô và ngưỡng?
- **Giá trị đo lường:** NTL và các chỉ số liên quan có phản ánh hiện tượng nghiên cứu phù hợp không?
- **Độ tin cậy vận hành:** Ứng dụng có xử lý ổn định trên môi trường triển khai thực, trong giới hạn tài nguyên đã thiết kế không?

| Trạng thái | Ý nghĩa | Không hàm ý |
|---|---|---|
| **ĐẠT: trong phạm vi thử** | Tính toán độc lập khớp trong dung sai hoặc tiêu chí đã công bố | Tất cả địa phương và năm đều đạt |
| **ĐÃ ĐÁNH GIÁ ĐỘ NHẠY** | Ảnh hưởng của giả định thay thế được định lượng | Mọi cấu hình đều có thể thay cho nhau |
| **MỘT PHẦN** | Có bằng chứng sơ bộ nhưng thiếu kiểm chứng độc lập của một khâu | Toàn bộ pipeline đã đạt |
| **CHƯA THỰC HIỆN** | Chưa có đủ bằng chứng kiểm thử | Khâu đó nhất thiết bị lỗi |
| **ĐÃ KHẮC PHỤC** | Có PR điều chỉnh và kiểm thử liên quan | Không còn giới hạn khoa học nào khác |

### 1.2. Nguyên tắc kết luận

Mỗi kết quả phải gắn với phiên bản mã, dữ liệu đầu vào, khu vực, năm, độ phân giải, quy ước xử lý giá trị thiếu, quy tắc thống kê và dung sai. Không thể dùng một kết quả kiểm thử đơn vị để thay cho đối chiếu vệ tinh thực; cũng không thể dùng tương quan với GHSL như bằng chứng quan hệ nhân quả hoặc xác thực GDP.

**Kết quả kiểm chứng hiện tại tập trung vào một địa bàn tham chiếu**. Phạm vi này phù hợp để kiểm tra số học sâu, nhưng chưa đủ để kết luận khả năng khái quát của ứng dụng.

<a id="s2"></a>
## 2. Bộ dữ liệu chuẩn và điều kiện tái lập

### 2.1. Trường hợp chuẩn

| Tham số | Giá trị |
|---|---|
| Địa bàn | Trung Quốc - Bắc Kinh - Diên Khánh (Yanqing) |
| Mã địa giới | `GID_2 = CHN.2.1.11_1` |
| Nguồn ranh giới | `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Beijing/CHN_Beijing_Yanqing_District.geojson` |
| Bộ dữ liệu vệ tinh | `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` |
| Band | `avg_rad` và `cf_cvg` |
| Năm | 2014, 2020 |
| Phép tổng hợp năm | Trung vị của các ảnh tháng sau khi loại pixel có `cf_cvg == 0` |
| Raster từ ứng dụng | `EPSG:4326`, scale danh nghĩa **463,83 mét** |
| Hệ tọa độ lưới | UTM 50N `EPSG:32650` |
| Lưới phân tích chính | 500 m × 500 m, cắt theo ranh giới |
| Tổng số ô | **8.333** |
| Diện tích | Khoảng **2.003,51 km²** |
| Quy tắc loại ô biên | Diện tích < 99% × 0,25 km² |
| Ô bị loại khỏi LISA | **600** |
| Ô tham gia LISA | **7.733** |
| Trọng số không gian | Queen; trung bình theo số láng giềng hợp lệ |
| Hoán vị Monte Carlo | 999 lượt; seed 42 cho baseline |
| Kiểm định | Hoán vị có điều kiện, lấy mẫu không hoàn lại; p hai phía theo quy ước ứng dụng; Benjamini–Hochberg FDR ở 5% |

### 2.2. Quy trình tạo và căn chỉnh dữ liệu

Ứng dụng tải GeoTIFF annual median trong bounding box từ Earth Engine, chuyển giá trị bức xạ sang kiểu số thực, giữ mask pixel không hợp lệ, **cắt giá trị bức xạ âm hợp lệ về 0** và tính trung bình theo tỷ lệ diện tích pixel giao với từng đa giác ô lưới bằng `exactextract`.

Lưới phân tích UTM 500 m **không phải** lưới pixel VIIRS nguyên thủy. Một ô có thể giao với nhiều pixel của raster `EPSG:4326`. Vì vậy, phép lấy giá trị tại tâm ô, lấy pixel gần nhất hoặc ghép hai lưới chưa căn chỉnh không thay được trung bình theo phần diện tích giao nhau.

Để tái lập chính xác các ô biên, phải giữ toàn bộ chữ số tọa độ ranh giới GADM và phép biến đổi raster. Kiểm tra ban đầu trên ranh giới bị làm tròn từng xuất hiện chênh lệch nhỏ; sai khác biến mất khi khôi phục tọa độ đầy đủ.

### 2.3. Dữ liệu đầu vào đã dùng

CSV chính:
- `dien_khanh_NTL_2020_500m.csv`;
- `CHN_beijing_yanqing_2020_500m_lisa_cells.csv`;
- `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv`.

GeoTIFF đối chứng:
- `yanqing_viirs_2020_reference.tif`, `yanqing_valid_months_2020.tif`;
- `yanqing_viirs_2020_annual_mean.tif`, `yanqing_viirs_2020_masked_median.tif`;
- `yanqing_viirs_2014_reference.tif`, `yanqing_valid_months_2014.tif`, `yanqing_viirs_2014_masked_median.tif`.

CSV xuất `ntl_mean` với bốn chữ số thập phân. Do đó, khi so trung bình raster chưa làm tròn với CSV, dung sai tuyệt đối phù hợp là **5×10⁻⁵ nW/cm²/sr**.

<a id="s3"></a>
## 3. Kiểm chứng ranh giới GADM

### 3.1. Thiết kế kiểm tra

Tập dữ liệu Trung Quốc đã biên tập chứa **2.420 file GeoJSON**. Từng đối tượng được so với GeoPackage GADM 4.1 Trung Quốc đủ độ phân giải. Các tiêu chí bao gồm mã hành chính, hình học, tính hợp lệ, mã trùng lặp, trùng khớp topology và diện tích chồng lấn lớn hơn ngưỡng phát hiện **1 m²**.

### 3.2. Kết quả

- Hình học và mã định danh của **2.420/2.420** đối tượng khớp nguồn tham chiếu trong dung sai kiểm tra.
- Không phát hiện đa giác không hợp lệ, mã GID trùng hoặc phần chồng lấn vượt ngưỡng.
- **2.419/2.420** tên khớp nguồn; trường hợp còn lại đã được đối chiếu và điều chỉnh.
- Tại `GID_2 = CHN.14.10.2_1`, tên trong bản biên tập từng là `Yiyang`, còn nguồn ghi `Nan`. **PR #10** sửa metadata, không thay hình học hay định danh file.
- Một bản ghi nguồn GADM có tên `NA` không nằm trong tập đã biên tập. Do đó, tập curated có hình học khớp nguồn **không mặc nhiên là danh mục một-một của toàn bộ bản ghi nguồn**.

### 3.3. Lựa chọn đơn vị hành chính phù hợp tài nguyên

Các đô thị trực thuộc trung ương hoặc địa bàn rất lớn được phân chia thành các district để bảo đảm ứng dụng hoạt động trong giới hạn RAM của Streamlit Community Cloud. Đây là biện pháp bảo vệ có chủ đích, **không phải lỗi thiếu tính năng phân tích toàn đô thị**. Khi cần số liệu cấp thành phố, nghiên cứu phải định nghĩa riêng cách tổng hợp từ các quận.

### 3.4. Kết luận

**ĐẠT về tính nhất quán hình học và mã định danh trong tập GADM Trung Quốc đã kiểm tra.** Khả năng chuẩn hóa giữa các quốc gia và tính tương đương kinh tế-xã hội của cấp hành chính nằm ngoài phạm vi kiểm tra này.

<a id="s4"></a>
## 4. Kiểm chứng thuật toán Local Moran và suy luận thống kê

### 4.1. Tập ô và cấu trúc láng giềng

Phương pháp baseline chuẩn hóa giá trị NTL của các ô sáng, sử dụng tập tham chiếu là các ô không bị loại bởi ngưỡng biên. Queen adjacency công nhận hai ô là láng giềng nếu chung cạnh **hoặc** chung đỉnh. Chỉ các ô hợp lệ được phép tham gia ma trận láng giềng và tập hoán vị.

Với tập láng giềng hợp lệ \(N_i\), độ trễ không gian là

\[
(Wz)_i=\frac{1}{|N_i|}\sum_{j\in N_i}z_j.
\]

Thống kê Local Moran theo quy ước chuẩn hóa ESDA:

\[
I_i=\frac{z_i(Wz)_i}{\sum_{j\in M}z_j^2/(|M|-1)},
\]

trong đó \(M\) là tập ô hợp lệ chung của phép kiểm định.

### 4.2. Suy luận Monte Carlo có điều kiện

Thuật toán đã sửa giữ giá trị z-score của ô trung tâm cố định. Trong mỗi lượt hoán vị, các ô láng giềng giả lập được lấy từ những ô hợp lệ **không kể ô trung tâm và không hoàn lại**. Cách này khắc phục lỗi lấy mẫu hoàn lại trước PR #10.

Ứng dụng tính pseudo-p **hai phía** bằng cách đếm thống kê mô phỏng ở ít nhất mức cực đoan tương ứng với thống kê quan sát, áp dụng hiệu chỉnh cộng 1, nhân đôi phía nhỏ hơn và giới hạn tối đa bằng 1. Khi dùng 999 hoán vị:

\[
p_{\min}=\frac{2}{999+1}=0{,}002.
\]

Quy tắc xử lý giá trị bằng nhau và p hai phía này **không nhất thiết trùng** với `esda.Moran_Local.p_sim` mặc định. Mọi benchmark phải căn chỉnh định nghĩa p trước.

Benjamini–Hochberg FDR được áp dụng trên những ô đủ điều kiện với \(\alpha=0{,}05\). Nhóm HH/LL/HL/LH được xác định bởi dấu z-score và độ trễ láng giềng; kết luận cụm cuối cùng cần vượt ngưỡng ý nghĩa.

### 4.3. Kiểm tra xác định

| Nội dung kiểm tra | Kết quả |
|---|---:|
| Tổng số ô | **8.333** |
| Ô bị loại ở biên | **600** |
| Ô được kiểm định | **7.733** |
| Số láng giềng Queen theo từng ô | **8.333/8.333 khớp** |
| Góc phần tư HH/LL/HL/LH chưa xét ý nghĩa | **7.733/7.733 khớp** |
| Sai khác tuyệt đối Local Moran I lớn nhất | Khoảng **0,00016805**, dùng CSV đã làm tròn |
| Quyết định BH-FDR tính lại từ `lisa_p_sim` | **Khớp 100%** |
| HH có ý nghĩa | **370** |
| LL có ý nghĩa | **2.510** |
| Không có ý nghĩa | **4.853** |
| Ô loại biên | **600** |

Sai khác nhỏ của Local Moran I không được xem là sai thuật toán, do `ntl_mean` và `lisa_I` trong CSV đã làm tròn.

### 4.4. Hoán vị với seed độc lập và tái lập chính xác

Lần kiểm chứng 999 lượt với seed **20261111** thu được tương quan Pearson của pseudo-p khoảng **0,9967** so với dữ liệu xuất. Kết quả seed độc lập: **2.879** ô có ý nghĩa thay vì **2.880**; HH **375** thay vì **370** (Jaccard **~0,935**); LL **2.504** thay vì **2.510** (Jaccard **~0,940**).

Những khác biệt gần ngưỡng FDR có thể do Monte Carlo. Muốn yêu cầu trùng hoàn toàn từng p-value phải dùng cùng thuật toán lấy mẫu, thứ tự hoán vị và seed. Các lượt kiểm chứng sau dùng seed 42 và cùng implementation đã tái lập **toàn bộ** nhãn/p-value baseline.

### 4.5. Kết luận

**ĐẠT trong cấu hình tham chiếu** về adjacency, Local Moran, hoán vị và BH-FDR. Điều đó **không** bảo đảm bản đồ hotspot bất biến khi đổi cách biến đổi NTL, trọng số không gian hoặc kích thước lưới.

<a id="s5"></a>
## 5. Kiểm chứng độc lập trích xuất VIIRS năm 2020

### 5.1. Ảnh tham chiếu Earth Engine

Ảnh năm 2020 được tạo độc lập từ các composite tháng trong khoảng `2020-01-01` đến `2021-01-01`, loại pixel `avg_rad` có `cf_cvg <= 0`, lấy median và sử dụng cùng quy tắc điền 0 với ứng dụng. GeoTIFF được xuất theo bounding box Diên Khánh đã dùng trong lần kiểm chứng.

### 5.2. Dựng đa giác lưới và phép đối chiếu

Ranh giới GADM đầy đủ tọa độ được chuyển sang EPSG:32650, dựng lưới 500 m và cắt theo đường ranh. Kết quả thu được đúng **8.333 đa giác**, với tổng diện tích khớp CSV trong dung sai tọa độ và làm tròn. Trung bình NTL theo ô được tính lại từ phần diện tích giao với pixel nguồn.

Kiểm chứng trung gian ban đầu xác nhận **7.703 ô vuông nguyên vẹn**, khoảng **30 ô cắt nhẹ**, còn **600 ô biên** cần hình học chính xác. Một ngoại lệ gần `grid_id=349` biến mất khi sử dụng tọa độ GADM đầy đủ. **Kết quả cuối cùng thay thế kết luận tạm thời.**

### 5.3. Kết quả cuối cùng

| Chỉ tiêu | Kết quả |
|---|---:|
| Ô được đối chiếu | **8.333** |
| Ô khớp trong dung sai CSV | **8.333/8.333** |
| Dung sai tuyệt đối | **0,00005 nW/cm²/sr** |
| Sai số tuyệt đối trung bình | Khoảng **0,000025 nW/cm²/sr** |
| Sai số tuyệt đối lớn nhất | Khoảng **0,000050 nW/cm²/sr** |
| Tương quan Pearson | Khoảng **0,99999999997** |
| Ô biên cũng được đối chiếu chính xác | **600/600** |
| Kích thước GeoTIFF | **217 × 142 = 30.814 pixel** |

Raster số tháng quan sát cho thấy **12 tháng có `cf_cvg > 0` tại mọi pixel trong vùng xuất**. Đây là số composite tháng đủ điều kiện, **không phải tổng số lần vệ tinh quan sát**. Ảnh median giữ mask không có pixel NoData trong bounding box này.

### 5.4. Kết luận

**ĐẠT:** toàn bộ quy trình raster VIIRS 2020 → trung bình theo đa giác ô lưới được tái lập độc lập đến độ chính xác CSV, kể cả ô ranh giới. Không suy diễn kết quả này cho nơi hoặc năm khác.

<a id="s6"></a>
## 6. Kiểm chứng độc lập trích xuất VIIRS năm 2014

### 6.1. Ảnh tham chiếu và chất lượng dữ liệu

Annual median năm 2014 được tạo độc lập với cùng collection Earth Engine, mặt nạ `cf_cvg > 0`, phạm vi địa lý, scale, phương pháp tổng hợp và trích xuất theo ô lưới.

Ba ảnh tham chiếu (baseline, median giữ mask, số tháng hợp lệ) đều có **217 × 142 pixel**, căn chỉnh với raster 2020. Toàn bộ **30.814 pixel** ghi nhận 12 composite tháng hợp lệ, không có NoData trong ảnh median.

**Một pixel có radiance âm nhẹ** ở năm 2014 giao với **hai ô phân tích**. Ứng dụng đưa giá trị âm hợp lệ về 0 trước `exactextract`; tái hiện đúng bước này đã xử lý chênh lệch ở hai ô.

### 6.2. Kết quả

| Chỉ tiêu | Kết quả |
|---|---:|
| Ô được so sánh | **8.333** |
| Ô khớp trong dung sai làm tròn | **8.333/8.333** |
| Sai số tuyệt đối trung bình | Khoảng **0,00002505 nW/cm²/sr** |
| Sai số tuyệt đối lớn nhất | Khoảng **0,00004999 nW/cm²/sr** |
| Pearson | Khoảng **0,9999999998** |
| Ô biên đạt | **600/600** |
| Pixel VIIRS có bức xạ âm | **1** |
| Ô lưới chịu ảnh hưởng | **2** |

### 6.3. Diễn giải chênh lệch hai năm

NTL trung bình không trọng số trên cùng lưới tăng từ **~0,4452 (2014)** lên **~1,4137 (2020)**, bằng khoảng **3,18 lần** mức năm 2014. Trong 8.333 ô, **8.221 ô tăng** và **112 ô giảm** radiance tuyệt đối.

**ĐẠT** đối với trích xuất raster 2014 và so sánh radiance của hai mốc. Tăng ánh sáng không tự động tương đương tăng GDP hay hoạt động kinh tế.

<a id="s7"></a>
## 7. Độ nhạy của phép tổng hợp ảnh theo năm và dữ liệu thiếu

### 7.1. Thiết kế

Baseline là median của các composite tháng hợp lệ. Hai biến thể được tính từ Earth Engine: (a) **mean không trọng số của các composite tháng** và (b) **median nhưng giữ missing dưới dạng NoData** thay vì điền 0. Giữ nguyên lưới đa giác, quy tắc trích xuất và các tham số LISA.

Annual mean ở đây **không** phải mean có trọng số theo tổng số quan sát vệ tinh `cf_cvg`; nó là mean của các composite tháng.

### 7.2. Kết quả

| Chỉ số | Median (baseline) | Mean năm | Median giữ NoData |
|---|---:|---:|---:|
| NTL trung bình mỗi ô | **1,4137** | **1,4754** | **1,4137** |
| Gini NTL | **0,6809** | **0,6861** | **0,6809** |
| Global Moran I (binary Queen, cùng 8.333 ô) | **0,91413** | **0,91456** | **0,91413** |
| HH có ý nghĩa | **370** | **385** | **370** |
| LL có ý nghĩa | **2.510** | **2.499** | **2.510** |
| Tỷ trọng diện tích HH | **4,617%** | **4,804%** | **4,617%** |

Mean tăng NTL trung bình khoảng **4,37%** so với median. Tuy nhiên, hai tập cụm HH và LL gần nhau: Jaccard HH **~0,961**, LL **~0,962**.

Median giữ mask và median điền 0 trùng hoàn toàn tại địa bàn này, bởi ảnh tham chiếu không có pixel missing. Thử nghiệm này **chưa kiểm tra tác động thực sự của việc điền 0 trong một dữ liệu có khoảng trống quan sát**.

### 7.3. Kết luận

Lựa chọn tổng hợp năm ảnh hưởng vừa phải tới cường độ và phân phối NTL; phần lớn cấu trúc cụm không gian vẫn ổn định trong pilot. **Annual median được giữ làm baseline**; annual mean là cấu hình kiểm tra độ nhạy.

<a id="s8"></a>
## 8. Độ nhạy theo phép biến đổi raw, P99 và log

### 8.1. Cấu hình

Sử dụng annual median 2020, lưới 500 m, Queen, 999 hoán vị, seed 42 và FDR 5%. P99 giới hạn giá trị NTL dương tại **phân vị 99 của ô sáng**, trước khi chuẩn hóa. Log ở LISA lấy **logarit tự nhiên của NTL dương**; khác với phép `log1p(NTL)` dùng trong module động học hai năm.

### 8.2. Kết quả

| Chỉ tiêu | Raw | P99 | Log tự nhiên |
|---|---:|---:|---:|
| HH có ý nghĩa | **370** | **457** | **1.050** |
| LL có ý nghĩa | **2.510** | **2.510** | **2.441** |
| Tổng ô có ý nghĩa | **2.880** | **2.967** | **3.491** |
| Tỷ trọng diện tích HH | **~4,62%** | **~5,70%** | **~13,10%** |
| Số ô quadrant HH trước FDR | **1.072** | **1.135** | **2.517** |

**Jaccard HH:** raw–P99 **0,810**, raw–log **0,352**, P99–log **0,435**.

Cả **370 HH raw** vẫn là HH dưới log, trong khi log bổ sung **680 ô HH**. NTL trung vị chưa biến đổi của 370 HH ban đầu khoảng **13,259**, của 680 HH bổ sung khoảng **2,731**. Khoảng **20,38%** ô kiểm định đổi quadrant khi chuyển raw sang log.

### 8.3. Giải thích thống kê

Phân phối NTL lệch phải rõ rệt. Các ô cực sáng tác động mạnh lên trung bình và độ lệch chuẩn raw. Log nén phần đuôi trên, làm thay đổi dấu z-score của một số ô cũng như dấu trung bình z-score láng giềng. Vì vậy, Jaccard raw–log thấp biểu thị **sự khác biệt có ý nghĩa về định nghĩa thống kê**, không đơn thuần là nhiễu hoán vị hoặc lỗi lập trình.

### 8.4. Quyết định phương pháp

Giữ **raw NTL** làm baseline khi nghiên cứu tập trung bức xạ tuyệt đối; dùng **P99** để kiểm tra phụ thuộc vào ô cực sáng và **log** để phân tích mức độ sáng tương đối. Không nên chọn cấu hình chỉ vì nó tạo nhiều hay ít cụm HH hơn. Khi kết luận nghiên cứu thay đổi mạnh theo phép biến đổi, cần báo cáo điều đó.

<a id="s9"></a>
## 9. Độ vững không gian: Queen/Rook và 500 m/1.000 m

### 9.1. Thiết kế

Queen xét ô chung cạnh hoặc chung đỉnh; Rook chỉ xét ô chung cạnh. Lưới 1.000 m được dựng lại từ ranh giới GADM và **raster VIIRS nguồn**, không tính bằng cách lấy trung bình đơn giản các ô 500 m trong CSV. Các biến thể đều dùng raw annual median, 999 hoán vị, seed 42, FDR 5%.

### 9.2. Bảng so sánh

| Cấu hình | Ô kiểm định | HH | LL | Tỷ trọng diện tích HH |
|---|---:|---:|---:|---:|
| Queen 500 m (baseline) | **7.733** | **370** | **2.510** | **4,62%** |
| Rook 500 m | **7.733** | **187** | **906** | **2,33%** |
| Queen 1.000 m | **1.865** | **92** | **562** | **4,59%** |
| Rook 1.000 m | **1.865** | **46** | **210** | **2,30%** |

Toàn bộ lưới 1.000 m có **2.162 đa giác**; con số **1.865** là số ô hợp lệ sau khi loại biên.

Ở 500 m, **187 HH của Rook** đều thuộc tập HH Queen. Thay đổi định nghĩa láng giềng khiến diện tích HH giảm xấp xỉ một nửa.

Khi đổi từ 500 sang 1.000 m, diện tích HH Queen từ **92,5 km² → 92,0 km²**; Rook từ **46,75 km² → 46,0 km²**. Tổng diện tích gần nhau không đồng nghĩa vị trí giống hệt. Kết quả chồng đa giác: **Jaccard không gian 0,655** cho Queen (giao HH ~**73,0 km²**) và **0,686** cho Rook (giao ~**37,75 km²**).

### 9.3. Kết luận

**ĐÃ ĐÁNH GIÁ ĐỘ NHẠY.** Tổng diện tích HH khá ổn định khi đổi kích thước ô, nhưng đường biên cụm thay đổi đáng kể; kết quả nhạy hơn với lựa chọn Queen hay Rook. Không có hệ trọng số nào tự động đúng trong mọi nghiên cứu. Cần chọn theo lý thuyết về quan hệ không gian và báo cáo độ vững tương ứng.

<a id="s10"></a>
## 10. Kiểm chứng động học không–thời gian và Spatial Markov

### 10.1. Chuẩn hóa theo từng năm và vector thay đổi

Module tính:

\[
v_{it}=\log(1+\max(\mathrm{NTL}_{it},0))
\]

và chuẩn hóa **riêng ở từng năm** trên tập ô hợp lệ, không thuộc biên:

\[
z_{it}=\frac{v_{it}-\bar{v}_t}{s_{v,t}}.
\]

Độ trễ Queen và các thay đổi:

\[
\Delta z_i=z_{i,2020}-z_{i,2014}, \qquad
\Delta Wz_i=(Wz)_{i,2020}-(Wz)_{i,2014},
\]

\[
m_i=\sqrt{(\Delta z_i)^2+(\Delta Wz_i)^2}.
\]

Ô chỉ được gán nhóm chuyển động khi đủ điều kiện và **\(m_i\ge 0{,}05\)**. Đây là **ngưỡng mô tả hướng thay đổi**, **không phải** p-value hoặc ngưỡng FDR.

### 10.2. Định nghĩa nhóm

| Mã CSV được giữ tương thích | Ý nghĩa hiển thị | Dấu thay đổi |
|---|---|---|
| `1_Synergistic_Growth` | Ô và láng giềng cùng tăng vị thế tương đối | Δz ≥ 0, ΔWz ≥ 0 |
| `2_Agglomeration_Shadow` | Ô giảm, láng giềng tăng vị thế tương đối | Δz < 0, ΔWz ≥ 0 |
| `3_Emergent_Pioneer` | Ô tăng, láng giềng giảm vị thế tương đối | Δz ≥ 0, ΔWz < 0 |
| `4_Synchronized_Decline` | **Ô và láng giềng cùng giảm vị thế tương đối** | Δz < 0, ΔWz < 0 |
| `Excluded_or_Static` | Không hợp lệ hoặc độ thay đổi dưới ngưỡng | Không hợp lệ hoặc m < 0,05 |

### 10.3. Kết quả quan sát

| Nhóm | Số ô | NTL tăng tuyệt đối | NTL giảm tuyệt đối |
|---|---:|---:|---:|
| Cùng tăng vị thế tương đối | **1.456** | 1.456 | 0 |
| Ô giảm / láng giềng tăng vị thế | **75** | 75 | 0 |
| Ô tăng / láng giềng giảm vị thế | **194** | 194 | 0 |
| **Cùng giảm vị thế tương đối** | **4.711** | **4.624** | **87** |
| Loại khỏi phân tích / thay đổi nhỏ | **1.897** | 1.872 | 25 |
| **Tổng** | **8.333** | **8.221** | **112** |

**4.624/4.711 ô (~98,15%)** mang mã `4_Synchronized_Decline` vẫn có **radiance tăng tuyệt đối**. Không có mâu thuẫn số học: vị thế của các ô và láng giềng trong phân phối NTL được chuẩn hóa **riêng mỗi năm** đã giảm tương đối.

### 10.4. Độ nhạy của ngưỡng mô tả

| Ngưỡng \(m_i\) | Số ô cùng giảm vị thế tương đối |
|---|---:|
| 0,025 | **5.242** |
| 0,050 | **4.711** |
| 0,100 | **2.949** |
| 0,200 | **1.111** |

Phân loại nhạy rõ với ngưỡng. Không được mô tả nhãn nhóm là “có ý nghĩa thống kê” chỉ vì ô được gán nhóm.

### 10.5. Spatial Markov

Module xếp hạng `log1p(NTL)` thành bốn quartile ở từng năm và tính ma trận chuyển dịch, gồm các phân nhóm theo độ sáng láng giềng ban đầu cao/thấp so với trung vị. Khoảng **74,90%** ô vẫn thuộc cùng quartile từ 2014 đến 2020. Điều này phản ánh **mức độ duy trì thứ hạng tương đối**, không phải độ sáng tuyệt đối không đổi.

### 10.6. Tái lập và ảnh hưởng làm tròn

Các công thức, nhãn hướng thay đổi và bảng chuyển dịch đã được tái tính từ CSV xuất. Có một ô `grid_id=3922` rất gần ngưỡng **0,05**; khi tính trực tiếp từ NTL lưu bốn chữ số thập phân, nhãn ô này có thể thay đổi. Dựa trên thông tin vector do ứng dụng xuất, kết quả tái lập **8.333/8.333** nhãn. Đây là hạn chế độ chính xác khi xuất số, chưa phải bằng chứng lỗi mới.

### 10.7. Điều chỉnh cách diễn giải

Nhãn cũ “Synchronized Decline” dễ gây hiểu nhầm thành suy giảm kinh tế hoặc ánh sáng tuyệt đối. **PR #11 đã merge** và sửa nhãn hiển thị theo hướng **giảm vị thế tương đối**, giải thích ngưỡng 0,05, trong khi giữ nguyên mã CSV và toàn bộ công thức số.

### 10.8. Giới hạn thời gian còn lại

Kiểm chứng raster độc lập hiện bao phủ **hai năm đầu–cuối (2014 và 2020)**, chưa phải chuỗi thời gian hằng năm đầy đủ. Vấn đề độ phủ từng năm, hiệu chỉnh cảm biến, ánh sáng nền và chính sách tổng hợp ảnh liên thời gian vẫn chưa hoàn tất.

<a id="s11"></a>
## 11. Kiểm chứng hội tụ với GHSL

### 11.1. Kết quả báo cáo từ ứng dụng

Bảng kiểm tra chất lượng của ứng dụng đối chiếu NTL với hai biến GHSL tại Diên Khánh năm 2020:

| Dữ liệu đối chứng | Spearman ρ | Khoảng tin cậy 95% theo block bootstrap | AUC cho nhóm 25% cao nhất |
|---|---:|---|---:|
| Bề mặt xây dựng GHSL | **0,629** | **~0,59–0,68** | **0,867** |
| Dân số GHSL | **0,616** | **~0,58–0,66** | **0,851** |

Khoảng **63%** giá trị GHSL ở cấp ô được hiển thị bằng 0, tùy sản phẩm và cách đo. Tương quan dương là bằng chứng hội tụ sơ bộ có giá trị tham khảo.

### 11.2. Trạng thái

**MỘT PHẦN.** Chưa tái lập độc lập toàn bộ nguồn raster GHSL, cách căn chỉnh lưới, xử lý zero, Spearman, AUC và block bootstrap. Các kết quả ở trên **do ứng dụng báo cáo**, chưa phải benchmark độc lập ngang cấp với kiểm chứng VIIRS. Bề mặt xây dựng và dân số GHSL không thể thay thế dữ liệu GDP hoặc hoạt động kinh tế thực địa.

### 11.3. Phép kiểm cần hoàn thành

Dùng cùng đa giác lưới, đúng phiên bản/sản phẩm GHSL, năm tham chiếu, hệ tọa độ nguồn và phép thống kê trích xuất. Công bố số ô zero, tái tính tương quan hạng, AUC với nhãn dương được định nghĩa rõ, block bootstrap cùng quy tắc chia cụm và khoảng tin cậy; đồng thời đánh giá độ lệch độ phân giải.

<a id="s12"></a>
## 12. Kiểm thử hồi quy và thay đổi mã nguồn

### 12.1. Phát hiện audit

Audit mã nguồn ban đầu phát hiện: (i) Local Moran lấy mẫu hoán vị có hoàn lại, trái với phương pháp mẫu có điều kiện không hoàn lại; (ii) nguy cơ mất mask cho NoData sentinel hữu hạn trong bước chuyển đổi raster; và (iii) trường hợp sai tên GADM nêu ở Mục 3.

**[PR #10](https://github.com/hoanfg/spatial-app/pull/10)** sửa lấy mẫu không hoàn lại, chuẩn hóa Local Moran theo quy ước ESDA, bảo toàn raster mask, sửa metadata và bổ sung kiểm thử hồi quy.

### 12.2. Kết quả CI

Sau khi PR #10 merge, hai nhóm GitHub Actions ghi nhận **32** và **22** kiểm thử đạt, tổng cộng **54** lượt kiểm thử trong các job liên quan. Đây là bằng chứng hồi quy mã nguồn theo fixture, không phải benchmark Earth Engine thực.

**[PR #11](https://github.com/hoanfg/spatial-app/pull/11)** cập nhật cách diễn giải chế độ Space-Time, ngưỡng 0,05 và giữ tương thích CSV. GitHub Actions của PR này hoàn thành thành công. Thay đổi chỉ liên quan giao diện/tài liệu, không sửa kết quả số.

### 12.3. Giới hạn tái lập

Fixture tĩnh không khẳng định hiệu năng trên mọi đầu vào. Hai cài đặt thống kê có thể dùng chung giả định phương pháp, nên sự phù hợp của chúng không loại bỏ toàn bộ thiên lệch thiết kế. Đối chiếu độc lập raster–đa giác trên dữ liệu vệ tinh thật là tầng bằng chứng bổ sung, được lưu cùng kết quả CI.

<a id="s13"></a>
## 13. Trạng thái toàn chương trình và công việc còn lại

| Mã | Hạng mục | Trạng thái | Nội dung chưa hoàn thành |
|---|---|---|---|
| V01 | Hình học/GID GADM Trung Quốc | **ĐẠT trong tập được audit** | Mở rộng khi thêm quốc gia |
| V02 | Kiểm thử tự động và sửa hồi quy | **ĐẠT theo CI đã xem** | Kiểm thử liên tục ở commit mới |
| V03 | LISA và BH-FDR độc lập | **ĐẠT: Diên Khánh 2020** | Thử thêm địa lý, seed |
| V04 | VIIRS raster 2020 → ô | **ĐẠT: 8.333/8.333** | Khả năng khái quát |
| V05 | VIIRS raster 2014 → ô | **ĐẠT: 8.333/8.333** | Nhiều năm, độ phủ thay đổi |
| V06 | Mean/median, missing | **ĐÃ ĐÁNH GIÁ ĐỘ NHẠY** | Địa bàn/năm có missing thực |
| V07 | Raw/P99/log | **ĐÃ ĐÁNH GIÁ ĐỘ NHẠY** | Kết quả ở vùng khác |
| V08 | Queen/Rook, kích thước ô | **ĐÃ ĐÁNH GIÁ ĐỘ NHẠY** | Địa hình, cấu trúc khác |
| V09 | Space-Time và Markov | **ĐẠT phép tính; ĐÃ SỬA diễn giải** | Kiểm chứng động học rộng hơn |
| V10 | GHSL | **MỘT PHẦN** | Tái tính độc lập từ raster GHSL |
| V11 | Kiểm chứng nhiều địa phương | **CHƯA THỰC HIỆN** | Ít nhất 2–3 địa bàn đối lập |
| V12 | Chuỗi nhiều năm liên tục | **MỘT PHẦN** | Raster và cờ chất lượng từng năm |
| V13 | Giá trị đại diện kinh tế | **CHƯA THỰC HIỆN** | Chỉ báo kinh tế độc lập phù hợp |
| V14 | Streamlit Cloud | **CHƯA THỰC HIỆN** | RAM, thời gian, xử lý lỗi, xuất dữ liệu |

### 13.1. Thứ tự ưu tiên

1. **Nhiều địa phương:** chọn lõi đô thị sáng mạnh, khu công nghiệp/ven đô và vùng nông thôn ánh sáng thấp; nêu lý do lựa chọn và tôn trọng cơ chế bảo vệ RAM.
2. **GHSL độc lập:** ghép đúng raster GHSL vào ô đã kiểm chứng và tái lập các chỉ số của bảng chất lượng.
3. **Chuỗi năm liên tục:** cùng ranh giới và lưới, đánh giá missing, bất thường và tính nhất quán composite từng năm.
4. **Vận hành:** ghi peak RAM, thời gian chạy, lỗi Earth Engine/retry và khả năng xuất dữ liệu trên Streamlit Community Cloud.
5. **Đại diện kinh tế:** đối chiếu với chỉ báo kinh tế có nguồn đáng tin và phạm vi địa lý tương ứng, không tự khẳng định nhân quả.

Một chương trình validation có giá trị khoa học không yêu cầu tất cả tương quan phải cao. Điều cần có là phép tính đúng, phương pháp rõ, phạm vi kiểm chứng xác định, đánh giá bất định và công bố minh bạch các kết quả phụ thuộc giả định.

<a id="s14"></a>
## 14. Danh mục và bảo quản bằng chứng

### 14.1. Báo cáo và sản phẩm liên quan

| Nhóm | Báo cáo Markdown gốc | Bằng chứng bổ sung |
|---|---|---|
| Audit repository | `verification-report.md`; `Báo cáo kiểm chứng NTL spatial econometrics.md` | `spatial-app-audit-evidence.zip` |
| LISA/FDR | `yanqing_validation_report.md` | `yanqing_validation_evidence.zip`; `yanqing_lisa_independent_cell_comparison.csv` |
| VIIRS 2020 tạm thời | `yanqing_viirs_validation_report.md` | `yanqing_viirs_validation_evidence.zip`; `yanqing_viirs_reference_interior_comparison.csv` |
| VIIRS 2020 cuối cùng | `yanqing_viirs_all_cells_validation_report.md` | `yanqing_viirs_all_cells_validation_evidence.zip`; `yanqing_viirs_all_8333_polygon_comparison.csv` |
| VIIRS 2014 | `yanqing_2014_temporal_raster_validation_report.md` | `yanqing_2014_temporal_raster_validation_evidence.zip`; `yanqing_2014_viirs_cell_validation.csv` |
| Độ nhạy tổng hợp ảnh | `yanqing_2020_measurement_sensitivity_report.md` | `yanqing_2020_measurement_sensitivity_evidence.zip`; `yanqing_2020_measurement_sensitivity_cells.csv` |
| Độ nhạy phép biến đổi | `yanqing_2020_transformation_sensitivity_report.md` | `yanqing_2020_transformation_sensitivity_evidence.zip`; `yanqing_2020_transformation_sensitivity_cells.csv` |
| Độ vững không gian | `yanqing_spatial_robustness_validation_report.md` | `yanqing_spatial_robustness_evidence.zip`; `yanqing_spatial_robustness_500m_cells.csv`; `yanqing_spatial_robustness_1000m_cells.csv` |
| Động học thời gian | `yanqing_temporal_validation_report.md` | `yanqing_temporal_validation_evidence.zip`; `yanqing_temporal_validation_by_cell.csv`; `yanqing_temporal_regime_summary.csv`; `yanqing_temporal_markov_counts.csv` |

### 14.2. Phạm vi lưu trữ

Repository hiện có **một phần bộ bằng chứng thực**, truy cập tại [validation/evidence/yanqing](../validation/evidence/yanqing/README.md), gồm các CSV gốc đủ 8.333 ô, bảng kiểm tra độc lập LISA và VIIRS 2020 theo ô, ZIP mã tái lập LISA, và GeoTIFF tham chiếu VIIRS 2014. Bảng chỉ mục ghi mã định danh Git và SHA-256 cho dữ liệu nhị phân đã công bố. Tuy nhiên, **chưa đăng đầy đủ** raster 2020, hình học lưới, toàn bộ script và kết quả các đợt độ nhạy. Gói ZIP tổng hợp 73 file đã được tạo và có checksum nhưng **chưa lưu trong GitHub**; không được khẳng định người ngoài có thể tái lập mọi kết quả chỉ từ repository.

Trước khi công bố học thuật, cần lưu gói bằng chứng đầy đủ vào kho bền vững và cập nhật đường dẫn cùng checksum tại đây.

### 14.3. Kết quả trung gian được thay thế

Kiểm chứng VIIRS 2020 ban đầu chỉ đối chiếu chính xác các ô nguyên vẹn và xấp xỉ phần biên. Kết quả đó đã được **thay thế** bằng kiểm chứng đa giác GADM đủ precision trên **8.333/8.333** ô. Tương tự, kết quả pseudo-p với seed khác là biến thiên ngẫu nhiên Monte Carlo, không mâu thuẫn với việc tái lập chính xác khi dùng cùng seed.

Không xóa các bản gốc khỏi lịch sử nghiên cứu; chỉ xác định rõ kết luận cuối cùng được ưu tiên.

<a id="s15"></a>
## 15. Quy trình cập nhật đặc tả

### 15.1. Thông tin bắt buộc cho đợt mới

Mỗi chiến dịch phải ghi rõ:

1. Ngày, commit/PR, mã validation và câu hỏi nghiên cứu.
2. Địa bàn/GID, năm, sản phẩm vệ tinh, band, scale, CRS.
3. Mặt nạ missing, quy tắc zero/âm, baseline và biến thể.
4. Lưới, ô biên, trọng số láng giềng, seed, số hoán vị, quy tắc p/FDR.
5. Tiêu chí chấp nhận, số ô, sai số, độ chồng lấp, ngoại lệ và độ bất định.
6. Script tái lập, danh mục đầu vào, hash và nơi lưu bằng chứng.
7. Kết luận có giới hạn phạm vi, trạng thái và hành động tiếp theo.

Cập nhật bảng trạng thái ở Mục 13, bổ sung kết quả chi tiết vào mục thích hợp (hoặc thêm mục đánh số mới), đồng thời ghi một dòng vào lịch sử. Không xóa hoặc âm thầm thay thế kết quả mâu thuẫn; phải nêu rõ vì sao kết luận được điều chỉnh.

### 15.2. Mẫu cập nhật

```markdown
### YYYY-MM-DD - Vxx: Tên đợt kiểm chứng
- Commit / Pull Request:
- Địa bàn (GID), năm, sản phẩm vệ tinh:
- Raster nguồn, mặt nạ, lưới, hệ tọa độ:
- Cấu hình baseline và cấu hình đối chứng:
- Script tái lập, hash dữ liệu, nơi lưu bằng chứng:
- Seed, số hoán vị, quy tắc ý nghĩa thống kê:
- Tiêu chí chấp nhận:
- Kết quả chi tiết và ngoại lệ:
- Diễn giải và giới hạn chưa giải quyết:
- Trạng thái mới và bước kế tiếp:
```

### 15.3. Lịch sử chỉnh sửa

| Ngày | Nội dung | Tham chiếu |
|---|---|---|
| 11/11/2026 | Audit GADM Trung Quốc; sửa Local Moran/NoData | [PR #10](https://github.com/hoanfg/spatial-app/pull/10) |
| 11/11/2026 | Kiểm chứng VIIRS 2014/2020 và các phép thử thống kê, không gian, thời gian | Danh mục bằng chứng ở Mục 14 |
| 11/11/2026 | Làm rõ chế độ Space-Time tương đối và ngưỡng mô tả | [PR #11](https://github.com/hoanfg/spatial-app/pull/11) |
| 11/11/2026 | Thiết lập sổ cái validation thống nhất | [PR #12](https://github.com/hoanfg/spatial-app/pull/12) |
| 11/11/2026 | Mở rộng tài liệu thành bản kỹ thuật tổng hợp | [PR #13](https://github.com/hoanfg/spatial-app/pull/13) |
| 11/11/2026 | Tách đặc tả validation thành phiên bản tiếng Việt và tiếng Anh | Lần cập nhật tài liệu hiện tại |

---

**Kết luận chung:** Việc trích xuất VIIRS, suy luận Local Moran và công thức động học hai thời điểm đã có bằng chứng độc lập mạnh **trong trường hợp Diên Khánh được thử**. Những độ nhạy quan trọng theo phép biến đổi, trọng số không gian và ngưỡng thời gian đã được định lượng. Khả năng áp dụng trên nhiều địa phương, pipeline GHSL độc lập, chuỗi nhiều năm liên tục, giá trị đại diện kinh tế và độ tin cậy trên Streamlit Cloud **vẫn chưa được kiểm chứng đầy đủ**.

[Về đầu trang](#top)
