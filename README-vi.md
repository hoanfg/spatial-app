# SỔ TAY KỸ THUẬT VÀ KHUNG PHƯƠNG PHÁP LUẬN

**Bộ trích xuất dữ liệu ánh sáng ban đêm (NTL) & Công cụ kinh tế lượng không gian**

[ 🇬🇧 English ](README.md) | [ 🇻🇳 Tiếng Việt ](README-vi.md)

--------------------------------------------------

> **Too long; didn't read (DÀNH CHO NGƯỜI CHỈ CÓ 30 GIÂY ĐỂ ĐỌC)**
> 
> Bạn bị "ngợp" bởi hàng tá công thức toán học bên dưới? Đây là bản dịch nôm na nhất về những gì hệ thống này làm được:
> 
> * Muốn biết một vùng nghèo hay giàu mà không có số liệu GDP? Người ta dùng ảnh chụp độ sáng ban đêm từ vệ tinh. **NHƯNG** đống dữ liệu này siêu nặng. Cứ cố chạy trên máy tính bình thường là sập RAM trắng màn hình. Làm thủ công thì mất cả tuần.
> * **App này làm gì?:** Bạn chọn một khu vực $\rightarrow$ App tự động móc nối với *Google Earth Engine* tải ảnh về $\rightarrow$ Dùng C/C++ tách hàng triệu điểm ảnh thành từng ô lưới $\rightarrow$ **Lách qua giới hạn 1GB RAM của server web mà không sập.**
> * Bấm 1 nút, app trả về cho bạn 1 file CSV dọn sẵn các chỉ số kinh tế: Đâu là lõi đô thị? Chỗ nào là "điểm nóng" (LISA)? Độ bất bình đẳng (Gini) cao hay thấp? Việc của bạn chỉ là tải về và ném vào mô hình chạy hồi quy.
> * [CLICK VÀO ĐÂY ĐỂ TRẢI NGHIỆM TRỰC TIẾP APP (LIVE DEMO)](https://spatial-app.streamlit.app/?)

--------------------------------------------------

Dự án này là một hệ thống thiết kế cho **kinh tế lượng không gian**, kết hợp giữa hạ tầng lưới không gian và luồng trích xuất dữ liệu ánh sáng ban đêm (nighttime lights - NTL).

Ứng dụng giải quyết bài toán từ việc chuẩn hóa ranh giới hành chính bất quy tắc thành ma trận lưới vuông, kết nối trực tiếp với Google Earth Engine (GEE) để tải dữ liệu Raster (SNPP-VIIRS), cho đến việc tự động tính toán các chỉ số thống kê không gian vi mô (LISA) để xuất ra dữ liệu bảng phục vụ các mô hình vĩ mô.

---

## CHƯƠNG 1: TỔNG QUAN KIẾN TRÚC HỆ THỐNG VÀ QUẢN TRỊ TÀI NGUYÊN

Hệ thống được thiết kế không chỉ như một công cụ trích xuất dữ liệu viễn thám, mà là một công cụ xử lý không gian hoạt động trên môi trường Web, kết nối trực tiếp quy trình tiền xử lý địa lý (GIS) với các mô hình kinh tế lượng không gian.

### 1.1. Kiến trúc phân tầng 4-tier

Để giải quyết tính phức tạp của việc kết hợp dữ liệu vector (ranh giới hành chính), dữ liệu raster (ảnh vệ tinh VIIRS) và thống kê suy diễn không gian, hệ thống phân rã luồng công việc thành 4 tầng độc lập:

* **Tier 1:** 
  Tầng này chịu trách nhiệm quét đệ quy cấu trúc thư mục GADM cục bộ. Bằng việc sử dụng thuật toán nhận diện mẫu, chuẩn hóa Unicode (NFC/NFD) và thư viện `pycountry`, hệ thống tự động suy diễn mã định danh ISO3, chuẩn hóa tên gọi hành chính và nạp vào giao diện người dùng (UI) mà không phụ thuộc vào cơ sở dữ liệu tĩnh - [[Đọc mô tả kỹ thuật phân loại quốc gia tại đây]](https://github.com/hoanfg/spatial-app/blob/main/GADM_v41-vi%20pipeline%20specification.md).

* **Tier 2:** 
  Chịu trách nhiệm xử lý hình học đa giác. Tầng này chiếu toàn bộ dữ liệu vector về hệ tọa độ phẳng UTM (Universal Transverse Mercator) động dựa trên kinh độ/vĩ độ tâm của hộp bao (bounding box), sau đó kiến tạo lưới không gian đều bằng kỹ thuật vector hóa qua `numpy.meshgrid` và `shapely.box`.
  
* **Tier 3:** 
  Máy chủ gửi truy vấn không gian tới Google Earth Engine (GEE) API để lọc mây, tổng hợp trung vị năm và cắt ảnh raster theo ranh giới vùng phân tích. Luồng byte-stream của ảnh GeoTIFF được nạp vào bộ nhớ tạm để **C/C++ engine** (`exactextract`) thực hiện tính toán thống kê vùng theo tỷ lệ phủ diện tích điểm ảnh giữa lưới Vector và Raster.

* **Tier 4:** 
  Tính toán kinh tế lượng không gian (Global Moran's I, Local Moran's I / LISA, nhận diện cụm điểm nóng liên thông, khoảng cách tới tâm lõi kinh tế, hệ số bất bình đẳng Gini) và kết xuất bản đồ tương tác đa lớp (Folium/Leaflet). Dữ liệu đầu ra được đóng gói qua cầu nối dữ liệu dưới dạng tệp CSV cấp độ ô lưới và cấp độ vùng - năm.

### 1.2. Giới hạn phần cứng và cơ chế phòng thủ "out-of-memory" (OOM) trên Cloud

Môi trường triển khai mục tiêu của hệ thống là Streamlit Community Cloud (hoặc các docker container chi phí thấp), nơi tài nguyên bị giới hạn ở mức **~1GB RAM** và **1 CPU Core**.

Xử lý hình học không gian có mức tiêu thụ bộ nhớ tăng rất nhanh theo độ phân giải lưới. Khi thực hiện phép cắt `geopandas.clip()` trên lưới 500m cho một đơn vị hành chính rộng $30,000 \, \mathrm{km}^2$, số lượng đa giác sinh ra có thể vượt ngưỡng $150,000$. Việc lưu trữ đồng thời cấu trúc hình học (topology) của số lượng đa giác này trên RAM sẽ kích hoạt cơ chế Linux OOM Killer làm sập tiến trình máy chủ.

**Cơ chế phòng thủ:**

1. **In-memory zip streaming & ephemeral cleanup:** Ảnh raster từ GEE được tải dưới dạng byte-stream, giải nén trực tiếp trên RAM và ghi ra tệp tạm (`tempfile`). Ngay khi `exactextract` hoàn tất phép tính trong khối `try...finally`, tệp tạm bị xóa cưỡng bức khỏi ổ cứng để giải phóng tài nguyên lập tức.

2. **Cầu chì đánh giá quy mô tiền tính toán:** Ước lượng số lượng ô lưới từ diện tích và chu vi trước khi khởi tạo hình học để khóa các truy vấn vượt trần bộ nhớ (mô tả chi tiết tại Mục 4.1).

3. **FIFO session cache:** Bộ đệm kết quả kiểm định LISA (`_lisa_cache`) được giới hạn tối đa 5 cấu hình tham số gần nhất theo cơ chế vào trước – ra trước (FIFO), đảm bảo chuyển đổi tức thời giữa các cấu hình mà không gây rò rỉ bộ nhớ.

### 1.3. Cơ chế stateless của trình duyệt web

Streamlit vận hành theo nguyên lý **stateless (không trạng thái)**: mỗi tương tác của người dùng với bất kỳ điều khiển nào trên giao diện đều buộc Python chạy lại từ đầu. Hệ thống duy trì trạng thái thông qua hai cơ chế:

1. **Memoization (`@st.cache_data`, `@st.cache_resource`):** Các tiến trình khởi tạo xác thực GEE, quét danh mục GADM, tính thống kê hình học ranh giới và tải ảnh vệ tinh được băm theo tham số đầu vào để tái sử dụng từ bộ nhớ đệm.

2. **Session state injection:** Tiến trình trích xuất nặng được cô lập trong hàm `run_pipeline()` và lưu kết quả vào `st.session_state["result"]`. Mọi thao tác tùy chỉnh bảng màu, thang đo hay lọc hiển thị trên bản đồ chỉ đọc dữ liệu từ `st.session_state`, tách biệt hoàn toàn tầng hiển thị (UI) khỏi tầng tính toán (backend).

---

## CHƯƠNG 2: PHƯƠNG PHÁP LUẬN XỬ LÝ KHÔNG GIAN (SPATIAL GEOPROCESSING)

### 2.1. Giải pháp cho vấn đề đơn vị diện tích có thể thay đổi (MAUP)

Trong các nghiên cứu kinh tế học không gian thực nghiệm, việc sử dụng trực tiếp ranh giới hành chính cấp tỉnh/huyện/xã tạo ra thiên lệch thống kê do sự khác biệt lớn về diện tích và hình thái hình học, được gọi là **vấn đề đơn vị diện tích có thể thay đổi (Modifiable areal unit problem – MAUP)** (Openshaw, 1984; Fotheringham & Wong, 1991). Hệ thống khắc phục vấn đề này bằng cách chuẩn hóa khu vực nghiên cứu về một ma trận lưới vuông đồng nhất (Donaldson & Storeygard, 2016).

**Thuật toán chiếu tọa độ động:**

Thay vì sử dụng cố định một mã EPSG cục bộ như ở bản thử nghiệm Phase 1 (`EPSG:32648`), hệ thống tự động nội suy múi chiếu phẳng **UTM (Universal Transverse Mercator)** tối ưu dựa trên kinh độ và vĩ độ tâm $(\lambda_{\mathrm{center}}, \phi_{\mathrm{center}})$ của hộp bao vùng nghiên cứu:

$$
\mathrm{Zone} = \min\left(60, \max\left(1, \left\lfloor \frac{\lambda_{\mathrm{center}} + 180}{6} \right\rfloor + 1\right)\right)
$$

Mã hệ tọa độ chuẩn EPSG (đơn vị: mét) được xác định tự động cho cả Bắc và Nam bán cầu:

$$
\mathrm{EPSG} = \begin{cases} 32600 + \mathrm{Zone} & \text{nếu } \phi_{\mathrm{center}} \ge 0 \text{ (Bắc bán cầu)} \\ 32700 + \mathrm{Zone} & \text{nếu } \phi_{\mathrm{center}} < 0 \text{ (Nam bán cầu)} \end{cases}
$$

Toàn bộ tọa độ gốc $(x_0, y_0)$ của lưới đều được căn chuẩn theo bội số nguyên của kích thước cạnh ô $\mathrm{size}$ trong không gian phẳng UTM, đảm bảo lưới của các quận/huyện liền kề khớp nhau tuyệt đối khi ghép nối.

### 2.2. Lọc mây trên GEE và trích xuất Zonal statistics bằng tỷ lệ phủ (fractional coverage)

Hệ thống khai thác chuỗi ảnh tháng từ bộ dữ liệu vệ tinh `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` (độ phân giải gốc $\approx 15\text{ arc-giây} \approx 463.83\text{ m}$ tại xích đạo). Tại các vùng nhiệt đới gió mùa, mây che phủ dày đặc trong các tháng mùa mưa có thể khiến điểm ảnh không có quan sát hợp lệ (`cf_cvg` $= 0$), dẫn đến giá trị bức xạ bằng $0$ giả tạo. Để loại bỏ thiên lệch âm này, hệ thống áp dụng mặt nạ lọc mây `cf_cvg` $> 0$ cho từng ảnh tháng trước khi lấy **trung vị năm (annual median composite)** (Elvidge et al., 2017, 2021).

Tiếp theo, thay vì sử dụng phương pháp tâm điểm ảnh (center-of-pixel) truyền thống vốn gây sai số lớn khi kích thước ô lưới tiến gần kích thước điểm ảnh VIIRS, hệ thống tích hợp thư viện C/C++ `exactextract` (Baston, 2023). Cường độ bức xạ trung bình $\mathrm{NTL}_i$ của ô lưới $i$ được tính bằng trung bình có trọng số theo tỷ lệ diện tích điểm ảnh $w_{ip} \in [0, 1]$ thực sự nằm bên trong đa giác ô lưới $i$:

$$
\mathrm{NTL}_i = \frac{\sum_{p \in i} x_p \cdot w_{ip}}{\sum_{p \in i} w_{ip}}
$$

Các giá trị rỗng hoặc âm phát sinh từ quá trình hiệu chỉnh ánh sáng nền của cảm biến được chuẩn hóa về $0.0$. Tổng lượng ánh sáng (sum of lights – SOL) của từng ô được tính bằng tích số giữa cường độ bức xạ trung bình và diện tích thực tế sau khi cắt: $\mathrm{SOL}_i = \mathrm{NTL}_i \times A_i$.

---

## CHƯƠNG 3: LÕI KINH TẾ LƯỢNG KHÔNG GIAN (LISA CORE ALGORITHM)

Mô-đun `lisa_core.py` được thiết kế độc lập hoàn toàn bằng đại số mảng trên `numpy` và `pandas`, loại bỏ sự phụ thuộc vào các thư viện nặng như `libpysal` hay `esda`, đồng thời giảm độ phức tạp tính toán đồ thị láng giềng xuống $\mathcal{O}(N \log N)$.

### 3.1. Xử lý dữ liệu lạm phát số 0 và ô biên

Dữ liệu bức xạ đêm tự nhiên thường chứa tỷ lệ lớn các quan sát bằng $0$ (rừng núi, mặt nước, đất nông nghiệp) và các mảnh đa giác biên bị cắt hẹp bởi ranh giới hành chính. Hệ thống xử lý đồng thời hai vấn đề này theo quy trình 3 bước:

1. **Lọc ô biên:** Một ô lưới $i$ được gắn cờ là ô biên (`is_border_cell = 1` và `is_edge_masked = 1`) và bị loại khỏi đồ thị láng giềng nếu diện tích thực tế sau khi cắt $A_i$ nhỏ hơn $99\%$ diện tích ô lưới chuẩn:

$$
A_i < 0.99 \times \left(\frac{\mathrm{size}}{1000}\right)^2 \quad (\mathrm{km}^2)
$$

2. **Chuẩn hóa Z-score trên tập tham chiếu lõi ($S$):** Gọi $S$ là tập các ô lõi (không phải ô biên, $A_i \ge 0.99 \times (\mathrm{size}/1000)^2$) thỏa mãn điều kiện đưa vào kiểm định. Ở chế độ mặc định (`include_zeros = False`), $S$ gồm các ô lõi có ánh sáng vượt ngưỡng ($\mathrm{NTL}_i > \mathrm{threshold}$). Ở chế độ mở rộng (`include_zeros = True`), $S$ bao gồm toàn bộ các ô lõi. Điểm chuẩn hóa $z_i$ được tính với độ lệch chuẩn mẫu hiệu chỉnh Bessel ($\mathrm{ddof} = 1$):

$$
\mu_S = \frac{1}{\lvert S \rvert} \sum_{i \in S} v_i, \quad \sigma_S = \sqrt{\frac{1}{\lvert S \rvert - 1} \sum_{i \in S} (v_i - \mu_S)^2}, \quad z_i = \frac{v_i - \mu_S}{\sigma_S} \quad \forall i \in S
$$

Trong đó $v_i = \ln(\mathrm{NTL}_i)$ (hoặc $\ln(1 + \mathrm{NTL}_i)$ khi bao gồm số $0$) nếu người dùng bật tùy chọn biến đổi logarit để nén đuôi phân phối lệch phải, và $v_i = \mathrm{NTL}_i$ nếu giữ nguyên thang đo bức xạ gốc.

3. **Hệ quả phương pháp luận của chế độ chỉ kiểm định ô sáng (`lit_only`):** Khi loại các ô tối ($\mathrm{NTL}_i \le \mathrm{threshold}$, gán nhãn `DARK`) khỏi đồ thị láng giềng $W$, trung bình $\mu_S$ đại diện cho **mức sáng trung bình nội bộ của khu vực có hoạt động chiếu sáng**. Khi đó:

   * Cụm **High-High (HH)** phản ánh lõi đô thị/thương mại có bức xạ cao vượt trội nằm liền kề nhau.

   * Cụm **Low-Low (LL)** phản ánh các khu vực có ánh sáng yếu (thấp hơn mức trung bình của vùng sáng, như vùng ven đô hoặc điểm dân cư thưa) tụ cụm với nhau, trong khi các vùng hoàn toàn không có ánh sáng đã được tách bạch vào trạng thái `DARK`.

   * Nhóm **High-Low (HL)** và **Low-High (LH)** phản ánh các điểm dị thường không gian (spatial outliers) ngay bên trong cấu trúc vùng sáng.

### 3.2. Đồ thị láng giềng Queen

Ma trận trọng số không gian $W$ được xây dựng theo quy tắc tiếp xúc Queen (8 hướng lân cận: 4 cạnh và 4 góc) trên lưới đều cho các ô thuộc tập kiểm định $S$. Từ tọa độ tâm $(c_{x,i}, c_{y,i})$ trong hệ mét UTM, thuật toán ánh xạ từng ô về cặp chỉ số nguyên $(ix_i, iy_i)$ và tạo khóa băm một chiều duy nhất:

$$
ix_i = \left\lfloor \frac{c_{x,i} + \epsilon}{\mathrm{size}} \right\rfloor, \quad iy_i = \left\lfloor \frac{c_{y,i} + \epsilon}{\mathrm{size}} \right\rfloor, \quad \mathrm{Key}_i = ix_i \cdot H + iy_i
$$

(với $\epsilon = 10^{-6}\text{ m}$ là hằng số bù sai số dấu phẩy động IEEE-754 và $H = \max(iy) - \min(iy) + 4$). Thuật toán sử dụng tìm kiếm nhị phân vector hóa `numpy.searchsorted` trên mảng khóa đã sắp xếp để xác định 8 láng giềng $(dx, dy) \in \{-1, 0, 1\}^2 \setminus \{(0,0)\}$. Trọng số không gian $w_{ij}$ được chuẩn hóa theo hàng:

$$
w_{ij} = \begin{cases} \frac{1}{k_i} & \text{nếu } j \in N(i) \cap S \\ 0 & \text{nếu ngược lại} \end{cases}
$$

với $k_i = \lvert N(i) \cap S \rvert$ là số láng giềng hợp lệ của ô $i$. Chỉ các ô $i \in S$ có $k_i \ge k_{\min}$ (mặc định $k_{\min} = 1$) mới được đưa vào tập kiểm định $\mathrm{Focal}$.

### 3.3. Kiểm định Local Moran's I (LISA) và hoán vị có điều kiện

Thống kê Local Moran's I (Anselin, 1995) và biến trễ không gian chuẩn hóa ($\mathrm{Spatial\ Lag}\ z$) cho mỗi ô $i \in \mathrm{Focal}$ được xác định bởi:

$$
I_i = \frac{z_i}{m_2} \sum_{j \in N(i) \cap S} w_{ij} z_j, \quad \mathrm{Lag}(z_i) = \sum_{j \in N(i) \cap S} w_{ij} z_j, \quad m_2 = \frac{1}{\lvert S \rvert} \sum_{r \in S} z_r^2
$$

**Hoán vị có điều kiện vector hóa:**

Vì bức xạ ánh sáng ban đêm không tuân theo phân phối chuẩn, ý nghĩa thống kê của $I_i$ được đánh giá thông qua mô phỏng Monte Carlo với $R$ lần hoán vị có điều kiện (mặc định $R = 499$, tối đa $R = 999$). Tại mỗi lần lặp $r \in \{1, \dots, R\}$, giá trị $z_i$ tại ô tâm được giữ cố định, trong khi $k_i$ giá trị láng giềng được rút ngẫu nhiên đồng thời bằng mảng chỉ số `rng.integers` từ quần thể $S \setminus \{i\}$ để tạo ra giá trị thống kê mô phỏng $I_i^{(r)}$.

Gọi $M_i$ là số lần mô phỏng rơi vào miền cực trị ở đuôi gần hơn (xử lý đồng hạng với dung sai số học $10^{-12}$):

$$
M_i = \min\left( \sum_{r=1}^R \mathbb{I}\left(I_i^{(r)} \ge I_i - 10^{-12}\right); \sum_{r=1}^R \mathbb{I}\left(I_i^{(r)} \le I_i + 10^{-12}\right) \right)
$$

Giá trị pseudo p-value hai phía (two-sided) được tính theo quy chuẩn của Anselin (1995) và Rey & Anselin (2007):

$$
p_i = \min\left(1.0; 2 \times \frac{M_i + 1}{R + 1}\right)
$$

### 3.4. Kiểm soát tỷ lệ phát hiện sai (FDR – Benjamini-Hochberg)

Khi thực hiện kiểm định đồng thời trên $m = \lvert \mathrm{Focal} \rvert$ ô lưới (có thể lên tới hàng chục ngàn ô ở độ phân giải 500m), việc áp dụng trực tiếp ngưỡng $\alpha = 0.05$ cho từng ô đơn lẻ sẽ làm bùng nổ sai số loại I (multiple testing problem) (Caldas de Castro & Singer, 2006). Hệ thống tích hợp thủ tục kiểm soát tỷ lệ phát hiện sai (false discovery rate – FDR) của Benjamini & Hochberg (1995):

1. Sắp xếp các giá trị $p_i$ của $m$ ô được kiểm định theo thứ tự tăng dần: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.

2. Tìm chỉ số $k \in \{1, \dots, m\}$ lớn nhất thỏa mãn bất đẳng thức:

$$
p_{(k)} \le \frac{k}{m} \alpha
$$

3. Nếu tồn tại $k$, bác bỏ giả thuyết không $H_0$ (công nhận có cụm không gian có ý nghĩa thống kê) cho toàn bộ các ô có $p_i \le p_{(k)}$.

Do mức sàn nhỏ nhất của pseudo p-value hai phía là $p_{\mathrm{floor}} = \frac{2}{R + 1}$, điều kiện cần toán học để thủ tục Benjamini–Hochberg có thể bác bỏ ít nhất một giả thuyết là số lượng ô đạt mức sàn $p_{\mathrm{floor}}$ phải thỏa mãn:

$$
k_{\mathrm{hit}} \ge \left\lceil \frac{p_{\mathrm{floor}} \cdot m}{\alpha} \right\rceil = \left\lceil \frac{2m}{(R + 1)\alpha} \right\rceil
$$

Hệ thống tự động tính toán ngưỡng $k_{\mathrm{hit}}$ (`fdr_min_hits_needed`) và hiển thị cảnh báo hướng dẫn người dùng tăng số hoán vị $R$ lên $999$ khi kích thước mẫu $m$ lớn.

### 3.5. Gom cụm điểm nóng liên thông và xác định tâm lõi kinh tế

Để phục vụ các mô hình kinh tế học đô thị nghiên cứu độ dốc mật độ kinh tế theo khoảng cách tới trung tâm, hệ thống tự động trích xuất các thành phần liên thông của các ô đạt chuẩn `High-High` trên đồ thị Queen bằng thuật toán lan truyền nhãn có bước nhảy con trỏ.

Một cụm `High-High` liên thông thứ $c$ được công nhận là một **cực tăng trưởng / điểm nóng đô thị** nếu số lượng ô của cụm đạt ngưỡng tối thiểu $n_c \ge n_{\min}$ (mặc định $n_{\min} = 4$ ô). Thay vì chọn tâm lõi kinh tế (central business district – CBD) bằng ô đơn lẻ có bức xạ cực đại $\arg\max_i(\mathrm{NTL}_i)$ vốn rất dễ bị lệch bởi các điểm nhiễu công nghiệp, cảng biển hoặc sân bay ở vùng rìa, tọa độ tâm lõi $(\mathrm{CBD}_x, \mathrm{CBD}_y)$ được xác định bằng **trọng tâm có trọng số tổng ánh sáng (SOL-weighted centroid) của cụm High-High có diện tích lớn nhất** ($C^{\star}$):

$$
\mathrm{CBD}_x = \frac{\sum_{i \in C^{\star}} c_{x,i} \cdot (\mathrm{NTL}_i \cdot A_i)}{\sum_{i \in C^{\star}} (\mathrm{NTL}_i \cdot A_i)}, \quad \mathrm{CBD}_y = \frac{\sum_{i \in C^{\star}} c_{y,i} \cdot (\mathrm{NTL}_i \cdot A_i)}{\sum_{i \in C^{\star}} (\mathrm{NTL}_i \cdot A_i)}
$$

Trong trường hợp địa phương chưa hình thành cụm `High-High` nào đạt ngưỡng $n_{\min}$, hệ thống tự động chuyển sang phương án dự phòng vững (robust fallback): chọn ô lõi không biên có điểm tổ hợp trung bình trượt không gian $0.5 \cdot \mathrm{NTL}_i + 0.5 \cdot \mathrm{Lag}(\mathrm{NTL}_i)$ cao nhất làm tâm. Từ đó, khoảng cách Euclid từ mọi ô lưới $i$ tới tâm lõi kinh tế (đơn vị: km) được xuất ra thành biến `dist_to_core_km`:

$$
d_{\mathrm{core}, i} = \frac{1}{1000}\sqrt{(c_{x,i} - \mathrm{CBD}_x)^2 + (c_{y,i} - \mathrm{CBD}_y)^2}
$$

---

## CHƯƠNG 4: THUẬT TOÁN QUẢN TRỊ TÀI NGUYÊN BỘ NHỚ (MEMORY SAFEGUARDS)

### 4.1. Cầu chì ước lượng quy mô lưới

Trước khi cho phép thực thi `geopandas.clip()`, hệ thống kích hoạt thuật toán chặn trước để dự phóng số lượng ô lưới sau khi cắt ($N_{\mathrm{clip}}$) và số lượng ô của hộp bao chữ nhật ($N_{\mathrm{bbox}}$) chỉ từ diện tích ($\mathrm{Area}$, $\mathrm{km}^2$) và chu vi ($\mathrm{Perimeter}$, $\mathrm{km}$) của ranh giới hành chính:

$$
N_{\mathrm{clip}} \approx \frac{\mathrm{Area}}{(\mathrm{size}/1000)^2} + \beta \frac{\mathrm{Perimeter}}{\mathrm{size}/1000}
$$

với $\beta = 0.65$ là hệ số hiệu chỉnh hình học cho các ô biên bị cắt. Nếu $N_{\mathrm{clip}} \ge N_{\max} = 150,000$ (`MAX_CELLS`) hoặc $N_{\mathrm{bbox}} > 4 \times N_{\max}$, nút thực thi sẽ tự động khóa và gợi ý độ phân giải lưới tối thiểu an toàn kế tiếp.

### 4.2. Kỹ thuật Winsorization động và cắt ngưỡng hiển thị trình duyệt

1. **Winsorization động cho thang màu bản đồ nhiệt:** Để ngăn chặn các điểm dị thường bức xạ cực cao (cảng biển, khu công nghiệp nặng, trạm đốt khí) làm mất độ tương phản của các khu dân cư đô thị, mức trần hiển thị $v_{\max}$ được tính động tại phân vị thứ 99 của tập các ô có ánh sáng $\mathrm{NTL}_{\mathrm{lit}} = \{\mathrm{NTL}_i \mid \mathrm{NTL}_i > 0\}$:

$$
v_{\mathrm{raw}} = \begin{cases} P_{99}(\mathrm{NTL}_{\mathrm{lit}}) & \text{nếu } \lvert \mathrm{NTL}_{\mathrm{lit}} \rvert > 10 \\ \max_i(\mathrm{NTL}_i) & \text{nếu } \lvert \mathrm{NTL}_{\mathrm{lit}} \rvert \le 10 \end{cases}, \quad v_{\max} = \begin{cases} v_{\mathrm{raw}} & \text{nếu } v_{\mathrm{raw}} > 0.1 \\ 1.0 & \text{nếu } v_{\mathrm{raw}} \le 0.1 \end{cases}
$$

2. **Trần kết xuất DOM trình duyệt (`RENDER_CAP = 30,000`):** Khi số lượng ô lưới vượt quá $30,000$, trình duyệt người dùng có nguy cơ bị treo khi dựng cây DOM SVG/Canvas của Leaflet. Hệ thống tự động ưu tiên giữ lại các ô có ý nghĩa thống kê LISA và các ô có bức xạ cao nhất để vẽ lên bản đồ, đồng thời làm tròn tọa độ hình học ở mức $10^{-6}$ độ (`shapely.set_precision`) để giảm dung lượng chuỗi GeoJSON. Toàn bộ tệp CSV xuất ra vẫn bảo toàn 100% quan sát gốc.

---

## CHƯƠNG 5: THIẾT KẾ CẤU TRÚC DỮ LIỆU PANEL VÀ CẦU NỐI KINH TẾ LƯỢNG (DATA BRIDGE)

Mục tiêu cốt lõi của hệ thống là cung cấp bộ biến số định lượng chuẩn xác, sẵn sàng đưa vào các phần mềm thống kê (Python, R, Stata) cho hai cấp độ phân tích: **Hồi quy vi mô cấp ô lưới (Cell-level cross-sectional / Spatial panel)** và **Hồi quy vĩ mô cấp vùng – năm (Region-Year panel)**.

### 5.1. Dữ liệu vi mô cấp ô lưới

Tệp CSV cấp độ ô lưới xuất ra 100% quan sát của địa phương (bao gồm cả các ô không sáng `DARK` và các ô biên `EDGE`). Việc giữ nguyên toàn bộ quan sát kèm theo các biến cờ (`is_border_cell`, `is_edge_masked`, `is_dark`) giúp nhà nghiên cứu chủ động kiểm soát **Thiên lệch chọn mẫu** (Heckman, 1979; Henderson et al., 2012).

**Các nhóm biến số vi mô trọng tâm:**

* **Nhóm biến cường độ và quy mô ánh sáng (`ntl_mean`, `ntl_sol`, `ntl_log`):**
  Biến `ntl_log` được định nghĩa là $\ln(1 + \mathrm{NTL}_i)$, giúp nén đuôi phân phối lệch phải và giảm ảnh hưởng của các quan sát cực trị trong hồi quy OLS/WLS. Tuy nhiên, theo chứng minh lý thuyết của Chen & Roth (2024), các phép biến đổi dạng $\ln(1 + Y)$ nhạy cảm với đơn vị đo của $Y$ khi dữ liệu có nhiều giá trị bằng $0$ (kết quả ước lượng trộn lẫn tác động theo chiều rộng: *extensive margin* và chiều sâu: *intensive margin*). Do đó, hệ thống cung cấp đồng thời cả `ntl_mean` và `ntl_sol` ở thang đo gốc để nhà nghiên cứu dễ dàng thực hiện hồi quy **Poisson Pseudo-Maximum Likelihood (PPML)** nhằm kiểm định độ vững (robustness check).

* **Nhóm biến trễ không gian và vị thế tương đối (`ntl_raw_lag`, `ntl_z_lit`, `lisa_lag_z`, `dist_to_core_km`):**
  Cung cấp trực tiếp biến trễ không gian của bức xạ gốc ($\mathrm{Lag}(\mathrm{NTL}_i)$), trễ không gian của điểm chuẩn hóa ($\mathrm{Lag}(z_i)$) và khoảng cách tới tâm lõi kinh tế (`dist_to_core_km`) để ước lượng hiệu ứng lan tỏa cũng như hàm suy giảm mật độ kinh tế từ tâm đô thị.

* **Nhóm biến phân loại cụm LISA (`lisa_I`, `lisa_p_sim`, `lisa_class`, `lisa_significant`, `hh_cluster_id`):**
  Cho phép tạo các biến giả hoặc phân tích ranh giới đô thị bằng thiết kế hồi quy gián đoạn không gian (spatial regression discontinuity design – Spatial RDD).

### 5.2. Cấu trúc dữ liệu panel cấp vùng – năm

Đối với các nghiên cứu vĩ mô phân tích sự phát triển cấp Quận/Huyện/Tỉnh qua nhiều năm, hệ thống tự động tổng hợp dữ liệu vi mô thành một dòng quan sát duy nhất cho mỗi tổ hợp `(iso3, region_id, year, cell_size_m)`. Các chỉ số được thiết kế để đo lường **cấu trúc không gian của sự phát triển**:

1. **Hệ số Gini bất bình đẳng ánh sáng (`gini_ntl_core_all`, `gini_ntl_core_lit`, `gini_sol_all`):**
   Kế thừa phương pháp chỉ số phát triển ánh sáng đêm (NLDI) của Elvidge et al. (2012) và các nghiên cứu bất bình đẳng không gian từ vệ tinh của Lessmann & Seidel (2017) và Mirza et al. (2021), hệ số Gini đo lường mức độ tập trung hoạt động kinh tế:

$$
G = \frac{2 \sum_{i=1}^n i \cdot x_{(i)}}{n \sum_{i=1}^n x_{(i)}} - \frac{n + 1}{n}
$$

(với $x_{(1)} \le x_{(2)} \le \dots \le x_{(n)}$ là chuỗi giá trị đã sắp xếp không giảm). Hệ thống xuất 3 biến thể Gini: `gini_ntl_core_all` (tính trên toàn bộ các ô lõi không biên, gồm cả ô tối, đảm bảo diện tích mỗi ô bằng nhau tuyệt đối), `gini_ntl_core_lit` (bất bình đẳng nội bộ trong khu vực có điện/ánh sáng), và `gini_sol_all` (Gini tính trên tổng lượng ánh sáng $\mathrm{SOL}_i$ của mọi ô).

2. **Tỷ trọng diện tích điểm nóng (`hh_area_share`, `hh_cluster_area_share`) và đa cực đô thị (`n_hh_clusters`):**
   Đo lường tỷ lệ diện tích lãnh thổ nằm trong các ô `High-High` có ý nghĩa thống kê (`hh_area_share`) hoặc nằm trong các cụm `High-High` liên thông đạt quy mô tối thiểu (`hh_cluster_area_share`):

$$
\mathrm{HH}_{\mathrm{share}} = \frac{\sum_{i \in \mathrm{HH}} A_i}{\sum_{i=1}^N A_i}
$$

Đây là biến đại diện (proxy) cho **mức độ đô thị hóa thực tế (de facto urbanization)**, khắc phục nhược điểm của số liệu diện tích đô thị hành chính truyền thống. Kết hợp với số lượng cụm điểm nóng độc lập (`n_hh_clusters`) và diện tích cụm lớn nhất (`largest_hh_cluster_km2`), nhà nghiên cứu có thể định lượng quá trình chuyển dịch từ cấu trúc đô thị đơn cực sang đa cực.

3. **Chỉ số tự tương quan không gian toàn cục: Global Moran's I (hiển thị tại tab Dữ liệu `app.py`):**
   Được tính trên toàn bộ $N$ ô lưới (bao gồm cả các ô $\mathrm{NTL} = 0$) với ma trận trọng số nhị phân Queen đối xứng (Moran, 1950):

$$
I_{\mathrm{global}} = \frac{N}{\sum_{i=1}^N \sum_{j=1}^N w_{ij}} \frac{\sum_{i=1}^N \sum_{j=1}^N w_{ij}(x_i - \bar{x})(x_j - \bar{x})}{\sum_{i=1}^N (x_i - \bar{x})^2}
$$

Nếu $I_{\mathrm{global}} > E[I] = -\frac{1}{N-1}$ và có ý nghĩa thống kê ($p < 0.05$), phần dư của hồi quy OLS truyền thống sẽ vi phạm giả định độc lập không gian, đòi hỏi nhà nghiên cứu phải sử dụng các mô hình Kinh tế lượng Không gian như SAR, SEM, SDM (LeSage & Pace, 2009) hoặc sai số chuẩn hiệu chỉnh tự tương quan không gian Conley (Conley, 1999).

4. **Chỉ số kết tụ nội tại vùng sáng: `moran_I_lit` (xuất trong bảng Panel CSV `lisa_core.py`):**
   Là trung bình cộng của thống kê Local Moran's I trên tập các ô sáng được kiểm định:

$$
\bar{I}_{\mathrm{lit}} = \frac{1}{\lvert \mathrm{Focal} \rvert} \sum_{i \in \mathrm{Focal}} I_i
$$

Chỉ số này đo lường cường độ kết tụ không gian bên trong ranh giới khu vực đã đô thị hóa/điện khí hóa của địa phương qua các năm.

### 5.3. Từ điển biến số cấp vùng – năm 

Bảng dưới đây định nghĩa đầy đủ các biến số trong tệp xuất `ntl_lisa_panel.csv`:

| Tên biến (Column) | Ý nghĩa Kỹ thuật & Kinh tế lượng |
| :--- | :--- |
| `iso3`, `region_id`, `region_label`, `year` | Bộ khóa định danh đơn vị hành chính và thời gian của dữ liệu bảng. |
| `cell_size_m` | Độ phân giải cạnh ô lưới vuông (mét): biến kiểm soát quy mô không gian (MAUP). |
| `n_cells`, `n_cells_edge_masked` | Tổng số ô lưới của địa phương và số lượng ô biên bị cắt ($A_i < 0.99 \times \mathrm{size}^2$). |
| `n_cells_lit`, `n_cells_tested` | Số lượng ô có ánh sáng ($\mathrm{NTL} > \mathrm{threshold}$) và số ô lõi đủ láng giềng được đưa vào kiểm định LISA. |
| `area_total_km2` | Tổng diện tích tự nhiên của địa phương tính theo lưới cắt ($\mathrm{km}^2$). |
| `lit_area_share` | Tỷ trọng diện tích lãnh thổ có tín hiệu ánh sáng ban đêm ($\in [0, 1]$): proxy cho độ phủ điện khí hóa/hạ tầng. |
| `hh_area_share` | Tỷ trọng diện tích toàn vùng thuộc các ô điểm nóng `High-High` có ý nghĩa thống kê. |
| `hh_area_share_of_tested` | Tỷ trọng diện tích `High-High` tính trên tổng diện tích các ô lõi được kiểm định. |
| `hh_cluster_area_share` | Tỷ trọng diện tích toàn vùng thuộc các cụm `High-High` liên thông đạt ngưỡng quy mô tối thiểu (`min_cluster_cells`). |
| `ll_area_share`, `hl_area_share`, `lh_area_share` | Tỷ trọng diện tích toàn vùng thuộc các trạng thái `Low-Low`, `High-Low` và `Low-High`. |
| `n_hh_clusters` | Số lượng cụm điểm nóng `High-High` liên thông độc lập, proxy đo lường cấu trúc đô thị đa cực. |
| `largest_hh_cluster_km2` | Diện tích ($\mathrm{km}^2$) của cụm điểm nóng `High-High` liên thông lớn nhất (hạt nhân đô thị chính). |
| `hotspot_dummy` | Biến giả nhị phân (`1/0`): nhận giá trị `1` nếu `n_hh_clusters > 0`. Sẵn sàng cho mô hình Hiệu số trong Hiệu số (DiD). |
| `gini_ntl_core_all` | Hệ số Gini bức xạ tính trên toàn bộ các ô lõi không biên (gồm cả ô tối), đo lường bất bình đẳng không gian tổng thể. |
| `gini_ntl_core_lit` | Hệ số Gini bức xạ tính riêng trên các ô lõi có ánh sáng, đo lường chênh lệch phân hóa nội bộ vùng sáng. |
| `gini_sol_all` | Hệ số Gini của tổng lượng ánh sáng ($\mathrm{SOL}_i = \mathrm{NTL}_i \times A_i$) trên toàn bộ các ô lưới. |
| `moran_I_lit` | Trung bình cộng thống kê Local Moran's I của các ô sáng được kiểm định, đo lường mức độ kết tụ đô thị. |
| `p_cfg_*`, `p_floor`, `fdr_min_hits_needed` | Tập siêu tham số lưu vết cấu hình kiểm định (`perms`, `alpha`, `fdr`, `log`, `lit_thr`, `edge_tol`, `min_nbr`, `min_cluster`) đảm bảo tính tái lập khoa học. |

---

## CHƯƠNG 6: GIỚI HẠN HỆ THỐNG VÀ HƯỚNG MỞ RỘNG (LIMITATIONS & FUTURE WORK)

### 6.1. Hạn chế của dữ liệu đầu vào

* Do đặc tính quang học của cảm biến VIIRS DNB và sự tán xạ khí quyển, ánh sáng từ các nguồn bức xạ cường độ mạnh (cảng biển, khu công nghiệp, cầu lớn) có xu hướng tràn sang các điểm ảnh lân cận hoặc phản chiếu trên mặt nước (Elvidge et al., 2017; Gibson et al., 2021). Điều này có thể làm mở rộng nhẹ ranh giới của các cụm `High-High` ven sông/biển.

* Việc cắt ngưỡng các giá trị bức xạ âm về $0$ sau quá trình hiệu chỉnh ánh sáng tạp (stray-light correction) giúp đảm bảo tính hợp lý vật lý, nhưng làm giảm phương sai thông tin tại các vùng nông thôn cực kỳ thưa dân có mật độ chiếu sáng gần bằng $0$ (Gibson et al., 2021).

* Do độ phân giải gốc của sản phẩm VIIRS tháng xấp xỉ $463.83\text{ m}$, một ô lưới $500 \times 500\text{ m}$ chỉ chứa khoảng $1.16$ điểm ảnh gốc. Ở độ phân giải này, hai ô lưới liền kề có thể chia sẻ chung một điểm ảnh VIIRS qua phép trích xuất tỷ lệ phủ (`exactextract`), tạo ra tự tương quan không gian cơ học. Với các mô hình hồi quy nhân quả, khuyến nghị sử dụng kích thước lưới $\ge 1000\text{ m}$ và kiểm tra độ vững qua nhiều kích thước lưới.

### 6.2. Hạn chế phần cứng

* Việc triển khai trên hạ tầng đám mây miễn phí (~1GB RAM) giới hạn số lượng đa giác xử lý đồng thời ở mức `MAX_CELLS` $= 150,000$ ô. Do đó, ở độ phân giải siêu mịn ($500\text{ m}$), hệ thống phù hợp nhất cho phân tích cấp quận/hạt/huyện hoặc bang/tỉnh/thành phố vừa và nhỏ; đối với quy mô vùng lớn hoặc quốc gia, người dùng cần nâng độ phân giải lưới lên $2000\text{ m} - 5000\text{ m}$ hoặc triển khai trên máy trạm cục bộ.

### 6.3. Hướng mở rộng

1. **Tích hợp bộ dữ liệu VIIRS chuẩn hóa đa năm (Annual VNL V2):** Tích hợp thêm nguồn ảnh năm đã khử nhiễu nền và pháo sáng khí đốt của Earth Observation Group (`NOAA/VIIRS/DNB/ANNUAL_V21` / `V22`) (Elvidge et al., 2021) song song với bộ tổng hợp trung vị tháng hiện tại, kết hợp hiệu ứng cố định theo năm (Year Fixed Effects) cho hồi quy chuỗi thời gian dài.

2. **Động học không gian – thời gian (Spatio-Temporal LISA – LISTA):** Nâng cấp mô-đun `lisa_core.py` để tính toán ma trận dịch chuyển Markov không gian (Spatial Markov Transitions) và thống kê tự tương quan không – thời gian cục bộ (LISTA) (Rey, Murray, & Anselin, 2011; Ye & Rey, 2013), cho phép theo dõi trực tiếp quỹ đạo lan tỏa của các cụm điểm nóng qua từng giai đoạn phát triển.

---

## TÀI LIỆU THAM KHẢO

1. Anselin, L. (1995). Local Indicators of Spatial Association—LISA. *Geographical Analysis*, 27(2), 93–115. https://doi.org/10.1111/j.1538-4632.1995.tb00338.x

2. Baston, D. (2023). *exactextract: Fast and accurate raster/polygon zonal statistics* [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.11396419

3. Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing. *Journal of the Royal Statistical Society: Series B (Methodological)*, 57(1), 289–300. https://doi.org/10.1111/j.2517-6161.1995.tb02031.x

4. Caldas de Castro, M., & Singer, B. H. (2006). Controlling the False Discovery Rate: A New Application to Account for Multiple and Dependent Tests in Local Statistics of Spatial Association. *Geographical Analysis*, 38(2), 180–208. https://doi.org/10.1111/j.0016-7363.2006.00682.x

5. Chen, J., & Roth, J. (2024). Logs with Zeros? Some Problems and Solutions. *The Quarterly Journal of Economics*, 139(2), 891–936. https://doi.org/10.1093/qje/qjad054

6. Chen, X., & Nordhaus, W. D. (2011). Using luminosity data as a proxy for economic statistics. *Proceedings of the National Academy of Sciences*, 108(21), 8589–8594. https://doi.org/10.1073/pnas.1017031108

7. Conley, T. G. (1999). GMM estimation with cross sectional dependence. *Journal of Econometrics*, 92(1), 1–45. https://doi.org/10.1016/S0304-4076(98)00084-0

8. Donaldson, D., & Storeygard, A. (2016). The View from Above: Applications of Satellite Data in Economics. *Journal of Economic Perspectives*, 30(4), 171–198. https://doi.org/10.1257/jep.30.4.171

9. Elvidge, C. D., Baugh, K. E., Anderson, S. J., Sutton, P. C., & Ghosh, T. (2012). The Night Light Development Index (NLDI): a spatially explicit measure of human development from satellite data. *Social Geography*, 7(1), 23–35. https://doi.org/10.5194/sg-7-23-2012

10. Elvidge, C. D., Baugh, K., Zhizhin, M., Hsu, F. C., & Ghosh, T. (2017). VIIRS night-time lights. *International Journal of Remote Sensing*, 38(21), 5860–5879. https://doi.org/10.1080/01431161.2017.1342050

11. Elvidge, C. D., Zhizhin, M., Ghosh, T., Hsu, F. C., & Taneja, J. (2021). Annual Time Series of Global VIIRS Nighttime Lights Derived from Monthly Averages: 2012 to 2019. *Remote Sensing*, 13(5), 922. https://doi.org/10.3390/rs13050922

12. Fotheringham, A. S., & Wong, D. W. S. (1991). The modifiable areal unit problem in multivariate statistical analysis. *Environment and Planning A: Economy and Space*, 23(7), 1025–1044. https://doi.org/10.1068/a231025

13. Gibson, J., Olivia, S., Boe-Gibson, G., & Li, C. (2021). Which night lights data should we use in economics, and where? *Journal of Development Economics*, 149, 102602. https://doi.org/10.1016/j.jdeveco.2020.102602

14. Heckman, J. J. (1979). Sample Selection Bias as a Specification Error. *Econometrica*, 47(1), 153–161. https://doi.org/10.2307/1912352

15. Henderson, J. V., Storeygard, A., & Weil, D. N. (2012). Measuring Economic Growth from Outer Space. *American Economic Review*, 102(2), 994–1028. https://doi.org/10.1257/aer.102.2.994

16. LeSage, J., & Pace, R. K. (2009). *Introduction to Spatial Econometrics*. Chapman and Hall/CRC. https://doi.org/10.1201/9781420064254

17. Lessmann, C., & Seidel, A. (2017). Regional inequality, convergence, and its determinants – A view from outer space. *European Economic Review*, 92, 110–132. https://doi.org/10.1016/j.euroecorev.2016.11.009

18. Mirza, M. U., Xu, C., van Bavel, B., van Nes, E. H., & Scheffer, M. (2021). Global inequality remotely sensed. *Proceedings of the National Academy of Sciences*, 118(18), e1919913118. https://doi.org/10.1073/pnas.1919913118

19. Moran, P. A. P. (1950). Notes on Continuous Stochastic Phenomena. *Biometrika*, 37(1/2), 17–23. https://doi.org/10.1093/biomet/37.1-2.17

20. Openshaw, S. (1984). *The Modifiable Areal Unit Problem*. Concepts and Techniques in Modern Geography (CATMOG), No. 38. Geo Books.

21. Rey, S. J., & Anselin, L. (2007). PySAL: A Python Library of Spatial Analytical Methods. *The Review of Regional Studies*, 37(1), 5–27. https://doi.org/10.52324/001c.8285

22. Rey, S. J., Murray, A. T., & Anselin, L. (2011). Visualizing regional income distribution dynamics. *Letters in Spatial and Resource Sciences*, 4(1), 81–90. https://doi.org/10.1007/s12076-010-0048-2

23. Ye, X., & Rey, S. J. (2013). A framework for exploratory space-time analysis of economic data. *The Annals of Regional Science*, 50(1), 315–339. https://doi.org/10.1007/s00168-011-0470-4
