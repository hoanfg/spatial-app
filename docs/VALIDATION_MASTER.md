# Spatial-app — sổ cái validation tổng hợp

> **Tài liệu sống (living validation register)** · Khởi tạo: **11/11/2026** · Ngôn ngữ: tiếng Việt, giữ nguyên tên biến/thuật ngữ kỹ thuật bằng tiếng Anh.  
> **Phạm vi:** repository [hoanfg/spatial-app](https://github.com/hoanfg/spatial-app), ứng dụng Streamlit sử dụng GADM 4.1, VIIRS NTL, LISA, GHSL và Space-Time.  
> **Mục tiêu:** tập trung các kết quả đã kiểm chứng, quyết định phương pháp, giới hạn và các việc chưa làm **trong một file duy nhất**. Những validation tiếp theo được bổ sung vào file này bằng PR, không tạo một báo cáo rời cho từng lần chạy.

## 0. Cách đọc và quy tắc bằng chứng

**Trạng thái:**
- **PASS (trong phạm vi thử nghiệm):** phép tính/đối chiếu đạt tiêu chí ghi rõ tại trường hợp được thử; **không đồng nghĩa** đã kiểm chứng trên mọi địa phương, năm hay môi trường triển khai.
- **SENSITIVITY CHARACTERIZED:** đã xác định được sự thay đổi khi đổi giả định; có thể nhạy lớn mà **không phải bug**.
- **PARTIAL:** có bằng chứng nhưng một phần pipeline hoặc phép đối chiếu độc lập còn thiếu.
- **PENDING:** chưa đủ bằng chứng thực nghiệm.
- **FIXED:** vấn đề mã nguồn/tài liệu được xử lý qua PR và có kiểm thử liên quan.

**Provenance:** Các kết quả số ở mục 2–9 tổng hợp từ các lượt phân tích độc lập và CSV/GeoTIFF đã trao đổi trong phiên validation ngày 11/11/2026. Không đưa các file raster/CSV nặng vào GitHub trong PR tài liệu này. Vì vậy đây là **sổ cái bằng chứng đã báo cáo**, không phải một pipeline end-to-end có thể tái lập chỉ bằng việc clone repository. Muốn tái lập độc lập cần truy xuất đúng đầu vào và script/ZIP bằng chứng từ đợt kiểm chứng tương ứng; nơi chưa có bằng chứng lưu trữ bền vững trong repo phải được coi là một hạn chế lưu trữ.

**Điều tuyệt đối không suy diễn:** kết quả “PASS” của VIIRS tại Yanqing không tự chứng minh VIIRS là đại diện không thiên lệch của GDP, tính nhân quả, độ chính xác của mọi chỉ số thứ cấp, hay hiệu năng trên mọi địa phương.

## 1. Tập kiểm chứng chuẩn (golden pilot)

| Thuộc tính | Thiết lập |
|---|---|
| Địa phương | **Yanqing (Diên Khánh), Beijing, China** |
| Ranh giới | GADM v4.1, `GID_2 = CHN.2.1.11_1`; `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Beijing/CHN_Beijing_Yanqing_District.geojson` |
| Thời gian | 2020 (NTL, LISA, GHSL); 2014 → 2020 (Space-Time) |
| Lưới | UTM `EPSG:32650`, 500 m, cắt theo ranh giới |
| Số ô | **8.333**, diện tích tổng **~2.003,51 km²** |
| Ô biên loại khỏi kiểm định LISA | **600** (diện tích < 99% diện tích ô chuẩn) |
| Ô đủ điều kiện LISA | **7.733** |
| VIIRS collection | `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG`; band `avg_rad`, lọc `cf_cvg > 0` từng tháng |
| Annual aggregation của app | median ảnh tháng hợp lệ → `unmask(0)` → GeoTIFF `EPSG:4326`, nominal scale 463,83 m → clip âm về 0 → exactextract coverage-weighted mean |
| Local LISA baseline | raw NTL, Queen row-standardized lag, 999 conditional permutations **without replacement**, seed 42, two-sided pseudo-p, Benjamini–Hochberg FDR 5% |
| Điểm lưu ý | `EPSG:4326` và nominal scale **463,83 m**, không phải 463,83 km; pixel raster và ô UTM 500 m là hai lưới khác nhau |

**Input thực nghiệm đã dùng (tên file ở phiên validation):**
- `dien_khanh_NTL_2020_500m.csv`;
- `CHN_beijing_yanqing_2020_500m_lisa_cells.csv`;
- `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv`;
- `yanqing_viirs_2020_reference.tif`, `yanqing_valid_months_2020.tif`;
- `yanqing_viirs_2020_annual_mean.tif`, `yanqing_viirs_2020_masked_median.tif`;
- `yanqing_viirs_2014_reference.tif`, `yanqing_valid_months_2014.tif`, `yanqing_viirs_2014_masked_median.tif`.

Tên file là **định danh provenance**, không khẳng định file đang được lưu trong GitHub. CSV xuất `ntl_mean` làm tròn **4 chữ số thập phân**: dùng dung sai `0.00005 nW/cm²/sr` khi so với phép tính raster có độ chính xác cao hơn.

## 2. Ma trận trạng thái toàn dự án

| ID | Hạng mục | Trạng thái | Bằng chứng và giới hạn chính |
|---|---|---|---|
| V01 | GADM China curated geometries | **PASS (hình học)** | Đối chiếu **2.420** GeoJSON với full-resolution GADM China GPKG; hình học/GID khớp trong ngưỡng đối chiếu, không phát hiện duplicate/invalid/overlap > 1 m²; một lỗi tên metadata đã sửa |
| V02 | Unit/integration tests, static regressions | **PASS trong CI** | Sau PR #10, hai nhóm test trong Actions đã ghi nhận **32 + 22 = 54 passed**; test giả lập không phải benchmark Earth Engine thật |
| V03 | Independent Local Moran, Queen, FDR | **PASS cho Yanqing 2020** | Queen neighbors, quadrants và BH-FDR tái lập; kiểm tra mô phỏng hạt giống độc lập có sai khác Monte Carlo có giải thích |
| V04 | VIIRS 2020 raster → 500 m zonal mean | **PASS cho Yanqing** | **8.333/8.333** ô khớp trong sai số làm tròn CSV; bao gồm 600 ô biên |
| V05 | VIIRS 2014 raster → 500 m zonal mean | **PASS cho Yanqing** | **8.333/8.333** ô khớp; xử lý đúng một pixel âm nhẹ |
| V06 | Mean/median, zero/NoData sensitivity | **SENSITIVITY CHARACTERIZED** | Mean làm tăng NTL trung bình ~4,37%; 2020 masked median trùng zero-filled tại phạm vi pilot |
| V07 | Raw/P99/log LISA sensitivity | **SENSITIVITY CHARACTERIZED** | Raw–log HH Jaccard ~0,352: độ nhạy phương pháp đáng kể, không phải lỗi tính toán |
| V08 | Queen/Rook; 500 m/1.000 m | **SENSITIVITY CHARACTERIZED** | Queen/Rook tạo độ khác lớn; trùng lặp không gian giữa hai scale ở mức trung bình–khá |
| V09 | Space-Time regimes / Spatial Markov 2014→2020 | **PASS phép tính; interpretation FIXED** | Công thức/nhãn gốc tái lập; `Synchronized Decline` là **giảm vị thế tương đối**, không nhất thiết giảm NTL tuyệt đối; PR #11 làm rõ nhãn hiển thị |
| V10 | GHSL built-up / population | **PARTIAL** | App cho tương quan và bootstrap đáng khích lệ, nhưng pipeline ghép GHSL và AUC/bootstrap chưa được tái tạo độc lập từ raster/ô nguồn |
| V11 | Cross-location representativeness | **PENDING** | Chưa kiểm thử hệ thống ở nhiều loại địa phương |
| V12 | Multi-year temporal consistency | **PARTIAL** | Đã xác minh hai mốc 2014, 2020 và Space-Time; chưa xác minh đầy đủ từng năm chuỗi dài |
| V13 | External economic validity (GDP, proxies) | **PENDING** | Chưa có benchmark với chỉ số kinh tế độc lập |
| V14 | Streamlit Cloud RAM, network, failures, E2E | **PENDING** | Chưa có thử nghiệm có kiểm soát trên môi trường sản xuất; giới hạn RAM và chia GADM districts là **thiết kế bảo vệ có chủ đích**, không mặc nhiên là lỗi |

## 3. Audit mã nguồn và ranh giới — V01/V02

### 3.1 Audit địa giới GADM v4.1

- Đã kiểm tra **2.420** curated China GeoJSON bằng GADM China GPKG đủ độ phân giải: đối chiếu hình học và GID; không thấy invalid geometry, duplicated GID, hay diện tích chồng lấn ngoài dung sai >1 m² trong tập đã thử.
- **2.419/2.420** bản ghi có tên phù hợp nguồn; bản ghi ngoại lệ thuộc một tên vùng do dữ liệu nguồn; một tên `Nan` từng bị gán nhầm `Yiyang` ở `GID_2 = CHN.14.10.2_1`, được sửa theo nguồn trong PR #10. Một đơn vị GADM nguồn có tên NA không có trong tập curated — cần lưu ý phạm vi curated khác tổng hợp nguồn.
- Một số thành phố lớn đã cố ý được chia thành district nhằm giảm tải RAM Streamlit. Không được diễn giải việc chia nhỏ này là “lỗi thiếu city-wide analysis”.

### 3.2 Vấn đề mã nguồn được sửa — [PR #10](https://github.com/hoanfg/spatial-app/pull/10)

- Conditional Local Moran permutations từng lấy mẫu **with replacement**; đã chuyển sang sampling **without replacement** và chuẩn hóa Local I theo quy ước ESDA.
- Giữ nguyên **quy tắc pseudo-p hai phía có tie tolerance và FDR riêng của app**: không đồng nhất trực tiếp với `esda.Moran_Local.p_sim` mặc định khi phương pháp đếm tail/tie khác nhau.
- Bảo toàn NoData sentinel/mask khi đọc raster bằng đường đi `ntl/zonal.py`, tránh biến giá trị missing hữu hạn thành số đo thật trước khi trích xuất.
- Chỉnh metadata GADM và thêm regression tests.
- CI sau merge PR #10 đã ghi nhận **54 passed** qua hai nhóm chạy. Chưa chứng minh hiệu năng Earth Engine thật hoặc Streamlit Cloud nhờ CI này.

### 3.3 Cách diễn giải Space-Time — [PR #11](https://github.com/hoanfg/spatial-app/pull/11)

- PR #11 **đã merge** (merge SHA `4554e8feea683ffd56f585693a89f1f6b5f14aec`), Actions có trạng thái **success**.
- UI hiển thị **Synchronized Relative Decline**, giải thích z-score chuẩn hóa **riêng mỗi năm**, và ngưỡng chuyển động 0,05 là **ngưỡng mô tả**, không phải kiểm định ý nghĩa thống kê.
- **Không đổi** giá trị `spacetime_regime` trong CSV (vẫn là `4_Synchronized_Decline`), công thức hay schema export. Chi tiết: `docs/spacetime-relative-regime-interpretation.md`.

## 4. Independent Local Moran — V03

Áp dụng trên cùng **8.333** ô, **7.733** ô kiểm định; **600** ô bị edge-mask.

- Tái lập từng ô: số láng giềng Queen và quadrant **khớp toàn bộ**. Local Moran I khớp trong dung sai do số chữ số thập phân của CSV; BH-FDR **khớp 100% khi tính lại trên p-value đã xuất**.
- Baseline lưu CSV: **370 HH**, **2.510 LL**, **4.853 Not Significant**, **600 Edge-Masked**; tổng **2.880** ô có ý nghĩa (HH+LL).
- Chạy lại conditional permutations (999) với **seed độc lập** cho p-value Pearson ~**0,9967**; FDR significant **2.879** so với **2.880** từ app. HH **375** so với **370** (Jaccard ~0,935), LL **2.504** so với **2.510** (Jaccard ~0,940). Sai khác gần ngưỡng FDR là khả dĩ do Monte Carlo; **không** buộc phải khớp p-value từng ô khi seed khác.
- Những đợt tái chạy tiếp theo dùng đúng **seed 42** và cùng implementation/đầu vào đã tái lập **toàn bộ nhãn và p-value baseline**; kết quả không mâu thuẫn với thử nghiệm seed độc lập.

**Phân biệt:** Global Moran I và Local Moran I có chuẩn hóa khác nhau; không thể so các trị số theo cùng một định nghĩa nếu chưa căn chỉnh weights và convention. Nhãn HH được công bố ở đây là cụm có ý nghĩa theo **phép kiểm định của app**, không khẳng định vị trí hotspot có ý nghĩa kinh tế độc lập.

## 5. Independent VIIRS extraction — V04/V05

### 5.1 Quy trình benchmark

Tạo độc lập annual median VIIRS bằng Earth Engine theo đúng collection, cửa sổ năm, filter `cf_cvg > 0`, phép median và `unmask(0)` của app; tải GeoTIFF tham chiếu. Dựng lại polygon lưới 500 m bằng **đúng GADM Yanqing đầy đủ precision**, trích xuất trung bình theo coverage intersection pixel–ô; clamp giá trị âm trước khi tổng hợp theo quy tắc app. So sánh bằng `grid_id`.

**Không** đánh giá “PASS” từ phép lấy pixel gần tâm ô: bước đầu center-sampling cho tương quan thấp hơn và không tương đương zonal mean. Phép kiểm tra chính dùng giao diện tích.

### 5.2 Bằng chứng số

| Chỉ tiêu | 2014 | 2020 |
|---|---:|---:|
| Số ô polygon đối chiếu | 8.333 | 8.333 |
| Ô khớp trong sai số làm tròn CSV | **8.333/8.333** | **8.333/8.333** |
| Sai số tuyệt đối trung bình (nW/cm²/sr) | ~0,00002505 | ~0,000025 |
| Sai số tuyệt đối lớn nhất (nW/cm²/sr) | ~0,00004999 | ~0,000050 |
| Pearson (NTL app vs benchmark) | ~0,9999999998 | ~0,99999999997 |
| Số pixel GeoTIFF | 217 × 142 = 30.814 | 217 × 142 = 30.814 |
| Số tháng hợp lệ (`cf_cvg > 0`) | 12 tại mọi pixel xuất | 12 tại mọi pixel xuất |
| Missing trong ảnh median giữ mask | Không quan sát thấy | Không quan sát thấy |

2014 có **một pixel radiance âm nhẹ**, đóng góp vào **hai** ô lưới; đối chiếu chỉ khớp sau khi áp dụng cùng quy tắc đưa âm về 0 như app.

**Kết luận được phép:** phép tải/sản xuất annual median và tính **coverage-weighted zonal mean** ở độ chính xác CSV được kiểm chứng thành công cho hai năm và địa bàn nêu trên. **Không** từ đó kết luận tính đại diện của radiance với GDP, hoặc rằng mọi vùng/năm không có missing.

## 6. Measurement sensitivity — V06

Cố định Yanqing 2020 và lưới 500 m; thay **annual median** bằng **annual mean không trọng số theo 12 composite tháng**; so với median giữ nguyên mask.

| Chỉ tiêu | Annual median (baseline) | Annual mean | Masked median |
|---|---:|---:|---:|
| NTL mean / ô | 1,4137 | 1,4754 | 1,4137 |
| Gini NTL | 0,6809 | 0,6861 | 0,6809 |
| Global Moran I* | 0,91413 | 0,91456 | 0,91413 |
| HH count | 370 | 385 | 370 |
| LL count | 2.510 | 2.499 | 2.510 |
| HH area share | 4,617% | 4,804% | 4,617% |

\* Global Moran I trong lần đối chiếu này được tính với **binary Queen weights trên 8.333 ô**; không được thay cho định nghĩa Moran I vùng khác khi chưa đồng nhất mẫu/weights.

- Mean NTL cao hơn median khoảng **4,37%**; **Jaccard HH ~0,961**, **Jaccard LL ~0,962**.
- Masked median và zero-filled median trùng nhau toàn bộ pixel năm 2020, do không quan sát thấy missing trong raster của pilot. Thực tế này **không** chứng minh `unmask(0)` an toàn trên mọi vùng/năm.
- **Annual mean** ở đây là mean các composite tháng, **không** phải bình quân pixel theo tổng số quan sát `cf_cvg` và không đương nhiên tốt hơn median.

## 7. Transformation sensitivity — V07

Giữ raw annual median, Queen 500 m, **999 permutations / seed 42 / FDR 5%**. P99 nghĩa là cắt ngưỡng phân vị 99 **của các ô có NTL dương**, rồi mới chuẩn hóa; log là **log NTL trên ô sáng** trong `run_lisa`, không đánh đồng với `log1p(NTL)` được dùng trong Space-Time.

| Chỉ tiêu | Raw | P99 winsorized | Log |
|---|---:|---:|---:|
| HH | **370** | **457** | **1.050** |
| LL | 2.510 | 2.510 | 2.441 |
| Significant cells | 2.880 | 2.967 | 3.491 |
| HH area share | ~4,62% | ~5,70% | ~13,10% |
| Raw quadrant HH trước FDR | 1.072 | 1.135 | 2.517 |

**Jaccard của tập HH:** raw–P99 **0,810**; raw–log **0,352**; P99–log **0,435**.

Toàn bộ **370 raw HH** vẫn là HH khi dùng log; log mở rộng thêm **680** ô có HH, chứ không thay thế toàn bộ hotspot cũ. Trung vị NTL của 370 raw HH là ~**13,259**; của 680 HH mới dưới log là ~**2,731**. Khoảng **20,38%** ô kiểm định đổi quadrant raw ↔ log, nên khác biệt không chỉ do p-value.

**Diễn giải:** phân phối NTL lệch phải và cách biến đổi giá trị cực sáng ảnh hưởng sâu đến ngưỡng “high/low”; đây là **sensitivity về định nghĩa chỉ số**, không mặc nhiên là bug. **Quyết định nghiên cứu:** raw làm baseline cho tập trung bức xạ tuyệt đối; P99 là robustness outlier; log là alternative specification cho khác biệt tương đối. Công bố cả ba nếu kết luận phụ thuộc vào HH.

## 8. Spatial robustness — V08

Các biến thể dùng raw annual median, 999 permutations, seed 42, FDR 5%. Với grid 1.000 m, dựng lại polygon từ cùng GADM và tính NTL từ raster thay vì lấy bình quân thô các giá trị ô 500 m.

| Cấu hình | Tested cells | HH | LL | HH area share |
|---|---:|---:|---:|---:|
| Queen 500 m | 7.733 | **370** | 2.510 | **4,62%** |
| Rook 500 m | 7.733 | **187** | 906 | **2,33%** |
| Queen 1.000 m | 1.865 | **92** | 562 | **4,59%** |
| Rook 1.000 m | 1.865 | **46** | 210 | **2,30%** |

Toàn bộ grid **1.000 m** có **2.162** ô (không phải 1.865; 1.865 là ô tham gia kiểm định sau edge-mask).

- Rook 500 m giữ **187/370** HH Queen; tất cả HH Rook thuộc tập HH Queen ở pilot.
- Diện tích HH Queen từ khoảng **92,5 km²** (500 m) sang **92,0 km²** (1.000 m), nhưng vị trí không trùng tuyệt đối.
- **Spatial polygon Jaccard** giữa hai scale: Queen **0,655** (HH giao **73,0 km²**), Rook **0,686** (HH giao **37,75 km²**).

**Diễn giải:** kết quả phụ thuộc rõ vào adjacency definition (Queen/Rook), trong khi tổng diện tích HH ít đổi hơn qua scale 500→1.000 m. Đánh giá kết quả không gian phải dùng **diện tích giao/union**, không chỉ số ô, vì diện tích ô 1.000 m lớn gấp bốn lần ô 500 m. Không có lý do tự động coi Queen/Rook là “đúng/sai”; phải chọn theo lý thuyết và công bố robustness.

## 9. Temporal VIIRS, Space-Time và Markov — V09/V12

### 9.1 NTL tuyệt đối

Trên cùng 8.333 ô: NTL mean không trọng số tăng từ ~**0,4452 (2014)** lên ~**1,4137 (2020)**; **8.221 ô tăng**, **112 ô giảm**. Đây là so sánh radiance, **không tự động là tăng trưởng GDP**.

### 9.2 Công thức phân loại Space-Time

Đặt `v_t = log1p(max(NTL_t,0))`; chuẩn hóa `z_t` **riêng cho mỗi năm** trên ô không bị edge-mask; dùng Queen-neighbor lag `W z_t`. Sau đó:

- `Δz = z_2020 - z_2014`;
- `ΔLag z = W z_2020 - W z_2014`;
- `movement_magnitude = sqrt(Δz² + ΔLag z²)`;
- chỉ phân nhóm nếu đủ điều kiện và `movement_magnitude >= 0.05`.

**Đây là phân loại hướng thay đổi theo ngưỡng mô tả, không có permutation p-value hay FDR cho regime.**

| Raw CSV identifier | Số ô | Tăng NTL tuyệt đối | Giảm NTL tuyệt đối |
|---|---:|---:|---:|
| `1_Synergistic_Growth` | 1.456 | 1.456 | 0 |
| `2_Agglomeration_Shadow` | 75 | 75 | 0 |
| `3_Emergent_Pioneer` | 194 | 194 | 0 |
| `4_Synchronized_Decline` | **4.711** | **4.624** | **87** |
| `Excluded_or_Static` | 1.897 | 1.872 | 25 |

**4.624/4.711 (~98,15%)** ô gắn nhãn máy `Synchronized_Decline` vẫn **tăng radiance tuyệt đối**. Ý nghĩa đúng: cả ô và láng giềng **giảm vị thế NTL tương đối** trong hai phân phối năm, không phải “suy giảm ánh sáng/kinh tế” tuyệt đối. PR #11 đã giải quyết nhãn UI, còn mã xuất CSV được giữ nguyên có chủ đích.

Khi thay ngưỡng mô tả `movement_magnitude`, số ô Synchronized Relative Decline lần lượt khoảng **5.242** (0,025), **4.711** (0,050), **2.949** (0,100), **1.111** (0,200): kết luận chế độ nhạy với cutoff. Spatial Markov quartile gợi ý khoảng **74,90%** ô giữ cùng quartile 2014→2020; đây là **ổn định thứ hạng**, không phải NTL đứng yên.

Sai khác một ô `grid_id=3922` xuất hiện khi tái tính ngưỡng trực tiếp từ NTL **đã làm tròn** trong CSV; nhãn xuất gốc phù hợp với chỉ số chuyển động đã lưu. Không đủ bằng chứng coi đó là lỗi thuật toán.

### 9.3 Phạm vi đã/ chưa có

- **Đã xác minh:** độc lập raster **2014 và 2020** từng ô; hai mốc đầu-cuối; công thức nhãn, biến đổi, chuyển dịch quartile từ CSV.
- **Chưa xác minh:** chuỗi trung gian đầy đủ, khả năng so sánh liên thời gian dài, thay đổi cảm biến/xử lý sản phẩm và nhiễu nguồn sáng theo từng năm; không nên gọi đây là “longitudinal validation completed”.

## 10. GHSL, external validity và performance — V10–V14

### 10.1 GHSL: **PARTIAL**

Kết quả quality panel từ app tại Yanqing 2020:

| Nguồn GHSL | Spearman ρ với NTL | Block bootstrap 95% CI (đã hiển thị) | AUC (top 25%) |
|---|---:|---|---:|
| Built-up surface | **0,629** | ~0,59–0,68 | **0,867** |
| Population | **0,616** | ~0,58–0,66 | **0,851** |

Khoảng **63%** ô GHSL có giá trị 0 tại pilot, tùy lớp. Đây là **bằng chứng hội tụ sơ bộ từ app**, không phải kết quả independent raster-to-grid benchmark: cần tái xuất GHSL nguồn, xác minh định nghĩa resampling/zonal statistic, tái tính rho, AUC, bootstrap block và khoảng tin cậy. GHSL **không phải GDP**, và tương quan dương không xác thực mọi chỉ số kinh tế.

### 10.2 Cross-location và temporal generalization: **PENDING**

Đề xuất một bộ mẫu nhỏ, có chủ đích: (i) vùng đô thị trung tâm sáng mạnh; (ii) vùng công nghiệp/ngoại vi; (iii) vùng nông thôn/thấp sáng, khác Yanqing. Chọn theo dữ liệu thực và giới hạn RAM ứng dụng. Mỗi trường hợp tái xuất đúng CSV/GeoTIFF, kiểm tra pixel availability, 500 m grids, LISA và GHSL; ghi ngày chạy, commit app và đầy đủ configuration.

Tiếp theo kiểm tra **nhiều năm liên tiếp** trên cùng ranh giới/lưới (không chỉ 2014 và 2020) và cảnh báo đột biến do coverage, biên giới, sensor/composite. Không giả định thời gian dài đồng nhất nếu chưa thử.

### 10.3 External economic construct validity: **PENDING**

So sánh với nguồn kinh tế độc lập phù hợp độ phân giải (ví dụ GDP/hoạt động kinh doanh được công bố có thể so sánh theo vùng-năm). Nêu rõ chênh lệch cấp địa lý, thước đo, khả năng endogeneity, nguồn sáng phi kinh tế và không tự suy ra quan hệ nhân quả.

### 10.4 Streamlit deployment: **PENDING**

Benchmark trên Streamlit Community Cloud với RAM, thời gian và lỗi network/Earth Engine, kích thước vùng và lưới; ghi peak memory, retry behavior và khả năng download CSV. **Không gỡ bỏ** safeguard RAM hay chiến lược chia district chỉ để chạy benchmark. Báo cáo giới hạn tối đa đã kiểm chứng, không bịa thông số bộ nhớ.

## 11. Quyết định đã thống nhất (không cần tranh luận lại mỗi đợt)

1. **Giữ 500 m làm baseline**, 1.000 m làm spatial robustness; các khu vực lớn có thể cần grid lớn hơn hoặc chia district theo guardrail hiện tại.
2. **Raw NTL / Queen / FDR** là baseline đã kiểm chứng của trường hợp Yanqing; dùng P99, log, Rook và scale khác để báo cáo độ nhạy, không đổi baseline chỉ vì một biến thể cho nhiều hotspot hơn.
3. **VIIRS annual median** là phương pháp hiện hành của app; annual mean được dùng làm sensitivity, chưa thay thế chính thức.
4. **Giữ NoData khác zero về mặt khái niệm**. Việc hai cách trùng ở Yanqing 2014/2020 không khẳng định trùng trên tất cả sản phẩm/năm.
5. **Space-Time regime là thay đổi vị thế tương đối**, không phải phát hiện suy thoái kinh tế hay kết quả kiểm định FDR; giữ raw CSV codes để tương thích.
6. **Không đánh đồng “PASS numerical reproducibility” với “scientific validity of economic proxy”**.
7. **Không đưa các raster/CSV khối lượng lớn vào PR tài liệu này**; cần có kế hoạch lưu trữ/published evidence bền vững cho peer review.

## 12. Backlog validation tiếp theo và acceptance criteria

| Ưu tiên | Mã | Bước | Tiêu chí hoàn thành |
|---|---|---|---|
| P1 | V11 | Cross-location (2–3 địa phương khác loại) | Chọn & công bố sampling rationale; mỗi địa phương có independent raster → polygon/cell benchmark, LISA check, tài liệu sai số/ngoại lệ |
| P1 | V10 | GHSL independent | Cùng raster/lưới, tái lập việc ghép data và chỉ số Spearman/AUC/block bootstrap; ghi xử lý zero và độ phân giải |
| P2 | V12 | Multi-year consistency | Chuỗi năm có cùng hình học, metadata coverage và kiểm định biến động ngoại lệ/thiếu quan sát |
| P2 | V14 | Streamlit Cloud deployment | Log tài nguyên, thời gian, lỗi mạng, export, các trường hợp lớn và guardrail hoạt động đúng |
| P3 | V13 | External economic validity | Benchmark kinh tế có nguồn, cấp và định nghĩa phù hợp; báo cáo uncertainty/limitations |

**Điều kiện đóng chương trình validation** (không phải yêu cầu tất cả chỉ số phải cao): tái lập pipeline chính trên nhiều trường hợp, GHSL độc lập, giải thích rõ các sensitivity đáng kể, xác minh giới hạn cloud, và minh bạch giới hạn diễn giải kinh tế.

## 13. Quy tắc cập nhật file này sau mỗi lần validation

**Chỉ cần PR sửa file `docs/VALIDATION_MASTER.md`:**

1. **Không ghi đè lịch sử:** thêm một mục dưới *Change log* và cập nhật dòng trạng thái tương ứng; nếu phát hiện kết luận cũ sai, ghi rõ “superseded by” và lý do.
2. Mỗi lần thêm bằng chứng phải có: **ngày**, **commit/PR version**, **địa phương & GID**, **năm**, **collection & band**, **CRS/scale**, **grid specification**, **phương pháp & seed/perms/FDR**, **input hashes hoặc bền vững link**, **acceptance tolerance**, **kết quả**, **exceptions**, **script/test locator**.
3. Tách rõ: **code test**, **independent raster reference**, **cross-location replicate**, **external construct validity**; không dùng chung một dấu PASS cho bốn loại khác nhau.
4. Nếu chỉ có ảnh chụp webapp: ghi **reported/UI-only**. Nếu chỉ có kết quả tóm tắt không giữ file nguồn: ghi **evidence storage incomplete**.
5. Nếu thay đổi core algorithm, đặt PR code riêng hoặc chung với regression test, chỉ đổi trạng thái sau khi CI chạy và benchmark thực nghiệm nếu cần. Nhãn/copy/UI không được tự ý thay CSV identifiers.
6. Giữ bản tài liệu đọc được độc lập; không yêu cầu người đọc phải tải hàng chục báo cáo rời để hiểu kết luận chính.

### Mẫu bổ sung

```markdown
### YYYY-MM-DD — [Vxx] Tên đợt validation
- Repository commit/PR:
- Location (GID), years, source collection:
- Grid, CRS, pixel resolution, processing:
- Baseline and alternative specification:
- Inputs + immutable hashes / archived evidence:
- Method (including seed, permutations, FDR):
- Pass/fail acceptance criteria:
- Numerical results:
- Deviations and uncertainty:
- Conclusion with scope:
- Follow-up action / issue / PR:
```

## 14. Change log

| Date (Asia/Ho_Chi_Minh) | Update | Relevant source |
|---|---|---|
| 2026-11-11 | Tổng hợp audit GADM/NoData/Local Moran và CI; regression fixes | [PR #10](https://github.com/hoanfg/spatial-app/pull/10), `docs/audit-fixes-2026-11-11.md` |
| 2026-11-11 | Ghi nhận Yanqing VIIRS 2014/2020, LISA, GHSL sơ bộ, measurement/transformation/spatial/temporal sensitivity | Các CSV, GeoTIFF và evidence archive của chiến dịch validation; **chưa archive trực tiếp trong repo** |
| 2026-11-11 | Cập nhật giải thích Space-Time “relative decline” và cutoff mô tả | [PR #11](https://github.com/hoanfg/spatial-app/pull/11), `docs/spacetime-relative-regime-interpretation.md` |
| 2026-11-11 | Khởi tạo một sổ cái validation tổng hợp, cập nhật tiếp bằng PR | PR tạo file này |

---

**Tình trạng chung:** numerically validated **for the specified Yanqing pilot and two VIIRS years**, with substantive method sensitivity documented. **Not yet validated generally** across locations, GHSL independent pipeline, full longitudinal panel, economic construct validity or production cloud performance.
