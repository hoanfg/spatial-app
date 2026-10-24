# ĐẶC TẢ KỸ THUẬT: KIẾN TRÚC TRÍCH XUẤT DỮ LIỆU GADM v4.1 & PHÂN LOẠI QUỐC GIA CHO KINH TẾ LƯỢNG KHÔNG GIAN

**Dự án:** Nighttime lights (NTL) data extractor & Spatial econometrics engine  

**Phiên bản tài liệu:** 1.0  

**Mục tiêu:** Chuẩn hóa ranh giới hành chính toàn cầu từ cơ sở dữ liệu GADM v4.1 (`.gpkg`) sang cấu trúc 3 cấp đồng nhất (`Quốc gia -> Thư mục Cấp 1 -> Tệp GeoJSON Cấp 2`) phục vụ trích xuất bức xạ đêm VIIRS và kiểm định LISA/Moran's I - [[Đọc sổ tay kỹ thuật tại đây]](README-vi.md).

---

## 1. CHẨN ĐOÁN NGUYÊN NHÂN GỐC RỄ CỦA DỮ LIỆU RÁC TRONG GADM v4.1

Khi xử lý tự động các tệp GeoPackage (`gadm41_XXX.gpkg`), có 5 cạm bẫy kỹ thuật khiến các kịch bản trích xuất thông thường sinh ra dữ liệu rác hoặc làm méo mó kết quả hồi quy không gian:

1. **Bẫy chuỗi ký tự `"NA"` (literal string `"NA"` vs. SQL `NULL`):**
   Cơ sở dữ liệu GADM v4.1 được xuất từ môi trường R (`terra` / `sf`), trong đó rất nhiều giá trị khuyết thiếu ở các cột `NAME_1`, `NAME_2`, `NAME_3`, `TYPE_2`, `ENGTYPE_2` được lưu dưới dạng **chuỗi văn bản `"NA"`** (hoặc `"?"`, `"Unknown"`) thay vì giá trị `NULL` (`NaN`). Do đó, hàm `.dropna()` của Pandas hoàn toàn bỏ lọt các dòng này, dẫn đến:
   * Tạo ra thư mục rác tên là `NA` (khi `NAME_1 == "NA"`).
   * Gộp hàng chục quận đô thị không liên quan (có chung `NAME_2 == "NA"`) thành một siêu đa giác nặng hàng chục MB.

2. **Bẫy đa giác mặt nước nội địa (`Water body` / `Lake` polygons):**
   Trong GADM v4.1, nhiều hồ lớn, vịnh hoặc vùng nước nội thủy được cắt thành các đa giác riêng biệt ở lớp `ADM_2` và `ADM_3` với cột `ENGTYPE_2` / `ENGTYPE_3` mang giá trị `"Water body"`, `"Lake"`, `"Inland water"`. Nếu không lọc bỏ các dòng này trước khi xuất file, mô hình kinh tế lượng sẽ đưa cả mặt hồ vào mẫu phân tích với giá trị bức xạ $\mathrm{NTL} = 0$, gây thiên lệch nghiêm trọng cho hệ số Gini ánh sáng và mật độ kinh tế.

3. **Bẫy trùng tên đơn vị hành chính (`name collision` khi không dùng `GID_x`):**
   Nếu vòng lặp trích xuất chỉ dùng `.unique()` trên cột `NAME_2` hoặc `NAME_3`, các đơn vị hành chính khác nhau nhưng có cùng tên phiên âm Latinh trong cùng một bang/tỉnh sẽ bị gộp chung thành một tệp `.geojson` duy nhất:
   * **Hoa Kỳ (`USA`):** Các thành phố độc lập (*Independent cities*) tại Virginia, Maryland, Missouri trùng tên với hạt bao quanh chúng (ví dụ: *Fairfax City* và *Fairfax County*; *Baltimore City* và *Baltimore County*; *St. Louis City* và *St. Louis County*). Chúng có cùng `NAME_2`, chỉ phân biệt qua `GID_2` và `ENGTYPE_2`.
   * **Trung Quốc (`CHN`) và Việt Nam (`VNM`):** Khi bỏ dấu hoặc phiên âm Pinyin trong GADM, nhiều quận/huyện khác chữ Hán hoặc khác cấp loại hình (`Shi` vs `Xian`) có cùng chuỗi ký tự trong `NAME_3` / `NAME_2`.
   * **Quy tắc bắt buộc:** Luôn nhóm (`groupby`) theo khóa định danh duy nhất `GID_x` (như `GID_2`, `GID_3`) thay vì `NAME_x`. Nếu trong cùng một thư mục có hai `GID_x` khác nhau nhưng trùng `NAME_x`, tự động hậu tố hóa bằng `ENGTYPE_x` hoặc mã `GID_x`.

