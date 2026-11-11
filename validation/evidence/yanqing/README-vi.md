# Bằng chứng kiểm định Yanqing: gói tài liệu tái lập (reproducibility package)

Thư mục này chứa các dữ liệu xuất nguồn và các sản phẩm so sánh độc lập cho quá trình kiểm định **Quận Yanqing (Diên Khánh), Bắc Kinh, Trung Quốc** của `spatial-app`. Đây là bằng chứng, không phải lời khẳng định rằng mọi tuyên bố về thống kê hay kinh tế đều đã được xác minh.

## Nội dung kho lưu trữ hiện tại

| Tệp | Số lượng bản ghi / loại | Kiểm định |
|---|---:|---|
| [Xuất dữ liệu LISA 2020](CHN_beijing_yanqing_2020_500m_lisa_cells.csv) | 8.333 ô | Kết quả đầu ra từ ứng dụng, nguồn cho kiểm tra láng giềng/Local Moran/FDR |
| [Xuất dữ liệu Không-Thời gian 2014→2020](CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv) | 8.333 ô | Kết quả đầu ra từ ứng dụng, nguồn cho kiểm tra hướng và phân vị |
| [Xuất dữ liệu NTL theo ô năm 2020](dien_khanh_NTL_2020_500m.csv) | 8.333 ô | Kết quả đầu ra từ ứng dụng, nguồn cho so sánh điểm ảnh với đa giác (pixel-to-polygon) |
| [So sánh từng ô LISA độc lập](yanqing_lisa_independent_cell_comparison.csv) | 8.333 ô | Chứa các so sánh tính toán lại về láng giềng / thống kê / độ ý nghĩa |
| [Kết quả pixel-to-polygon 2020 độc lập](yanqing_viirs_all_8333_polygon_comparison.csv) | 8.333 ô | Bảng so sánh bức xạ nguồn và dữ liệu trích xuất đa giác |
| [Mã nguồn và kết quả LISA độc lập](archives/yanqing_validation_evidence.zip) | ZIP | Gói kiểm định LISA độc lập gốc gồm script Python, CSV và các chỉ số |
| [Ảnh tham chiếu VIIRS 2014](rasters/yanqing_viirs_2014_reference.tif) | GeoTIFF, 217 × 142 | Ảnh raster tham chiếu chưa qua chỉnh sửa từ Earth Engine |

Các dữ liệu xuất CSV nguồn trong kho lưu trữ này đã được chuẩn hóa về định dạng UTF-8 không có BOM khi truyền tải, đồng thời giữ nguyên các giá trị số. Định danh Git blob và kích thước tệp được ghi lại dưới đây để so sánh minh bạch ở cấp độ byte. Tệp CSV so sánh 2020 được sao chép dưới dạng xuất văn bản và có thể khác biệt ở cấp độ byte so với tệp gốc; không được đại diện tệp này là trùng khớp hoàn toàn từng bit (bit-for-bit).

| Tệp | Git blob SHA-1 | Số byte trong kho lưu trữ |
|---|---|---:|
| `CHN_beijing_yanqing_2020_500m_lisa_cells.csv` | `45823384dbaccd4f5848152897d4c36aee6333ab` | 2.616.153 |
| `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv` | `614433fcd90edfb155c6034467dc2309a9ea255e` | 3.533.025 |
| `dien_khanh_NTL_2020_500m.csv` | `df88c819f435818a79c7f91ea4011a68f9220fce` | 1.556.802 |
| `yanqing_lisa_independent_cell_comparison.csv` | `13e8c0611543c2d0775a353a09f0af075e1f0618` | 813.039 |
| `yanqing_validation_evidence.zip` | `81b9c84095ee3e50960ab6f424e8b4829955ebb5` | 184.943 |
| `yanqing_viirs_2014_reference.tif` | `e52c812adac823d84f6dbd6b116e54e80d271cec` | 140.603 |

## Tính toàn vẹn của tệp lưu trữ

```text
yanqing_validation_evidence.zip
SHA-256: 51a662cb875ffe4bccfd3c628eeafb136aa9025bb500b5bdaa94d31b24ca5b93

yanqing_viirs_2014_reference.tif
SHA-256: 637661ab304986ef19befa4c7ca62d1e9cface500862803f02ad76a4b6637c31
```

