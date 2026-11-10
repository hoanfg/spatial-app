<a id="top"></a>

# 🗂️ Đặc tả kỹ thuật: trích xuất dữ liệu GADM v4.1 & phân loại quốc gia cho kinh tế lượng không gian

| Hạng mục | Nội dung |
| :--- | :--- |
| **Dự án** | Nighttime lights (NTL) data extractor & Spatial econometrics engine |
| **Mục tiêu** | Chuẩn hóa ranh giới hành chính toàn cầu từ cơ sở dữ liệu GADM v4.1 (`.gpkg`) sang cấu trúc 3 cấp đồng nhất, phục vụ trích xuất bức xạ đêm VIIRS và kiểm định LISA/Moran's I. |
| **Tài liệu liên quan** | [📘 Đọc sổ tay kỹ thuật tại đây](https://github.com/hoanfg/spatial-app/blob/main/README-vi.md) |

Cấu trúc đầu ra mà toàn bộ quy trình hướng tới:

```text
Quốc gia
└── Thư mục Cấp 1   (tỉnh / bang)
    └── Tệp GeoJSON Cấp 2   (quận / huyện / hạt)
```

> [!TIP]
> **⚡ Đọc nhanh trong 20 giây**
>
> - **Vấn đề:** dữ liệu GADM v4.1 không "sạch" như vẻ ngoài. Có giá trị khuyết bị lưu thành chữ `"NA"`, có cả hồ nước bị tính như một đơn vị hành chính, có những đơn vị trùng tên, có nước thì cấp hành chính quá nhỏ, có nước lại thiếu hẳn một cấp trung gian.
> - **Nếu bỏ qua:** thư mục rác, đa giác khổng lồ ghép sai, mẫu phân tích lẫn lộn nhiều cấp hành chính, và kết quả hồi quy lệch.
> - **Cách giải:** không đoán mò, mà dùng một **bảng quy tắc khai báo theo từng nhóm quốc gia** (4 nhóm, xem [Mục 3](#s3)), rồi cho mọi tệp đầu ra đi qua **5 lần kiểm định chất lượng** (xem [Mục 4](#s4)).

<details>
<summary><b>📖 Vài ký hiệu hay gặp (bấm để mở)</b></summary>

<br>

| Ký hiệu | Ý nghĩa |
| :--- | :--- |
| **GADM** | Cơ sở dữ liệu ranh giới hành chính toàn cầu. |
| **`.gpkg`** | Tệp GeoPackage chứa dữ liệu không gian, mỗi quốc gia một tệp (`gadm41_XXX.gpkg`). |
| **`ADM_ADM_1`, `ADM_ADM_2`, `ADM_ADM_3`** | Các lớp (layer) trong tệp `.gpkg`, ứng với cấp hành chính 1, 2, 3. |
| **`NAME_x`** | Tên đơn vị hành chính ở cấp *x*. Có thể trùng nhau. |
| **`GID_x`** | Mã định danh **duy nhất** của đơn vị ở cấp *x*. |
| **`TYPE_x`, `ENGTYPE_x`** | Loại hình đơn vị (bản địa và bản tiếng Anh), ví dụ County, Independent City, Water body. |
| **ETL** | Extract – Transform – Load: quy trình trích xuất, biến đổi và ghi dữ liệu. |

</details>

---

<a id="s1"></a>

## 🔍 1. Chẩn đoán nguyên nhân gốc rễ của dữ liệu rác trong GADM v4.1

Khi xử lý tự động các tệp GeoPackage (`gadm41_XXX.gpkg`), có 5 cái bẫy kỹ thuật khiến các kịch bản trích xuất thông thường sinh ra dữ liệu rác, hoặc làm méo kết quả hồi quy không gian.

### 🪤 Bẫy 1: chuỗi `"NA"` (literal string `"NA"` so với SQL `NULL`)

Cơ sở dữ liệu GADM v4.1 được xuất từ môi trường R (`terra` / `sf`). Ở đó, rất nhiều giá trị khuyết trong các cột `NAME_1`, `NAME_2`, `NAME_3`, `TYPE_2`, `ENGTYPE_2` không phải `NULL` (`NaN`) mà được lưu thành **chuỗi văn bản `"NA"`** (hoặc `"?"`, `"Unknown"`). Hàm `.dropna()` của Pandas vì thế bỏ lọt hoàn toàn những dòng này, và hậu quả là:

- Sinh ra một thư mục rác tên `NA` (khi `NAME_1 == "NA"`).
- Gộp hàng chục quận đô thị chẳng liên quan gì nhau (cùng có `NAME_2 == "NA"`) thành một siêu đa giác nặng hàng chục MB.

### 🪤 Bẫy 2: đa giác mặt nước nội địa (`Water body` / `Lake`)

Trong GADM v4.1, nhiều hồ lớn, vịnh hoặc vùng nước nội thủy được cắt thành các đa giác riêng ở lớp `ADM_2` và `ADM_3`. Cột `ENGTYPE_2` / `ENGTYPE_3` của chúng mang các giá trị như `"Water body"`, `"Lake"`, `"Inland water"`.

Nếu không lọc bỏ những dòng này trước khi xuất file, mô hình kinh tế lượng sẽ đưa cả mặt hồ vào mẫu phân tích với bức xạ $\mathrm{NTL} = 0$. Hệ quả là hệ số Gini ánh sáng và mật độ kinh tế bị lệch nghiêm trọng.

### 🪤 Bẫy 3: trùng tên đơn vị hành chính (name collision khi không dùng `GID_x`)

Nếu vòng lặp trích xuất chỉ dùng `.unique()` trên cột `NAME_2` hoặc `NAME_3`, các đơn vị hành chính khác nhau nhưng cùng tên phiên âm Latinh trong một bang/tỉnh sẽ bị gộp vào một tệp `.geojson` duy nhất.

- **Hoa Kỳ (`USA`).** Các thành phố độc lập (*Independent cities*) ở Virginia, Maryland và Missouri trùng tên với hạt bao quanh chúng. Chúng có cùng `NAME_2`, chỉ phân biệt được qua `GID_2` và `ENGTYPE_2`:

  | Thành phố độc lập | Hạt trùng tên |
  | :--- | :--- |
  | *Fairfax City* | *Fairfax County* |
  | *Baltimore City* | *Baltimore County* |
  | *St. Louis City* | *St. Louis County* |

- **Trung Quốc (`CHN`) và Việt Nam (`VNM`).** Khi bỏ dấu hoặc phiên âm Pinyin trong GADM, nhiều quận/huyện khác chữ Hán, hoặc khác cấp loại hình (`Shi` so với `Xian`), lại có cùng chuỗi ký tự trong `NAME_3` / `NAME_2`.

> [!IMPORTANT]
> **Quy tắc bắt buộc:** luôn nhóm (`groupby`) theo khóa định danh duy nhất `GID_x` (như `GID_2`, `GID_3`), không nhóm theo `NAME_x`. Nếu trong cùng một thư mục có hai `GID_x` khác nhau nhưng trùng `NAME_x`, tự động thêm hậu tố bằng `ENGTYPE_x` hoặc mã `GID_x`.

### 🪤 Bẫy 4: phân mảnh vi mô

| Thông số | Giá trị |
| :--- | :--- |
| Độ phân giải gốc của ảnh VIIRS DNB hàng tháng | $\approx 463.83 \text{ m}$ (diện tích một điểm ảnh $\approx 0.215 \text{ km}^2$) |
| Số ô lưới tối thiểu để kiểm định LISA/Moran's I suy diễn có ý nghĩa | $N \ge 30$ |
| Lưới tiêu chuẩn | $500 \text{ m}$ - $1000 \text{ m}$ |
| Diện tích lý tưởng của một đơn vị phân tích (cấp Quận/Huyện/Thành phố) | $10 \text{ km}^2$ đến $5,000 \text{ km}^2$ |
| Diện tích đơn vị ở cấp Xã/Phường | $0.2 - 5 \text{ km}^2$ |

Nếu kịch bản cứ tự động đọc lớp sâu nhất (`ADM_3` hoặc `ADM_4`) cho mọi quốc gia, các nước như Việt Nam, Pháp, Thái Lan, Indonesia sẽ bị đẩy xuống cấp Xã/Phường. Ở quy mô đó, mỗi đơn vị quá nhỏ và kiểm định LISA gần như tê liệt.

### 🪤 Bẫy 5: bất đối xứng phân cấp giữa đô thị và nông thôn

Một số quốc gia có đại đô thị trực thuộc trung ương, hoặc hạt đô thị bị khuyết cấp trung gian:

| Quốc gia | Biểu hiện |
| :--- | :--- |
| `GBR` | Các Metropolitan counties và Unitary authorities có `NAME_2 == "NA"`. |
| `CHN` | 4 thành phố trực thuộc trung ương (Bắc Kinh, Thượng Hải, Thiên Tân, Trùng Khánh) nằm ngay ở `NAME_1`. |

<sub>[↑ Về đầu trang](#top)</sub>

---

<a id="s2"></a>

## ⚖️ 2. Đánh đổi kiến trúc (architectural trade-off analysis)

Bảng dưới đây so sánh 3 phương án kiến trúc cho đường ống dữ liệu (🔴 yếu, 🟡 tạm được, 🟢 tốt):

| Tiêu chí đánh giá | Phương án 1: Blind dynamic self-healing<br><sub>(tự động đọc lớp sâu nhất + nhảy cột khi gặp `'NA'`)</sub> | Phương án 2: Simple strict extractor + front-end alias JSON<br><sub>(cắt cứng + ánh xạ tên ở UI)</sub> | ⭐ Phương án 3 (khuyến nghị): Declarative rule-driven ETL<br><sub>(trích xuất điều khiển bằng bảng quy tắc quốc gia)</sub> |
| :--- | :--- | :--- | :--- |
| **Chất lượng hình học** | 🔴 **Thấp:** dễ trộn đa giác cấp Hạt (lớn) với cấp Xã/Quận (nhỏ) trong cùng một quốc gia, khi chỉ một số dòng có `NAME_2 == 'NA'`. | 🔴 **Thấp (nếu dữ liệu gốc bất đối xứng):** file JSON ở front-end chỉ đổi được nhãn hiển thị, không thể tách một đa giác `NA` 37MB đã bị gộp sai dưới ổ cứng. | 🟢 **Triệt để:** xử lý dứt điểm việc gộp/tách hình học (`dissolve` theo `GID`) ngay ở bước tạo file `.geojson`. |
| **Tính đồng nhất kinh tế lượng** | 🔴 **Kém:** gây hiện tượng *cross-level mixing* (các dòng trong bảng panel không cùng cấp hành chính, vi phạm giả định đồng nhất đơn vị quan sát). | 🟡 **Tốt** với các nước đồng nhất (`CHN`, `VNM`), nhưng **thất bại** với các nước lai ghép (`GBR`, `TWN`). | 🟢 **Tối ưu:** đảm bảo 100% các tệp `.geojson` trong một quốc gia đại diện cho các đơn vị kinh tế tương đương. |
| **Hiệu năng runtime trên Streamlit Cloud (~1GB RAM)** | 🔴 **Rủi ro tràn bộ nhớ:** sinh ra hàng chục ngàn file cấp xã/phường cho các nước có `ADM_3`/`ADM_4`. | 🟡 **Nhanh:** front-end nhẹ, nhưng phải duy trì một file JSON khổng lồ hàng chục ngàn dòng nếu muốn sửa tên từng quận. | 🟢 **Tối ưu nhất:** toàn bộ chi phí xử lý nặng làm offline đúng 1 lần. `app.py` giữ nguyên cấu trúc đọc thư mục cực nhẹ hiện tại. |
| **Khả năng bảo trì** | 🔴 Khó kiểm soát lỗi ngầm khi thêm quốc gia mới. | 🟡 Phải sửa cả script trích xuất lẫn file JSON ở front-end. | 🟢 Chỉ cần thêm 1 dòng khai báo quy tắc (5 thuộc tính) vào từ điển `COUNTRY_RULES` trong script ETL. |

> [!IMPORTANT]
> **Kết luận kiến trúc.** Không đặt logic chữa lỗi hình học ở front-end, và không để trình trích xuất tự đoán lớp sâu nhất một cách mù quáng. Hãy dùng **trình trích xuất điều khiển bằng quy tắc khai báo** với đủ 5 thuộc tính cho mỗi nhóm quốc gia:
>
> | Thuộc tính | Quy định |
> | :--- | :--- |
> | `layer` | Đọc lớp nào |
> | `folder_expr` | Cột nào làm thư mục |
> | `file_expr` | Cột nào làm tệp |
> | `gid_col` | Khóa định danh nhóm duy nhất |
> | `type_col` / `ENGTYPE_x` | Cột loại hình đơn vị (để lọc đa giác mặt nước và gắn hậu tố phân biệt khi trùng tên) |

<sub>[↑ Về đầu trang](#top)</sub>

---

<a id="s3"></a>

## 🌍 3. Bảng phân loại quốc gia GADM v4.1

Toàn bộ các quốc gia và vùng lãnh thổ (khớp với danh mục `COUNTRY_NAMES` trong `app.py`) được phân vào **4 nhóm cấu trúc**:

| Nhóm | Tên | Dùng cho | Lớp đọc | Thư mục | Tệp |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | `STANDARD_ADM2` | Chiếm ~85% quốc gia, cấp 2 là quận/huyện chuẩn | `ADM_ADM_2` | `NAME_1` | `NAME_2` |
| **2** | `SHIFTED_ADM3_PREFECTURE` | Cấp 1 quá rộng, quận/huyện nằm ở cấp 3 (điển hình: `CHN`) | `ADM_ADM_3` | Cấp địa khu (xem [Nhóm 2](#nhom2)) | `NAME_3` |
| **3** | `ASYMMETRIC_HYBRID` | Khuyết cấp trung gian `NAME_2 = "NA"` (`GBR`, `TWN`) | `ADM_ADM_3` (cho `GBR`; `TWN` có cấu hình riêng) | `NAME_1` (cho `GBR`) | `COALESCE(NAME_3, NAME_2)` (cho `GBR`) |
| **4** | `SHALLOW_ADM1_CITY_STATE` | Thành bang và quốc gia nhỏ chỉ dùng cấp 1 | `ADM_ADM_1` | Tên quốc gia hoặc vùng lớn | `NAME_1` |

### 🟦 Nhóm 1: `STANDARD_ADM2` (chuẩn cấp 2, chiếm ~85% quốc gia)

**Đặc điểm:** Cấp 1 (`NAME_1`) là Bang / Tỉnh / Thành phố trực thuộc trung ương. Cấp 2 (`NAME_2`) là Quận / Huyện / Hạt / Thành phố thuộc tỉnh, phủ kín 100% lãnh thổ và có quy mô diện tích lý tưởng cho lưới NTL (cạnh ô lưới $500 \text{ m}$ - $2000 \text{ m}$).

**Cấu hình trích xuất:**

| Tham số | Giá trị |
| :--- | :--- |
| `layer` | `ADM_ADM_2` |
| Thư mục (State/Province) | `NAME_1` |
| Tệp (District/County) | `NAME_2` (nhóm theo `GID_2`, dùng `ENGTYPE_2` để phân biệt nếu trùng `NAME_2`) |

**Danh sách quốc gia áp dụng:**

<details open>
<summary><b>🌏 Đông Nam Á</b></summary>

<br>

| Mã | Quốc gia | Cấp 1 (thư mục) | Cấp 2 (tệp) |
| :---: | :--- | :--- | :--- |
| `VNM` | Việt Nam | 63 tỉnh | 705 quận/huyện |
| `THA` | Thái Lan | 77 tỉnh | 928 Amphoe/Khet |
| `IDN` | Indonesia | 34 tỉnh | 514 Kabupaten/Kota |
| `MYS` | Malaysia | 16 bang | 160 Daerah |
| `PHL` | Philippines | 81 tỉnh + Metro Manila | 1,634 đô thị |
| `KHM` | Campuchia | 25 tỉnh | 197 huyện |
| `LAO` | Lào | 18 tỉnh | 148 huyện |
| `MMR` | Myanmar | 15 bang/vùng | 330 townships |
| `TLS` | Đông Timor | 13 đô thị | 65 subdistricts |

</details>

<details>
<summary><b>🏯 Đông Á & Nam Á</b></summary>

<br>

| Mã | Quốc gia | Cấp 1 (thư mục) | Cấp 2 (tệp) |
| :---: | :--- | :--- | :--- |
| `JPN` | Nhật Bản | 47 tỉnh | ~1,741 Shi/Ku/Machi/Mura |
| `KOR` | Hàn Quốc | 17 tỉnh/thành | ~250 Si/Gun/Gu |
| `PRK` | Triều Tiên | — | — |
| `MNG` | Mông Cổ | 22 tỉnh | 339 Sums |
| `IND` | Ấn Độ | 36 bang/UT | ~676 Districts |
| `BGD` | Bangladesh | 8 Divisions | 64 Districts; hoặc `ADM_3` cho 544 Upazilas |
| `PAK` | Pakistan | 8 đơn vị cấp 1 | ~36 Divisions ở `ADM_2` hoặc ~160 Districts ở `ADM_3` |
| `LKA` | Sri Lanka | 25 Districts ở `ADM_1` | 331 DS Divisions ở `ADM_2` |
| `NPL` | Nepal | — | — |

</details>

<details>
<summary><b>🗽 Châu Mỹ</b></summary>

<br>

| Mã | Quốc gia | Cấp 1 (thư mục) | Cấp 2 (tệp) |
| :---: | :--- | :--- | :--- |
| `USA` | Hoa Kỳ | 50 bang + DC | 3,143 Counties/Independent Cities |
| `CAN` | Canada | 13 tỉnh/lãnh thổ | 293 Census Divisions |
| `MEX` | Mexico | 32 bang | 2,469 Municipios |
| `BRA` | Brazil | 27 bang | 5,570 Municípios |
| `ARG` | Argentina | 24 tỉnh | 528 Departamentos/Partidos |
| `CHL` | Chile | 16 vùng | 56 tỉnh ở `ADM_2` hoặc 346 Comunas ở `ADM_3` |
| `COL` | Colombia | 33 vùng | 1,122 Municipios |
| `PER` | Peru | 26 vùng | 196 Provincias |
| `VEN`, `CUB` | Venezuela, Cuba | — | — |

</details>

<details>
<summary><b>🏰 Châu Âu</b></summary>

<br>

| Mã | Quốc gia | Cấp 1 (thư mục) | Cấp 2 (tệp) |
| :---: | :--- | :--- | :--- |
| `DEU` | Đức | 16 bang | 401 Kreise/Kreisfreie Städte |
| `FRA` | Pháp | 13 vùng | 96 Départements ở `ADM_2` |
| `ITA` | Ý | 20 vùng | 107 tỉnh/thành phố đô thị ở `ADM_2` |
| `ESP` | Tây Ban Nha | 17 cộng đồng tự trị | 52 tỉnh ở `ADM_2` hoặc 326 Comarcas ở `ADM_3` |
| `POL` | Ba Lan | 16 tỉnh | 380 Powiaty |
| `NLD` | Hà Lan | 12 tỉnh | 342 Gemeenten |
| `BEL` | Bỉ | 3 vùng | 11 tỉnh/Arrondissements |
| `CHE` | Thụy Sĩ | 26 Cantons | 143 Bezirke |
| `AUT` | Áo | 9 bang | 94 Bezirke |
| `SWE` | Thụy Điển | 21 hạt | 290 Kommuner |
| `NOR` | Na Uy | 11 hạt | 356 Kommuner |
| `DNK` | Đan Mạch | 5 vùng | 99 Kommuner |
| `RUS` | Nga | ~85 chủ thể liên bang | ~2,350 Raions/Cities |
| `TUR` | Thổ Nhĩ Kỳ | 81 tỉnh | 973 Ilçe |
| `CZE`, `HUN`, `ROU`, `BGR`, `GRC`, `PRT`, `FIN`, `UKR` | — | — | — |

</details>

<details>
<summary><b>🦘 Châu Đại Dương, Trung Đông & Châu Phi</b></summary>

<br>

| Mã | Quốc gia | Cấp 1 (thư mục) | Cấp 2 (tệp) |
| :---: | :--- | :--- | :--- |
| `AUS` | Úc | 8 bang/lãnh thổ | 562 Local Government Areas |
| `NZL` | New Zealand | 16 vùng | 67 Territorial Authorities |
| `NGA` | Nigeria | 37 bang | 774 LGAs |
| `SAU`, `EGY`, `ZAF`, `KEN`, `ETH`, `MAR`, `DZA`, `GHA`, `TZA`, `KAZ`, `UZB`, `IRN`, `IRQ` | — | — | — |

</details>

---

<a id="nhom2"></a>

### 🟧 Nhóm 2: `SHIFTED_ADM3_PREFECTURE` (dịch chuyển cấp 3: cấp địa khu làm thư mục, cấp quận/huyện làm tệp)

**Đặc điểm:**

- `ADM_1` quá rộng (quy mô 50–120 triệu dân, tương đương một quốc gia châu Âu).
- `ADM_2` mới là các thành phố cấp địa khu (Prefecture-level cities như Thâm Quyến, Quảng Châu, Vũ Hán, Tô Châu) hoặc phân vùng lớn.
- Các quận đô thị lõi và huyện (`Qu` / `Xian` / `Xianjishi`) nằm ở **`ADM_3`**.

#### 🇨🇳 Trường hợp điển hình nhất: Trung Quốc (`CHN`)

Nếu xuất ở `ADM_2`, toàn bộ thành phố Thâm Quyến hay Quảng Châu chỉ là một file duy nhất. Khi đó không thể phân tích sự phân hóa giữa các quận lõi (Nam Sơn, Phúc Điền, Thiên Hà) và vùng ven.

**Xử lý ngoại lệ cho 4 thành phố trực thuộc trung ương (`Beijing`, `Shanghai`, `Tianjin`, `Chongqing`) và các huyện trực thuộc tỉnh (`NAME_2 == "NA"`).** Ở 4 đô thị này, tên thành phố nằm ngay ở `NAME_1`. Do đó, công thức đặt tên Thư mục chuẩn xác nhất cho `CHN` là:

| Trường hợp | Thư mục |
| :--- | :--- |
| `NAME_1` thuộc `{"Beijing", "Shanghai", "Tianjin", "Chongqing"}`, hoặc `NAME_2` là `"NA"` / trùng `NAME_1` | `NAME_1` |
| 27 tỉnh/khu tự trị còn lại | `NAME_1 + " - " + NAME_2` (ví dụ: `Guangdong - Shenzhen`, `Guangdong - Guangzhou`, `Jiangsu - Suzhou`) |

Cách đặt tên này giúp người dùng vừa tìm theo Tỉnh dễ dàng trên thanh chọn của Streamlit, vừa tách biệt từng thành phố địa khu. Các tệp bên trong là toàn bộ Quận/Huyện ở `NAME_3` (nhóm theo `GID_3`).

#### 🌐 Các quốc gia khác có thể áp dụng Nhóm 2 (hoặc cấu hình `ADM_3`)

| Mã | Muốn phân tích ở cấp... | Thay vì... | Cấu hình |
| :---: | :--- | :--- | :--- |
| `PAK` | 160 `Districts` tại `ADM_3` | 36 `Divisions` tại `ADM_2` | Thư mục = `NAME_1`, Tệp = `NAME_3` |
| `BGD` | 544 `Upazilas` tại `ADM_3` | 64 `Districts` tại `ADM_2` | — |
| `FRA` | 333 `Arrondissements` tại `ADM_3` | — | Thư mục = `NAME_2` (Département) |

---

### 🟨 Nhóm 3: `ASYMMETRIC_HYBRID` (bất đối xứng / khuyết cấp trung gian `NAME_2 = "NA"`)

**Đặc điểm:** hệ thống hành chính lai ghép giữa mô hình hai cấp (two-tier shire counties) và mô hình một cấp (single-tier Unitary Authorities / Metropolitan Boroughs).

#### 🇬🇧 Trường hợp 1: Vương quốc Anh (`GBR`)

**Cấu trúc thực tế trong `gadm41_GBR.gpkg`:**

| Lớp | Nội dung |
| :--- | :--- |
| `ADM_ADM_1` | 4 quốc gia cấu thành: `England`, `Scotland`, `Wales`, `Northern Ireland`. |
| `ADM_ADM_2` | Chỉ chứa các hạt nông thôn hai cấp (như `Kent`, `Essex`, `West Sussex`). Toàn bộ 33 quận của Đại London, 36 quận của 6 hạt đô thị lớn (Greater Manchester, West Midlands, Merseyside, South Yorkshire, West Yorkshire, Tyne and Wear), toàn bộ các Unitary Authorities của England, cùng nhiều vùng của Scotland/Wales đều bị gán `NAME_2 = "NA"`. |
| `ADM_ADM_3` | Chứa **đầy đủ 100% các đơn vị chính quyền địa phương cấp Quận/Hạt chuẩn** (Local Authority Districts / London Boroughs / Metropolitan Districts / Unitary Authorities / Council Areas) trên toàn Vương quốc Anh. Ở các vùng khuyết `NAME_2` (`"NA"`), tên quận nằm ở `NAME_3`. Ở một vài hạt đơn nhất nhỏ khuyết `NAME_3` (`"NA"`), tên nằm ở `NAME_2`. |

**Giải pháp trích xuất chuẩn cho `GBR`:**

| Tham số | Giá trị |
| :--- | :--- |
| Lớp đọc | **`ADM_ADM_3`** |
| Thư mục (State/Region) | `NAME_1` (`England`, `Scotland`, `Wales`, `Northern Ireland`). Nếu muốn chia nhỏ `England` theo hạt thì dùng `COALESCE(NAME_2, "England_Unitary_and_Metro")`. Để đồng nhất với 4 bang trong giao diện hiện tại của bạn, đặt Thư mục = `NAME_1`. |
| Tệp (District/Borough) | Hàm hợp nhất **`COALESCE(NAME_3, NAME_2)`** (lấy `NAME_3` nếu hợp lệ, nếu `NAME_3` là `"NA"` thì lùi về `NAME_2`), nhóm theo khóa duy nhất `COALESCE(GID_3, GID_2)`. |

> [!NOTE]
> **Kết quả:** không mất bất kỳ quận nào của London hay Manchester, không sinh ra đa giác `NA` 37MB nào, và 100% tệp xuất ra đều là các Local Authority Districts đồng cấp.

#### 🇹🇼 Trường hợp 2: Đài Loan (`TWN`)

Trong GADM v4.1, một số huyện/thành phố bị lệch cấp giữa `NAME_1` và `NAME_2` (do `NAME_1` có hai tỉnh danh nghĩa `Fujian` và `Taiwan` bên cạnh các thành phố trực thuộc trung ương).

**Giải pháp cho `TWN`:** đọc lớp sâu nhất của Đài Loan (`ADM_ADM_2` hoặc `ADM_ADM_3`, tùy bản đóng gói).

| Tham số | Giá trị |
| :--- | :--- |
| Thư mục | `COALESCE(NAME_2, NAME_1)`: 22 Huyện/Thành phố như *Taipei, New Taipei, Taichung, Kaohsiung, Hsinchu* |
| Tệp | Cấp kế tiếp: 368 Quận/Hương/Trấn (*Qu/Xiang/Zhen*) |

---

### 🟥 Nhóm 4: `SHALLOW_ADM1_CITY_STATE` (thành bang & quốc gia diện tích nhỏ chỉ dùng cấp 1)

**Đặc điểm:** quốc gia có diện tích nhỏ hoặc là thành bang đô thị. Lớp `ADM_ADM_2` hoặc không tồn tại trong `.gpkg`, hoặc nếu có thì chỉ gồm các tổ dân phố nhỏ vài trăm mét vuông.

**Cấu hình trích xuất:**

| Tham số | Giá trị |
| :--- | :--- |
| Lớp đọc | **`ADM_ADM_1`** (hoặc tự động lùi về `ADM_ADM_1` khi không có `ADM_ADM_2`) |
| Thư mục | Tên quốc gia (`COUNTRY` / `NAME_0`) hoặc vùng lớn |
| Tệp | `NAME_1` (nhóm theo `GID_1`) |

**Danh sách quốc gia áp dụng:**

| Mã | Quốc gia | Chi tiết |
| :---: | :--- | :--- |
| `SGP` | Singapore | 5 vùng quy hoạch ở `ADM_1` |
| `HKG` | Hồng Kông | 18 quận hành chính nằm ngay ở `ADM_1` |
| `MAC` | Ma Cao | Các khu vực nằm ở `ADM_1` |
| `BRN` | Brunei | 4 quận Daerah ở `ADM_1`, hoặc dùng `ADM_2` cho 38 Mukim |
| `QAT` | Qatar | 8 đô thị Baladiyat ở `ADM_1` |
| `MDV` | Maldives | 21 Atolls ở `ADM_1` |
| `ISR` | Israel | 6 Districts ở `ADM_1`, hoặc 15 Sub-districts ở `ADM_2` |
| `IRL` | Ireland | 26 Counties truyền thống nằm ở `ADM_1`; lớp `ADM_2` là các Municipal Districts |

<sub>[↑ Về đầu trang](#top)</sub>

---

<a id="s4"></a>

## ✅ 4. Quy trình kiểm định chất lượng dữ liệu đầu ra

Mỗi tệp `.geojson` trước khi được ghi xuống ổ cứng để đưa vào `app.py` đều phải đi qua **5 lần kiểm định tự động** trong tập lệnh trích xuất:

```mermaid
flowchart LR
    S["📥 Dữ liệu từ<br/>.gpkg"] --> C1["1️⃣ Chuỗi rác"]
    C1 --> C2["2️⃣ Thủy văn"]
    C2 --> C3["3️⃣ Hợp nhất<br/>theo GID"]
    C3 --> C4["4️⃣ Chống ghi đè<br/>trùng tên"]
    C4 --> C5["5️⃣ Diện tích<br/>tối thiểu"]
    C5 --> G["📄 Tệp .geojson<br/>hợp lệ"]
```

### 1️⃣ Lần 1: kiểm tra chuỗi rác

Mọi giá trị thuộc tập `{"NA", "N/A", "NULL", "NONE", "UNKNOWN", "?", "", "NAN"}` (không phân biệt hoa thường, đã cắt khoảng trắng hai đầu) đều bị ép về `None` thực sự trước khi phân tích. Mọi dòng có `NAME_1 is None` (như `bang NA` trong `gadm41_GBR.gpkg`) bị loại bỏ, hoặc được gán lại từ cấp con nếu hợp lệ.

### 2️⃣ Lần 2: bộ lọc thủy văn

Loại bỏ hoàn toàn các đa giác có `TYPE_x` hoặc `ENGTYPE_x` chứa một trong các từ khóa `Water body`, `Lake`, `Inland water`, `Sea`, `Estuary`.

### 3️⃣ Lần 3: hợp nhất hình học theo mã định danh

Sửa lỗi tự cắt (self-intersection) bằng `shapely.make_valid()`, rồi gộp (`dissolve`) theo đúng mã `GID` mục tiêu, để đảm bảo một đơn vị hành chính ứng với đúng một tệp `.geojson`.

### 4️⃣ Lần 4: chống ghi đè trùng tên

Nếu trong cùng một thư mục Tỉnh/Bang có hai đơn vị khác mã `GID` nhưng trùng tên hiển thị (ví dụ: *Fairfax County* và *Fairfax City*), hệ thống tự động gắn hậu tố phân biệt lấy từ `ENGTYPE_x`:

```text
USA_Virginia_Fairfax_County.geojson
USA_Virginia_Fairfax_Independent_City.geojson
```

Cách đặt tên này tương thích với hàm `list_counties()` và `split_county()` trong `app.py`.

### 5️⃣ Lần 5: kiểm tra diện tích tối thiểu cho VIIRS

Cảnh báo nếu một đa giác có diện tích $< 0.25 \text{ km}^2$, tức nhỏ hơn một ô lưới $500 \times 500 \text{ m}$.

<sub>[↑ Về đầu trang](#top)</sub>