4. **Bẫy phân mảnh vi mô:**
   Độ phân giải gốc của ảnh vệ tinh VIIRS DNB hàng tháng là $$\approx 463.83 \text{ m}$$ (diện tích 1 điểm ảnh $\approx 0.215 \text{ km}^2$), và thuật toán kiểm định LISA/Moran's I trong hệ thống yêu cầu tối thiểu $N \ge 30$ ô lưới để suy diễn thống kê có ý nghĩa. Với lưới tiêu chuẩn $$500 \text{ km}^2$$ - $$1000 \text{ km}^2$$, đơn vị phân tích lý tưởng phải có diện tích tối thiểu từ $$10 \text{ km}^2$$ đến $$5,000 \text{ km}^2$$ (tương đương cấp Quận/Huyện/Thành phố). Nếu kịch bản tự động đọc lớp sâu nhất (`ADM_3` hoặc `ADM_4`) cho mọi quốc gia, các nước như Việt Nam, Pháp, Thái Lan, Indonesia sẽ bị đẩy xuống cấp Xã/Phường ($$0.2 - 5 \text{ km}^2$$, làm tê liệt kiểm định LISA.

5. **Bẫy bất đối xứng phân cấp giữa đô thị và nông thôn:**
   Một số quốc gia có các đại đô thị trực thuộc trung ương hoặc hạt đô thị bị khuyết cấp trung gian (như `GBR` với các Metropolitan counties và Unitary authorities có `NAME_2 == "NA"`; hoặc `CHN` với 4 thành phố trực thuộc trung ương Bắc Kinh, Thượng Hải, Thiên Tân, Trùng Khánh nằm ngay ở `NAME_1`).

---

## 2. ĐÁNH ĐỔI KIẾN TRÚC (ARCHITECTURAL TRADE-OFF ANALYSIS)

Bảng dưới đây so sánh 3 phương án kiến trúc cho đường ống dữ liệu:

| Tiêu chí đánh giá | Phương án 1: Blind dynamic self-healing (Tự động đọc lớp sâu nhất + nhảy cột khi gặp `'NA'`) | Phương án 2: Simple strict extractor + front-end alias JSON (Cắt cứng + Ánh xạ tên ở UI) | Phương án 3 (Khuyến nghị): Declarative rule-driven ETL (Trích xuất điều khiển bằng bảng quy tắc quốc gia) |
| :--- | :--- | :--- | :--- |
| **Chất lượng hình học** | **Thấp:** Dễ trộn lẫn đa giác cấp Hạt (lớn) với cấp Xã/Quận (nhỏ) trong cùng một quốc gia khi chỉ một số dòng có `NAME_2 == 'NA'`. | **Thấp (nếu dữ liệu gốc bất đối xứng):** File JSON ở Front-end chỉ đổi được nhãn hiển thị, không thể tách một đa giác `NA` 37MB đã bị gộp sai từ dưới ổ cứng. | **Tuyệt đối:** Xử lý dứt điểm việc gộp/tách hình học (`dissolve` theo `GID`) ngay tại bước tạo file `.geojson`. |
| **Tính đồng nhất kinh tế lượng** | **Kém:** Gây hiện tượng *Cross-level mixing* (các dòng trong bảng Panel không cùng cấp độ hành chính, vi phạm giả định đồng nhất đơn vị quan sát). | **Tốt** đối với các nước đồng nhất (`CHN`, `VNM`), nhưng **thất bại** với các nước lai ghép (`GBR`, `TWN`). | **Tối ưu:** Đảm bảo 100% các tệp `.geojson` trong cùng một quốc gia đại diện cho các đơn vị kinh tế tương đương. |
| **Hiệu năng Runtime trên Streamlit Cloud (~1GB RAM)** | **Rủi ro tràn bộ nhớ:** Sinh ra hàng chục ngàn file cấp xã/phường cho các nước có `ADM_3`/`ADM_4`. | **Nhanh:** Front-end nhẹ, nhưng phải duy trì file JSON khổng lồ hàng chục ngàn dòng nếu muốn sửa tên từng quận. | **Tối ưu nhất:** Toàn bộ chi phí xử lý nặng được thực hiện Offline 1 lần. `app.py` giữ nguyên cấu trúc đọc thư mục cực nhẹ hiện tại. |
| **Khả năng bảo trì** | Khó kiểm soát lỗi ngầm khi thêm quốc gia mới. | Phải sửa cả script trích xuất lẫn file JSON ở Front-end. | Chỉ cần thêm 1 dòng khai báo quy tắc (5 thuộc tính) vào từ điển `COUNTRY_RULES` trong script ETL. |

