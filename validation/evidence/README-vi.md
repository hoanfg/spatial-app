# Hướng dẫn bằng chứng

[English](README.md) · [Tiếng Việt](README-vi.md) · [Tình trạng kiểm chứng](../README-vi.md) · [Dữ liệu và phương pháp](../../docs/README-vi.md)

Thư mục này chứa dữ liệu và kết quả dùng để kiểm tra ứng dụng. Mỗi kết quả chỉ áp dụng cho đúng địa bàn, năm, lưới và tệp đầu vào đã nêu.

## Bằng chứng hiện có
| Bằng chứng | Tệp | Kết quả có căn cứ | Giới hạn |
| --- | --- | --- | --- |
| Bảo An 2020 | [CSV 7.148 ô, JSON hiệu năng và bản tóm tắt đã kiểm tra](audit-2026-11-15/) | Mã ô không trùng; toàn bộ dòng có trạng thái đã quan sát và đủ năm trường chất lượng A02 hữu hạn. Toàn quy trình mất 46,6687 giây, trong đó A02 mất 25,0028 giây. | Một lượt có dữ liệu quan sát; chưa bao phủ ca thật sự thiếu hoặc ít quan sát. |
| A02 sau thay đổi xử lý nhiều dải | [CSV từng ô và JSON hiệu năng](a02_post_pr27/) | Mọi giá trị trong 32 cột chung khớp bản xuất 7.148 dòng trước đó; tệp sau có thêm các cột LISA. Toàn quy trình mất 37,6479 giây, trong đó A02 mất 26,4623 giây. | A02 không nhanh hơn trong lượt đo này; cần thêm các lượt chạy cùng cấu hình. |
| Diên Khánh 2014 và 2020 | [Dữ liệu từng ô, raster tham chiếu, bảng đối chiếu độc lập và chỉ số](yanqing/README-vi.md) | Hỗ trợ kết quả VIIRS, LISA và phép tính hai mốc thời gian cho 8.333 ô. | Hai mốc năm không chứng minh xu thế hằng năm liên tục. Một số raster nguồn của chiến dịch lớn hơn chưa có trong repo. |
| Thượng Hải, Bảo An và Kỳ Môn | [Ranh giới và quy trình đối chiếu độc lập](../cross_location/README-vi.md) | Kết quả V11 đã ghi bao phủ 17.177 ô và nêu dung sai được chấp nhận cho ô đầy đủ cùng ô cắt biên. | Chưa có đủ cặp raster nguồn, kết quả từng ô và biểu đồ. |
| Ca kiểm soát nhân tạo | [Kết quả kiểm thử A02](a02/) và bộ kiểm thử của repo | Kiểm tra hợp đồng số học, mặt nạ, cấu trúc dữ liệu và xử lý lỗi. | Kiểm thử nhân tạo không thay thế đối chiếu thực địa. |

## Vì sao cần các phép kiểm này

| Câu hỏi | Lý do | Bằng chứng sử dụng |
| --- | --- | --- |
| Có phân biệt được giá trị 0 đo được với trường hợp thiếu quan sát không? | Đầu ra cũ điền NTL thiếu bằng 0. Nếu không có trường hỗ trợ riêng, bóng tối và dữ liệu thiếu có thể bị nhầm với nhau. | Các cột A02 tại Bảo An, ca thiếu dữ liệu nhân tạo và kiểm thử cấu trúc |
| Thay đổi xử lý nhiều dải có làm đổi giá trị cũ không? | Chỉ chấp nhận thay đổi hiệu năng khi giá trị và danh tính ô được giữ nguyên. | Bản xuất Bảo An 32 cột trước và bản sau có thêm cột LISA |
| A02 có nhanh hơn không? | Tổng thời gian ngắn hơn không chứng minh riêng bước A02 đã cải thiện. | JSON thời gian từng bước trước và sau thay đổi |
| Kết quả trích xuất raster có khớp tham chiếu độc lập không? | Mã đúng vẫn có thể dùng nhầm raster, phép chiếu, mặt nạ hoặc hình học ô. | Đối chiếu raster và đa giác tại Diên Khánh cùng quy trình ba địa bàn |
| Local Moran và FDR có khớp khi tính độc lập không? | Cách dựng láng giềng, làm tròn, hạt hoán vị và đếm hai đuôi có thể đổi nhãn ý nghĩa. | Đối chiếu LISA từng ô tại Diên Khánh và kiểm thử hồi quy của repo |

