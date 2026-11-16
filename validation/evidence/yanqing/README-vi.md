# Bằng chứng kiểm chứng tại Diên Khánh

[English](README.md) · [Tiếng Việt](README-vi.md) · [Danh mục bằng chứng](../README-vi.md)

Thư mục này chứa đầu vào công khai và kết quả đối chiếu độc lập cho quận Diên Khánh, Bắc Kinh. Kết quả chỉ áp dụng cho đúng tệp, năm và dung sai đã ghi.

| Tệp | Nội dung | Mục đích |
| --- | ---: | --- |
| [Dữ liệu LISA 2020](CHN_beijing_yanqing_2020_500m_lisa_cells.csv) | 8.333 ô | Đầu ra ứng dụng để kiểm tra láng giềng, Local Moran và FDR |
| [Dữ liệu Không gian và Thời gian 2014 đến 2020](CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv) | 8.333 ô | Đầu ra ứng dụng để kiểm tra hướng biến động và chế độ |
| [Dữ liệu NTL 2020](dien_khanh_NTL_2020_500m.csv) | 8.333 ô | Đầu ra ứng dụng cho phép đối chiếu raster |
| [Đối chiếu LISA độc lập](yanqing_lisa_independent_cell_comparison.csv) | 8.333 ô | Láng giềng, thống kê và mức ý nghĩa được tính lại |
| [Đối chiếu VIIRS độc lập](yanqing_viirs_all_8333_polygon_comparison.csv) | 8.333 ô | So bức xạ nguồn với kết quả trích xuất theo đa giác |
| [Gói kiểm tra LISA độc lập](archives/yanqing_validation_evidence.zip) | ZIP | Mã Python, bảng kết quả, tóm tắt và nhật ký chạy |
| [Ảnh VIIRS tham chiếu 2014](rasters/yanqing_viirs_2014_reference.tif) | GeoTIFF, 217 × 142 | Raster tham chiếu từ Earth Engine |

## Tính toàn vẹn

| Tệp | SHA-256 |
| --- | --- |
| `yanqing_validation_evidence.zip` | `51a662cb875ffe4bccfd3c628eeafb136aa9025bb500b5bdaa94d31b24ca5b93` |
| `yanqing_viirs_2014_reference.tif` | `637661ab304986ef19befa4c7ca62d1e9cface500862803f02ad76a4b6637c31` |

Các CSV đã chuyển vẫn giữ giá trị số nhưng có thể được chuẩn hóa kiểu xuống dòng UTF-8. Chỉ ghi nhận trùng từng byte khi mã băm tương ứng khớp.

## Kết quả được hỗ trợ và giới hạn

Dữ liệu đã lưu hỗ trợ phép đối chiếu VIIRS năm 2014 và 2020, phép đối chiếu LISA năm 2020 cùng phép tính Không gian và Thời gian giữa hai mốc tại Diên Khánh. Dữ liệu chưa chứng minh xu thế hằng năm liên tục, chưa tái lập GHSL độc lập đầy đủ và chưa chứa mọi sản phẩm của chiến dịch kiểm chứng 73 tệp. Raster nguồn còn thiếu và kết quả chạy lại chi tiết vẫn chưa có trong repo.

Phương pháp của ứng dụng nằm trong [hướng dẫn dữ liệu và phương pháp](../../../docs/README-vi.md). Trạng thái chấp nhận hiện tại được duy trì trong [hướng dẫn kiểm chứng](../../README-vi.md).
