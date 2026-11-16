# Danh mục bằng chứng

[English](README.md) · [Tiếng Việt](README-vi.md) · [Trạng thái kiểm chứng](../README-vi.md) · [Dữ liệu và phương pháp](../../docs/README-vi.md)

Đây là hướng dẫn tiếng Việt duy nhất của thư mục bằng chứng. Tài liệu cho biết repo đang giữ dữ liệu nào, mỗi dữ liệu hỗ trợ kết luận gì và nguồn nguyên bản nằm ở đâu.

| Bằng chứng | Dữ liệu đã lưu | Phạm vi |
| --- | --- | --- |
| Bảo An 2020 | CSV 7.148 ô, JSON hiệu năng, danh mục băm và bản tóm tắt đã kiểm tra trong [bộ kiểm chứng](audit-2026-11-15/) | Kiểm tra trực tiếp cấu trúc cột, giá trị, ID và mã băm đã lưu. Không chạy lại Earth Engine hoặc phép trích xuất raster. |
| Diên Khánh 2014 và 2020 | Dữ liệu từng ô, raster tham chiếu, bảng đối chiếu độc lập và chỉ số trong [thư mục Diên Khánh](yanqing/README-vi.md) | Hỗ trợ kết quả VIIRS, LISA và phép tính hai mốc thời gian đã ghi cho địa bàn này. |
| A02 | CSV từng ô và JSON hiệu năng trong [bộ A02](a02_post_pr27/) | Hỗ trợ trường hợp dữ liệu có quan sát và thời gian chạy đã ghi. Chưa bao phủ ca thiếu hỗ trợ thực tế. |
| Ca kiểm soát nhân tạo | Kết quả kiểm thử trong [thư mục kiểm soát A02](a02/) | Chỉ kiểm tra các hợp đồng số học và cấu trúc dữ liệu cụ thể. |

## Hồ sơ nguồn nguyên bản

Ba hồ sơ lớn được giữ dưới dạng văn bản thuần để GitHub không trình bày tài liệu lịch sử lẫn ngôn ngữ như hướng dẫn hiện hành:

- [Hồ sơ thực địa tổng hợp](CONSOLIDATED_FIELD_EVIDENCE_2026-11.txt)
- [Kho mười ba tài liệu lịch sử](historical_document_sources_2026-11-15.txt), kèm [chỉ mục byte](historical_document_sources_index.json)
- [Bảy mươi tám báo cáo khôi phục](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.txt), kèm danh mục JSON và CSV gốc trong cùng thư mục

Các tệp này giữ nguyên ngôn ngữ, dấu câu, công thức và kiểu xuống dòng đã nhận vì mã SHA-256 cùng phạm vi byte là bằng chứng kiểm toán. Kết luận hiện hành được cập nhật trong các cặp README tiếng Anh và tiếng Việt, không nhân bản thành nhiều bản đọc riêng.

## Kiểm tra

Chạy tại thư mục gốc của repo:

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/audit_docs_archive.mjs
node validation/check_docs.mjs
```

Hai lệnh đầu kiểm tra byte và chỉ mục đã lưu. Lệnh kiểm tra tài liệu bảo đảm đúng cặp README hiện hành, liên kết, tiêu đề theo từng ngôn ngữ, dấu câu và dấu công thức cơ bản.
