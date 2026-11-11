# Kiểm toán tích hợp và hồi quy — spatial-app

**Ngày:** 11/11/2026  
**Commit được đánh giá:** `44f2347cffca1e761350bb948df8fa7ce4f22f9f` (`main` tại thời điểm bắt đầu)  
**Phạm vi:** `app.py`, `ntl/`, `tests/`, `.github/workflows/`, khai báo dependencies và ranh giới tích hợp các chức năng. **Không** kiểm định lại 19.987 GeoJSON.  
**Phương pháp:** đọc mã nguồn, xác định hợp đồng dữ liệu giữa các module, đối chiếu CI run thực tế và thêm kiểm thử hồi quy tổng hợp. Không thay đổi thuật toán trong PR này.

> **Mức độ bằng chứng:** Đọc được toàn bộ 23 file Python của repo qua GitHub, kiểm tra workflow và log GitHub Actions thực tế trên main. Đợt kiểm toán mới **không** tự tải dữ liệu Earth Engine hoặc chạy end-to-end trên Streamlit Cloud; các kết quả này phải được phân biệt với regression tests dùng dữ liệu tổng hợp.

## 1. Kết quả xác minh bằng CI

- Trên main tại commit nêu trên, GitHub Actions run [#43053877659](https://github.com/hoanfg/spatial-app/actions/runs/43053877659) **SUCCESS**, gồm **32** test ở job `core` và **22** test ở job `ui-smoke`, tổng **54 passed**.
- CI trước thay đổi chạy năm file: `test_lisa_reliability.py`, `test_robustness.py`, `test_zonal.py`, `test_ui_smoke.py`, `test_audit_regressions.py`.
- File `tests/test_spacetime_labels.py` có trong `tests/`, nhưng **không nằm trong lệnh pytest của workflow**. Đây là phát hiện A01 xác nhận được: CI xanh không chứng minh file đó được thực thi.
- Branch audit bổ sung test này vào job giao diện, cộng `tests/test_pipeline_integration.py` mới. Trạng thái final của CI trên branch/PR phải được ghi bằng chính run tương ứng; **không dùng trạng thái main để tuyên bố PR mới PASS**.

## 2. Phát hiện và phân loại

| Mã | Phát hiện | Phân loại | Mức độ | Hành động |
|---|---|---|---|---|
| A01 | CI bỏ qua `test_spacetime_labels.py` | **Lỗi xác nhận** | P0 | Bổ sung vào workflow; kiểm tra log job |
| A02 | `.unmask(0)` và `.fillna(0)` khiến missing/no-observation và zero quan sát có thể cùng xuất thành 0 | **Chính sách dữ liệu hiện hành, rủi ro diễn giải** | P1 | Giữ thông tin coverage/quality flags; benchmark dữ liệu có missing trước khi đổi |
| A03 | Global Moran dùng toàn lưới/binary Queen; Local Moran dùng tập ô hợp lệ và row-standardized Queen | **Khác biệt estimand có chủ ý, nguy cơ bị diễn giải như cùng một mẫu** | P1 | Cập nhật tài liệu thuật ngữ, kiểm tra xuất metadata |
| A04 | Hai hàm Gini khác nhau về xử lý NaN/âm (`app.py` vs `ntl/lisa_core.py`) | **Trùng logic, hành vi khác nhau với dữ liệu lỗi** | P2 | Thêm test hợp đồng và thống nhất quy tắc sau review |
| A05 | `requirements.txt` phần lớn chưa pin phiên bản; CI core dùng Python 3.11, smoke dùng 3.13 | **Rủi ro tái lập môi trường** | P1 | Lock/tested matrix, ghi phiên bản tại export |
| A06 | `app.py` ~2.688 dòng kiêm tải raster, grid, Moran, UI, export | **Coupling/maintainability** | P1 | Refactor từ từ sau khi có E2E tests, không viết lại toàn bộ |
| A07 | MAUP trong `ntl/robustness.py` sử dụng block aggregation từ ô mịn, không đồng nhất bắt buộc với dựng trực tiếp lưới thô từ raster | **Khác biệt phương pháp** | P1 | Đặt tên đúng, so sánh 2 cách trên dữ liệu thật |
| A08 | GHSL `nearest_epoch()` và `unmask(0)` | **Giới hạn temporal/missingness** | P1 | Kiểm tra năm sản phẩm và mask, tái lập GHSL độc lập |
| A09 | Ngưỡng `rho = 0.40/0.60` mang tính thực hành | **Giới hạn suy luận đã nêu trong code** | P2 | Giữ là tham khảo, không coi là kiểm định thống kê |
| A10 | Cache theo phiên, theo kết quả và cấu hình; chưa stress-test nhiều phiên | **Chưa kiểm chứng performance** | P2 | Đo RAM/TTL/invalidation sau khi có benchmark |
| A11 | `test_ui_smoke.py` gọi `render_lisa_tab` với dữ liệu tổng hợp; không kích hoạt toàn pipeline Earth Engine | **Khoảng trống E2E** | P1 | Test hợp đồng raster→LISA→CSV, sau đó Cloud/Earth Engine thật |
| A12 | README, specification, validation song ngữ chứa mô tả phương pháp trùng lặp | **Nguy cơ drift tài liệu** | P2 | Tách nguồn chân lý và kiểm tra version/config ở các tài liệu |

### 2.1. Chi tiết A02: zero khác với thiếu quan sát

- `app.py:1406–1443` tính `median` ảnh tháng hợp lệ rồi `unmask(0.0)`.
- `app.py:1911–1927` chuyển thống kê zonal `NaN` và kết quả không ghép được thành `0.0`.
- `ntl/zonal.py` giữ masked/NaN của raster hợp lệ trước lúc trích xuất, nhưng mặc định `fill_missing=0.0` nếu caller không đổi.
- `ntl/data_quality.py` có metadata và cảnh báo phù hợp; `quality_ui.py` có phép đếm tháng hợp lệ theo yêu cầu.
- **Không có bằng chứng từ Yanqing 2014/2020 cho thấy lỗi missing xảy ra**: raster pilot có 12 composite tháng hợp lệ trên toàn bounding-box được thử. Không nên coi một tình huống khác là bug đã tác động đến kết quả Yanqing.

### 2.2. Chi tiết A07: đừng nhập hai phép MAUP làm một

`robustness.aggregate_blocks` nhóm chỉ số lưới mịn thành factor×factor và lấy bình quân theo diện tích ô trước khi chạy lại LISA. Điều này là phép thử block aggregation, **không nhất thiết tái lập** raster→polygon của lưới 1.000 m được dựng trực tiếp từ ranh giới. Sự khác biệt phải ghi trong cả phần diễn giải và bảng phương pháp, không tự kết luận sai số hay thay kết quả trước đó.

## 3. Thử nghiệm tích hợp mới

File `tests/test_pipeline_integration.py` dùng GeoTIFF tổng hợp lưu trong bộ nhớ và đa giác UTM 500 m, gồm bốn phép kiểm:

1. **Raster → zonal mean → Local Moran → CSV**: kiểm tra thứ tự và định danh 16 ô, dữ liệu NTL, nhãn cụm, xuất/đọc CSV.
2. **Missing vs measured zero**: pixel 0 quan sát, NoData sentinel và negative radiance hợp lệ phải phân biệt được trước khi `fill_missing=0`; ghi rõ rằng chính sách fill làm các giá trị cuối có thể giống nhau.
3. **Space-Time label compatibility**: hàm hiển thị không được biến đổi `regime_summary` hoặc mã CSV gốc.
4. **Space-Time CSV contract**: kiểm tra trường số, mã regime và sự ổn định sau CSV roundtrip.

Đây là kiểm tra liên module trên dữ liệu nhân tạo; **không** thay thế thực nghiệm ảnh từ Earth Engine, GHSL hoặc Streamlit Cloud. Trạng thái chạy CI của branch/PR được xem là bằng chứng riêng, không suy diễn từ main.

## 4. Những điều chưa thể xác nhận

- Chưa thu thập bằng chứng của 3 địa phương Cross-location V11; vẫn **PENDING**.
- Chưa chạy export/download VIIRS, GHSL, hoặc hoàn thiện E2E trên Streamlit Community Cloud trong đợt này.
- Chưa kiểm tra đầy đủ mọi hành vi interactive của Streamlit (nhiều phiên, tải lại, reset cache, errors).
- Chưa xác minh toàn bộ so sánh văn bản README, tài liệu kỹ thuật và UI theo từng câu.
- Chưa pin production dependency hay thay đổi công thức phân tích.

## 5. Tiêu chí chấp nhận và thứ tự ưu tiên

- **Ngay:** CI phải chạy đủ 6 file có sẵn + file integration mới; test mới phải PASS và không che giấu fail bằng skip không chủ đích.
- **Sau đó:** tạo bộ dữ liệu cố ý có NoData, low coverage, negative pixel để đo ảnh hưởng đến LISA và CSV; chỉ thay policy khi có kết quả thực nghiệm.
- **Tiếp:** đối chiếu MAUP coarsening từ block với exact raster-on-coarse-grid; độc lập kiểm tra GHSL.
- **Cuối:** benchmark tài nguyên và multiple sessions trên Streamlit Cloud; thiết lập lockfile/compatibility matrix; refactor từng phần có regression test.

**Quy tắc thay đổi:** không gộp việc sửa thuật toán, đổi kết quả CSV hoặc chính sách missing vào PR chỉ bổ sung tests. Mọi thay đổi khoa học cần test hồi quy và bằng chứng đối chiếu riêng.

## 6. Nhật ký bằng chứng

| Bằng chứng | Nơi kiểm tra |
|---|---|
| Commit gốc được audit | `44f2347cffca1e761350bb948df8fa7ce4f22f9f` |
| Main CI run (54 PASS) | https://github.com/hoanfg/spatial-app/actions/runs/43053877659 |
| Workflow CI | `.github/workflows/tests.yml` |
| Regression source | `tests/test_spacetime_labels.py` |
| New contract tests | `tests/test_pipeline_integration.py` |
| Main pipeline, export | `app.py:1382–1504, 1845–1960, 2639–2675` |
| Spatial inference and dynamics | `ntl/lisa_core.py:41–190, 385–729` |
| Robustness | `ntl/robustness.py:18–192` |
| Data quality and GHSL | `ntl/data_quality.py`, `ntl/quality_ui.py`, `ntl/ee_extra.py` |
| Raster extraction contract | `ntl/zonal.py` |

