<a id="top"></a>

# 📘 Spatial-app — Comprehensive Validation Specification & Evidence Register

| Item | Details |
| :--- | :--- |
| **Project** | `hoanfg/spatial-app` — GADM v4.1 / VIIRS NTL / Moran / LISA / GHSL / Space-Time |
| **Document** | `docs/VALIDATION_MASTER.md` — **single authoritative validation specification** |
| **Revision** | 2026-11-11, expanded from the initial brief register into the complete technical record |
| **Pilot** | Yanqing (Diên Khánh), Beijing, China; 8,333 grid cells; 2014 and 2020 |
| **Status** | Core computation replicated in the specified pilot; cross-location, GHSL independent, economic validity and Cloud E2E remain unverified |
| **Maintenance** | Update **this same file** with a PR when a validation campaign is completed |

> [!IMPORTANT]
> **What this document is:** A consolidated, detailed account of the actual audits and validation reports, including full methodologies, numerical tables, assumptions, evidence manifests, known limitations, and a controlled future validation protocol. It preserves original technical records instead of replacing them with high-level summaries.
>
> **What this document is not:** A proof that all scientific or economic interpretations are validated, nor a self-contained source-data archive. Source reports and evidence ZIPs were generated during the validation conversation and are **not currently committed to GitHub**. Reproducibility requires those inputs or their future archival deposit.

### Quick navigation