**Kết luận kiến trúc:**  
Không đặt logic chữa lỗi hình học ở front-end và không để trình trích xuất tự đoán lớp sâu nhất một cách mù quáng. Hãy sử dụng **trình trích xuất điều khiển bằng quy tắc khai báo**: quy định rõ từng nhóm quốc gia đọc lớp nào (`layer`), cột nào làm thư mục (`folder_expr`), cột nào làm tệp (`file_expr`), và khóa nhóm duy nhất (`gid_col`).

---

## 3. BẢNG PHÂN LOẠI QUỐC GIA GADM v4.1

Toàn bộ các quốc gia và vùng lãnh thổ (khớp với danh mục `COUNTRY_NAMES` trong `app.py`) được phân loại vào **4 nhóm cấu trúc** dưới đây:

### Nhóm 1: `STANDARD_ADM2` (Chuẩn cấp 2, Chiếm ~85% quốc gia)

* **Đặc điểm:** Cấp 1 (`NAME_1`) là Bang / Tỉnh / Thành phố trực thuộc trung ương; Cấp 2 (`NAME_2`) là Quận / Huyện / Hạt / Thành phố thuộc tỉnh, phủ kín 100% lãnh thổ và có quy mô diện tích lý tưởng cho lưới NTL ($$500 \text{ km}^2$$ - $$2000 \text{ km}^2$$).

* **Cấu hình trích xuất:**
  * `layer`: `ADM_ADM_2`
  * `Thư mục (State/Province)`: `NAME_1`
  * `Tệp (District/County)`: `NAME_2` (nhóm theo `GID_2`, dùng `ENGTYPE_2` để phân biệt nếu trùng `NAME_2`)
   