Ví dụ kiểm tra tính toàn vẹn từ thư mục gốc của kho lưu trữ:

```bash
python -c "import hashlib,pathlib; p=pathlib.Path('validation/evidence/yanqing/archives/yanqing_validation_evidence.zip'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

Tệp ZIP LISA chứa mã nguồn tính toán độc lập (`validate_yanqing_lisa.py`), bảng kết quả đầu ra, tóm tắt kết quả và nhật ký thực thi. Để chạy lại, giải nén tệp lưu trữ và đặt tệp CSV ứng dụng LISA gốc bên cạnh script, hoặc cấu hình đường dẫn đầu vào của script sao cho phù hợp.

## Gói chiến dịch đầy đủ và các tệp đính kèm công khai còn thiếu

Chiến dịch kiểm định độc lập hoàn chỉnh cũng đã tạo ra một tệp ZIP hợp nhất gồm **73 tệp / 5.554.282 byte**, bao gồm tất cả các script cần thiết, bảng so sánh, hình học GADM và các tệp GeoTIFF VIIRS nguồn, cùng với `EVIDENCE_MANIFEST.json` chứa các mã băm SHA-256 cho từng tệp thành phần.

```text
spatial_app_2026_11_11_validation_evidence_complete.zip
SHA-256: 95b3874d4253eec2269f2477b648a067fb14d1c94be54bc0ed38f8795599260c
```

**QUAN TRỌNG: Tệp ZIP hợp nhất này hiện chưa được lưu trữ trên kho lưu trữ GitHub này.** Tệp hiện có sẵn dưới dạng tệp đính kèm có thể tải xuống trong cuộc trò chuyện kiểm định. Việc tái lập độc lập từ bên thứ ba đối với mọi kết quả từ raster sang lưới (raster-to-grid) và các thông số kỹ thuật thay thế vẫn **chưa hoàn tất** cho đến khi một bản sao lâu dài của tệp ZIP hoàn chỉnh (hoặc một tệp tương đương đã xác minh mã băm) được xuất bản. Đừng vội đánh dấu toàn bộ kho lưu trữ bằng chứng này là có thể thu thập độc lập từ GitHub.

Các tệp đang chờ tải lên bao gồm các đa giác lưới tái thiết có độ chính xác đầy đủ, raster tham chiếu VIIRS 2020, bản so sánh điểm ảnh theo ô hoàn chỉnh năm 2014, các script chạy lại về đo lường/biến đổi/không gian/thời gian và toàn bộ kết quả đầu ra của chúng. Các tệp này nằm trong gói hoàn chỉnh được nêu ở trên, nhưng sự vắng mặt của chúng trên kho lưu trữ công khai phải được ghi rõ ràng.

## Diễn giải và trạng thái bằng chứng

- **LISA:** CSV nguồn, các so sánh độc lập theo ô và mã kiểm định có sẵn tại đây.
- **VIIRS 2014:** CSV Không-Thời gian nguồn và TIFF tham chiếu hàng năm có sẵn tại đây; hình học đa giác độc lập và so sánh theo ô chưa được xuất bản đầy đủ tại đây.
- **VIIRS 2020:** CSV nguồn và so sánh theo ô có sẵn tại đây; TIFF tham chiếu và các script tái thiết chưa được lưu trữ công khai tại đây.
- **Độ nhạy đo lường/biến đổi/không gian/thời gian:** phương pháp và kết quả chi tiết nằm trong hai phiên bản đặc tả kỹ thuật, trong khi các sản phẩm có thể thực thi đầy đủ vẫn cần gói hợp nhất.
- **GHSL:** các chỉ số chất lượng do ứng dụng báo cáo chỉ là sơ bộ và chưa được tái lập độc lập từ các raster GHSL gốc.
- **Cấu trúc kinh tế và hiệu suất đám mây:** chưa được kiểm định đạt mức độ hoàn thiện để xuất bản.

Phương pháp luận liên quan: `docs/VALIDATION MASTER.md` (tiếng Anh), `docs/VALIDATION MASTER-vi.md` (tiếng Việt). Các lần tải lên bằng chứng trong tương lai nên cập nhật chỉ mục này và cả hai tài liệu cùng lúc.