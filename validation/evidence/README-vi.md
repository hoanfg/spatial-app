# Hướng dẫn bằng chứng

[English](README.md) · [Tiếng Việt](README-vi.md) · [Tình trạng kiểm chứng](../README-vi.md) · [Dữ liệu và phương pháp](../../docs/README-vi.md)

Thư mục này chứa dữ liệu và kết quả dùng để kiểm tra ứng dụng. Mỗi kết quả chỉ áp dụng cho đúng địa bàn, năm, lưới và tệp đầu vào đã nêu.

## Bằng chứng hiện có

| Bằng chứng | Tệp | Kết quả có căn cứ | Giới hạn |
| --- | --- | --- | --- |
| Bảo An 2020 | [CSV 7.148 ô, JSON hiệu năng và bản tóm tắt đã kiểm tra](audit-2026-11-15/) | Mã ô không trùng; toàn bộ dòng có trạng thái đã quan sát và đủ năm trường chất lượng A02 hữu hạn. Toàn quy trình mất 46,6687 giây, trong đó A02 mất 25,0028 giây. | Một lượt có dữ liệu quan sát; chưa bao phủ ca thật sự thiếu hoặc ít quan sát. |
| A02 sau thay đổi xử lý nhiều dải | [CSV từng ô và JSON hiệu năng](a02_post_pr27/) | CSV NTL trùng từng byte với bản tham chiếu Bảo An đã lưu. Toàn quy trình mất 37,6479 giây, trong đó A02 mất 26,4623 giây. | A02 không nhanh hơn trong lượt đo này; cần thêm các lượt chạy cùng cấu hình. |
| Diên Khánh 2014 và 2020 | [Dữ liệu từng ô, raster tham chiếu, bảng đối chiếu độc lập và chỉ số](yanqing/README-vi.md) | Hỗ trợ kết quả VIIRS, LISA và phép tính hai mốc thời gian cho 8.333 ô. | Hai mốc năm không chứng minh xu thế hằng năm liên tục. Một số raster nguồn của chiến dịch lớn hơn chưa có trong repo. |
| Thượng Hải, Bảo An và Kỳ Môn | [Ranh giới và quy trình đối chiếu độc lập](../cross_location/README-vi.md) | Kết quả V11 đã ghi bao phủ 17.177 ô và nêu dung sai được chấp nhận cho ô đầy đủ cùng ô cắt biên. | Chưa có đủ cặp raster nguồn, kết quả từng ô và biểu đồ. |
| Ca kiểm soát nhân tạo | [Kết quả kiểm thử A02](a02/) và bộ kiểm thử của repo | Kiểm tra hợp đồng số học, mặt nạ, cấu trúc dữ liệu và xử lý lỗi. | Kiểm thử nhân tạo không thay thế đối chiếu thực địa. |

## Cách kiểm tra

Chạy từ thư mục gốc của repo:

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/check_docs.mjs
python -m pytest -q tests
```

Lệnh đầu kiểm tra CSV Bảo An, bản tóm tắt hiệu năng và các danh mục bằng chứng đã lưu. Lệnh tài liệu kiểm tra các cặp hướng dẫn Anh–Việt cùng liên kết. Bộ Python kiểm tra hợp đồng của ứng dụng; không tải dữ liệu vệ tinh mới.

## Bằng chứng cần bổ sung

- một ca A02 thực tế không có hoặc có ít quan sát;
- đầy đủ cặp raster nguồn và kết quả từng ô cho đối chiếu V11 ba địa bàn;
- bản xuất GHSL trực tiếp theo từng ô để đối chiếu độc lập;
- nhiều lượt đo hiệu năng với cùng phiên bản triển khai và cấu hình;
- chuỗi VIIRS nhiều năm liên tục và biến kinh tế độc lập để mở rộng diễn giải.
