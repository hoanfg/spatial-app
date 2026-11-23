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

## Phương pháp định lượng và quy tắc diễn giải

**1. Sai số raster trên đa giác.** Lấy trung bình theo diện tích giao raster VIIRS với từng polygon, ghép bằng `grid_id`, so với `ntl_mean` app và tính `e_i = |NTL_ref_i - NTL_app_i|`. **Vì sao:** sai số cục bộ, nhất là ô biên, có thể bị hệ số tương quan toàn vùng che lấp. Ngưỡng `0.00005` xuất phát từ mức làm tròn bốn chữ số của CSV, **không** phải giới hạn sai số cảm biến.

**2. Local Moran và tính ngẫu nhiên.** Xây Queen trên tâm ô 500 m, chuẩn hóa NTL cho tập ô tham gia và tính `I_i = z_i × mean(z_neighbor) / [sum(z²)/(m-1)]`. Giữ ô `i` cố định, tráo ngẫu nhiên các giá trị ở tập còn lại, lấy mẫu không hoàn lại; dùng quy tắc hai đuôi kể cả trường hợp hòa, hiệu chỉnh `(count+1)/(B+1)`, rồi BH-FDR trên đúng họ kiểm định. **Vì sao:** các bước chuẩn hóa, chọn hàng xóm, tính p và đa kiểm định có thể sai độc lập dù NTL đúng. Dữ liệu kiểm chứng dùng `ntl_mean` **đã làm tròn** và RNG riêng nên 179 khác biệt nhãn không thể được quy ngay cho sai số lõi.

**3. Hai mốc thời gian.** So `NTL_2020 - NTL_2014` theo đơn vị bức xạ và so **riêng** thay đổi `log1p(NTL)` đã chuẩn hóa từng năm cùng độ trễ láng giềng. **Vì sao:** một ô có thể tăng ánh sáng tuyệt đối nhưng giảm **vị thế tương đối**. Vì thế nhãn `4_Synchronized_Decline` không được diễn giải tự động thành giảm ánh sáng hoặc suy giảm kinh tế.

**4. Tái lập và giới hạn.** SHA-256 chỉ nhận dạng tệp; để tái lập thống kê cần đúng polygon, raster, phương pháp mặt nạ, seed và cách tính p. Raster tham chiếu thô 2020 không nằm trong thư mục này, nên đối chiếu raster 2020 hiện dựa trên **bảng từng ô đã lưu**, không phải một phép chạy lại nguồn từ đầu. Dữ liệu 2014 không có đủ dải hỗ trợ quan sát để suy ra đúng/sai của chính sách thiếu dữ liệu.

## Kết quả

| Phép kiểm | Kết quả | Diễn giải |
| --- | --- | --- |
| Đối chiếu đa giác VIIRS 2020 | 8.332/8.333 ô nằm trong ngưỡng 0,00005. Sai số tuyệt đối trung bình là 0,0000250270. Sai số lớn nhất là 0,0000643242 tại ô biên `grid_id=349`. | Kết quả khớp ở mức chính xác CSV, trừ một ô biên vượt ngưỡng nhưng vẫn được giữ lại. |
| Nhãn LISA cuối | 8.154/8.333 nhãn khớp; 7.733 ô tham gia LISA và 600 ô bị che biên. | Có 179 khác biệt được ghi đầy đủ: 80 trường hợp Không ý nghĩa thành Low-Low, 74 Low-Low thành Không ý nghĩa, 15 High-High thành Không ý nghĩa và 10 Không ý nghĩa thành High-High. |
| Local I | Sai khác tuyệt đối lớn nhất trong các cặp Local I có giá trị là 0,0001680453. | Bảng dùng NTL đã làm tròn nên không phải phép so đồng nhất ở độ chính xác đầy đủ. |
| Chế độ Không gian và Thời gian | 1.456 Tăng trưởng cộng hưởng; 75 Bóng tích tụ; 194 Tiên phong mới nổi; 4.711 Cùng giảm vị thế tương đối; 1.897 Bị loại hoặc ổn định. | Đây là nhóm mô tả hai mốc, không phải kết quả nhân quả hoặc nhãn ý nghĩa hoán vị. |
| Siêu dữ liệu raster tham chiếu 2014 | Dữ liệu ghi 30.814 điểm ảnh hữu hạn, một điểm ảnh âm và không có điểm ảnh bằng 0. | Raster cũ không có dải đếm quan sát nên chưa biết mức hỗ trợ theo tháng. |

