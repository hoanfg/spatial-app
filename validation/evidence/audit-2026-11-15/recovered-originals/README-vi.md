# Danh mục kiểm chứng đã khôi phục

[English](README.md) · [Tiếng Việt](README-vi.md) · [Danh mục bằng chứng](../../README-vi.md)

Thư mục này ghi lại phần danh mục có thể khôi phục từ đợt kiểm chứng ngày 15 tháng 11 năm 2026. Tài liệu này thay cho bản ghép nguyên văn dài 5.340 dòng, trong đó lặp nhiều ghi chú chuẩn bị, hướng dẫn mở PR và nhiều bản sao của cùng một báo cáo. Các đoạn điều phối đó không phải kết quả khoa học nên không được giữ như tài liệu hiện hành.

## Dữ liệu được giữ lại

| Tệp | Mục đích | Giá trị kiểm chứng |
| --- | --- | --- |
| [Danh mục JSON](SPATIAL_APP_AUDIT_EVIDENCE_MANIFEST_2026-11-15.json) | Siêu dữ liệu của 118 tệp trực tiếp và 271 thành viên từng được ghi trong các tệp ZIP lịch sử | Ghi tên, kích thước, mã băm và thông tin nguồn theo danh mục đã cung cấp |
| [Danh mục CSV](SPATIAL_APP_AUDIT_FILE_MANIFEST_2026-11-15.csv) | Bảng của cùng 118 tệp trực tiếp | Cho phép đối chiếu tự động với danh mục JSON |
| [Chương trình kiểm tra gốc](verify_spatial_app_audit_archive.py) | Công cụ đi kèm kho bằng chứng riêng | Chỉ kiểm tra đầy đủ khi có tệp ZIP gốc và chỉ mục phạm vi byte |
| [Biên nhận khôi phục lịch sử](recovery_receipt.json) | Ghi kích thước và mã băm của các tệp khôi phục đã nhận | Được giữ làm siêu dữ liệu nguồn; bản ghép nguyên văn đã bỏ không còn được kiểm tra trong repo |

Repo không có toàn bộ raster, chương trình, ảnh chụp, biểu đồ hoặc thành viên ZIP được liệt kê. Một dòng trong danh mục không có nghĩa dữ liệu tương ứng đang được công bố tại đây.

## Kết quả có thể giữ lại từ các báo cáo

| Hạng mục | Kết luận có căn cứ | Giới hạn |
| --- | --- | --- |
| Đối chiếu V11 nhiều địa bàn | Báo cáo lịch sử ghi 17.177 ô tại nội đô Thượng Hải, Bảo An và Kỳ Môn. Các ô đầy đủ đạt dung sai CSV bốn chữ số thập phân; 1.846/1.847 ô cắt biên đạt ngưỡng chặt 0,00005 và toàn bộ đạt 0,0000501. | Repo chưa có cặp raster nguồn, toàn bộ kết quả đối chiếu từng ô và biểu đồ. |
| Siêu dữ liệu A02 tại Bảo An | CSV công khai có 7.148 dòng, mã ô không trùng, toàn bộ ở trạng thái đã quan sát và đủ năm trường chất lượng hữu hạn. | Chỉ bao phủ trường hợp có dữ liệu; chưa kiểm tra ca thật sự thiếu hoặc ít quan sát. |
| Hiệu năng A02 | Mốc lịch sử ghi 46,6687 giây cho toàn quy trình, 25,0028 giây cho A02 và đỉnh RSS lấy mẫu 728,531 MiB. | Đây là một lượt trước tối ưu, không có mã commit; không phải cam kết năng lực hay bằng chứng tăng tốc. |
| GHSL tại Thượng Hải | Báo cáo lịch sử ghi nhận việc sửa phép cộng lượng trên lưới nguồn và phép đối chiếu tổng hợp độc lập khớp mức làm tròn của giao diện trên 715 ô lõi đủ điều kiện. | Chưa có bản xuất GHSL trực tiếp theo từng ô. Biểu đồ Bảo An và Kỳ Môn không thay thế phép kiểm từng ô độc lập. |
| Diên Khánh | Các báo cáo khôi phục bao phủ VIIRS, LISA, độ nhạy đo lường, phép biến đổi, độ vững không gian và phép tính hai mốc thời gian. | Dữ liệu công khai có thể dùng lại và giới hạn hiện tại nằm trong [hướng dẫn bằng chứng Diên Khánh](../../yanqing/README-vi.md). |

Trạng thái chấp nhận hiện tại được duy trì trong [hướng dẫn kiểm chứng](../../../README-vi.md). Khi cùng đầu vào và phạm vi, bằng chứng mới hơn thay cho nhận định ở bản chuẩn bị cũ. Đề xuất lịch sử, danh sách lệnh hoặc hướng dẫn mở PR không được coi là kết quả.

## Phép kiểm có thể chạy

Chạy từ thư mục gốc của repo:

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/check_docs.mjs
```

Lệnh đầu kiểm tra dữ liệu Bảo An đang công bố và đối chiếu hai danh mục JSON/CSV. Lệnh này không tái tạo tệp riêng còn thiếu và không chạy Earth Engine.
