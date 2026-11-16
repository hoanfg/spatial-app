<a id="top"></a>

# Hướng dẫn kiểm chứng và danh mục bằng chứng

[English](README.md) · [Tiếng Việt](README-vi.md) · [Sổ tay ứng dụng](../README-vi.md) · [GADM và phương pháp](../docs/README-vi.md)

Kết quả kiểm chứng chỉ áp dụng cho địa bàn, năm, dữ liệu và độ chính xác đã nêu. CI xanh không tái tạo raster Earth Engine; tương quan quan sát được cũng không xác nhận một kết quả kinh tế.

| Cần xem | Nơi đọc |
| --- | --- |
| Trạng thái và việc còn mở | [Bảng dưới đây](#tinh-trang-hien-tai) |
| Danh mục bằng chứng, nguồn gốc và giới hạn | [Hướng dẫn bằng chứng](evidence/README-vi.md) |
| Dữ liệu và phép kiểm có thể chạy | [Diên Khánh, Bắc Kinh](evidence/yanqing/README-vi.md), [Bảo An](evidence/audit-2026-11-15/), [quy trình nhiều địa bàn](cross_location/README-vi.md) |

## Tình trạng hiện tại

| Hạng mục | Kết quả có bằng chứng | Giới hạn còn lại |
| --- | --- | --- |
| GADM Trung Quốc | 2.420 đơn vị biên tập khớp nguồn GADM 4.1 đầy đủ trong sai số ghi nhận; tên Nan đã sửa ở PR #10 | Không xác nhận ranh giới pháp lý hiện nay hoặc mọi quốc gia |
| VIIRS và LISA tại Diên Khánh, Bắc Kinh | Đối chiếu raster độc lập theo 8.333 ô cho từng năm 2014 và 2020; công thức, FDR và phép tính 2014→2020 được kiểm tra trong phạm vi báo cáo | Hai mốc năm không chứng minh xu thế hằng năm liên tục |
| V11 Thượng Hải / Bảo An / Kỳ Môn | Báo cáo 2020: 15.330/15.330 ô đầy đủ trong giới hạn làm tròn CSV; 1.846/1.847 ô cắt biên trong ngưỡng chặt 0,00005, tất cả trong 0,0000501. Có đối chiếu Queen/FDR với giới hạn về làm tròn và seed | Hình học ô cắt biên lấy từ GeoJSON app; repo thiếu raster, kết quả chi tiết và biểu đồ |
| Siêu dữ liệu A02 | CSV Bảo An 7.148 ô đều có trạng thái đã quan sát và năm trường chất lượng hữu hạn; CSV NTL sau PR #27 trùng byte với bản lưu | Chưa có ca thiếu hoặc ít quan sát thực; chưa lưu cấu trúc phản hồi tải dữ liệu thô khi chạy trực tiếp |
| GHSL Thượng Hải | PR #24–26 đã sửa phép cộng lượng trên lưới nguồn. Rho, khoảng bootstrap và AUC độc lập tại 715 ô lõi khớp mức làm tròn giao diện | Chưa có GHSL từng ô do ứng dụng đang chạy xuất; biểu đồ Kỳ Môn/Bảo An không thay phép kiểm từng ô độc lập |
| Hiệu năng A02 | Một hồ sơ đo tại Bảo An sau PR #27 ghi A02 26,4623 giây, so với mốc trước 25,0028 giây; PR #29 thêm thời gian từng bước con và `source_commit` | Chưa chứng minh tăng tốc; cần nhiều lượt chạy đám mây cùng cấu hình |

[Hướng dẫn bằng chứng](evidence/README-vi.md) ghi dữ liệu đã lưu, hồ sơ nguồn và phép kiểm SHA-256. Danh mục 78 báo cáo liệt kê 118 tệp trực tiếp và 271 thành viên ZIP; repo có báo cáo và một số CSV/JSON, **không có** toàn bộ raster, mã kiểm, biểu đồ hay thành viên ZIP đã liệt kê.

## Kết quả rà soát và việc còn mở

| Mã | Việc cần làm hoặc quyết định | Bằng chứng cần có |
| --- | --- | --- |
| S01–S03 | Giữ các chốt chặn của công cụ kiểm chứng ngoài đối với độ phủ/độ phân giải GHSL và vùng tham chiếu A02 nếu khôi phục được mã gốc | Báo cáo ghi ca âm nhân tạo; repo chưa có mã kiểm tra và đầu vào thực địa đó |
| S04 | So tâm UTM/WGS84 của từng đa giác dựng lại theo `grid_id`; so diện tích không phát hiện tráo hai ô cùng diện tích | Đã có trong `main`, kèm ca âm tại `tests/test_cross_location_identity.py` |
| S05 | Công cụ độc lập cần từ chối số tháng quan sát dạng phân số | Cấu trúc A02 khi vận hành đã kiểm tra số nguyên; mã kiểm tra trong bản lưu cũ chưa có ở repo |
| A02 | Kiểm chứng ca thật sự không có hoặc ít quan sát mà chưa tự đổi chính sách `legacy_zero_fill` | Raster support và CSV app cùng lượt chạy |
| A03, A07, A09 | Tách biệt mẫu và trọng số Global/Local Moran; gọi đúng MAUP gộp ô; coi ngưỡng rho là quy ước diễn giải | Vẫn cần so trực tiếp với lưới thô từ raster; chưa suy ra lỗi số học chỉ từ thuật ngữ |
| A04 | Quyết định quy tắc NaN/giá trị âm trước khi thống nhất hai hàm Gini | Hợp đồng dữ liệu khoa học và test hồi quy |
| A05, A06, A12 | Ghi ma trận phiên bản thư viện đã kiểm tra; tách dần `app.py` khi có E2E; đồng bộ tài liệu song ngữ | Chưa có lockfile, refactor rộng hoặc kiểm toán mọi câu tài liệu |
| A08, A10, A11 | Kiểm tra kỳ GHSL hoặc mặt nạ khác, lượt Earth Engine đến ứng dụng rồi CSV, hiệu năng/RSS đám mây lặp lại và nhiều phiên | Dịch vụ có quyền truy cập và số đo gắn mã commit triển khai |
| V12, V13 | Xem chuỗi VIIRS nhiều năm và đối chứng kinh tế độc lập cùng thời gian/địa bàn | So sánh hai mốc và GHSL không tự chứng minh hai điều này |

A01 về CI đã sửa trong PR #19. PR #10 sửa Local Moran, mask NoData và một tên nguồn GADM; #20–22 thêm A02 và các phép kiểm số; #24–27 sửa phần vận hành A02/GHSL và gộp reducer nhiều band; #28 công bố bằng chứng khôi phục được; #29 thêm chẩn đoán A02; #31 thêm chốt kiểm tra danh tính ô S04. [Kho nguồn văn bản thuần](evidence/historical_document_sources_2026-11-15.txt) giữ nguyên các báo cáo từng nằm rải trong `docs/` và thư mục này.

## Phương pháp và khả năng tái lập

| Câu hỏi | Phương pháp / giới hạn |
| --- | --- |
| NTL mỗi ô | Trung bình bức xạ VIIRS theo tỷ lệ phủ điểm ảnh; giá trị âm hợp lệ được chặn về 0 ở đầu ra cũ. Bức xạ thiếu được điền 0 ở nguồn, kèm trường A02 về hỗ trợ quan sát. |
| Local Moran | Ô lõi/ô sáng đủ điều kiện, Queen chuẩn hóa theo hàng hoặc Rook được chọn, rút ô khác tâm không hoàn lại, đuôi bao gồm trường hợp bằng nhau và BH-FDR. Global Moran dùng toàn ô và Queen nhị phân. |
| GHSL | Cộng lượng từng điểm ảnh nguồn theo tỷ lệ giao với đa giác, sau đó chia diện tích ô để lấy mật độ. Chuyển đa giác sang CRS nguồn; không cộng các giá trị điểm ảnh đã nội suy lại như những lượng nguồn độc lập. |
| Mức bằng chứng | CI và kiểm thử nhân tạo, kiểm tra số liệu lưu trữ, đối chiếu raster thực địa độc lập và phép đo vận hành trực tiếp trả lời những câu hỏi khác nhau. Mỗi kết luận cần mã băm đầu vào, phiên bản mã, địa bàn, năm, lưới và dung sai. |

[Sổ tay kỹ thuật](../README-vi.md) trình bày công thức và từ điển CSV. [Hướng dẫn GADM/phương pháp](../docs/README-vi.md) trình bày quy tắc trích xuất và cách hiểu nhãn Space-Time. Bản lưu có toàn bộ phép tính chi tiết cũ; việc viết gọn ở đây không đổi công thức ứng dụng hay số liệu đã công bố.

### Kiểm tra có thể chạy từ repo

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/audit_docs_archive.mjs
node validation/check_docs.mjs
python -m pytest -q tests
```

Hai lệnh đầu kiểm tra byte của tài liệu/dữ liệu đã nộp và tóm tắt CSV công khai; `check_docs.mjs` kiểm tra liên kết và dấu công thức cơ bản. Bộ Python kiểm tra hợp đồng mã; không tự chạy lại Earth Engine, GHSL thực địa hoặc phép đo hiệu năng đám mây. Chỉ ghi đạt sau khi có kết quả chạy thực tế.