## Diễn giải thay đổi giữa hai mốc

CSV Không gian và Thời gian đã lưu cho phép kiểm tra riêng thay đổi bức xạ tuyệt đối. NTL trung bình theo ô tăng từ 0,4451583 năm 2014 lên 1,4137191 năm 2020. Trong toàn bộ 8.333 ô, 8.221 ô tăng và 112 ô giảm; không có ô bằng nhau ở mức chính xác của tệp xuất.

Mã chế độ dựa trên thay đổi của `log1p(NTL)` đã chuẩn hóa riêng từng năm cùng độ trễ không gian của nó. Vì vậy, mã này đo thay đổi vị thế tương đối chứ không nhất thiết là thay đổi bức xạ thô. Trong 4.711 ô mang mã `4_Synchronized_Decline`, có 4.624 ô tăng NTL tuyệt đối và 87 ô giảm. Cách đọc phù hợp là cùng giảm vị thế tương đối. Kết quả không chứng minh 4.711 ô bị mất ánh sáng hoặc suy giảm kinh tế.

Lệnh kiểm tra bằng chứng tính lại trực tiếp các số đếm này từ CSV đã lưu. Phép so vẫn chỉ có hai mốc, dùng giá trị xuất đã làm tròn và không cho biết diễn biến trong các năm ở giữa.

## Tính toàn vẹn

| Tệp | SHA-256 |
| --- | --- |
| `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv` | `56450adc6f46ce06f7fa9b68ebbfdd704b8e3bd1445ec0be32809d3cd98d198c` |
| `CHN_beijing_yanqing_2020_500m_lisa_cells.csv` | `37186205051561607d611597a80cc3ce3cd22ec2cc201d9c9c842e23f3a87ec6` |
| `dien_khanh_NTL_2020_500m.csv` | `0d7f29127621e1964c338bd97e62544e342a4377ac830821bdbef0bee124206b` |
| `yanqing_lisa_independent_cell_comparison.csv` | `83fc8d94cc2badc785ba9fdbbe85be3619462afdf419a35cd47090653bca4bdd` |
| `yanqing_viirs_all_8333_polygon_comparison.csv` | `c5af295ea01f9f927c133d8fb5596ab8fd4848334d9ea33046c63df248174250` |
| `yanqing_validation_evidence.zip` | `51a662cb875ffe4bccfd3c628eeafb136aa9025bb500b5bdaa94d31b24ca5b93` |
| `yanqing_viirs_2014_reference.tif` | `637661ab304986ef19befa4c7ca62d1e9cface500862803f02ad76a4b6637c31` |

Các mã băm này định danh đúng byte đang được lưu trong repo. Một lần chạy lại phải báo mã khác nếu công cụ viết lại kiểu xuống dòng hoặc cách tuần tự hóa, kể cả khi giá trị số vẫn bằng nhau.

## Giới hạn

- Repo không có raster tham chiếu thô năm 2020 đã dùng để tạo bảng đối chiếu đa giác.
- Raster năm 2014 không có dải đếm quan sát theo tháng nên không kiểm tra được ngữ nghĩa hỗ trợ A02.
- Giá trị LISA độc lập dùng đầu vào CSV đã làm tròn và chuỗi hoán vị độc lập.
- Hai mốc năm không tạo thành xu thế hằng năm liên tục.
- Các tệp này không tái lập GHSL và không chứng minh NTL là một kết quả kinh tế hợp lệ.

Phương pháp của ứng dụng nằm trong [hướng dẫn dữ liệu và phương pháp](../../../docs/README-vi.md). Trạng thái chấp nhận hiện tại được duy trì trong [hướng dẫn kiểm chứng](../../README-vi.md).