* **Danh sách quốc gia áp dụng:**
  * **Đông Nam Á:** `VNM` (Việt Nam - 63 tỉnh, 705 quận/huyện), `THA` (Thái Lan - 77 tỉnh, 928 Amphoe/Khet), `IDN` (Indonesia - 34 tỉnh, 514 Kabupaten/Kota), `MYS` (Malaysia - 16 bang, 160 Daerah), `PHL` (Philippines - 81 tỉnh + Metro Manila, 1,634 đô thị), `KHM` (Campuchia - 25 tỉnh, 197 huyện), `LAO` (Lào - 18 tỉnh, 148 huyện), `MMR` (Myanmar - 15 bang/vùng, 330 townships), `TLS` (Đông Timor - 13 đô thị, 65 subdistricts).
  
  * **Đông Á & Nam Á:** `JPN` (Nhật Bản - 47 tỉnh, ~1,741 Shi/Ku/Machi/Mura), `KOR` (Hàn Quốc - 17 tỉnh/thành, ~250 Si/Gun/Gu), `PRK` (Triều Tiên), `MNG` (Mông Cổ - 22 tỉnh, 339 Sums), `IND` (Ấn Độ - 36 bang/UT, ~676 Districts), `BGD` (Bangladesh - 8 Divisions, 64 Districts; hoặc `ADM_3` cho 544 Upazilas), `PAK` (Pakistan - 8 đơn vị cấp 1, ~36 Divisions ở `ADM_2` hoặc ~160 Districts ở `ADM_3`), `LKA` (Sri Lanka - 25 Districts ở `ADM_1`, 331 DS Divisions ở `ADM_2`), `NPL` (Nepal).
  
  * **Châu Mỹ:** `USA` (Hoa Kỳ - 50 bang + DC, 3,143 Counties/Independent Cities), `CAN` (Canada - 13 tỉnh/lãnh thổ, 293 Census Divisions), `MEX` (Mexico - 32 bang, 2,469 Municipios), `BRA` (Brazil - 27 bang, 5,570 Municípios), `ARG` (Argentina - 24 tỉnh, 528 Departamentos/Partidos), `CHL` (Chile - 16 vùng, 56 tỉnh ở `ADM_2` hoặc 346 Comunas ở `ADM_3`), `COL` (Colombia - 33 vùng, 1,122 Municipios), `PER` (Peru - 26 vùng, 196 Provincias), `VEN`, `CUB`.
  
  * **Châu Âu:** `DEU` (Đức - 16 bang, 401 Kreise/Kreisfreie Städte), `FRA` (Pháp - 13 vùng, 96 Départements ở `ADM_2`), `ITA` (Ý - 20 vùng, 107 tỉnh/thành phố đô thị ở `ADM_2`), `ESP` (Tây Ban Nha - 17 cộng đồng tự trị, 52 tỉnh ở `ADM_2` hoặc 326 Comarcas ở `ADM_3`), `POL` (Ba Lan - 16 tỉnh, 380 Powiaty), `NLD` (Hà Lan - 12 tỉnh, 342 Gemeenten), `BEL` (Bỉ - 3 vùng, 11 tỉnh/Arrondissements), `CHE` (Thụy Sĩ - 26 Cantons, 143 Bezirke), `AUT` (Áo - 9 bang, 94 Bezirke), `CZE`, `HUN`, `ROU`, `BGR`, `GRC`, `PRT`, `SWE` (Thụy Điển - 21 hạt, 290 Kommuner), `NOR` (Na Uy - 11 hạt, 356 Kommuner), `DNK` (Đan Mạch - 5 vùng, 99 Kommuner), `FIN`, `RUS` (Nga - ~85 chủ thể liên bang, ~2,350 Raions/Cities), `UKR`, `TUR` (Thổ Nhĩ Kỳ - 81 tỉnh, 973 Ilçe).
  
  * **Châu Đại Dương, Trung Đông & Châu Phi:** `AUS` (Úc - 8 bang/lãnh thổ, 562 Local Government Areas), `NZL` (New Zealand - 16 vùng, 67 Territorial Authorities), `SAU`, `EGY`, `ZAF`, `NGA` (Nigeria - 37 bang, 774 LGAs), `KEN`, `ETH`, `MAR`, `DZA`, `GHA`, `TZA`, `KAZ`, `UZB`, `IRN`, `IRQ`.

---

### Nhóm 2: `SHIFTED_ADM3_PREFECTURE` (Dịch chuyển cấp 3: Cấp Địa khu làm thư mục, Cấp Quận/Huyện làm tệp)

* **Đặc điểm:** Cấp `ADM_1` quá rộng (quy mô 50–120 triệu dân như một quốc gia châu Âu), `ADM_2` mới là các Thành phố cấp địa khu (Prefecture-level cities như Thâm Quyến, Quảng Châu, Vũ Hán, Tô Châu) hoặc Phân vùng lớn, còn các Quận đô thị lõi và Huyện (`Qu` / `Xian` / `Xianjishi`) nằm ở **`ADM_3`**.
  
* **Trường hợp điển hình nhất: Trung Quốc (`CHN`):**
  * Nếu xuất ở `ADM_2`, toàn bộ thành phố Thâm Quyến hay Quảng Châu chỉ là 1 file duy nhất, không thể phân tích sự phân hóa giữa các quận lõi (Nam Sơn, Phúc Điền, Thiên Hà) và vùng ven.
  * **Xử lý ngoại lệ 4 Thành phố trực thuộc trung ương (`Beijing`, `Shanghai`, `Tianjin`, `Chongqing`) và các huyện trực thuộc tỉnh (`NAME_2 == "NA"`):**
    Ở 4 đô thị này, tên thành phố nằm ngay ở `NAME_1`. Do đó, công thức tạo tên Thư mục chuẩn xác nhất cho `CHN` là:
    * Nếu `NAME_1` thuộc `{"Beijing", "Shanghai", "Tianjin", "Chongqing"}` hoặc `NAME_2` là `"NA"` / trùng `NAME_1`: Thư mục = `NAME_1`.
    * Với 27 tỉnh/khu tự trị còn lại: Thư mục = `NAME_1 + " - " + NAME_2` (ví dụ: `Guangdong - Shenzhen`, `Guangdong - Guangzhou`, `Jiangsu - Suzhou`). Cách đặt tên này giúp người dùng vừa tìm theo Tỉnh dễ dàng trên thanh chọn của Streamlit, vừa tách biệt từng thành phố địa khu, và các tệp bên trong là toàn bộ Quận/Huyện ở `NAME_3` (nhóm theo `GID_3`).
   
