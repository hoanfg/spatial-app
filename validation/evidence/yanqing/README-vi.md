# Bằng chứng kiểm chứng tại Diên Khánh

[English](README.md) · [Tiếng Việt](README-vi.md) · [Danh mục bằng chứng](../README-vi.md)

Thư mục này chứa đầu vào công khai và kết quả đối chiếu độc lập cho quận Diên Khánh, Bắc Kinh. Kết quả chỉ áp dụng cho đúng tệp, năm và dung sai đã ghi.

## Câu hỏi và lý do kiểm tra

| Phép kiểm | Lý do |
| --- | --- |
| Raster VIIRS sang lưới | Xác nhận phép chiếu, tỷ lệ phủ đa giác và mức làm tròn CSV tạo đúng NTL cho từng ô. |
| Local Moran và FDR | Xác nhận quan hệ láng giềng, Local I, ý nghĩa hoán vị và nhãn sau hiệu chỉnh đa kiểm định có thể được tính độc lập ngoài ứng dụng. |
| Kết quả Không gian và Thời gian 2014 đến 2020 | Xác nhận các trường hai mốc và mã chế độ trong tệp xuất nhất quán nội bộ. |
| Tính toàn vẹn của tệp | Tránh nhầm một tệp bị thay sau này với đúng đầu vào đã dùng cho kết quả. |

| Tệp | Nội dung | Mục đích |
| --- | ---: | --- |
| [Dữ liệu LISA 2020](CHN_beijing_yanqing_2020_500m_lisa_cells.csv) | 8.333 ô | Đầu ra ứng dụng để kiểm tra láng giềng, Local Moran và FDR |
| [Dữ liệu Không gian và Thời gian 2014 đến 2020](CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv) | 8.333 ô | Đầu ra ứng dụng để kiểm tra hướng biến động và chế độ |
| [Dữ liệu NTL 2020](dien_khanh_NTL_2020_500m.csv) | 8.333 ô | Đầu ra ứng dụng cho phép đối chiếu raster |
| [Đối chiếu LISA độc lập](yanqing_lisa_independent_cell_comparison.csv) | 8.333 ô | Láng giềng, thống kê và mức ý nghĩa được tính lại |
| [Đối chiếu VIIRS độc lập](yanqing_viirs_all_8333_polygon_comparison.csv) | 8.333 ô | So bức xạ nguồn với kết quả trích xuất theo đa giác |
| [Gói kiểm tra LISA độc lập](archives/yanqing_validation_evidence.zip) | ZIP | Mã Python, bảng kết quả, tóm tắt và nhật ký chạy |
| [Ảnh VIIRS tham chiếu 2014](rasters/yanqing_viirs_2014_reference.tif) | GeoTIFF, 217 × 142 | Raster tham chiếu từ Earth Engine |

## Cách đối chiếu

Bảng VIIRS so `ntl_mean` của ứng dụng với trung bình đa giác `ntl_ref_polygon` được tính độc lập cho cùng `grid_id`. Dung sai chặt là 0,00005, tương ứng mức làm tròn CSV bốn chữ số thập phân. Các ô biên vẫn được giữ trong kết quả.

Bảng LISA dựng lại láng giềng Queen, tính lại Local I từ NTL đã làm tròn trong tệp xuất, chạy chuỗi hoán vị độc lập và áp dụng BH-FDR. Bảng so cả giá trị trung gian lẫn nhãn cuối. Vì đầu vào đã làm tròn và hạt hoán vị độc lập, mọi khác biệt nhãn được ghi rõ thay vì ép kết quả phải giống nhau.

CSV Không gian và Thời gian được kiểm tra theo số dòng và mã chế độ của toàn bộ 8.333 ô.

## Kết quả

| Phép kiểm | Kết quả | Diễn giải |
| --- | --- | --- |
| Đối chiếu đa giác VIIRS 2020 | 8.332/8.333 ô nằm trong ngưỡng 0,00005. Sai số tuyệt đối trung bình là 0,0000250270. Sai số lớn nhất là 0,0000643242 tại ô biên `grid_id=349`. | Kết quả khớp ở mức chính xác CSV, trừ một ô biên vượt ngưỡng nhưng vẫn được giữ lại. |
| Nhãn LISA cuối | 8.154/8.333 nhãn khớp; 7.733 ô tham gia LISA và 600 ô bị che biên. | Có 179 khác biệt được ghi đầy đủ: 80 trường hợp Không ý nghĩa thành Low-Low, 74 Low-Low thành Không ý nghĩa, 15 High-High thành Không ý nghĩa và 10 Không ý nghĩa thành High-High. |
| Local I | Sai khác tuyệt đối lớn nhất trong các cặp Local I có giá trị là 0,0001680453. | Bảng dùng NTL đã làm tròn nên không phải phép so đồng nhất ở độ chính xác đầy đủ. |
| Chế độ Không gian và Thời gian | 1.456 Tăng trưởng cộng hưởng; 75 Bóng tích tụ; 194 Tiên phong mới nổi; 4.711 Cùng giảm vị thế tương đối; 1.897 Bị loại hoặc ổn định. | Đây là nhóm mô tả hai mốc, không phải kết quả nhân quả hoặc nhãn ý nghĩa hoán vị. |
| Siêu dữ liệu raster tham chiếu 2014 | Dữ liệu ghi 30.814 điểm ảnh hữu hạn, một điểm ảnh âm và không có điểm ảnh bằng 0. | Raster cũ không có dải đếm quan sát nên chưa biết mức hỗ trợ theo tháng. |

## Tính toàn vẹn

| Tệp | SHA-256 |
| --- | --- |
| `yanqing_validation_evidence.zip` | `51a662cb875ffe4bccfd3c628eeafb136aa9025bb500b5bdaa94d31b24ca5b93` |
| `yanqing_viirs_2014_reference.tif` | `637661ab304986ef19befa4c7ca62d1e9cface500862803f02ad76a4b6637c31` |

Các CSV đã chuyển vẫn giữ giá trị số nhưng có thể được chuẩn hóa kiểu xuống dòng UTF-8. Chỉ ghi nhận trùng từng byte khi mã băm tương ứng khớp.

## Giới hạn

- Repo không có raster tham chiếu thô năm 2020 đã dùng để tạo bảng đối chiếu đa giác.
- Raster năm 2014 không có dải đếm quan sát theo tháng nên không kiểm tra được ngữ nghĩa hỗ trợ A02.
- Giá trị LISA độc lập dùng đầu vào CSV đã làm tròn và chuỗi hoán vị độc lập.
- Hai mốc năm không tạo thành xu thế hằng năm liên tục.
- Các tệp này không tái lập GHSL và không chứng minh NTL là một kết quả kinh tế hợp lệ.

Phương pháp của ứng dụng nằm trong [hướng dẫn dữ liệu và phương pháp](../../../docs/README-vi.md). Trạng thái chấp nhận hiện tại được duy trì trong [hướng dẫn kiểm chứng](../../README-vi.md).