- [Part I — Current status, decisions, and backlog](#part-i)
- [Part II — Full original validation and audit records](#part-ii)
- [Record 1: Independent repository audit and benchmark](#r1)
- [Record 2: Original app-level NTL spatial econometrics verification](#r2)
- [Record 3: Independent Local Moran / LISA validation](#r3)
- [Record 4: Initial 2020 VIIRS reference (intermediate)](#r4)
- [Record 5: Final 2020 VIIRS polygon benchmark — all cells](#r5)
- [Record 6: 2014 VIIRS raster benchmark and coverage](#r6)
- [Record 7: Measurement sensitivity — mean/median and NoData](#r7)
- [Record 8: Transformation sensitivity — raw/P99/log](#r8)
- [Record 9: Spatial robustness — Queen/Rook, 500/1,000 m](#r9)
- [Record 10: Temporal Space-Time and Markov validation](#r10)
- [Record 11: Repository audit fix documentation (PR #10)](#repo-audit-doc)
- [Record 12: Space-Time interpretation documentation (PR #11)](#repo-spacetime-doc)
- [Part III — Evidence inventory, versioning, and maintenance](#part-iii)

<a id="part-i"></a>

# Part I — Current status and scientific scope

> **Tài liệu sống (living validation register)** · Khởi tạo: **11/11/2026** · Ngôn ngữ: tiếng Việt, giữ nguyên tên biến/thuật ngữ kỹ thuật bằng tiếng Anh.  
> **Phạm vi:** repository [hoanfg/spatial-app](https://github.com/hoanfg/spatial-app), ứng dụng Streamlit sử dụng GADM 4.1, VIIRS NTL, LISA, GHSL và Space-Time.  
> **Mục tiêu:** tập trung các kết quả đã kiểm chứng, quyết định phương pháp, giới hạn và các việc chưa làm **trong một file duy nhất**. Những validation tiếp theo được bổ sung vào file này bằng PR, không tạo một báo cáo rời cho từng lần chạy.

#### 0. Cách đọc và quy tắc bằng chứng

**Trạng thái:**
- **PASS (trong phạm vi thử nghiệm):** phép tính/đối chiếu đạt tiêu chí ghi rõ tại trường hợp được thử; **không đồng nghĩa** đã kiểm chứng trên mọi địa phương, năm hay môi trường triển khai.
- **SENSITIVITY CHARACTERIZED:** đã xác định được sự thay đổi khi đổi giả định; có thể nhạy lớn mà **không phải bug**.
- **PARTIAL:** có bằng chứng nhưng một phần pipeline hoặc phép đối chiếu độc lập còn thiếu.
- **PENDING:** chưa đủ bằng chứng thực nghiệm.
- **FIXED:** vấn đề mã nguồn/tài liệu được xử lý qua PR và có kiểm thử liên quan.

**Provenance:** Các kết quả số ở mục 2–9 tổng hợp từ các lượt phân tích độc lập và CSV/GeoTIFF đã trao đổi trong phiên validation ngày 11/11/2026. Không đưa các file raster/CSV nặng vào GitHub trong PR tài liệu này. Vì vậy đây là **sổ cái bằng chứng đã báo cáo**, không phải một pipeline end-to-end có thể tái lập chỉ bằng việc clone repository. Muốn tái lập độc lập cần truy xuất đúng đầu vào và script/ZIP bằng chứng từ đợt kiểm chứng tương ứng; nơi chưa có bằng chứng lưu trữ bền vững trong repo phải được coi là một hạn chế lưu trữ.

**Điều tuyệt đối không suy diễn:** kết quả “PASS” của VIIRS tại Yanqing không tự chứng minh VIIRS là đại diện không thiên lệch của GDP, tính nhân quả, độ chính xác của mọi chỉ số thứ cấp, hay hiệu năng trên mọi địa phương.

#### 1. Tập kiểm chứng chuẩn (golden pilot)

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

#### 2. Ma trận trạng thái toàn dự án

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

#### 3. Audit mã nguồn và ranh giới — V01/V02

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

#### 4. Independent Local Moran — V03

Áp dụng trên cùng **8.333** ô, **7.733** ô kiểm định; **600** ô bị edge-mask.

- Tái lập từng ô: số láng giềng Queen và quadrant **khớp toàn bộ**. Local Moran I khớp trong dung sai do số chữ số thập phân của CSV; BH-FDR **khớp 100% khi tính lại trên p-value đã xuất**.
- Baseline lưu CSV: **370 HH**, **2.510 LL**, **4.853 Not Significant**, **600 Edge-Masked**; tổng **2.880** ô có ý nghĩa (HH+LL).
- Chạy lại conditional permutations (999) với **seed độc lập** cho p-value Pearson ~**0,9967**; FDR significant **2.879** so với **2.880** từ app. HH **375** so với **370** (Jaccard ~0,935), LL **2.504** so với **2.510** (Jaccard ~0,940). Sai khác gần ngưỡng FDR là khả dĩ do Monte Carlo; **không** buộc phải khớp p-value từng ô khi seed khác.
- Những đợt tái chạy tiếp theo dùng đúng **seed 42** và cùng implementation/đầu vào đã tái lập **toàn bộ nhãn và p-value baseline**; kết quả không mâu thuẫn với thử nghiệm seed độc lập.

**Phân biệt:** Global Moran I và Local Moran I có chuẩn hóa khác nhau; không thể so các trị số theo cùng một định nghĩa nếu chưa căn chỉnh weights và convention. Nhãn HH được công bố ở đây là cụm có ý nghĩa theo **phép kiểm định của app**, không khẳng định vị trí hotspot có ý nghĩa kinh tế độc lập.

#### 5. Independent VIIRS extraction — V04/V05

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

#### 6. Measurement sensitivity — V06

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

#### 7. Transformation sensitivity — V07

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

#### 8. Spatial robustness — V08

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

#### 9. Temporal VIIRS, Space-Time và Markov — V09/V12

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

#### 10. GHSL, external validity và performance — V10–V14

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

#### 11. Quyết định đã thống nhất (không cần tranh luận lại mỗi đợt)

1. **Giữ 500 m làm baseline**, 1.000 m làm spatial robustness; các khu vực lớn có thể cần grid lớn hơn hoặc chia district theo guardrail hiện tại.
2. **Raw NTL / Queen / FDR** là baseline đã kiểm chứng của trường hợp Yanqing; dùng P99, log, Rook và scale khác để báo cáo độ nhạy, không đổi baseline chỉ vì một biến thể cho nhiều hotspot hơn.
3. **VIIRS annual median** là phương pháp hiện hành của app; annual mean được dùng làm sensitivity, chưa thay thế chính thức.
4. **Giữ NoData khác zero về mặt khái niệm**. Việc hai cách trùng ở Yanqing 2014/2020 không khẳng định trùng trên tất cả sản phẩm/năm.
5. **Space-Time regime là thay đổi vị thế tương đối**, không phải phát hiện suy thoái kinh tế hay kết quả kiểm định FDR; giữ raw CSV codes để tương thích.
6. **Không đánh đồng “PASS numerical reproducibility” với “scientific validity of economic proxy”**.
7. **Không đưa các raster/CSV khối lượng lớn vào PR tài liệu này**; cần có kế hoạch lưu trữ/published evidence bền vững cho peer review.

#### 12. Backlog validation tiếp theo và acceptance criteria

| Ưu tiên | Mã | Bước | Tiêu chí hoàn thành |
|---|---|---|---|
| P1 | V11 | Cross-location (2–3 địa phương khác loại) | Chọn & công bố sampling rationale; mỗi địa phương có independent raster → polygon/cell benchmark, LISA check, tài liệu sai số/ngoại lệ |
| P1 | V10 | GHSL independent | Cùng raster/lưới, tái lập việc ghép data và chỉ số Spearman/AUC/block bootstrap; ghi xử lý zero và độ phân giải |
| P2 | V12 | Multi-year consistency | Chuỗi năm có cùng hình học, metadata coverage và kiểm định biến động ngoại lệ/thiếu quan sát |
| P2 | V14 | Streamlit Cloud deployment | Log tài nguyên, thời gian, lỗi mạng, export, các trường hợp lớn và guardrail hoạt động đúng |
| P3 | V13 | External economic validity | Benchmark kinh tế có nguồn, cấp và định nghĩa phù hợp; báo cáo uncertainty/limitations |

**Điều kiện đóng chương trình validation** (không phải yêu cầu tất cả chỉ số phải cao): tái lập pipeline chính trên nhiều trường hợp, GHSL độc lập, giải thích rõ các sensitivity đáng kể, xác minh giới hạn cloud, và minh bạch giới hạn diễn giải kinh tế.

#### 13. Quy tắc cập nhật file này sau mỗi lần validation

**Chỉ cần PR sửa file `docs/VALIDATION_MASTER.md`:**

1. **Không ghi đè lịch sử:** thêm một mục dưới *Change log* và cập nhật dòng trạng thái tương ứng; nếu phát hiện kết luận cũ sai, ghi rõ “superseded by” và lý do.
2. Mỗi lần thêm bằng chứng phải có: **ngày**, **commit/PR version**, **địa phương & GID**, **năm**, **collection & band**, **CRS/scale**, **grid specification**, **phương pháp & seed/perms/FDR**, **input hashes hoặc bền vững link**, **acceptance tolerance**, **kết quả**, **exceptions**, **script/test locator**.
3. Tách rõ: **code test**, **independent raster reference**, **cross-location replicate**, **external construct validity**; không dùng chung một dấu PASS cho bốn loại khác nhau.
4. Nếu chỉ có ảnh chụp webapp: ghi **reported/UI-only**. Nếu chỉ có kết quả tóm tắt không giữ file nguồn: ghi **evidence storage incomplete**.
5. Nếu thay đổi core algorithm, đặt PR code riêng hoặc chung với regression test, chỉ đổi trạng thái sau khi CI chạy và benchmark thực nghiệm nếu cần. Nhãn/copy/UI không được tự ý thay CSV identifiers.
6. Giữ bản tài liệu đọc được độc lập; không yêu cầu người đọc phải tải hàng chục báo cáo rời để hiểu kết luận chính.

#### Mẫu bổ sung

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

#### 14. Change log

| Date (Asia/Ho_Chi_Minh) | Update | Relevant source |
|---|---|---|
| 2026-11-11 | Tổng hợp audit GADM/NoData/Local Moran và CI; regression fixes | [PR #10](https://github.com/hoanfg/spatial-app/pull/10), `docs/audit-fixes-2026-11-11.md` |
| 2026-11-11 | Ghi nhận Yanqing VIIRS 2014/2020, LISA, GHSL sơ bộ, measurement/transformation/spatial/temporal sensitivity | Các CSV, GeoTIFF và evidence archive của chiến dịch validation; **chưa archive trực tiếp trong repo** |
| 2026-11-11 | Cập nhật giải thích Space-Time “relative decline” và cutoff mô tả | [PR #11](https://github.com/hoanfg/spatial-app/pull/11), `docs/spacetime-relative-regime-interpretation.md` |
| 2026-11-11 | Khởi tạo một sổ cái validation tổng hợp, cập nhật tiếp bằng PR | PR tạo file này |

---

**Tình trạng chung:** numerically validated **for the specified Yanqing pilot and two VIIRS years**, with substantive method sensitivity documented. **Not yet validated generally** across locations, GHSL independent pipeline, full longitudinal panel, economic construct validity or production cloud performance.

---

<a id="part-ii"></a>

# Part II — Full technical validation records

The following records incorporate the **complete Markdown text of each previous validation report**. Their original report names are retained for provenance; headings are nested for readability. Reports from earlier phases were written before subsequent evidence became available, so **their contemporaneous limitations must be interpreted against the current summary in Part I and later records**.

| # | Full report | Original Markdown | Interpretation |
|---:|---|---|---|
| 1 | [Independent repository audit and benchmark](#r1) | `verification-report.md` | Full record |
| 2 | [Original app-level NTL spatial econometrics verification](#r2) | `Báo cáo kiểm chứng NTL spatial econometrics.md` | Historical intermediate |
| 3 | [Independent Local Moran / LISA validation](#r3) | `yanqing_validation_report.md` | Full record |
| 4 | [Initial 2020 VIIRS reference (intermediate)](#r4) | `yanqing_viirs_validation_report.md` | Historical intermediate |
| 5 | [Final 2020 VIIRS polygon benchmark — all cells](#r5) | `yanqing_viirs_all_cells_validation_report.md` | Full record |
| 6 | [2014 VIIRS raster benchmark and coverage](#r6) | `yanqing_2014_temporal_raster_validation_report.md` | Full record |
| 7 | [Measurement sensitivity — mean/median and NoData](#r7) | `yanqing_2020_measurement_sensitivity_report.md` | Full record |
| 8 | [Transformation sensitivity — raw/P99/log](#r8) | `yanqing_2020_transformation_sensitivity_report.md` | Full record |
| 9 | [Spatial robustness — Queen/Rook, 500/1,000 m](#r9) | `yanqing_spatial_robustness_validation_report.md` | Full record |
| 10 | [Temporal Space-Time and Markov validation](#r10) | `yanqing_temporal_validation_report.md` | Full record |

<a id="r1"></a>

## Independent repository audit and benchmark

**Original source:** `verification-report.md`. **Status:** retained technical record.

> [!NOTE]
> **Full validation record** — embedded from the source report below; any cross-reference to a separate ZIP is an evidence inventory item, not a GitHub-tracked artifact.

### Independent audit of hoanfg/spatial-app

Audit date: 11 November 2026 (Asia/Saigon). Commit: **81a53c96eb1405c56665146325383c6e02350dc9**. Branch main was checked against origin before and after testing. The repository's tracked files were not edited. All additional harnesses live outside the clone.

#### Assessment

The existing software suite is reproducibly healthy with full GIS dependencies: **36 passed, 0 skipped, 27.02 seconds**. This strengthens the evidence beyond the Claude report's 32 local passes and dependency skips. It does **not** justify an unconditional statement that the application or its scientific inferences are validated.

The independent checks found a consequential difference in LISA inference: the app samples neighbors **with replacement**, whereas the conventional conditional permutation benchmark samples without replacement. Local statistics also use a different normalization from ESDA. A source-metadata check found one district-name mismatch. Fractional raster extraction works on the tested cases, but finite NoData sentinels lose their masks.

Real VIIRS, observation-count and GHSL downloads remain **blocked by absent Earth Engine authorization**. The network itself worked. No real satellite measurements or empirical proxy correlations were produced.

#### Reproducibility and scope

A Git partial clone with a sparse checkout was used: complete application source, tests, docs, workflow/config files, and all China data. Other countries' data and full historical blobs were intentionally not downloaded. This is a clone of the actual pinned commit, not code reconstructed from a chat preview. The two earlier unfiltered clone attempts were stopped in favor of this smaller clone.

The original uploaded Claude report is preserved as `claude-checklist.md`. Python **3.13.7**, Windows 11, 4 physical/8 logical CPUs and **7.86 GiB physical RAM** were used. Full dependency versions are in `environment-freeze.txt`; installation logs include the initial overlapping-pip file-lock failure and the successful sequential retry. `pip check` reports no broken requirements. Important libraries: geopandas 1.2.0, rasterio 1.5.2, exactextract 0.3.0, ESDA 2.10.0, libpysal 4.15.1, NumPy 2.5.4, SciPy 1.18.1, Streamlit 1.67.0. See the freeze for the complete environment.

Selected pure functions in `app.py` were extracted using Python's AST, with their original function bodies unchanged and caching decorators removed, to avoid launching the application or initializing Earth Engine. The required globals were supplied by the harness. This tests those functions directly; it is not an end-to-end authenticated app run.

| Claude checklist item | Independent result | Evidence |
| --- | --- | --- |
| Syntax | Passed compilation of app, ntl and tests | final-checks.log |
| Complete existing suite | 36 passed, no skipped tests | pytest-full.log |
| GIS/exactextract dependencies | Installed and exercised | dependency-install.log; requirements-retry.log |
| Local/Global Moran against PySAL | Global matches; Local scaling and null-model differences identified | moran-comparison.json; moran-n30-exact.json |
| Real China GADM geometry and metadata | All 2,420 geometries checked; one source-name mismatch | china-topology-validation.json; china-gpkg-validation.json; china-schema-validation.json |
| Four municipalities | Separate units preserved; source units selected by their IDs cover GADM level 1 | china-gpkg-validation.json |
| Synthetic zonal extraction | Existing tests and independent fractional-coverage tests passed; finite NoData limitation reproduced | raster-comparison.json |
| Additional UI buttons | Five LISA/panel buttons and offline negative-clipping button ran without exceptions/errors | ui-clicks.json; quality-ui-click.json |
| Real VIIRS / cloud-free month count / GHSL | Blocked: Earth Engine account not authorized | earth-engine-probe.json |
| 500 m RAM | Measured synthetic grid/extraction/LISA plus real municipality grid construction | ram-benchmark.json; municipality-grid-benchmark.json |
| Threshold calibration / housing-vacancy interpretation | Not empirically validated; no ground-truth dataset supplied | Scope limitation |
| VIIRS temporal continuity across 2022 | No real time-series test possible without authorized data access | Scope limitation |
| GitHub CI history | Workflow configuration reviewed; historical CI logs were not independently re-audited | Local full-suite run supplies direct evidence instead |
| Contributor sidebar cache | Outside the computational audit; not tested | No claim made |

#### Findings requiring attention

##### 1. Local Moran inference uses a different conditional null model (high priority)

`ntl/lisa_core.py:local_moran` draws neighbor indices using `rng.integers` for each neighbor slot. The focal observation is excluded, but other observations can repeat within the same simulated neighborhood. This is conditional resampling **with replacement**, not the usual conditional randomization without replacement. It changes the null distribution, particularly for small active samples or high neighbor counts. Matching a seed alone cannot make two different algorithms equivalent.

For a 3×3 synthetic grid corner, exhaustive enumeration gives a two-sided smaller-tail probability of **0.142857** without replacement (56 combinations), versus **0.218750** with replacement (512 ordered samples). The app gives **0.221020** using 99,999 simulations, consistent with its with-replacement implementation.

This also occurs at the app's stated minimum sample size, not only on a nine-cell illustration. On a 30-cell 6×5 grid, exact corner probabilities are **0.564860** without replacement and **0.583624** with replacement; the app gives **0.579220**, and ESDA gives **0.562700** after explicitly converting its one-tail pseudo p to the two-tail convention. In this particular 30-cell fixture, the app identifies **0** cells at unadjusted 5%, versus **1** for ESDA. This is one reproducible fixture, not an estimate of the error rate across real datasets.

The application counts both tails inclusively with a 1e-12 tie tolerance. ESDA's smaller-tail handling also differs at ties. Consequently raw `p_sim` values must not be compared as if all conventions were identical. The exact enumerations isolate the with/without-replacement difference independently of those tie and seed details.

Recommendation: choose and document the intended conditional null; use sampling without replacement if conventional ESDA/GeoDa comparability is intended, then rerun significance, FDR and downstream hotspot checks. **No fix was applied.** Until resolved, report LISA significance as this implementation's custom resampling result, not as independently ESDA-validated inference.

##### 2. Local I normalization differs from ESDA (explicit convention required)

For all six Queen/Rook cases (n=9, 100, 400), all raw quadrants agree. The app's unrounded Local I equals ESDA Local I multiplied by **n/(n−1)**. Multiplying the app values by (n−1)/n leaves a maximum discrepancy of about **1.8e-15**. This is a normalization difference rather than evidence of wrong neighbor signs or quadrants. It should be documented or aligned before exchanging Local I values with ESDA.

This scaling is separate from the p-value problem above. Changing only the scaling will not correct the null model.

##### 3. One China district name differs from the GADM source (medium priority)

The file `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Hunan_Yiyang/CHN_Hunan_Yiyang_Yiyang_District.geojson` has `GID_2 = CHN.14.10.2_1` and `NAME_2 = Yiyang`. The matching GADM 4.1 level-3 source record has `GID_3 = CHN.14.10.2_1` and **NAME_3 = Nan**. Its geometry is preserved; its display/file label does not preserve the source name. This can misidentify selected or exported observations even when the geometry is correct. No rationale for the alias was established in this audit.

All other **2,419** source level-3 names match exactly. All **2,420** types match source `ENGTYPE_3`.

##### 4. Finite raster NoData masks are dropped (limited current-path exposure)

`ntl/zonal.py:zonal_stat` reads an unmasked array and rewrites it without copying the source NoData metadata. On a one-row raster `[10, -9999]`, where -9999 is explicitly marked NoData, the clipped mean is **5**, whereas a mask-preserving mean of valid pixels is **10**. Keeping negatives would also admit the sentinel into calculations.

The main `app.py` path uses the same read/rewrite pattern. The current Earth Engine path explicitly unmask-fills missing values with zero upstream, so this fixture is a robustness limitation for finite-sentinel rasters, not proof that an actual Earth Engine result was corrupted. Zero-filling absent observations is itself an intentional measurement convention and must remain visible in provenance.

#### Numerical and raster checks

Global Moran in `app.py:morans_i` uses **binary Queen weights**. With that same weight definition, ESDA and the app agree to numerical precision: for n=100, app I = **0.2774650541675269**, ESDA I = **0.27746505416752687**. The second n=400 case also matches to numerical precision. This validates the observed I on the tested grids; no claim of identical p-values is made where permutation generators or tail definitions differ.

Local Moran uses **row-standardized** weights on the active/lit, non-edge sample. Comparisons used the same active sample and remapped ESDA's quadrant codes. Main-app binary Global Moran and the LISA region summary are not interchangeable statistics: their weights and potentially their samples differ.

The independent 2×2 raster test used fractional polygon coverage and deliberately nonsequential IDs. A polygon spanning half of all four pixels yields mean **4**, weighted sum **8**; the single top-left pixel yields **1** for both. Ordering is retained. Outside-raster mean stays NaN when `fill_missing=None`; an outside sum is zero. The existing negative-clipping and NaN-to-zero tests also passed. These cases establish tested fractional-coverage behavior, not the accuracy of every projection/resampling configuration or real satellite product.

#### China GADM validation

All **2,420** curated GeoJSON files were decoded and checked: no invalid/empty geometry, no duplicate district GID, and no pairwise polygon overlap exceeding **1 m²**, measured after projection to EPSG:6933. Sub-m² slivers and exact zero-tolerance topology were not asserted away.

The full-resolution official GADM GeoPackage has **2,421** level-3 records. Every curated ID matches a source level-3 ID. The sole omitted source record has every administrative attribute set to the literal `NA`; it is not silently counted as a named district. No unmatched curated ID was found.

All **2,420** curated geometries match the source coordinate structure after Polygon/MultiPolygon normalization and coordinate tolerance **1e-8 degree**; maximum relative planar area discrepancy is **5.09e-13**. This demonstrates preservation of the downloaded GADM source within serialization precision, not present-day legal boundary accuracy. The source GeoPackage SHA-256 is recorded in `source-hashes.json`.

The curated schema is deliberately remapped: source `GID_3` becomes curated `GID_2`; `NAME_3` becomes `NAME_2`; `ENGTYPE_3` becomes `TYPE_2`; and curated `NAME_1` is the processing folder/group, often province plus prefecture, rather than always the original province. All folder grouping rules match after normalization of accents, whitespace and punctuation. External joins must use the preserved ID, not assume original GADM column semantics.

| Municipality | Curated units | Folder | Source units selected by curated IDs vs ADM1 symmetric-difference fraction |
| --- | ---: | --- | ---: |
| Beijing | 11 | Beijing | 0 |
| Shanghai | 12 | Shanghai | 0 |
| Tianjin | 12 | Tianjin | 0 |
| Chongqing | 32 | Chongqing | 0 |

The zero fractions are computed from source subdivisions selected by the curated ID set; preservation of the actual curated coordinates is established separately at the 1e-8-degree tolerance above. Thus these municipalities were not accidentally replaced with one whole-city analysis file. Their subdivision count and any aggregated central-city unit reflect this GADM source; this does not establish that they are a complete set of today's official districts.

An initial comparison used GADM's much smaller downloadable GeoJSON, whose geometry differs from the full-resolution GeoPackage. Exact geometry equality and raw NAME_1 comparisons from that preliminary pass are superseded by the GeoPackage and explicit schema-mapping checks. Do not interpret the preliminary differences as missing or corrupted geometry.

#### Earth Engine and dataset checks

The Earth Engine discovery endpoint returned HTTP **200**, as did the GHSL catalog. `ee.Initialize()` failed with `EEException: Please authorize access to your Earth Engine account ...`. No authentication ceremony was started and no private keys were requested or copied.

Planned live ROI: **116.38–116.40° E, 39.89–39.91° N**, year **2020**. Annual VIIRS median, cloud-free observation-month raster, GHSL built-up and GHSL population were all gated on successful initialization and therefore **not executed**. There is no live-data agreement statistic in this report.

The public catalog confirms the app's VIIRS dataset identifier and bands `avg_rad`/`cf_cvg`, and GHSL dataset identifiers and semantic bands `built_surface`/`population_count`. GHSL epochs are spaced five years apart, with interpolation/extrapolation in the products. The code's `nearest_epoch` caps selection at 2020; that cap should not be read as proof every 2020 pixel is a direct observation. Selecting GHSL band index 0 is position-dependent and was not exercised against the live collection here.

The `MAX_PIXELS=3,000,000` preflight is a code safeguard, not an empirical proof all download shapes satisfy Earth Engine limits. Official getDownloadURL limits also include **32 MB** and **10,000 pixels per dimension**. Long thin regions and reprojection details remain untested against the service.

VIIRS nominal pixel size **463.83 m** is a length, approximately **0.215 km²** per square pixel; a 500 m analytical cell is **0.25 km²**. Neither should be described as 463 or 500 square metres. The monthly product is not filtered for all temporary lights/background. No empirical calibration, temporal discontinuity test, vacancy/price validation, or causal interpretation was established.

#### 500 m memory benchmarks

Each case ran in a fresh subprocess. The monitor sampled at 50 ms and included the Python launcher **and all child processes**, recording peak summed resident RAM and peak private committed bytes. The first launcher-only monitor was recognized as invalid and discarded; only corrected runs below are used. There was no enforced 1 GiB container limit. Peak RSS sampling can miss short spikes, and summed RSS may double-count shared pages. Windows private commitment is not Linux container RSS.

Synthetic cases use square UTM boundaries, one float32 raster pixel per 500 m cell, the actual `build_grid`, actual `zonal_stat`, and actual `run_lisa` with **499 permutations**. The raster values are synthetic. Global Moran, Folium rendering, Streamlit/cache state, real EE response buffers, and concurrent sessions are excluded. Pure-function harness overhead is included. Runs were single measurements; timings are indicative and affected by other audit work on the same machine.

| Cells | Grid seconds | Zonal seconds | LISA seconds | Peak RSS MiB | Peak private MiB |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 0.47 | 3.85 | 0.80 | 162.6 | 609.9 |
| 50,176 | 2.56 | 20.33 | 9.33 | 215.5 | 665.3 |
| 149,769 | 9.24 | 65.97 | 29.54 | 343.4 | 798.1 |

Real municipality geometries were unioned and reprojected with the app's dynamic UTM rule, then passed to its unmodified grid constructor. These cases measure **grid construction only**, not real VIIRS extraction or whole-city LISA:

| Municipality | Result / cells | Grid seconds | Peak RSS MiB | Peak private MiB |
| --- | ---: | ---: | ---: | ---: |
| Beijing | 66607 | 26.234 | 209.9 | 423.8 |
| Shanghai | 29021 | 136.381 | 191.9 | 400.3 |
| Tianjin | 47677 | 33.932 | 183.2 | 394.0 |
| Chongqing | Guard rejected | 0.000 | 109.9 | 301.8 |

Chongqing's bounding-box estimate is **844,161**, exceeding the preclip guard **600,000**; it rejects before allocating the grid. Its estimated clipped count is **333,830**, also beyond the 150,000 cap. Beijing, Shanghai and Tianjin do build at 500 m in this environment. Therefore the blanket claim that every whole-city 500 m grid is impossible is unsupported, while partitioning large or complex areas remains useful and Chongqing's rejection is verified.

These results do **not** verify the README's universal “within 1GB without crashing” claim on Streamlit Community Cloud. A full authenticated app/container workload, real geometry/raster complexity, caching, and concurrent user activity could increase memory. No cloud OOM experiment was performed.

#### UI coverage and remaining limits

The existing two Streamlit AppTests passed. An additional harness clicked seed stability, raw/P99/log comparison, tail-fraction sensitivity, robustness checks, and add-to-panel using the suite's 400-cell synthetic fixture. All five had zero app exceptions and zero `st.error` elements. A separate raster-backed quality-panel test clicked “compare without clipping negatives” and populated the expected cache (4 cells, 25% changed, maximum difference 2).

These are AppTest checks, not manual browser/rendering QA. Earth Engine-backed quality buttons and the real acquisition-to-export workflow remain blocked by authentication. No claims are made for external housing/vacancy validity, calibrated “strong/weak” thresholds, multi-year continuity or production cloud behavior.

#### Next actions supported by evidence

1. Resolve/document the conditional permutation model and Local I normalization before relying on LISA significance as ESDA-compatible.
2. Review the Nan/Yiyang source-name discrepancy using `CHN.14.10.2_1` as the identity.
3. Preserve finite NoData masks if accepting rasters beyond the current zero-unmasked EE path.
4. Run the supplied Earth Engine probe in an authorized project, then compare real annual values, observation counts, GHSL aggregation and temporal continuity.
5. Measure the complete deployed application under its actual memory limit before retaining an unconditional 1 GB reliability claim.

No repository fixes or external publications were made.

#### Primary references

- [Audited commit](https://github.com/hoanfg/spatial-app/tree/81a53c96eb1405c56665146325383c6e02350dc9)
- [GADM 4.1 download page](https://gadm.org/download_country.html) and [China full-resolution GeoPackage](https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_CHN.gpkg)
- [VIIRS monthly VCMSLCFG catalog](https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_MONTHLY_V1_VCMSLCFG)
- [GHSL built surface catalog](https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S)
- [GHSL population catalog](https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP)
- [Earth Engine getDownloadURL limits](https://developers.google.com/earth-engine/apidocs/ee-image-getdownloadurl)
- ESDA implementation actually installed: see `esda-reference-excerpts.txt` and package version in `environment-freeze.txt`; comparison formulas were inspected locally rather than relying on recalled documentation.


<a id="r2"></a>

## Original app-level NTL spatial econometrics verification

**Original source:** `Báo cáo kiểm chứng NTL spatial econometrics.md`. **Status:** historical / superseded where later checks completed.

> [!CAUTION]
> **Historical/intermediate verification.** This record is retained in full for auditability, but its scope limits or partial findings were superseded by the later final validation chapters. Read the final chapter and the current status table for the authoritative result.

### Báo cáo kiểm chứng: NTL spatial econometrics

Nov 11, 2026 · @hoang le

#### Kết luận

**Logic tính toán đã được kiểm tra trên dữ liệu giả lập; chưa có bất kỳ phép thử nào trên dữ liệu vệ tinh thật.** 32 test qua, 2 test bị bỏ qua ở máy mình vì thiếu thư viện, và CI trên GitHub báo xanh cho bản `main` hiện tại. Không có benchmark đối chiếu với phần mềm khác hoặc kết quả đã công bố.

- **Đã kiểm chứng:** cú pháp, 32 test logic trên dữ liệu tổng hợp, CI xanh, và mã trong `main` trùng với mã đã kiểm (trừ một dòng tiêu đề giao diện).
- **Chưa kiểm chứng:** mã tải dữ liệu từ Earth Engine (đếm tháng, GHSL), các bảng điều khiển mới khi bấm nút, hiệu năng và bộ nhớ 1GB như README nêu, và các ngưỡng kết luận.
- **Hệ quả cho nghiên cứu:** chưa nên trích số liệu từ công cụ như bằng chứng thực nghiệm cho đến khi chạy một vùng thật và đối chiếu được (mục 4 và 5).

#### Lệnh đã chạy và kết quả thực tế

Chạy ngày 11/11/2026 trên `main` tại commit `81a53c96`, Python 3.13.18, numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, pytest 9.1.1. Máy này **không có** streamlit, altair, geopandas, rasterio, exactextract, earthengine-api và folium, và không cài thêm được vì mạng bị chặn.

| Lệnh | Kết quả thực tế | Ý nghĩa |
| --- | --- | --- |
| `python3 -m py_compile app.py ntl/*.py tests/*.py` | OK, không lỗi | Chỉ chứng minh cú pháp hợp lệ, không chứng minh đúng |
| `python3 -m pytest -q -rs` | 32 passed, 2 skipped trong 4,55 s | Skip: `test_ui_smoke.py` (thiếu streamlit), `test_zonal.py` (thiếu rasterio) |
| `pytest --collect-only` | 22 test ở `test_lisa_reliability.py`, 10 test ở `test_robustness.py` | T01–T20 lõi LISA, T21–T28 phần mới |
| `same_logic.py origin/robustness-suite` (so cây cú pháp AST) | Tất cả file `OK`, trừ `ntl/quality_ui.py` khác | Khác chỉ ở một chuỗi tiêu đề ("Kiểm tra sâu (chạy khi bấm nút)" thành "Kiểm tra sâu") và docstring. Logic trong `main` trùng mã đã kiểm |
| GitHub Actions, workflow `tests`, `main` @ `81a53c96` | `success` | CI có cài đủ thư viện, nên `test_zonal` và `test_ui_smoke` chạy ở đó. Mình thấy kết luận từng lần chạy, chưa đọc lại log chi tiết hôm nay |
| GitHub Actions, nhánh `robustness-suite` | Lần 1 `failure` (01:18 UTC), lần sau sửa test `success` (01:22 UTC) | Lỗi lần 1 là kỳ vọng sai trong `test_zonal` do mình tính nhầm, không phải lỗi mã |

#### Benchmark và ngưỡng đã dùng

**Không có benchmark bên ngoài.** Trong các lệnh mình tra lại được, không có phép so sánh với PySAL/esda hay GeoDa (hai gói `esda` và `libpysal` không có trên máy này), không so với kết quả đã công bố, và không đo thời gian hay bộ nhớ. Các test kiểm tính đúng đắn nội bộ: bất biến toán học (ví dụ T07 kiểm định lý hoán vị của trung bình đệ tâm), trường hợp suy biến (toàn tối, hằng số, đảo biệt lập) và ổn định theo seed.

Các ngưỡng sau là **quy ước thực hành được đặt cứng trong mã, chưa hiệu chỉnh bằng dữ liệu hay tài liệu**:

| Ngưỡng | Giá trị | Dùng để |
| --- | --- | --- |
| Jaccard trung vị của các biến thể | ≥ 0,70 "vững"; ≥ 0,50 "trung bình"; dưới đó "yếu" | Kết luận độ vững của cụm High-High |
| "Lõi vững" | Là HH ở bản gốc và trong ít nhất 80% số lần chạy | Diện tích ổn định |
| Spearman ρ với GHSL | ≥ 0,60 "mạnh"; dưới 0,40 "yếu"; cần ít nhất 30 ô lõi | Mức đồng thuận ngoài |
| Bootstrap theo khối | 200 lần, khối 5×5 ô | Khoảng tin cậy của ρ |
| Cảnh báo chất lượng dữ liệu | pixel âm > 10%; có pixel NaN; ô bằng 0 > 50% (chỉ lưu ý); pixel không có tháng quan sát > 1%; pixel dưới 3 tháng > 20% | Khung "Chất lượng dữ liệu" |
| So sánh cắt âm / giữ âm | Cảnh báo nếu ρ dưới 0,98 hoặc tỷ lệ ô thay đổi vượt 10% | Kết luận về xử lý giá trị âm |
| Sàn p-value | 2 / (số hoán vị + 1) | Với ít hoán vị và FDR, cụm có thể không bao giờ bị bác bỏ (đã gặp với 199 hoán vị) |

Khi viết bài, nên gọi đây là ngưỡng mô tả tham khảo và báo cáo từng Jaccard thay vì chỉ nhãn "vững".

#### Phép thử có dữ liệu thật

**Không có.** Trong các lệnh mình tra lại được, không có lần nào chạy trên ảnh VIIRS, dữ liệu GHSL hay ranh giới GADM thật.

- **Dữ liệu của các test** đều do mã tự sinh bằng `numpy.random.default_rng` với seed cố định (trừ `test_zonal`, dùng GeoTIFF nhỏ tự dựng trong bộ nhớ).
- **`test_zonal`** dùng thư viện thật (rasterio, exactextract) nhưng trên ảnh 2×4 pixel dựng sẵn. Nó chỉ chạy trên CI.
- **`test_ui_smoke`** chạy giao diện bằng `AppTest` với dữ liệu tổng hợp, không gọi Earth Engine. Nó kiểm tra tab LISA hiển thị không lỗi và có khung chẩn đoán; không bấm nút nào.
- **Thư mục `data/`** có ranh giới GADM của 35 nước nhưng không test nào đọc chúng.
- **Mạng:** môi trường chạy của mình không ra được Earth Engine và không có thông tin đăng nhập.

Bạn đã chạy ứng dụng thật ở spatial-app.streamlit.app và gửi ảnh chụp giao diện. Đây là bằng chứng rằng ứng dụng chạy được, nhưng mình chưa đối chiếu số liệu nhìn thấy trong ảnh với một nguồn độc lập.

#### Những điểm chưa thể kiểm chứng

Bảng dưới đây nêu từng điểm, vì sao chưa kiểm được và cách kiểm.

| Điểm chưa kiểm chứng | Vì sao | Cách kiểm |
| --- | --- | --- |
| Mã tải từ Earth Engine: đếm tháng quan sát (`cf_cvg`), GHSL (`JRC/GHSL/P2023A/GHS_BUILT_S`, `GHS_POP`), tên band, epoch, giới hạn 3 triệu pixel | Không có mạng tới Earth Engine và không có thông tin đăng nhập; test chỉ dùng đối tượng giả (`MagicMock`) | Chạy từng nút trong ứng dụng thật với một vùng nhỏ; đối chiếu tên band và đơn vị với tài liệu dataset |
| Các khung mới khi bấm nút ("Chất lượng dữ liệu" ở tab Dữ liệu, "Kiểm định độ vững" ở tab LISA) | Smoke test chỉ hiển thị tab LISA, không bấm nút; khung "Chất lượng dữ liệu" nằm trong `app.py` nên không được test nào chạm tới | Mở ứng dụng, bấm từng nút, theo dõi lỗi; thêm test `AppTest` có bấm nút |
| Đúng đắn của LISA so với phần mềm chuẩn | Chưa cài `esda`, `libpysal` và không có mạng | Chạy cùng một lưới với esda (hoặc GeoDa), so Moran's I, quadrant, p-value với cùng seed và số hoán vị |
| Hiệu năng và giới hạn \~1GB RAM mà README nêu | Chưa đo thời gian hay bộ nhớ trên vùng lớn | Đo trên Streamlit Cloud với vùng lớn nhất bạn dự định; ghi đỉnh RAM và thời gian |
| Ngưỡng kết luận (Jaccard, ρ, các cảnh báo chất lượng) | Là quy ước, chưa hiệu chỉnh | Mô phỏng trên dữ liệu có đáp án biết trước; hoặc nêu rõ là tham khảo khi viết bài |
| Chuỗi VIIRS có bị đổi mã hóa hay hiệu chỉnh theo năm không (bộ `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG`) | Chưa tra tài liệu dataset; một bài 2026 nêu thay đổi mã hóa năm 2022 ở một sản phẩm VIIRS khác | Đọc mô tả dataset trên Earth Engine; vẽ ánh sáng trung bình cả nước theo năm để tìm bước nhảy |
| Khung "khoảng tối" có thực sự phát hiện nhà bỏ trống/bong bóng không | Không có dữ liệu giá nhà hay nhà trống để đối chiếu, và công cụ chưa tính "khoảng tối" như một đại lượng | Đây là việc của nghiên cứu, không phải của phần mềm: cần dữ liệu giá nhà/nhà trống của ít nhất một nước |
| Danh sách Contributors trên GitHub | API và lịch sử đã sạch; thanh bên vẫn hiện "claude" do bộ nhớ đệm | Kiểm tra lại sau vài ngày; nếu còn, liên hệ GitHub Support |


<a id="r3"></a>

## Independent Local Moran / LISA validation

**Original source:** `yanqing_validation_report.md`. **Status:** retained technical record.

> [!NOTE]
> **Full validation record** — embedded from the source report below; any cross-reference to a separate ZIP is an evidence inventory item, not a GitHub-tracked artifact.

### Kiểm chứng độc lập Local Moran / LISA — Diên Khánh, Bắc Kinh (2020, 500 m)

**Ngày:** 11/11/2026. **Nguồn:** `CHN_beijing_yanqing_2020_500m_lisa_cells.csv` do người dùng xuất từ spatial-app. **Công thức đối chiếu:** repository `hoanfg/spatial-app`, `main` sau PR #10, commit `9574cf872c52d266aa15c363df7965cce31601f0`. Đây là phân tích độc lập trên bản CSV đã xuất, **không phải** một phép đo lặp lại từ raster VIIRS gốc hay một phiên chạy ESDA.

#### Kiểm chứng xác định (deterministic)

| Phép kiểm | Kết quả |
|---|---|
| Số dòng / ô | 8.333 |
| Ô biên theo ngưỡng diện tích < 0,99 × 0,25 km² | 600; khớp hoàn toàn |
| Ô tham gia LISA | 7.733 |
| Ma trận láng giềng Queen, so số láng giềng từng ô | 8.333/8.333 khớp |
| Quadrant thô HH, LL, HL, LH | 7.733/7.733 khớp |
| Local Moran I tái tính từ NTL đã xuất | Sai khác tuyệt đối tối đa 0,00016805 |
| Benjamini–Hochberg ở α = 0,05, tính lại từ `lisa_p_sim` xuất | Khớp tuyệt đối, 2.880 ô |
| HH / LL từ BH trên p-value xuất | 370 / 2.510 ô |

Sai khác Local I không được diễn giải như sai số thuật toán: cột `ntl_mean` và `lisa_I` trong CSV đã được làm tròn, còn thuật toán gốc có dữ liệu trước khi làm tròn.

#### Conditional permutation độc lập

- Mô hình: giữ focal cố định, lấy các phần tử khác **không hoàn lại** trong mỗi lần hoán vị, độ trễ không gian chuẩn hóa theo số láng giềng, Local Moran theo chuẩn ESDA. **999 permutations**, seed độc lập **20261111**.
- Quy tắc pseudo p-value: hai phía, lấy hai lần đuôi nhỏ hơn, cộng một, tie tolerance 1e-12; sau đó BH ở α = 0,05.
- Tương quan giữa p-value tái mô phỏng và CSV của app: **0,996736**.
- Mean absolute difference của p: **0,015636**; P95 absolute difference: **0,058**.
- Số ô BH significant: **2.879** (độc lập) so với **2.880** (app); **179 ô** khác quyết định BH theo seed này.

| Cụm | App | Độc lập | Giao | Hợp | Jaccard |
|---|---:|---:|---:|---:|---:|
| High–High | 370 | 375 | 360 | 385 | 0,9351 |
| Low–Low | 2.510 | 2.504 | 2.430 | 2.584 | 0,9404 |

Không nên coi 179 ô đổi quyết định là 179 lỗi: pseudop có sai số Monte Carlo, đặc biệt quanh ngưỡng FDR; dữ liệu NTL xuất ra cũng đã bị làm tròn. Để quy kết sai lệch, cần thêm các thử nghiệm thay seed và tăng số hoán vị. Những test deterministic đã tái lập đúng cấu trúc quan sát được.

#### Giới hạn còn lại

1. Không có raster VIIRS gốc, vì thế **chưa** kiểm tra độc lập giá trị zonal/`exactextract` ở từng ô hoặc số tháng quan sát `cf_cvg`.
2. Không có bảng GHSL per-cell, vì thế **chưa** tính lại Spearman/AUC/bootstrap từ đầu; hình chụp màn hình là kết quả **trong app**.
3. Đây là phép triển khai lại phép tính từ CSV; **không phải** benchmark phần mềm ESDA trên toàn 8.333 ô trong phiên hiện tại.
4. Bản export không mang theo đầy đủ hyperparameters hay `lisa_method_version`; cấu hình được suy ra từ source code, p-value và kết quả xuất. Nên xuất thêm metadata vùng/cấu hình để audit được toàn bộ.

#### File tái lập

- `validate_yanqing_lisa.py`: code độc lập, cần NumPy/Pandas, chạy cùng thư mục với CSV nguồn.
- `yanqing_lisa_independent_cell_comparison.csv`: so sánh từng `grid_id`.
- `yanqing_lisa_independent_summary.json`: thống kê máy đọc được.
- `validation_run_log.txt`: log chạy.

**Đánh giá:** Tầng statistical validation vượt qua các kiểm tra định lượng đầu tiên, với giới hạn Monte Carlo được nhận diện rõ. Tầng raster-extraction và external proxy vẫn cần dữ liệu cấp pixel hoặc GHSL per-cell độc lập.


<a id="r4"></a>

## Initial 2020 VIIRS reference (intermediate)

**Original source:** `yanqing_viirs_validation_report.md`. **Status:** historical / superseded where later checks completed.

> [!CAUTION]
> **Historical/intermediate verification.** This record is retained in full for auditability, but its scope limits or partial findings were superseded by the later final validation chapters. Read the final chapter and the current status table for the authoritative result.

### Independent VIIRS extraction validation — Yanqing, Beijing (2020)

**Date:** 2026-11-11  
**Target application:** `hoanfg/spatial-app`, post-merge commit `9574cf872c52d266aa15c363df7965cce31601f0`  
**Input files:** `dien_khanh_NTL_2020_500m.csv`, `yanqing_viirs_2020_reference.tif`, `yanqing_valid_months_2020.tif`.

#### Verdict

**PASS for the 7,703 fully uncut 500-m UTM cells**, when compared with an independently exported Earth Engine VIIRS annual raster and an independent, fractional-coverage polygon-weighted raster calculation. All 7,703 agree with the four-decimal application CSV within its 0.00005 rounding bound. This verifies the output's cell-level extraction/aggregation for these cases, not the entire scientific validity of the satellite product.

**PARTIAL for all 8,333 cells.** The remaining 630 cells have some boundary clipping (600 are flagged `is_border_cell=1`; 30 more are flagged 0 but are slightly smaller than 0.25 km²). Boundary-clipped polygons cannot be reconstructed exactly from CSV centroid and area alone; no exact independent test was performed for these 630 cells. The 30 nearly uncut cells were approximated as uncut UTM squares for a diagnostic only.

#### Earth Engine outputs

- `yanqing_viirs_2020_reference.tif`: EPSG:4326, float32, 217 columns × 142 rows (30,814 pixels); 0.00416665578233° pixel step; 115.69969776–116.60386207° longitude, 40.22906158–40.82072670° latitude.
- Valid annual raster values: minimum 0.225, maximum 59.445, mean 1.0597132 nW/cm²/sr over the **exported bounding rectangle**, not the district polygon. All 30,814 exported pixels are unmasked and positive.
- `yanqing_valid_months_2020.tif`: same grid, uint8, **all 30,814 values equal 12**. The Earth Engine Console reported 12 monthly images. This validates the month-count *indicator* generated by the supplied script for the exported rectangle; it is not a count of individual cloud-free satellite observations. Upstream `.unmask(0)` can obscure earlier missing-data distinctions.

#### Reference computation

- Original `spatial-app` run used GADM Yanqing and UTM EPSG:32650, analytic cells of 500 × 500 meters, VIIRS monthly `VCMSLCFG`, `avg_rad` masked by monthly `cf_cvg > 0`, annual median then zero unmask. This is the reference **method** for building the Earth Engine export, but the exported GeoTIFF was generated by a separate Earth Engine Code Editor script.
- A separate Python script (`validate_viirs_yanqing.py`) recreated each **full, uncut** 500 m UTM polygon from its exported UTM centroid, projected the polygon into raster CRS, intersected it with the GeoTIFF pixel footprints, and calculated a polygon-overlap-area-weighted average. The independent implementation does not import `ntl.zonal` or `exactextract`.
- The CSV stores `ntl_mean` with four decimal places; a true match to full precision should therefore be within approximately 0.00005 per cell, not precisely 0.

##### Fully uncut cells (area = 0.25 km² at exported precision)

| Metric | Result |
|---|---:|
| Exact 0.25 km² square cells compared | **7,703** |
| Pearson correlation (all 7,733 diagnostic non-border cells) | **0.9999999992** |
| Mean absolute error, 7,703 full cells | **0.0000252502** nW/cm²/sr |
| Maximum absolute error, 7,703 full cells | **0.0000499933** nW/cm²/sr |
| Cells exceeding 0.00005 absolute difference | **0 / 7,703** |

##### Diagnostic including 30 almost-full clipped cells

The `is_border_cell=0` group contains 7,733 cells, **30** of which have area slightly below 0.25 km². Their reference was approximated as a full 500 m square for the diagnostic only.

| Metric | Result |
|---|---:|
| Cells in diagnostic | 7,733 |
| Mean absolute error | 0.0000271554 |
| Median absolute error | 0.0000255623 |
| 95th percentile absolute error | 0.0000475461 |
| Maximum absolute error | 0.0133583 |
| Largest discrepancy grid_id | **1682** (area **0.247942 km²**, not a full square) |

For comparison, a **center-pixel sample** instead of a fractional-coverage mean produced Pearson r ≈ 0.98789 and mean absolute error ≈ 0.15008. This illustrates why the correct pixel-overlap calculation matters.

#### Limitations and next action

1. **630 partly clipped boundary cells** remain unverified to rounding precision. For an all-cell benchmark, obtain the exact Yanqing source polygon used by the app and repeat this independent calculation on the clipped polygons, using matching geometry-cleaning and grid-building conventions. The 600 `is_border_cell=1` cells are excluded from current polygon-mean reconstruction; 30 slightly clipped but unflagged cells were evaluated approximately.
2. Although the independent export agrees numerically on complete cells, this does **not** independently adjudicate whether annual median and upstream `unmask(0)` are appropriate scientific measurement choices; those are sensitivity analyses.
3. All 12 months are valid in the provided *exported monthly indicator*. This is not proof that there are no missing individual satellite observations, and not a test for other years.
4. `Export.image.toDrive` may have different raster alignment from app's `getDownloadURL`; near-perfect agreement here suggests matching effective pixel footprint values over this region. A pixel-by-pixel comparison would require the original app GeoTIFF.
5. No live authenticated application session, GEE API call, or Streamlit Cloud RAM measurement was performed in this local comparison. The Earth Engine exports were supplied by the user.

**Conclusion:** The **VIIRS annual zonal extraction pipeline is independently corroborated with extremely high precision on the 7,703 fully uncut cells** in the Yanqing 2020 dataset. The next optional step is clipping the remaining 630 cells against the exact curated GADM polygon, rather than repeating broad benchmarks or raising Streamlit RAM caps.


<a id="r5"></a>

## Final 2020 VIIRS polygon benchmark — all cells

**Original source:** `yanqing_viirs_all_cells_validation_report.md`. **Status:** retained technical record.

> [!NOTE]
> **Full validation record** — embedded from the source report below; any cross-reference to a separate ZIP is an evidence inventory item, not a GitHub-tracked artifact.

### Xác thực độc lập VIIRS — Diên Khánh (Yanqing), Bắc Kinh, năm 2020

**Ngày:** 11/11/2026  
**Commit spatial-app:** [`9574cf872c52d266aa15c363df7965cce31601f0`](https://github.com/hoanfg/spatial-app/commit/9574cf872c52d266aa15c363df7965cce31601f0)  
**Địa bàn GADM 4.1:** `CHN.2.1.11_1`, EPSG:32650, lưới phân tích 500 m  
**Nguồn ảnh:** người dùng xuất hai GeoTIFF từ Google Earth Engine bằng một script độc lập khỏi ứng dụng.

#### Kết luận

**PASS cho toàn bộ 8.333/8.333 ô**: trung bình ảnh VIIRS tính độc lập theo tỷ lệ diện tích giao polygon–pixel trùng với `ntl_mean` của webapp khi làm tròn đến bốn chữ số thập phân. Tất cả sai khác tuyệt đối đều ≤ 0,00005 nW/cm²/sr; **không còn ô biên ngoại lệ**. Kết quả khẳng định việc tổng hợp raster thành các ô lưới 500 m của mẫu Yanqing 2020 được tái lập độc lập trong phạm vi độ chính xác của file CSV xuất ra.

| Đại lượng | Kết quả |
|---|---:|
| Tổng ô | **8.333** |
| Ô nguyên 0,25 km² | **7.703** |
| Ô cắt nhẹ nhưng không đánh dấu biên | **30** |
| Ô được gắn nhãn biên | **600** |
| Khớp 4 chữ số thập phân | **8,333/8.333** |
| MAE | **0.0000250230** nW/cm²/sr |
| Median absolute error | **0.0000253275** nW/cm²/sr |
| 95th percentile absolute error | **0.0000473949** nW/cm²/sr |
| Max absolute error | **0.0000499933** nW/cm²/sr |
| Pearson r | **0.999999999971** |
| Tổng diện tích CSV | **2003.508895** km² |
| Tổng diện tích polygon tái dựng | **2003.508912** km² |

#### Phương pháp

1. Sử dụng GeoJSON Yanqing tại commit đã kiểm định và khôi phục đầy đủ tọa độ nguồn. GeoJSON, giá trị nguồn và SHA-256 của các input có trong bộ bằng chứng. Mã GID `CHN.2.1.11_1` được giữ nguyên.
2. Chiếu ranh giới sang UTM EPSG:32650; tạo các ô vuông 500 × 500 m bắt đầu tại tọa độ bội số của 500, nới một ô; cắt từng ô bằng ranh giới. Kiểm tra được **đúng 8.333 đa giác** theo cùng thứ tự `grid_id` và diện tích/tâm tọa độ trùng với các giá trị được làm tròn trong CSV.
3. Chiếu mỗi **đa giác đã cắt** về CRS raster EPSG:4326. Với mỗi pixel, tính diện tích giao nhau giữa polygon và pixel theo hệ tọa độ raster, nhân với `avg_rad` rồi chia tổng diện tích giao nhau. Script tính độc lập không import `ntl.zonal` hoặc `exactextract`.
4. So sánh kết quả reference với `ntl_mean` của CSV theo từng `grid_id` — cả 630 ô bị cắt (600 biên + 30 cắt nhẹ), không chỉ ô nguyên vẹn. File `yanqing_viirs_all_8333_polygon_comparison.csv` chứa các phép đối chiếu và sai số.

#### Kiểm tra theo nhóm

| Nhóm ô | Số ô | MAE | Sai số lớn nhất | Khớp 4 chữ số |
|---|---:|---:|---:|---:|
| `full` | 7,703 | 0.000025250 | 0.000049993 | 7,703/7,703 |
| `minor_clipped` | 30 | 0.000027901 | 0.000046435 | 30/30 |
| `edge_masked` | 600 | 0.000021962 | 0.000049888 | 600/600 |

##### Giá trị tổng hợp vùng

- Trung bình có trọng số diện tích từ app: **1.445496506 nW/cm²/sr**.
- Trung bình có trọng số diện tích từ reference: **1.445496216 nW/cm²/sr**.
- Tổng `NTL × km²` từ app: **2896.065108050**; từ reference: **2896.064526359**. Đây chỉ là tổng quy ước trên lưới, không phải GDP.

##### Số tháng quan sát

Earth Engine Console báo 12 ảnh tháng. Raster `yanqing_valid_months_2020.tif` chứa **30.814/30.814 pixel bằng 12** trong bounding rectangle được xuất. Đây là số tháng có chỉ thị `cf_cvg > 0` theo script cung cấp, không phải số quan sát vệ tinh riêng lẻ hoặc bằng chứng rằng không có sai số cảm biến.

#### Vì sao phép đối chiếu lần trước còn một ô khác biệt?

Khi dùng ranh giới được lượng tử hóa còn 7 chữ số thập phân, `grid_id 349` có sai số ~0,0000643. Sau khi tái dựng với phần thập phân nguồn đầy đủ, sai số ô này giảm xuống mức làm tròn CSV. Điều này chỉ ra độ nhạy của **ô bị cắt** với độ chính xác hình học; không phải bằng chứng có lỗi trong phép trích xuất NTL của ứng dụng.

#### Giới hạn khoa học còn lại

- **Đây là validation việc tái lập giá trị NTL theo cùng nguồn và cùng quy tắc**, không phải validation rằng NTL luôn đo đúng GDP, hoạt động kinh tế hoặc nhà bỏ trống.
- Raster tham chiếu được xuất bằng `Export.image.toDrive`, không phải chính byte raster của `getDownloadURL` trong app. Hai phương thức có thể có khác biệt về căn chỉnh lưới; với bộ dữ liệu này kết quả zonal mean khớp đến mức làm tròn.
- `annual median`, `cf_cvg > 0`, `unmask(0)` và clipping âm là những lựa chọn xử lý cần đánh giá thêm nếu muốn kết luận về bias đo lường. Ảnh tháng hợp lệ 12/12 tại ROI này không chứng minh điều tương tự ở khu vực/năm khác.
- Chưa benchmark RAM toàn diện của Streamlit Cloud; chưa kiểm tra vùng khác, năm khác, hoặc đối chiếu độ chính xác sản phẩm VIIRS với quan sát mặt đất.
- Từ số CSV chỉ lưu bốn chữ số thập phân, phép kiểm tra không thể chứng minh khớp chính xác ở độ chính xác toàn phần của số thực chưa làm tròn.

#### Bằng chứng và tái lập

- `yanqing_viirs_all_8333_polygon_comparison.csv`: đối chiếu từng ô và sai số.
- `yanqing_viirs_all_cells_metrics.json`: số liệu + SHA-256 dữ liệu đầu vào.
- `validate_yanqing_all_cells.py`: mã Python tính độc lập theo polygon overlap.
- `yanqing_gadm41_source.geojson`: ranh giới nguồn lưu lại với tọa độ chính xác.
- `yanqing_grid_reconstructed.geojson`: toàn bộ 8.333 polygon đã cắt trong hệ tọa độ địa lý.
- Hai raster VIIRS/month count và CSV gốc (nếu cần tái lập) được lưu trong ZIP bằng chứng.

**Kết luận cuối:** Đạt kiểm chứng cấp ô và vùng cho **toàn bộ 8.333 ô** thuộc Diên Khánh 2020. Phần kiểm chứng tiếp theo nên chuyển sang đánh giá **measurement sensitivity** và **external validity** thay vì mở thêm một vòng kiểm thử cùng công thức.


<a id="r6"></a>

## 2014 VIIRS raster benchmark and coverage

**Original source:** `yanqing_2014_temporal_raster_validation_report.md`. **Status:** retained technical record.

> [!NOTE]
> **Full validation record** — embedded from the source report below; any cross-reference to a separate ZIP is an evidence inventory item, not a GitHub-tracked artifact.

### Independent VIIRS 2014 & Temporal Input Validation — Yanqing, Beijing

**Date:** 2026-11-11  
**Reference app commit:** `9574cf872c52d266aa15c363df7965cce31601f0`  
**Region:** GADM v4.1 `CHN.2.1.11_1` (Yanqing), 500 m analysis grid, EPSG:32650.

#### Result: PASS for 2014 VIIRS extraction

An independent Google Earth Engine 2014 annual-median GeoTIFF was combined with the **8,333 original clipped polygons**, recovered from the independently audited 2020 validation evidence. Area-weighted pixel–polygon overlap was calculated without importing spatial-app's `exactextract` implementation. To match the app, each finite negative radiance pixel was clipped to zero **before** zonal averaging.

| Measurement | Result |
|---|---:|
| Number of cells | 8,333 |
| Matches within CSV's 4-decimal precision (absolute difference ≤ 0.00005) | **8,333 / 8,333** |
| Mean absolute difference | **0.0000250540** nW/cm²/sr |
| 95th-percentile absolute difference | **0.0000476443** nW/cm²/sr |
| Largest absolute difference | **0.0000499896** nW/cm²/sr |
| Pearson correlation | **0.999999999785** |
| Full 500 m squares | 7,703 / 7,703 passed |
| Slightly clipped cells | 30 / 30 passed |
| Edge-masked cells | 600 / 600 passed |

##### Raster / coverage audit

The 2014 annual-median zero-filled reference, NoData-preserving median and month-coverage GeoTIFF all have **217 × 142 = 30,814 pixels**, CRS **EPSG:4326**, and the same affine transform as the independently exported 2020 reference raster. Their spatial extent and pixel grid match exactly.

- `yanqing_valid_months_2014.tif`: **all 30,814 pixels have value 12** (the count of monthly images with `cf_cvg > 0`), with no masked pixels. This is not equivalent to 12 individual clear-sky satellite observations.
- `yanqing_viirs_2014_masked_median.tif`: **no masked/NoData pixels**, `nodata=-9999` recorded in metadata. Every pixel value equals the zero-filled median file, so `unmask(0)` does not influence this particular output.
- The reference median has **one pixel of negative radiance**, minimum **−0.010230635 nW/cm²/sr**. As spatial-app clips finite negatives to zero before computing grid means, independent reproduction must do likewise. That single pixel affects two grid cells, `grid_id=7442` and `7443`. Raw un-clipped zonal means are **0.016861** and **0.038360**; clipped means **0.022089** and **0.039794**, matching webapp exports `0.0221` and `0.0398` to four decimals. This confirms the clipping rule has a measurable, localized effect in 2014, though not large at district scale.

##### Temporal comparison (2014 → 2020)

For the same 8,333 grid cells, comparing independently extracted **2014 annual-median means** with the app's validated **2020 grid means**:

| Metric | 2014 | 2020 |
|---|---:|---:|
| Unweighted mean cell NTL (nW/cm²/sr) | **0.445159** | **1.413719** |

- Mean change: **+0.968560** nW/cm²/sr; 2020 mean was roughly **3.176 times** 2014 (about **+217.6%**).
- **8,221 cells increased** in absolute NTL, **112 cells decreased**; none are tied using extracted 2014 values and four-decimal 2020 values.
- The app assigns **4,711** cells to `4_Synchronized_Decline`, but among these **4,624 increased** in absolute NTL and **87 decreased**.

**Interpretation:** `Synchronized_Decline` in `run_spacetime_lisa` is defined when the year-standardized `log1p(NTL)` z-score **and** neighboring z-score both fall (`delta_z < 0`, `delta_lag_z < 0`), conditional on movement magnitude ≥0.05. It measures **declining relative standing**, not a drop in absolute radiance or evidence of economic contraction. The four regimes are directional classifications, **not independently statistically significant Local Moran tests**. A clearer display label is `Synchronized Relative Decline` with an explicit explanatory note.

##### Scope and limitations

This test establishes **computational reproduction** of 2014 VIIRS extraction and, together with prior 2020 audit, validates both temporal endpoint inputs at exported CSV precision. It does **not** establish sensor calibration accuracy, causal economic interpretation, a continuous 2014–2020 annual trend, or the appropriateness of using nighttime lights as a GDP proxy.

- GeoTIFFs were exported through Google Earth Engine's `Export.image.toDrive`, whereas the app uses `getDownloadURL`. The two outputs here share the same spatial grid and reproduce output means, but this does not prove all raster exports always align identically.
- The 2020 data in the basic temporal counts come from the app's 2020 column, previously verified against the separate 2020 reference raster (8,333/8,333).
- Source-cell CSV stores four decimal places. Equality can only be established **within its rounding precision**, not to full unrounded pixel or geometry precision.
- Because all 2014/2020 pixel locations are covered by twelve monthly composites in this export, missing-data robustness here is uninformative for less-observed locations/years.
- The year-by-year magnitude of NTL increase should not automatically be attributed to economic growth: satellite calibration, processing, background removal, measurement choices and local circumstances can contribute.

#### Artifacts

- `yanqing_2014_viirs_cell_validation.csv`: original and independently calculated 2014 NTL cell means and absolute errors for all cells.
- `validate_viirs_2014.py`: polygon–pixel overlap code, from source GeoTIFF to per-cell output.
- `yanqing_2014_validation_execution.log`: execution output and detailed comparisons.
- The 2014 source rasters, temporal input CSV and 8,333-cell reconstructed GeoJSON are included in the evidence archive.


<a id="r7"></a>

## Measurement sensitivity — mean/median and NoData

**Original source:** `yanqing_2020_measurement_sensitivity_report.md`. **Status:** retained technical record.

> [!NOTE]
> **Full validation record** — embedded from the source report below; any cross-reference to a separate ZIP is an evidence inventory item, not a GitHub-tracked artifact.

### Measurement sensitivity validation — Yanqing, Beijing (2020, 500 m)

**Ngày:** 11/11/2026. **Đối tượng:** 8.333 ô lưới của Diên Khánh (Yanqing), `CHN.2.1.11_1`, 2020. **Mã ứng dụng được đối chiếu:** commit `9574cf872c52d266aa15c363df7965cce31601f0` sau PR #10.

#### Kết luận chính

**Đạt kiểm chứng tính nhất quán về dữ liệu và độ nhạy đo lường trong pilot này:**
- `masked median` và `zero-filled median` giống nhau **tuyệt đối** tại cả 30.814 pixel của raster đã tải; masked median có **0 pixel NoData**. Do đó, không có thay đổi NTL/Gini/Moran/LISA khi giữ mask cho mẫu này.
- Đổi `annual median` thành `annual mean` làm tăng NTL trung bình không trọng số **4.366%**, từ **1.4137188** lên **1.4754449 nW/cm²/sr**. Gini NTL tăng từ **0.6809244** lên **0.6861015**.
- Binary-Queen Global Moran's I trên toàn bộ ô từ **0.914128499** lên **0.914558970**. Đây là Moran tính độc lập trong script trên toàn bộ mẫu, không nhất thiết bằng một chỉ số khác của LISA panel.
- Giữ nguyên quy trình LISA (999 conditional permutations **không hoàn lại**, seed 42, hai đuôi, tie tol 1e−12, BH-FDR alpha 0.05): HH từ **370** lên **385**, LL từ **2510** xuống **2499**. Jaccard HH **0.96104**, LL **0.96201**.
- Baseline median tái lập **100% nhãn LISA** từ CSV ứng dụng, cùng số HH và LL, giúp phân biệt ảnh hưởng tổng hợp ảnh tháng khỏi khác biệt giả lập.

#### Input và kiểm tra GeoTIFF

| Raster | Kích thước | Pixel NoData | Min–max trong ROI | Bản chất |
|---|---:|---:|---:|---|
| Baseline median+zero | 217×142 | 0 | 0.225–59.445 | `yanqing_viirs_2020_reference.tif` |
| Annual mean+zero | 217×142 | 0 | 0.236–57.370 | `yanqing_viirs_2020_annual_mean.tif` |
| Median giữ NoData | 217×142 | 0 | 0.225–59.445 | `yanqing_viirs_2020_masked_median.tif` |

- Ba ảnh có cùng hệ tọa độ EPSG:4326, affine transform và kích thước. `masked median` có metadata `nodata=-9999`, nhưng không chứa pixel mask thực tế trong phạm vi xuất.
- File đếm tháng quan sát `yanqing_valid_months_2020.tif` đã được kiểm tra trước đây: các pixel xuất ra đều có 12 tháng hợp lệ; điều này nhất quán với kết quả không có pixel missing trong median của mẫu này.
- Ranh giới GADM và lưới 500 m đã được dựng lại từ dữ liệu kiểm định trước; **trung bình mỗi ô được tính bằng diện tích giao nhau của polygon và pixel**, không dùng lấy mẫu tại tâm ô, không import `ntl.zonal` hoặc `exactextract`.

#### Các chỉ tiêu so sánh

| Chỉ tiêu | Median baseline | Annual mean | Masked median |
|---|---:|---:|---:|
| NTL trung bình không trọng số | 1.4137188 | 1.4754449 | 1.4137188 |
| NTL trung bình có trọng số diện tích | 1.4454962 | 1.5091569 | 1.4454962 |
| Gini toàn bộ 8.333 ô | 0.6809244 | 0.6861015 | 0.6809244 |
| Gini 7.733 ô không biên | 0.6861742 | 0.6910807 | 0.6861742 |
| Global Moran binary Queen, toàn vùng | 0.914128499 | 0.914558970 | 0.914128499 |
| Global Moran binary Queen, không biên | 0.914175690 | 0.914704806 | 0.914175690 |
| Dark share (đúng 0 trong polygon mean) | 0% | 0% | 0% |
| HH cells | 370 | 385 | 370 |
| LL cells | 2510 | 2499 | 2510 |
| HH area share | 4.61690% | 4.80407% | 4.61690% |

**Annual mean – median (mỗi ô):** MAE 0.0771845, median AE 0.0103399, P95 AE 0.3205303, max AE 6.0436231 nW/cm²/sr, Pearson r 0.9972279, Spearman rho 0.9941553.

**Kiểm định LISA:** Queen neighbors trên tập ô không biên (area>=0.99×0.25 km²), standardized z trên cùng active set, 999 permutations conditional without replacement, 2-sided +1 Monte Carlo p với ties, Benjamini–Hochberg alpha 0.05. Mô phỏng **paired** dùng chính xác cùng các bộ chỉ số láng giềng rút ngẫu nhiên cho median và mean. Baseline mô phỏng khớp 100% nhãn của file xuất ứng dụng.

#### Giới hạn cần nêu khi viết bài

1. Không có pixel thiếu trong Yanqing 2020, do đó **không thể đánh giá mức độ sai lệch do `unmask(0)` trong một trường hợp thực sự có missing**. Muốn kiểm định giả định này cần địa bàn/năm có missing hoặc một thí nghiệm mask có kiểm soát (khi đó chỉ đo độ nhạy trên dữ liệu giả lập).
2. Annual mean là **trung bình không trọng số của 12 ảnh tổng hợp tháng**, không phải annual mean theo số quan sát `cf_cvg`. Không thể gọi đây là lựa chọn đo lường luôn tốt hơn/trung vị luôn tốt hơn.
3. Các kết quả LISA có p-value phụ thuộc phương pháp permutation, seed, và BH. Ở đây cùng seed/draws giúp cô lập thay đổi phương pháp tổng hợp ảnh, không phải chứng minh ý nghĩa kinh tế của hotspot.
4. Bằng chứng chỉ bao phủ **một vùng, một năm, cùng sản phẩm VIIRS**; chưa xác thực tính ổn định theo thời gian hoặc tính khái quát sang vùng khác.
5. Phân tích này không kiểm tra lại tương quan GHSL vì chưa có file dữ liệu GHSL cấp ô; không suy diễn về GDP, giá nhà hay nhà trống.
6. Kết quả không đòi hỏi tăng RAM của Streamlit và **không sửa repository**.

#### Tái lập

- `run_yanqing_measurement_sensitivity.py`: mã phân tích độc lập.
- `yanqing_2020_measurement_sensitivity_cells.csv`: dữ liệu từng ô, gồm NTL ba cách tính, Local I, p-value, nhãn cụm, sai khác mean−median.
- `yanqing_2020_measurement_sensitivity_metrics.json`: metric/mask info và SHA-256 đầu vào.
- Ranh giới GADM, polygon ô lưới, CSV gốc và cả ba GeoTIFF trong ZIP bằng chứng.


<a id="r8"></a>

## Transformation sensitivity — raw/P99/log

**Original source:** `yanqing_2020_transformation_sensitivity_report.md`. **Status:** retained technical record.

> [!NOTE]
> **Full validation record** — embedded from the source report below; any cross-reference to a separate ZIP is an evidence inventory item, not a GitHub-tracked artifact.

### Independent Transformation Sensitivity Validation — Yanqing, Beijing (2020)

**Date:** 11 November 2026  
**Baseline:** `hoanfg/spatial-app`, post-PR #10 method (`conditional-wor-esda-v2`).  
**Input:** 8,333 Yanqing 500 m cells. Full-precision `ntl_baseline_ref` comes from independently re-extracted VIIRS raster in the previous validation; `ntl_mean` in original app CSV is rounded to four decimals.

#### Purpose and methods

This test isolates *how NTL transformation changes LISA inference*, not whether a satellite measurement is correct. The same 8,333 cells, 7,733 non-edge cells, snapped UTM Queen-neighborhood indices, 999 conditional permutations **without replacement** (seed 42), inclusive two-sided pseudo-p with `(min(ge,le)+1)*2/1000`, and BH-FDR at alpha=0.05 were used for all three versions. The transformations mirror `ntl/lisa_diagnostics.py` and `ntl/lisa_core.py`:

- **Raw:** positive annual-median radiance as measured.
- **P99:** `min(NTL, quantile(NTL[NTL>0], .99))`; positive-N​TL cap **21.996610** nW/cm²/sr (84 cells capped). The resulting radiance is re-standardized.
- **Log:** `ln(NTL)`, *not* `log1p(NTL)`, and then re-standardized over the same active sample. All 8,333 Yanqing NTL values are strictly positive in this dataset.

The independent implementation reconstructs Queen neighbors from snapped exported UTM centroids, uses ESDA-scaled Local I, and the same replacement-free conditional null with synchronized random permutation draws for all methods. **Raw reproduces all 8,333 app LISA class labels and every exported p-value exactly.** Its computed Local I differs from the rounded exported version by no more than 0.000050.

#### Results

| Metric | Raw | P99 winsorization | Log NTL |
|---|---:|---:|---:|
| High–High cells | 370 | 457 | 1,050 |
| Low–Low cells | 2,510 | 2,510 | 2,441 |
| All significant cells after FDR | 2,880 | 2,967 | 3,491 |
| HH area share | 4.617% | 5.702% | 13.102% |
| HH raw quadrants before significance | 1,072 | 1,135 | 2,517 |
| NTL mean (raw units where applicable) | 1.413719 | 1.331317 | — |
| Standardized input skewness | 6.312 | 4.905 | 1.928 |
| Excess kurtosis | 48.127 | 25.754 | 3.659 |

##### High–High overlap

| Comparison | Intersection | Union | Jaccard | First-only | Second-only |
|---|---:|---:|---:|---:|---:|
| Raw vs P99 | 370 | 457 | 0.809628 | 0 | 87 |
| Raw vs log | 370 | 1,050 | 0.352381 | 0 | 680 |
| P99 vs log | 457 | 1,050 | 0.435238 | 0 | 593 |

**Crucial interpretation:** All 370 raw HH cells persist under P99 and log. A low raw-log Jaccard is due to the **expansion** of log-HH (+680), not displacement of the 370 brightest-core hotspots. The new 680 log HH cells were all `Not Significant` under raw; the additional P99 HH cells were similarly all raw `Not Significant`.

Among the 680 newly identified log-HH cells, raw radiance has median **2.731** nW/cm²/sr (range 1.096–10.894), versus median **13.259** for the original 370 raw HH cells. These newly identified cells are therefore typically moderately bright, not the brightest radiance outliers.

##### Why log makes the difference

Raw NTL is strongly right-skewed (**skewness 6.31**, excess kurtosis 48.13). Extremely bright cells strongly influence the *raw-scale* mean and standard deviation. Under log transformation, the relative influence of extremes falls. In this dataset, the mean raw radiance on the active analysis sample is **1.474**, whereas exponentiating the mean logged radiance gives a geometric center of **0.624**. Both the standardized signs (quadrants) and the Monte Carlo significance pattern can change after that transformation. The proportion of focal-cell quadrant assignments that differs between raw and log is **20.38%**. Raw has 1,072 candidate HH quadrants; log has 2,517. Because a transformation changes the reference distribution and autocorrelation scores, a lower threshold alone is **not** a complete explanation.

Raw-to-P99 changes far less: candidate HH quadrants rise from 1,072 to 1,135, while P99-capping reduces skewness from 6.31 to 4.90. P99 caps 84 exceptionally bright cells at 21.9966, reducing their leverage. Under the tested settings, the LL significance count is unaffected by P99 but changes under log.

A few statistical decisions also move outside HH: 83 raw-LL cells become nonsignificant under log, and 14 previously nonsignificant cells become LL. These are legitimate sensitivity findings rather than, by themselves, code failures.

#### Validation status and limits

- **Passed:** raw reproduction of app classes and p-values; identical Queen-neighbor degrees; reproducible, paired raw/P99/log Monte Carlo comparison under documented rules.
- **Sensitivity confirmed:** log is a materially different *estimand/analysis scale*: HH footprint rises from 4.617% to 13.102%; neither is automatically the scientifically correct representation.
- **Not concluded:** which scale best predicts economic activity, building occupancy, GDP or growth; whether hotspot thresholds are optimal; generalization to other cities or years; sensitivity to alternate weight specifications and grid scales. GHSL concordance shown in prior app screenshots applies to the original configuration; recalculation for transformed NTL requires matching GHSL cell-level data.

#### Research recommendation

Pre-specify **raw annual-median VIIRS radiance as the primary physical-light measurement**, with P99 and log as explicit robustness alternatives. If the substantive question concerns **relative differences across dim and moderately lit places**, log can be justified as its own primary specification, but it must not be presented as numerically interchangeable with raw. Report all three HH footprints and their Jaccard overlap, not only labels such as “robust” or “weak.” Do not pool transformed NTL levels or their hotspot flags in one regression without defining the measurement scale.

The VIIRS input is nonnegative in this sample and `ln(NTL)` was feasible; across other cities/years where `NTL=0`, the app's log rule excludes zeros when `include_zeros=False`, requiring consistent treatment and disclosure.

#### Reproducibility

Run `python validate_yanqing_transformations.py` with NumPy, pandas and SciPy from the ZIP evidence package and the three CSV files named in the script (or adjust `P`). Files `yanqing_2020_transformation_sensitivity_metrics.json` and `yanqing_2020_transformation_sensitivity_cells.csv` record the numerical output. SHA-256 source file hashes are included in JSON. No repository changes or Earth Engine downloads were needed in this stage.


<a id="r9"></a>

## Spatial robustness — Queen/Rook, 500/1,000 m

**Original source:** `yanqing_spatial_robustness_validation_report.md`. **Status:** retained technical record.

> [!NOTE]
> **Full validation record** — embedded from the source report below; any cross-reference to a separate ZIP is an evidence inventory item, not a GitHub-tracked artifact.

### Independent Spatial Robustness Validation — Yanqing, Beijing, 2020

**Status:** Completed (four LISA specifications). **Scope:** VIIRS annual median, GADM v4.1 Yanqing, EPSG:32650, 500 m and 1,000 m, Queen vs Rook. **Date:** 2026-11-11.

#### Executive summary

The independent code exactly replicates **8,333/8,333 cell classifications** and the exported simulation p-values for the original **Queen / 500 m** webapp result. Recomputing spatial weights with Rook materially reduces significant High–High (HH) and Low–Low (LL) cells. Doubling the grid size yields a similar fraction of regional land in HH, but only partial geographical agreement between the two spatial resolutions (area-weighted intersection-over-union for Queen HH = 0.6547). There is **no evidence of a software calculation error** from these tests. There is meaningful **model specification sensitivity**.

#### Reproducible data and method

- Source: user-provided `yanqing_viirs_2020_reference.tif`, independently validated against the app's 500 m NTL extraction in the previous stage; same GADM boundary file and CSV as the previous stages.
- 500 m: original 8,333 GADM-clipped grid polygons, NTL values computed from the reference GeoTIFF, without CSV rounding.
- 1,000 m: **new grid snapped to 1,000 m UTM coordinates** following the app's `build_grid` logic; clip to the same GADM geometry; area-weighted polygon/raster intersection to extract NTL independently. There are 2,162 grid polygons and the region areas agree within 0.00002 km².
- LISA: NTL raw, reference standardization on non-edge cells (sample SD, ddof=1); exclude polygons with area < 99% of nominal cell area. Queen has up to 8 adjacent cells (including corners); Rook up to 4 edge-sharing cells. Excluded cells cannot be neighbors. Conditional permutation *without replacement* (999 permutations, seed 42); two-sided p = min(1, 2(min(ge,le)+1)/1000), with inclusive ties, BH FDR at α=0.05 over tested cells. This matches the app's post-PR#10 implementation.
- Difference between resolutions assessed with polygon-set geometry: spatial Jaccard = intersection area / union area; it is not meaningful to compare raw cell counts across different grid sizes.
- No Streamlit execution or app modification required.

#### LISA results

| Specification | Grid polygons | Tested cells | Edge-masked | HH count | LL count | HH area (km²) | HH share (%) | LL area (km²) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Queen 500 m | 8,333 | 7,733 | 600 | 370 | 2,510 | 92.50 | 4.6169 | 627.50 |
| Rook 500 m | 8,333 | 7,733 | 600 | 187 | 906 | 46.75 | 2.3334 | 226.50 |
| Queen 1,000 m | 2,162 | 1,865 | 297 | 92 | 562 | 92.00 | 4.5919 | 561.98 |
| Rook 1,000 m | 2,162 | 1,865 | 297 | 46 | 210 | 46.00 | 2.2960 | 209.99 |

All four analyses found zero FDR-significant High–Low and Low–High cells. The denominator of HH area share is total clipped Yanqing area (~2,003.51 km²), including edge cells. Edge masking changes the eligible analysis area and needs to be kept explicit in any paper.

#### Queen versus Rook, at fixed resolution

| Comparison | HH cell intersection | HH cell Jaccard | LL cell intersection | LL cell Jaccard |
|---|---:|---:|---:|---:|
| 500 m Queen versus Rook | 187 | 0.5054 | 906 | 0.3610 |
| 1,000 m Queen versus Rook | 46 | 0.5000 | 210 | 0.3737 |

The Rook significant HH and LL sets are subsets of the corresponding Queen sets in both tested scales. Their smaller size may reflect fewer neighbors, different spatial lag, permutation null distribution and changes in FDR significance; the tests do not identify a single causal reason without further decomposition. Rook is not automatically more correct or more conservative in all geographies.

#### Changing resolution at fixed weights — geographical footprint overlap

| Comparison | 500 m HH area (km²) | 1,000 m HH area (km²) | Intersection (km²) | Spatial Jaccard | Share of 500 m HH retained |
|---|---:|---:|---:|---:|---:|
| Queen HH | 92.50 | 92.00 | 73.00 | 0.6547 | 78.92% |
| Rook HH | 46.75 | 46.00 | 37.75 | 0.6864 | 80.75% |

Additional spatial Jaccard: Queen LL 0.8371; Rook LL 0.5479.

The broadly consistent aggregate HH area is **not** proof of complete location stability. New 1,000 m grid alignment, changing support, edge-mask share, and scale dependence (modifiable areal unit problem / MAUP) can change both neighbor structure and statistics.

#### Quality checks

- Exact replication of **all 8,333** published labels for Queen 500 m. Maximum absolute difference between recalculated and exported 500 m Queen `p_sim` = **0.00000**.
- Full-source region boundary yields 2,162 1,000 m cells and approximately the same regional area as the existing 500 m grid.
- No missing or nonpositive annual-median NTL values in the extracted 1,000 m polygon means.
- All calculations performed using the same reference GeoTIFF that had previously passed independent 500 m extraction validation.

#### Assessment and research recommendations

1. **Software reproducibility (Queen 500 m): PASS**. Method comparison is not a code defect test; no new defect established.
2. **Weight specification robustness: SENSITIVE**. HH area roughly halves and LL classifications drop sharply with Rook, although Rook-significant areas remain nested within Queen-significant areas.
3. **Spatial resolution robustness: MODERATE**. HH area proportion is stable, but about 21% of the original Queen HH footprint does not overlap the 1,000 m HH footprint, yielding spatial Jaccard 0.655.
4. For research, prespecify one primary weights model (Queen 500 m is the app baseline), disclose Rook and 1,000 m as robustness checks, and avoid presenting the exact hotspot boundaries as scale-invariant.
5. Future checks: consistency across an independent urban geography/year, month-level NTL observation quality in imperfect-data contexts, and the interpretation of space-time LISA regime labels. Bootstrapping the geographical stability, or cross-scale agreement across seed choices, would further separate permutation variability from scale effects.

##### Reproducibility bundle

- `validate_yanqing_spatial_robustness.py`: full independent code, no imports from `spatial-app`.
- `yanqing_spatial_robustness_metrics.json`: all numerical metrics and SHA-256 hashes of key input files.
- `yanqing_spatial_robustness_500m_cells.csv`, `yanqing_spatial_robustness_1000m_cells.csv`: each specification's neighborhood count, p-value and final LISA class.
- `yanqing_spatial_robustness_1000m.geojson`: 1,000 m polygons with NTL and both LISA classes.
- `yanqing_spatial_robustness_execution.log`: execution output.
- Source GADM geometry, baseline VIIRS GeoTIFF, original app-export CSVs and full-precision reference mean CSV are included in the ZIP.

**Limitation:** This is an internal-method benchmark with independent implementation and original VIIRS values, not an external ground-truth validation of NTL as a measure of economic activity; results pertain to Yanqing 2020 only.


<a id="r10"></a>

## Temporal Space-Time and Markov validation

**Original source:** `yanqing_temporal_validation_report.md`. **Status:** retained technical record.

> [!NOTE]
> **Full validation record** — embedded from the source report below; any cross-reference to a separate ZIP is an evidence inventory item, not a GitHub-tracked artifact.

### Temporal Validation — Yanqing (Diên Khánh), Bắc Kinh, 2014 → 2020

**Trạng thái:** PASS về tái lập phép tính Space-Time từ dữ liệu CSV đã xuất, với một sai khác tại ngưỡng do làm tròn; **chưa PASS** về kiểm chứng độc lập raster VIIRS năm 2014, vốn chưa được cung cấp.

**Nguồn:** `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv` (8.333 ô); đối chiếu công thức trong `ntl/lisa_core.py`, repository `hoanfg/spatial-app`, phiên bản sau PR #10 (merge SHA `9574cf872c52d266aa15c363df7965cce31601f0`). Các công thức được lập trình lại bằng Python riêng (`validate_temporal.py`) thay vì gọi trực tiếp hàm ứng dụng. Việc kiểm chứng tính toán trên CSV không đồng nghĩa xác nhận dữ liệu ảnh vệ tinh đầu vào năm 2014.

#### 1. Các phép tính đã tái lập

- **8.333 ô**, trong đó **7.733 ô nội vùng** và **600 ô loại tại biên**.
- `ntl_2020` bằng `ntl_mean` ở cả 8.333 ô.
- `delta_ntl`, `delta_ln_ntl`, `z_2014`, `z_2020`, `delta_z`, `delta_lag_z`, `movement_magnitude` tái lập từ `ntl_2014`, `ntl_2020`, tọa độ và Queen neighbors trong sai số được kỳ vọng từ làm tròn bốn chữ số NTL đầu vào.
- Queen neighbor counts khớp **8.333/8.333** với cột đã xuất.
- Nhãn Space-Time từ **giá trị dịch chuyển và hướng đã làm tròn do app xuất** khớp **8.333/8.333**. Khi tính lại trực tiếp từ NTL có bốn chữ số thập phân, **8.332/8.333** nhãn khớp. Ô `grid_id=3922` có `movement_magnitude` tính lại ≈ **0,049964**, trong khi CSV xuất **0,0500** (ngưỡng 0,05), tạo sai khác một nhãn. Điều này không đủ để kết luận lỗi tính toán trong ứng dụng: đầu vào CSV là giá trị đã làm tròn, còn app sử dụng giá trị chưa làm tròn trước khi xuất.

#### 2. Định nghĩa *Synchronized Decline* thực tế

Ứng dụng sử dụng:

`v_t = ln(1 + max(NTL_t, 0))`; `z_t = (v_t - mean(v_t on core))/(sd(v_t on core, ddof=1))`.

`delta_z = z_2020 - z_2014`; `delta_lag_z = QueenLag(z_2020) - QueenLag(z_2014)`.

Độ lớn thay đổi `m = sqrt(delta_z² + delta_lag_z²)`. Chỉ những ô nội vùng có `m >= 0.05` mới thuộc một trong bốn chế độ định hướng:

- **Synergistic Growth:** `delta_z >= 0`, `delta_lag_z >= 0`.
- **Agglomeration Shadow:** `delta_z < 0`, `delta_lag_z >= 0`.
- **Emergent Pioneer:** `delta_z >= 0`, `delta_lag_z < 0`.
- **Synchronized Decline:** `delta_z < 0`, `delta_lag_z < 0`.

**Quan trọng:** Tên `Synchronized Decline` chỉ **suy giảm vị thế tương đối** (Z-score log NTL của ô và láng giềng giảm sau khi chuẩn hóa riêng tại mỗi năm), **không có nghĩa giá trị NTL tuyệt đối giảm**. Các nhãn cũng không phải kết quả của permutation test hay FDR: đây là phân loại mô tả dựa trên hướng và ngưỡng thay đổi.

#### 3. Kết quả theo nhãn gốc từ webapp

| Chế độ | Số ô | Ô NTL tăng tuyệt đối | Ô NTL giảm tuyệt đối | NTL 2014 TB | NTL 2020 TB |
|---|---:|---:|---:|---:|---:|
| Synergistic Growth | 1.456 | 1.456 | 0 | 0,481 | 3,859 |
| Agglomeration Shadow | 75 | 75 | 0 | 0,819 | 2,148 |
| Emergent Pioneer | 194 | 194 | 0 | 0,324 | 1,075 |
| **Synchronized Decline** | **4.711** | **4.624** | **87** | **0,532** | **1,029** |
| Excluded or Static | 1.897 | 1.872 | 25 | 0,201 | 0,498 |

- **98,15%** ô của chế độ `Synchronized Decline` thực chất **tăng NTL tuyệt đối**. Trung bình nhóm này tăng gần gấp đôi.
- `Synchronized Decline` chiếm **60,92% của 7.733 ô nội vùng** (và 56,53% tổng 8.333 ô). Phần lớn sự thay đổi là giảm tương đối so với phân phối đã chuẩn hóa, không phải suy giảm đô thị/economic activity.
- Toàn vùng: NTL trung bình không trọng số **0,4452 → 1,4137**; **8.221 ô tăng**, **112 ô giảm** tuyệt đối, tính cả ô biên.
- Vì chỉ có hai mốc 2014/2020, đây là **so sánh hai thời điểm**, không chứng minh khuynh hướng tăng liên tục ở các năm giữa.

#### 4. Spatial Markov từ CSV

Bảng chuyển trạng thái các phân vị NTL (Q1–Q4), đơn vị **số ô** (mẫu 7.733 ô nội vùng):

| 2014 → 2020 | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| Q1 | 1.482 | 422 | 23 | 6 |
| Q2 | 446 | 1.190 | 245 | 53 |
| Q3 | 4 | 321 | 1.426 | 181 |
| Q4 | 0 | 1 | 239 | 1.694 |

- **74,90%** ô vẫn thuộc cùng quartile giữa hai mốc, mặc dù NTL tuyệt đối toàn vùng tăng mạnh.
- Chỉ số Shorrocks theo phép tính của source ứng dụng: khoảng **0,3347** (dựa trên bảng xác suất chuyển tiếp đã làm tròn một chữ số phần trăm). Chỉ tiêu này mô tả sự dịch chuyển thứ hạng, không phải tăng trưởng ánh sáng tuyệt đối.

#### 5. Sensitivity theo ngưỡng movement magnitude

Thay ngưỡng của quy tắc phân loại, giữ nguyên các delta do app xuất và không đổi dữ liệu:

| Ngưỡng | Synergistic Growth | Agglomeration Shadow | Emergent Pioneer | Synchronized Decline | Excluded/Static |
|---|---:|---:|---:|---:|---:|
| 0,025 | 1.555 | 137 | 438 | 5.242 | 961 |
| **0,050 (baseline)** | **1.456** | **75** | **194** | **4.711** | **1.897** |
| 0,100 | 1.254 | 42 | 62 | 2.949 | 4.026 |
| 0,200 | 998 | 23 | 20 | 1.111 | 6.181 |

Như vậy, **số ô được gắn nhãn theo chuyển động khá nhạy với ngưỡng**. Điều này không chứng tỏ thuật toán sai, nhưng người dùng nên đọc đây là một phân tích mô tả có giả định cần công bố. Ở biên ngưỡng, việc xuất số làm tròn có thể làm một số ô chuyển nhóm khi người khác tính lại từ CSV.

#### 6. Kết luận và khuyến nghị cho ứng dụng

1. **PASS — công thức và phân loại trong CSV:** kiểm tra độc lập cho kết quả nhất quán; ngoại lệ `grid_id=3922` là tình huống nhạy với việc CSV làm tròn gần 0,05.
2. **Cần chỉnh diễn giải/nhãn UI:** thay vì hiểu `Synchronized Decline` là "suy giảm ánh sáng/kinh tế", nên mô tả rõ "Relative Z-score decline of cell and spatial neighborhood" (suy giảm vị thế tương đối của ô và láng giềng). Tương tự, `Synergistic Growth` không tự bảo đảm tốc độ tăng kinh tế cao.
3. **Nhãn Space-Time không phải nhãn có ý nghĩa thống kê:** kết quả không thực hiện permutations hay FDR; không gọi các nhóm này là statistically significant mà không có kiểm định riêng.
4. **Ngưỡng `movement_magnitude=0,05` cần được công bố** và trình bày kết quả robustness theo nhiều ngưỡng.
5. **Chưa kiểm chứng đầu vào 2014:** cần raster VIIRS 2014 do một pipeline Earth Engine độc lập tạo ra để đối chiếu lại tất cả 8.333 ô như đã làm năm 2020. Nếu muốn kiểm chứng tính nhất quán liên thời gian, nên xem thêm các năm trung gian 2015–2019, không chỉ hai mốc.
6. Các phát biểu liên quan đến **GDP, đô thị hóa hay tác động kinh tế** vẫn cần kiểm chứng bên ngoài; thay đổi NTL không tự động chứng minh thay đổi GDP.

#### 7. Artefacts

- `yanqing_temporal_validation_by_cell.csv`: biến tái tính, nhãn app và nhãn độc lập từng `grid_id`.
- `yanqing_temporal_regime_summary.csv`: thống kê theo nhóm (nhãn tái tính từ CSV, có một ngoại lệ do làm tròn; bảng nhãn gốc phía trên là số chính thức từ app).
- `yanqing_temporal_markov_counts.csv`: bảng chuyển quartile dạng số ô.
- `yanqing_temporal_validation_results.json`: kiểm định, sai số và sensitivity chi tiết.
- `validate_temporal.py`: mã tái lập độc lập từ CSV nguồn.

Không chỉnh sửa repository trong bước này.


<a id="repo-audit-doc"></a>

## Repository audit fixes — implementation notes

**Original source:** `docs/audit-fixes-2026-11-11.md`. **Status:** retained technical record.

> [!NOTE]
> **Full validation record** — embedded from the source report below; any cross-reference to a separate ZIP is an evidence inventory item, not a GitHub-tracked artifact.

### Audit corrections and migration (11 November 2026)

Primary evidence: `verification-report.md` and `spatial-app-audit-evidence.zip`,
auditing commit `81a53c96eb1405c56665146325383c6e02350dc9`. Current main was
inspected and still matched that commit before these changes.

#### Local Moran

The conditional null now fixes the focal observation and samples k **distinct**
values uniformly from the other m−1 active members, without replacement within
each replicate. Replicates are independent and may repeat. Sequential rejection
sampling retains bounded O(number of focal cells × maximum grid degree) working
memory, without constructing an m×m matrix. Queen/Rook weights, active sample,
edge handling, minimum sample/neighbor requirements and grid guards are unchanged.

Observed and simulated Local I now use
`(m−1) * z_i * mean(neighbor z) / sum(active z²)`, matching ESDA's normalization.
Consequently new I equals old I × (m−1)/m for the same sample. Signs, spatial lag
and raw quadrants are unchanged by normalization. The regional `moran_I_lit`
is a mean of these Local I values, not the app's binary-weight Global Moran I;
Global Moran's implementation has not changed.

The app retains inclusive upper/lower tails with absolute tie tolerance 1e-12,
the +1 Monte Carlo correction, doubled smaller-tail p capped at one, and the
existing Benjamini–Hochberg FDR family and thresholds. Its p floor remains
2/(permutations+1). ESDA's one-tail `p_sim` and tie handling differ, so raw p-values
are not promised to match, and matching seeds do not match random streams.

Recompute prior p-values, FDR decisions, hotspot areas, cluster membership,
spillover treatment/control assignments and downstream panel results. Old and new
results must not be pooled silently. Region exports include
`lisa_method_version=conditional-wor-esda-v2`; the LISA session-cache key also
changes. Restart active app sessions and regenerate stored exports/panels.

#### Raster masks

Both main-app raster rewrites and `zonal_stat` now preserve explicit NoData and
GDAL masks and exclude NaN/infinite pixels before clipping valid negatives.
The rewritten raster declares NaN as NoData. Thus [10, −9999 NoData] has mean 10,
not 5 (clipped) or −4994.5 (unclipped). Valid zeros remain observations.

`fill_missing=None` preserves missing zonal means; the default final cell fill
remains zero. The app also retains its explicit final cell-level zero fill and
reports missing-result counts. Entirely missing/outside sums remain zero under
exactextract's sum convention. These final fills do not add invalid pixels to
partially observed pixel means. Earth Engine's existing upstream unmask-to-zero
convention is unchanged: an upstream zero cannot subsequently be distinguished
from an observed zero. No real satellite data agreement is claimed.

#### Nan / Yiyang metadata

The audit's official full-resolution GADM 4.1 GeoPackage (SHA-256
`e8f9e5ead4526e30e0ccd83365b06c10ce25bbef8831f7881bdbc05a026f00bc`)
identifies source GID_3 `CHN.14.10.2_1` as NAME_3 `Nan`, under Yiyang.
The curated schema maps GID_3→GID_2 and NAME_3→NAME_2. Only NAME_2 is corrected
from Yiyang to Nan. The legacy filename `CHN_Hunan_Yiyang_Yiyang_District.geojson`
is deliberately retained for path compatibility; it is not an authoritative name.
Geometry, GID, type and processing folder are preserved. Joins should use GIDs;
name-based joins and saved display labels may need updating. This restores the
GADM source label and makes no claim about current legal administrative status.

#### Validation

Use Python 3.12+ for the ESDA 2.10.0 benchmark dependencies (the application
runtime requirements are unchanged). `python -m pip install -r requirements-test.txt`
then `python -m pytest -q`.
Independent regression tests compare observed I with ESDA 2.10.0 on Queen/Rook
grids of 9, 100 and 400 cells, and conditional p with exhaustive corner-neighbor
combinations on 9- and 30-cell fixtures, distinguishing replacement nulls.
Complete-neighborhood ties, mask/sentinel/nonfinite raster means and sums,
ordering, outside coverage and both app rewrite sites are also covered.

No grid splitting/resolution, resource guard, Earth Engine authentication or
deployment policy was changed. Live Earth Engine acquisition and validation
remain conditional on legitimate authorization and were not performed here.


<a id="repo-spacetime-doc"></a>

## Space-Time relative regime interpretation — implementation notes

**Original source:** `docs/spacetime-relative-regime-interpretation.md`. **Status:** retained technical record.

> [!NOTE]
> **Full validation record** — embedded from the source report below; any cross-reference to a separate ZIP is an evidence inventory item, not a GitHub-tracked artifact.

### Space-Time LISA regime interpretation (display-only clarification)

#### What the four regimes measure

The Space-Time module computes `log1p(max(NTL, 0))` at each of two selected years and standardizes the transformed values **separately within each year**, over the valid, non-edge analysis cells. It computes the mean neighboring z-score using the active Queen grid.

- `delta_z = z_t1 - z_t0`
- `delta_lag_z = lag(z)_t1 - lag(z)_t0`
- `movement_magnitude = sqrt(delta_z**2 + delta_lag_z**2)`

A regime is assigned only if the cell has valid neighbors and `movement_magnitude >= 0.05`. Cells below the threshold are `Excluded_or_Static`. This **0.05 cutoff is descriptive**, not a p-value, FDR cutoff, or other statistical significance test. In particular, Space-Time regime labels are not significance-tested Local Moran classifications.

The signs of `delta_z` and `delta_lag_z` identify changes in **relative NTL position**, not changes in the underlying radiance itself. A cell can increase in absolute NTL yet receive a relative-decline label if its within-year standardized position worsens.

| CSV identifier (unchanged) | English user-facing interpretation |
|---|---|
| `1_Synergistic_Growth` | Synergistic Relative Growth (focal and neighboring relative positions increase) |
| `2_Agglomeration_Shadow` | Cell Relative Decline / Neighbor Relative Growth |
| `3_Emergent_Pioneer` | Cell Relative Growth / Neighbor Relative Decline |
| `4_Synchronized_Decline` | Synchronized Relative Decline (both relative positions decrease) |

#### Compatibility and scope

This change **only** updates bilingual explanatory text and the display table. It deliberately leaves the `spacetime_regime` CSV codes, `regime_summary` raw result, Space-Time equations, `movement_magnitude` threshold, Spatial Markov calculations, and export column names untouched. Existing scripts filtering `4_Synchronized_Decline` will continue to work.

The Yanqing, Beijing 2014–2020 validation found that 4,624 of the 4,711 cells classified with raw identifier `4_Synchronized_Decline` increased in **absolute** NTL. This illustrates the distinction; it does not imply a calculation error or verify the interpretation for every location/year.

#### Remaining scientific limitations

Because z-scores are normalized separately by year, the regimes show changes in relative spatial standing. They do not directly measure economic growth or decline, and they do not establish causality. The proportion of cells in each regime is sensitive to the descriptive movement threshold; report this choice and consider sensitivity analyses when publishing results.


---

<a id="part-iii"></a>

# Part III — Evidence custody and ongoing validation protocol

## A. Detailed report and evidence-bundle inventory

The report chapters above reproduce the ten full original Markdown reports, plus the two repository documentation records. The following supporting files were produced during the validation campaign and were used to reproduce the results; **the names below do not imply they reside in GitHub**.

| Area | Core evidence items (generated or uploaded during validation) |
|---|---|
| Audit | `spatial-app-audit-evidence.zip`, `verification-report.md` |
| LISA | `yanqing_validation_evidence.zip`, `yanqing_lisa_independent_cell_comparison.csv` |
| VIIRS 2020 preliminary | `yanqing_viirs_validation_evidence.zip`, `yanqing_viirs_reference_interior_comparison.csv` |
| VIIRS 2020 final | `yanqing_viirs_all_cells_validation_evidence.zip`, `yanqing_viirs_all_8333_polygon_comparison.csv` |
| VIIRS 2014 | `yanqing_2014_temporal_raster_validation_evidence.zip`, `yanqing_2014_viirs_cell_validation.csv` |
| Measurement | `yanqing_2020_measurement_sensitivity_evidence.zip`, `yanqing_2020_measurement_sensitivity_cells.csv` |
| Transformation | `yanqing_2020_transformation_sensitivity_evidence.zip`, `yanqing_2020_transformation_sensitivity_cells.csv` |
| Spatial | `yanqing_spatial_robustness_evidence.zip`, `yanqing_spatial_robustness_500m_cells.csv`, `yanqing_spatial_robustness_1000m_cells.csv` |
| Temporal | `yanqing_temporal_validation_evidence.zip`, `yanqing_temporal_validation_by_cell.csv`, `yanqing_temporal_regime_summary.csv`, `yanqing_temporal_markov_counts.csv` |

### Traceability and storage limitations

- The Markdown reports and their key tables are **embedded here**. You do not need to open the standalone Markdown reports to read the findings and original caveats.
- Raw GeoTIFFs, CSVs, GeoJSON grids, scripts, metrics JSON and logs have **not** been added to this documentation-only PR. For an independently reproducible publication artifact, deposit a versioned evidence package to durable storage with immutable digests and add its locator here.
- Some preliminary notes originally said “no raster available” or “only interior cells tested.” Those statements were accurate **at their original stage**, but were **superseded** by the subsequent complete 2014/2020 raster validation. They are preserved for audit trail, not as current blockers.
- CI results validate the repository code paths under their test fixtures; Earth Engine GeoTIFF checks validate the stated pilot; GHSL correlations derived from the app remain **UI-reported only** pending a separate independent extraction benchmark.

## B. Future PR acceptance checklist

- [ ] Identify validation ID (V01–V14 or a new ID), date, repository SHA/PR, and a precise scientific question.
- [ ] State source dataset, product/band, geographic GID/extent, study year(s), CRS, raster pixel scale, grid resolution and masks.
- [ ] State baseline and alternative configurations, random seed, permutations, p-value convention, FDR correction and tolerance.
- [ ] Include full reproducible methods, code/script names, data hashes and durable evidence references, or state why they are unavailable.
- [ ] Include numeric tables (sample size, errors, overlap, outliers), not only verdict labels.
- [ ] Separate correctness, robustness, construct validity and performance verdicts; call limitations out explicitly.
- [ ] Update the Part I status matrix and decisions, and append a **complete new validation chapter** to Part II.
- [ ] Add a chronological change-log entry; never silently replace an older result.
- [ ] Preserve machine-readable CSV identifiers and statistical definitions unless a separately tested migration is approved.

## C. Standing decisions

- Maintain the current 500 m baseline and district-level RAM safeguards unless independent evidence warrants a clearly documented revision.
- Raw NTL and Queen weights remain the defined Yanqing baseline; P99/log, Rook, and alternate cell sizes are independent sensitivity specifications, not interchangeable estimands.
- Space-Time relative-decline labels are directional changes in year-standardized NTL and spatial lag—not absolute radiance decline, GDP contraction, or a significance-test result.
- A single successful locality cannot establish cross-location or multi-year robustness.
- Documentation corrections may be merged separately from numerical implementation changes; new substantive metrics require matching evidence and tests.

[Back to top](#top)