* **Các quốc gia khác có thể áp dụng Nhóm 2 (hoặc cấu hình `ADM_3`):**
  * `PAK` (Pakistan - nếu muốn phân tích ở cấp 160 `Districts` tại `ADM_3` thay vì 36 `Divisions` tại `ADM_2`, dùng Thư mục = `NAME_1` và Tệp = `NAME_3`).
  * `BGD` (Bangladesh - nếu muốn phân tích ở cấp 544 `Upazilas` tại `ADM_3` thay vì 64 `Districts` tại `ADM_2`).
  * `FRA` (Pháp - nếu muốn phân tích ở cấp 333 `Arrondissements` tại `ADM_3` với Thư mục = `NAME_2` Département).

---

### Nhóm 3: `ASYMMETRIC_HYBRID` (Bất đối xứng / Khuyết cấp trung gian `NAME_2 = "NA"`)
* **Đặc điểm:** Hệ thống hành chính lai ghép giữa mô hình 2 cấp (Two-tier shire counties) và mô hình 1 cấp (Single-tier Unitary Authorities / Metropolitan Boroughs).
  
* **Trường hợp 1: Vương quốc Anh (`GBR`):**
  * **Cấu trúc thực tế trong `gadm41_GBR.gpkg`:**
    * Lớp `ADM_ADM_1`: Gồm 4 quốc gia cấu thành (`England`, `Scotland`, `Wales`, `Northern Ireland`).
      
    * Lớp `ADM_ADM_2`: Chỉ chứa các hạt nông thôn 2 cấp (như `Kent`, `Essex`, `West Sussex`). Toàn bộ 33 quận của Đại London, 36 quận của 6 hạt đô thị lớn (Greater Manchester, West Midlands, Merseyside, South Yorkshire, West Yorkshire, Tyne and Wear), toàn bộ các Unitary Authorities của England, cùng nhiều vùng của Scotland/Wales đều bị gán `NAME_2 = "NA"`.
      
    * Lớp `ADM_ADM_3`: Chứa **đầy đủ 100% các đơn vị chính quyền địa phương cấp Quận/Hạt chuẩn (Local Authority Districts / London Boroughs / Metropolitan Districts / Unitary Authorities / Council Areas)** trên toàn bộ Vương quốc Anh! Ở các vùng mà `NAME_2` bị khuyết (`"NA"`), tên quận nằm ở `NAME_3`. Ở một vài hạt đơn nhất nhỏ mà `NAME_3` bị khuyết (`"NA"`), tên nằm ở `NAME_2`.
      
  * **Giải pháp trích xuất chuẩn cho `GBR`:**
    * Đọc lớp **`ADM_ADM_3`**.
      
    * **Thư mục (State/Region):** Dùng `NAME_1` (`England`, `Scotland`, `Wales`, `Northern Ireland`), hoặc nếu muốn chia nhỏ `England` theo hạt thì dùng `COALESCE(NAME_2, "England_Unitary_and_Metro")`. Để đồng nhất với 4 bang trong giao diện hiện tại của bạn, đặt Thư mục = `NAME_1`.
      
    * **Tệp (District/Borough):** Dùng hàm hợp nhất **`COALESCE(NAME_3, NAME_2)`** (lấy `NAME_3` nếu hợp lệ, nếu `NAME_3` là `"NA"` thì lùi về lấy `NAME_2`) và nhóm theo khóa duy nhất `COALESCE(GID_3, GID_2)`.
      
    * **Kết quả:** Không mất bất kỳ quận nào của London hay Manchester, không sinh ra bất kỳ đa giác `NA` 37MB nào, và toàn bộ 100% tệp xuất ra đều là các Local Authority Districts đồng cấp.
      
* **Trường hợp 2: Đài Loan (`TWN`):**
  * Trong GADM v4.1, một số huyện/thành phố có sự lệch cấp giữa `NAME_1` và `NAME_2` (do sự tồn tại của 2 tỉnh danh nghĩa `Fujian` và `Taiwan` ở `NAME_1` bên cạnh các thành phố trực thuộc trung ương).
    
  * **Giải pháp cho `TWN`:** Đọc lớp sâu nhất của Đài Loan (`ADM_ADM_2` hoặc `ADM_ADM_3` tùy bản đóng gói), dùng `COALESCE(NAME_2, NAME_1)` làm Thư mục (22 Huyện/Thành phố như *Taipei, New Taipei, Taichung, Kaohsiung, Hsinchu*) và cấp kế tiếp làm Tệp (368 Quận/Hương/Trấn - *Qu/Xiang/Zhen*).