## Kiểm tra hỗ trợ quan sát tại Bảo An

**Lý do.** A02 được bổ sung để người nghiên cứu phân biệt NTL bằng 0 do đo được với NTL bằng 0 do thiếu hỗ trợ quan sát.

**Cách kiểm tra.** Lệnh bằng chứng đọc toàn bộ CSV năm 2020, lưới 500 m. Lệnh yêu cầu 7.148 `grid_id` không trùng, `dq_status=observed`, `dq_stat_missing=false`, chính sách `legacy_zero_fill` và giá trị hữu hạn ở cả năm trường chất lượng. Các tỷ lệ phải thuộc $[0,1]$ và số tháng hợp lệ trung bình thuộc $[0,12]$.

**Kết quả.**

- 7.148/7.148 dòng đạt kiểm tra cấu trúc.
- `dq_observed_fraction` bằng 1 ở mọi dòng.
- Tỷ lệ giá trị âm, giá trị 0 đo được và ít tháng đều bằng 0 ở mọi dòng.
- Số tháng hợp lệ trung bình nằm từ 10 đến 12, trung bình 11,9880599727.
- Bản xuất sau vẫn có 7.148 dòng. Mọi giá trị trong 32 cột chung khớp hoàn toàn với bản trước; các trường bổ sung là kết quả LISA.

**Giới hạn.** Đây là trường hợp toàn bộ đều có quan sát. Kết quả xác nhận A02 có thể tạo đủ trường, nhưng chưa chứng minh một điểm ảnh thực sự thiếu hoặc ít quan sát được phân loại đúng.

## So sánh hiệu năng

**Lý do.** Thay đổi nhiều dải nhắm tới việc A02 phải duyệt raster nhiều lần. Vì vậy cần tách thời gian A02 khỏi tổng thời gian và khỏi bước dựng lưới hoặc tính NTL.

| Chỉ tiêu | Lượt trước | Lượt sau | Diễn giải |
| --- | ---: | ---: | --- |
| Toàn quy trình | 46,6687 giây | 37,6479 giây | Lượt sau ngắn hơn 9,0208 giây |
| Dựng lưới | 9,7399 giây | 5,0124 giây | Một bước khác cũng ngắn hơn |
| Trung bình vùng NTL | 9,6193 giây | 4,4589 giây | Một bước khác cũng ngắn hơn |
| Chất lượng ô A02 | 25,0028 giây | 26,4623 giây | Bước mục tiêu dài hơn 1,4595 giây trong lượt này |
| Đỉnh tiến trình lấy mẫu | 728,531 MiB | 688,941 MiB | Đỉnh lấy mẫu thấp hơn, không phải giới hạn bộ nhớ chắc chắn |

Cả hai lượt đều thành công, nhưng mỗi bên chỉ có một phép đo và hồ sơ trước không ghi mã commit. Vì vậy bằng chứng chỉ hỗ trợ kết luận “chưa chứng minh A02 tăng tốc”, không đủ để kết luận suy giảm hiệu năng chung hoặc năng lực tối đa.

## Độ nhạy với dữ liệu thiếu nhân tạo

**Lý do.** CSV Bảo An không có dòng thiếu hỗ trợ nên không cho thấy hệ quả thống kê của việc coi dữ liệu thiếu là 0.

Ca nhân tạo 36 ô che sáu ô. So với dữ liệu đầy đủ, chính sách điền 0 làm trung bình NTL đổi từ 10,9444 xuống 9,1944, tỷ lệ ô bằng 0 từ 0,0278 lên 0,1944, Gini từ 0,3054 lên 0,4289 và Global Moran Queen nhị phân từ 0,7319 xuống 0,6210. Trong ví dụ dựng sẵn, sáu nhãn LISA và 33 chế độ Không gian và Thời gian thay đổi.

Đây là phản ví dụ chẩn đoán, không phải ước lượng sai lệch ngoài thực địa. Kết quả giải thích vì sao phải xuất trường hỗ trợ quan sát và vì sao ca thiếu hỗ trợ thực vẫn là bước tiếp theo.

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
