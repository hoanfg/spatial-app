# Danh mục bằng chứng

[English](README.md) · [Tiếng Việt](README-vi.md) · [Trạng thái kiểm chứng](../README-vi.md) · [Dữ liệu và phương pháp](../../docs/README-vi.md)

Đây là hướng dẫn tiếng Việt của thư mục bằng chứng. Tài liệu cho biết repo đang giữ dữ liệu nào và mỗi dữ liệu hỗ trợ kết luận gì.

| Bằng chứng | Dữ liệu đã lưu | Phạm vi |
| --- | --- | --- |
| Bảo An 2020 | CSV 7.148 ô, JSON hiệu năng, danh mục băm và bản tóm tắt đã kiểm tra trong [bộ kiểm chứng](audit-2026-11-15/) | Kiểm tra trực tiếp cấu trúc cột, giá trị, ID và mã băm đã lưu. Không chạy lại Earth Engine hoặc phép trích xuất raster. |
| Diên Khánh 2014 và 2020 | Dữ liệu từng ô, raster tham chiếu, bảng đối chiếu độc lập và chỉ số trong [thư mục Diên Khánh](yanqing/README-vi.md) | Hỗ trợ kết quả VIIRS, LISA và phép tính hai mốc thời gian đã ghi cho địa bàn này. |
| A02 | CSV từng ô và JSON hiệu năng trong [bộ A02](a02_post_pr27/) | Hỗ trợ trường hợp dữ liệu có quan sát và thời gian chạy đã ghi. Chưa bao phủ ca thiếu hỗ trợ thực tế. |
| Ca kiểm soát nhân tạo | Kết quả kiểm thử trong [thư mục kiểm soát A02](a02/) | Chỉ kiểm tra các hợp đồng số học và cấu trúc dữ liệu cụ thể. |

## Hồ sơ nguồn đã khôi phục

Các bản văn bản thuần trước đây lặp lại báo cáo đã lỗi thời, trộn hai ngôn ngữ và giữ cả hướng dẫn chuẩn bị PR không có giá trị khoa học. Phần kết luận hữu ích đã được đưa vào cặp README này, hướng dẫn kiểm chứng và [danh mục kiểm chứng đã khôi phục](audit-2026-11-15/recovered-originals/README-vi.md).

Danh mục JSON, CSV, biên nhận khôi phục và các chỉ mục byte gốc vẫn được giữ làm siêu dữ liệu nguồn. Các bằng chứng CSV, JSON, raster và ZIP được chọn vẫn nằm trong thư mục theo chủ đề. Repo không nhận là đang giữ toàn bộ tệp riêng được nhắc trong danh mục lịch sử; chỉ mục byte được giữ cũng không được coi là có thể chạy khi không còn bản ghép cũ.

## Kiểm tra

Chạy tại thư mục gốc của repo:

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/check_docs.mjs
```

Lệnh bằng chứng kiểm tra dữ liệu Bảo An đã nộp và đối chiếu danh mục JSON với CSV. Lệnh tài liệu bảo đảm đúng các cặp README được duy trì, liên kết, tiêu đề theo từng ngôn ngữ, dấu câu và dấu công thức cơ bản.