---

### Nhóm 4: `SHALLOW_ADM1_CITY_STATE` (Thành bang & Quốc gia diện tích nhỏ chỉ dùng cấp 1)
* **Đặc điểm:** Quốc gia có diện tích nhỏ hoặc là thành bang đô thị; lớp `ADM_ADM_2` hoặc không tồn tại trong `.gpkg`, hoặc nếu tồn tại thì chỉ là các tổ dân phố nhỏ vài trăm mét vuông.
  
* **Cấu hình trích xuất:**
  * Đọc lớp **`ADM_ADM_1`** (hoặc tự động lùi về `ADM_ADM_1` khi không có `ADM_ADM_2`).
  * **Thư mục:** Tên quốc gia (`COUNTRY` / `NAME_0`) hoặc vùng lớn.
  * **Tệp:** `NAME_1` (nhóm theo `GID_1`).
    
* **Danh sách quốc gia áp dụng:**
  * `SGP` (Singapore - 5 vùng quy hoạch ở `ADM_1`).
  * `HKG` (Hồng Kông - 18 quận hành chính nằm ngay ở `ADM_1`).
  * `MAC` (Ma Cao - các khu vực nằm ở `ADM_1`).
  * `BRN` (Brunei - 4 quận Daerah ở `ADM_1`, hoặc dùng `ADM_2` cho 38 Mukim).
  * `QAT` (Qatar - 8 đô thị Baladiyat ở `ADM_1`).
  * `MDV` (Maldives - 21 Atolls ở `ADM_1`).
  * `ISR` (Israel - 6 Districts ở `ADM_1`, hoặc 15 Sub-districts ở `ADM_2`).
  * `IRL` (Ireland - 26 Counties truyền thống nằm ở `ADM_1`; lớp `ADM_2` là các Municipal Districts).

---

## 4. QUY TRÌNH KIỂM ĐỊNH CHẤT LƯỢNG DỮ LIỆU ĐẦU RA

Mỗi tệp `.geojson` trước khi được ghi xuống ổ cứng để đưa vào `app.py` đều phải đi qua **5 lần kiểm định tự động** trong tập lệnh trích xuất:

1. **Lần 1: Kiểm tra chuỗi rác:**
   Mọi giá trị thuộc tập `{"NA", "N/A", "NULL", "NONE", "UNKNOWN", "?", "", "NAN"}` (không phân biệt hoa thường, đã cắt khoảng trắng) đều bị ép về `None` thực sự trước khi phân tích. Mọi dòng có `NAME_1 is None` (như `bang NA` trong `gadm41_GBR.gpkg`) đều bị loại bỏ hoặc gán lại từ cấp con nếu hợp lệ.

3. **Lần 2: Bộ lọc thủy văn:**
   Loại bỏ hoàn toàn các đa giác có `TYPE_x` hoặc `ENGTYPE_x` chứa từ khóa `Water body`, `Lake`, `Inland water`, `Sea`, `Estuary`.
   
5. **Lần 3: Hợp nhất hình học theo mã định danh:**
   Sửa lỗi tự cắt (self-intersection) bằng `shapely.make_valid()` và gộp (`dissolve`) theo đúng mã `GID` mục tiêu để đảm bảo 1 đơn vị hành chính = 1 tệp `.geojson` duy nhất.
   
7. **Lần 4: Chống ghi đè trùng tên:**
   Nếu trong cùng một thư mục Tỉnh/Bang có 2 đơn vị khác mã `GID` nhưng trùng tên hiển thị (ví dụ: *Fairfax County* và *Fairfax City*), hệ thống tự động gắn hậu tố phân biệt từ `ENGTYPE_x` (ví dụ: `USA_Virginia_Fairfax_County.geojson` và `USA_Virginia_Fairfax_Independent_City.geojson`), tương thích với hàm `list_counties()` và `split_county()` trong `app.py`.
   
9. **Lần 5: Kiểm tra diện tích tối thiểu cho VIIRS:**
   Cảnh báo nếu đa giác có diện tích $< 0.25	ext{ km}^2$ (nhỏ hơn 1 ô lưới $500 	imes 500	ext{ m}$).
