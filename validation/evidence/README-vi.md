# Hướng dẫn bằng chứng

[English](README.md) · [Tiếng Việt](README-vi.md) · [Tình trạng kiểm chứng](../README-vi.md) · [Dữ liệu và phương pháp](../../docs/README-vi.md)

Thư mục này chứa dữ liệu và kết quả dùng để kiểm tra ứng dụng. Mỗi kết quả chỉ áp dụng cho đúng địa bàn, năm, lưới và tệp đầu vào đã nêu.

## Cách phân loại bằng chứng

Repo có nhiều loại phép kiểm. Mỗi loại trả lời một câu hỏi khác nhau, vì vậy không thể gộp tất cả thành một kết luận đạt chung.

| Mức | Ý nghĩa | Ví dụ |
| --- | --- | --- |
| Có tệp và chạy lại được | Đầu vào hoặc bảng kết quả nằm trong repo và có lệnh cục bộ để kiểm tra. | A02 tại Bảo An, bảng đối chiếu Diên Khánh, kiểm thử hồi quy nhân tạo |
| Kiểm chứng lưu trữ đã hoàn tất | Phép kiểm đã hoàn tất, còn báo cáo, danh mục, mã băm và tên các đầu vào/kết quả; checkout hiện tại không bung mọi tệp nhị phân để chạy mới. | V11 ba địa bàn và GHSL tại Thượng Hải |
| Kiểm thử hợp đồng | Một ca nhỏ có kiểm soát kiểm tra công thức, cấu trúc dữ liệu, mặt nạ hoặc đường xử lý lỗi. | Gini, Moran, FDR, NoData và bộ nhớ đệm |
| Câu hỏi còn mở | Repo chưa có đủ bằng chứng để kết luận về khoa học hoặc vận hành. | Ca A02 thật sự thiếu hỗ trợ, tải Cloud nhiều phiên, giá trị đại diện kinh tế |

## Kiểm toán phát biểu khoa học

Trích dẫn, kiểm thử mã và đối chiếu thực địa là ba loại hỗ trợ khác nhau. Bảng dưới ghi loại hỗ trợ hiện có cho các nhóm phát biểu khoa học chính trong bộ hướng dẫn. Một phương pháp có cơ sở học thuật không vì thế trở thành kết quả đã kiểm chứng thực địa cho ứng dụng này.

| Nhóm phát biểu | Cơ sở bên ngoài | Phép kiểm trong repo | Kết luận sau kiểm toán |
| --- | --- | --- | --- |
| Phép đo VIIRS và hỗ trợ quan sát | [Danh mục VIIRS của Earth Engine](https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_MONTHLY_V1_VCMSLCFG) ghi `avg_rad`, `cf_cvg`, điểm ảnh 463,83 m, khả năng có bức xạ âm, độ phủ tháng không đầy đủ và ánh sáng tạm thời chưa được lọc hết trong chuỗi Phiên bản 1. | Kiểm thử cấu trúc A02 và bản xuất Bảo An kiểm tra các trường do ứng dụng tạo ra. | Đặc tính nguồn và các trường của ứng dụng có căn cứ. Bảo An là ca toàn bộ có quan sát; hỗ trợ thiếu thực tế và nhiễu ánh sáng tạm thời vẫn chưa được kiểm tra. |
| Trích xuất raster theo tỷ lệ phủ | Baston (2023), [DOI 10.5281/zenodo.11396419](https://doi.org/10.5281/zenodo.11396419), mô tả thống kê raster và đa giác có tính phần diện tích phủ. | Kiểm thử thống kê vùng xác định và đối chiếu raster Diên Khánh đã lưu kiểm tra đường triển khai. | Trọng số theo phần diện tích đã được triển khai và có một đối chiếu thực địa trong repo. Không khẳng định một mức sai số chung cho phương án tâm điểm ảnh. |
| MAUP và hỗ trợ lưới | Openshaw (1984) cùng Fotheringham và Wong (1991), [DOI 10.1068/a231025](https://doi.org/10.1068/a231025), cho thấy độ nhạy theo quy mô và cách phân vùng. | A07 kiểm tra đường gộp khối dùng trong phép thử độ vững của ứng dụng. | Lưới đều chuẩn hóa hỗ trợ không gian nhưng không loại bỏ MAUP. Bằng chứng hiện có chưa chứng minh gộp khối tương đương với trích xuất raster mới trên lưới thô. |
| Moran, LISA và kiểm định nhiều lần | Moran (1950), [DOI 10.1093/biomet/37.1-2.17](https://doi.org/10.1093/biomet/37.1-2.17); Anselin (1995), [DOI 10.1111/j.1538-4632.1995.tb00338.x](https://doi.org/10.1111/j.1538-4632.1995.tb00338.x); Benjamini và Hochberg (1995), [DOI 10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x), cung cấp cơ sở thống kê. | Chuẩn tính tay, không gian mẫu liệt kê, kiểm thử hồi quy và đối chiếu độc lập Diên Khánh kiểm tra các phần triển khai đã chọn. | Các công thức được kiểm thử và quy tắc đã công bố có căn cứ. Cụm có ý nghĩa vẫn mô tả liên kết không gian, không phải tác động nhân quả hoặc ranh giới đô thị chính thức. |
| Ánh sáng ban đêm như biến đại diện kinh tế | Henderson và cộng sự (2012), [DOI 10.1257/aer.102.2.994](https://doi.org/10.1257/aer.102.2.994), cùng Gibson và cộng sự (2021), [DOI 10.1016/j.jdeveco.2020.102602](https://doi.org/10.1016/j.jdeveco.2020.102602), chỉ ra cả tiềm năng và giới hạn đo lường phụ thuộc bối cảnh. | Repo chưa có GDP, thu nhập, giá hoặc kết quả hộ gia đình khớp địa bàn và thời gian với các ca đã lưu. | Ứng dụng đo và mô tả bức xạ. Giá trị đại diện cho khái niệm kinh tế vẫn là câu hỏi mở; không kết quả README nào được đồng nhất NTL với GDP, phúc lợi hoặc hoạt động kinh tế nhân quả. |
| Mức đồng thuận bên ngoài với GHSL | Hồ sơ kỹ thuật JRC định nghĩa [GHS-BUILT-S](https://doi.org/10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA) và [GHS-POP](https://doi.org/10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE). | Kiểm thử bảo toàn trên lưới gốc có thể chạy lại; gói Thượng Hải đã hoàn tất được lập danh mục với raster, JSON kiểm chứng từng ô, chương trình, mã băm và báo cáo. | GHSL là biến đại diện định cư riêng, không phải chuẩn đúng cho NTL hoặc kết quả kinh tế. Kết quả Thượng Hải đã kiểm chứng nhưng chưa rõ vì cả hai khoảng rho đều chứa 0. |

## Bằng chứng hiện có
| Bằng chứng | Tệp | Kết quả có căn cứ | Giới hạn |
| --- | --- | --- | --- |
| Bảo An 2020 | [CSV 7.148 ô, JSON hiệu năng và bản tóm tắt đã kiểm tra](audit-2026-11-15/) | Mã ô không trùng; toàn bộ dòng có trạng thái đã quan sát và đủ năm trường chất lượng A02 hữu hạn. Toàn quy trình mất 46,6687 giây, trong đó A02 mất 25,0028 giây. | Một lượt có dữ liệu quan sát; chưa bao phủ ca thật sự thiếu hoặc ít quan sát. |
| A02 sau thay đổi xử lý nhiều dải | [CSV từng ô và JSON hiệu năng](a02_post_pr27/) | Mọi giá trị trong 32 cột chung khớp bản xuất 7.148 dòng trước đó; tệp sau có thêm các cột LISA. Toàn quy trình mất 37,6479 giây, trong đó A02 mất 26,4623 giây. | A02 không nhanh hơn trong lượt đo này; cần thêm các lượt chạy cùng cấu hình. |
| Diên Khánh 2014 và 2020 | [Dữ liệu từng ô, raster tham chiếu, bảng đối chiếu độc lập và chỉ số](yanqing/README-vi.md) | Hỗ trợ kết quả VIIRS, LISA và phép tính hai mốc thời gian cho 8.333 ô. | Hai mốc năm không chứng minh xu thế hằng năm liên tục. Một số raster nguồn của chiến dịch lớn hơn chưa có trong repo. |
| Thượng Hải, Bảo An và Kỳ Môn | [Ranh giới và quy trình đối chiếu độc lập](../cross_location/README-vi.md) cùng manifest phục hồi | V11 đã hoàn tất trên 17.177 ô; manifest ghi cặp raster, CSV ứng dụng, tệp từng ô biên và mã băm. | Không phải mọi tệp nhị phân lưu trữ đều được bung trong checkout; đây là giới hạn đóng gói để chạy mới, không phải kiểm chứng khoa học chưa hoàn thành. |
| Ca kiểm soát nhân tạo | [Kết quả kiểm thử A02](a02/) và bộ kiểm thử của repo | Kiểm tra hợp đồng số học, mặt nạ, cấu trúc dữ liệu và xử lý lỗi. | Kiểm thử nhân tạo không thay thế đối chiếu thực địa. |

## Vì sao cần các phép kiểm này

| Câu hỏi | Lý do | Bằng chứng sử dụng |
| --- | --- | --- |
| Có phân biệt được giá trị 0 đo được với trường hợp thiếu quan sát không? | Đầu ra cũ điền NTL thiếu bằng 0. Nếu không có trường hỗ trợ riêng, bóng tối và dữ liệu thiếu có thể bị nhầm với nhau. | Các cột A02 tại Bảo An, ca thiếu dữ liệu nhân tạo và kiểm thử cấu trúc |
| Thay đổi xử lý nhiều dải có làm đổi giá trị cũ không? | Chỉ chấp nhận thay đổi hiệu năng khi giá trị và danh tính ô được giữ nguyên. | Bản xuất Bảo An 32 cột trước và bản sau có thêm cột LISA |
| A02 có nhanh hơn không? | Tổng thời gian ngắn hơn không chứng minh riêng bước A02 đã cải thiện. | JSON thời gian từng bước trước và sau thay đổi |
| Kết quả trích xuất raster có khớp tham chiếu độc lập không? | Mã đúng vẫn có thể dùng nhầm raster, phép chiếu, mặt nạ hoặc hình học ô. | Đối chiếu raster và đa giác tại Diên Khánh cùng quy trình ba địa bàn |
| Local Moran và FDR có khớp khi tính độc lập không? | Cách dựng láng giềng, làm tròn, hạt hoán vị và đếm hai đuôi có thể đổi nhãn ý nghĩa. | Đối chiếu LISA từng ô tại Diên Khánh và kiểm thử hồi quy của repo |

## Giải thích lựa chọn phương pháp cho từng kiểm toán A01-A12

Ma trận kết quả phía dưới cho biết **đã quan sát được gì**. Bảng này giải thích thêm **vì sao phép thử trả lời được câu hỏi kiểm toán**, đâu là điểm phát hiện sai sót và vì sao không được suy rộng.

| Mã | Phương pháp và chuẩn đối chiếu | Lý do chọn và cách đọc |
| --- | --- | --- |
| A01 | Kiểm tra cây `tests/` được phân công cho hai tác vụ CI, không bỏ sót hoặc tính trùng; xác nhận trạng thái kết thúc của cả hai. | Đây là bài kiểm **mức bao phủ thực thi**, không đo đúng đắn khoa học; 100% bài đã chạy vẫn có thể bỏ sót một giả thuyết chưa viết test. |
| A02 | Kiểm tra tính duy nhất `grid_id`, các tỷ lệ `dq_*` trong [0,1], số tháng trong [0,12], trạng thái quan sát hợp logic; tạo mặt nạ thiếu dữ liệu nhân tạo để xem thống kê thay đổi. | Dữ liệu thiếu được điền 0 có thể giả tạo bóng tối. Mẫu Bảo An chỉ xác minh schema và trường hợp đủ quan sát; mô phỏng chỉ phơi lộ độ nhạy. |
| A03 | Dùng đáp án tính tay của Global Moran (`1/3`), Local I trên lưới nhỏ, láng giềng Queen, trường hợp hoán vị liệt kê được và bộ p cố định cho BH; đối chiếu mã độc lập trên Diên Khánh. | Mẫu nhỏ cô lập lỗi công thức; đối chiếu Diên Khánh thăm dò đầu ra thực. Chênh LISA có thể do làm tròn hoặc chuỗi hoán vị, không tự động là bug. |
| A04 | So Gini với `sum_i sum_j |x_i-x_j|/(2 n² mean(x))` trên mẫu hữu hạn không âm; sai số tuyệt đối `1e-12`; đầu vào không hữu hạn/âm phải bị từ chối. | Đây là một **oracle toán học độc lập**, giúp bắt bất nhất khi các nhánh tính Gini nhận mẫu khác nhau. Không thay thế chính sách xử lý radiance âm trước đó. |
| A05 | Ghi Python, phiên bản thư viện thống kê, tệp phụ thuộc và đối chiếu khả năng chạy lại. | Kết quả phụ thuộc môi trường; cố định một vài thư viện chưa tương đương khóa tất cả phụ thuộc, nên không gọi là tái lập môi trường hoàn toàn. |
| A06 | Kiểm thử đường dữ liệu giữa raster, lưới, phân tích, giao diện và tệp xuất, thay vì chỉ kiểm tra các hàm rời. | Lỗi thường xuất hiện khi ghép mô-đun; test tích hợp không chứng minh rằng mọi hành vi trong `app.py` đã được bao phủ. |
| A07 | So chẩn đoán gộp khối MAUP theo cách ứng dụng thực hiện với ý tưởng dựng lại lưới 1.000 m và trích xuất raster trực tiếp. | Trung bình của các ô 500 m, đặc biệt ô biên, không nhất thiết bằng trung bình pixel trên polygon 1.000 m mới; không nhận hai phương pháp là tương đương khi chưa đối chiếu thực. |
| A08 | Bảo toàn lượng GHSL trên pixel 100 m hệ Mollweide: `sum(quantity_pixel × area_intersection / area_pixel)`, đổi sang mật độ trên diện tích ô, rồi so rho, AUC và lấy lại mẫu theo khối. | GHSL chứa **lượng**, không phải radiance; tái lấy mẫu rồi cộng thô làm tăng giả tổng lượng. Việc sửa số học không tự biến GHSL thành chuẩn kinh tế độc lập. |
| A09 | Spearman rho cho quan hệ đơn điệu; AUC Mann-Whitney cho phân biệt nhóm NTL cao; lấy lại mẫu theo khối giữ phần nào phụ thuộc không gian. | Rho mô tả thứ hạng, AUC mô tả phân tách; các ngưỡng màu 0,4/0,6 không phải quy tắc kiểm định. Khoảng rho chứa 0 không cho phép tuyên bố tương quan khác 0. |
| A10 | Phân rã thời gian `wall time` theo bước và RSS tiến trình được lấy mẫu, so những lượt cùng cấu hình. | Tổng thời gian giảm có thể do lưới hay mạng thay vì A02; RSS lấy mẫu không phải peak chắc chắn hoặc RAM trên từng người dùng. |
| A11 | Kiểm thử tích hợp có kiểm soát, smoke test giao diện, số dòng/giá trị CSV và profiler ghi các giai đoạn. | Kiểm tra đường đi phần mềm khác với bài end-to-end có tài khoản Earth Engine và lỗi mạng thật; thiếu bài thứ hai phải ghi thiếu. |
| A12 | Kiểm tra các đường dẫn, số cặp tài liệu, dấu toán học và quy tắc định dạng; đọc thủ công để xác nhận tính tương đương ngữ nghĩa. | Link hợp lệ không bảo đảm công thức đúng, dịch đúng hoặc bằng chứng có sức nặng phù hợp. |
| V11 | So trung bình theo tỷ lệ giao pixel-raster trên **cùng polygon app** tại ba địa bàn, ghi sai số tuyệt đối từng `grid_id` và riêng ô đầy đủ/ô biên. | Dung sai `0.00005` xuất phát từ CSV NTL làm tròn 4 chữ số, không phải sai số cảm biến. Hai nhánh dùng cùng NOAA VIIRS nên đây là đối chiếu xử lý, không phải phép đo ánh sáng độc lập. |
| GADM | So GID định danh, loại hình hành chính, hình học và kết quả biên tập với GADM 4.1; không dùng tên trùng làm khóa. | Bắt lỗi gộp đơn vị khác nhau do trùng tên hoặc cấp quản lý; phù hợp bản GADM tham chiếu, không chứng nhận ranh giới pháp lý hiện tại. |

**Quy tắc chung:** nêu **cỡ mẫu, tập ô loại trừ, dung sai, seed, phương pháp lấy mẫu, phép tính gốc, dữ liệu nguồn và ngoại lệ** trước khi dùng từ “khớp”. Không suy diễn một kết quả có p-value, khoảng tin cậy hay ý nghĩa nhân quả nếu phép kiểm không thực sự tính và hiệu chuẩn đại lượng đó.

## Ma trận câu hỏi kiểm toán đầy đủ

Ma trận này hợp nhất đợt rà soát A01 đến A12 và các phép kiểm thực địa về sau. Cột kết quả chỉ nêu điều mà bằng chứng được dẫn có thể hỗ trợ.

| Mã và câu hỏi khoa học | Bằng chứng sử dụng | Cách kiểm tra và điều kiện chấp nhận | Kết quả định lượng | Giới hạn |
| --- | --- | --- | --- | --- |
| A01. CI có chạy mọi tệp kiểm thử đang được duy trì không? | [Quy trình CI](../../.github/workflows/tests.yml) và [bộ kiểm thử](../../tests/) | Tác vụ lõi chạy hai tệp thống kê nhẹ. Tác vụ thứ hai chạy phần còn lại của cây `tests/`, chỉ bỏ qua đúng hai tệp đã chạy ở tác vụ lõi. Cả hai tác vụ phải thành công. | Khoảng trống ban đầu đã được đóng khi kiểm thử Không gian và Thời gian được đưa vào CI. Kết quả kiểm tra của nhánh hiện tại là bằng chứng thực thi; con số lịch sử 54 lên 61 không được dùng làm tổng hiện tại vì bộ kiểm thử đã tăng. | CI chỉ xác nhận các đường mã đã được chạy trong môi trường cài đặt của nó. Đây không phải phép kiểm Earth Engine trực tiếp, dữ liệu thực địa hoặc tải Cloud. |
| A02. Có phân biệt được giá trị 0 đo được với thiếu hỗ trợ quan sát không? | [CSV Bảo An và bản tóm tắt đã kiểm tra](audit-2026-11-15/), [JSON độ nhạy nhân tạo](a02/synthetic_sensitivity.json), `tests/test_data_semantics.py` và `tests/test_a02_field_schema.py` | Yêu cầu mã ô không trùng, có trạng thái và chính sách rõ ràng, các trường chất lượng hữu hạn và nằm trong miền hợp lệ. Dùng ca thiếu dữ liệu có kiểm soát để xem điền 0 có làm đổi thống kê phía sau hay không. | Bảo An: 7.148/7.148 dòng ở trạng thái đã quan sát; số tháng hợp lệ trung bình từ 10 đến 12, trung bình 11,9880599727. Ca che sáu ô làm đổi trung bình, tỷ lệ ô 0, Gini, Global Moran, sáu nhãn LISA và 33 chế độ Không gian và Thời gian. | Bảo An không có dòng thật sự thiếu hỗ trợ. Ca nhân tạo chứng minh độ nhạy, không ước lượng sai lệch ngoài thực địa. |
| A03. Công thức thống kê có khớp chuẩn tham chiếu độc lập không? | `tests/test_numerical_validation_a03.py`, `tests/test_advanced_statistics_a03b.py`, `tests/test_audit_regressions.py` và [bằng chứng Diên Khánh](yanqing/README-vi.md) | So Gini với định nghĩa sai khác tuyệt đối theo từng cặp; so Global Moran Queen nhị phân với chuỗi bốn ô tính tay; kiểm tra Local I và láng giềng Queen trên lưới nhỏ; kiểm tra BH-FDR bằng p-value cố định; kiểm tra hoán vị có điều kiện bằng cách liệt kê không gian mẫu. | Chuẩn tính tay cho Global Moran là $1/3$; Local I là $[0,45;0,15;0,15;0,45]$; BH-FDR 5% bác bỏ giá trị thứ hai và thứ tư trong $[0,2;0,01;0,04;0,001]$. Diên Khánh có 8.154/8.333 nhãn LISA cuối khớp. | Kiểm thử nhỏ không xác nhận mọi dạng không gian hoặc toàn bộ phân phối hoán vị có điều kiện trên dữ liệu thực. Diên Khánh dùng NTL đã làm tròn và hạt độc lập. |
| A04. Mọi đầu ra Gini có cùng quy tắc đầu vào không? | Hàm dùng chung `ntl/ntl_distribution.py::gini`, các nơi gọi trong ứng dụng/LISA, đường Lorenz và kiểm thử số học | So mẫu hữu hạn không âm với công thức cặp đôi độc lập ở dung sai tuyệt đối $10^{-12}$; buộc đầu vào âm hoặc không hữu hạn gây lỗi mà không loại dòng. | Các ca chính xác: `[5,5,5,5]` cho 0,000000; `[0,0,10,10]` cho 0,500000; `[1,2,3,4]` cho 0,250000; mẫu rỗng và toàn 0 cho 0. Ba ca sai quy tắc gồm `-0,1`, NaN và vô cực đều gây `ValueError`. Toàn bộ CI đạt 34 kiểm thử lõi và 84 kiểm thử còn lại, tổng 118. | Đây là hợp đồng phần mềm, không phải quy tắc cho rằng bức xạ âm thô không có ý nghĩa khoa học. Quy trình đo lường vẫn phải quyết định việc cắt riêng và giữ các trường chất lượng. |
| A05. Có tái lập được môi trường phần mềm không? | `requirements.txt`, `requirements-test.txt` và quy trình CI | Ghi phiên bản Python và thư viện dùng trong CI cùng quá trình tạo bằng chứng; yêu cầu chạy lặp trong môi trường được khai báo. | Phần kiểm thử cố định ESDA 2.10.0 và libpysal 4.15.1. Phần lớn thư viện vận hành chưa cố định phiên bản; CI dùng Python 3.11 và 3.13 ở hai tác vụ. | Chưa có tệp khóa đầy đủ hoặc kết quả tương đương giữa nhiều phiên bản. Một lượt CI đạt không bảo đảm tái lập lâu dài. |
| A06. Mức liên kết giữa các phần ứng dụng đã đủ an toàn cho thay đổi chưa? | `app.py`, các mô-đun trong `ntl/` và bộ kiểm thử tích hợp | Dùng hồi quy tích hợp và cấu trúc dữ liệu để phát hiện thay đổi qua ranh giới raster, lưới, thống kê, giao diện và CSV. | Các phép tính lõi cùng nhiều đường giao diện đã có kiểm thử hồi quy; các mô-đun thống kê được tách dưới `ntl/`. | Phần điều phối lớn vẫn nằm trong `app.py`. Chưa có chỉ số nào chứng minh mọi lần tách mã sau này giữ nguyên hành vi ngoài phạm vi kiểm thử. |
| A07. Gộp khối có tương đương với trích xuất raster trực tiếp trên lưới thô không? | `ntl/robustness.py`, `tests/test_robustness.py` và phương pháp nhiều địa bàn | Phân biệt việc gộp trung bình các ô 500 m thành khối với việc dựng lại lưới 1.000 m rồi trích xuất raster. Chỉ phép so cùng dữ liệu mới xác nhận tương đương. | Ứng dụng tính đường gộp khối và mức chồng lấn HH của nó. Chưa có đối chiếu thực địa được lưu để chứng minh bằng với trích xuất trực tiếp trên lưới thô. | Kết quả MAUP là chẩn đoán độ vững cho đúng cách gộp đã triển khai, không phải kết quả chung cho mọi cách dựng lưới khác. |
| A08. Lượng GHSL có được bảo toàn và căn đúng với lưới không? | `ntl/ghsl_native.py`, `tests/test_ghsl_native_grid.py`, `tests/test_ghsl_computepixels.py` và gói Thượng Hải đã hoàn tất được ghi trong manifest phục hồi | Giữ lượng GHSL trên lưới Mollweide 100 m gốc, chuyển đa giác sang hệ tọa độ đó, nhân lượng từng điểm ảnh với tỷ lệ giao, từ chối vùng không phủ, rồi so rho, khoảng bootstrap theo khối và AUC trên các ô lõi đủ điều kiện. | Phép tái chiếu cũ tại Thượng Hải làm diện tích xây dựng tăng sai 16,51428% và dân số tăng sai 16,59686%. Sau sửa, 715 ô cho diện tích xây dựng: rho -0,0794533, khoảng [-0,220123;0,086086], AUC 0,394636; dân số: rho 0,1358105, khoảng [-0,029628;0,271008], AUC 0,576274. | Gói lưu trữ không được bung đầy đủ trong checkout hiện tại. Kết quả Thượng Hải đã hoàn tất không khái quát sang Bảo An, Kỳ Môn hoặc epoch khác. |
| A09. Ngưỡng diễn giải có phải tiêu chí chấp nhận khoa học không? | `ntl/validation.py` và kết quả GHSL Thượng Hải | Tính rho, khoảng bootstrap theo khối không gian và AUC của nhóm một phần tư cao nhất. Xem các mốc 0,4 và 0,6 là quy ước hiển thị, không phải ngưỡng kiểm định phổ quát. | Hai khoảng rho tại Thượng Hải đều chứa 0. Vì vậy mẫu nội đô này chưa chứng minh quan hệ đơn điệu khác 0 một cách tin cậy. | GHSL là biến bối cảnh, không phải chuẩn đúng của ánh sáng ban đêm hoặc biến kinh tế độc lập. AUC ở đây chỉ mang tính mô tả. |
| A10. Bộ nhớ đệm và hiệu năng có được giới hạn không? | `ntl/lisa_ui.py`, các JSON hiệu năng và kiểm thử vận hành | Giới hạn bộ nhớ đệm trong phiên, ghi thời gian từng bước cùng RSS tiến trình được lấy mẫu và chỉ so các lượt cùng cấu hình. Muốn kết luận năng lực cần nhiều phép đo đồng thời. | Bộ nhớ đệm LISA giới hạn năm bộ tham số. Đỉnh lấy mẫu tại Bảo An là 728,531 và 688,941 MiB; thời gian toàn quy trình là 46,6687 và 37,6479 giây. | RSS là số lấy mẫu của tiến trình máy chủ, không tách theo người dùng. Chưa đo năng lực nhiều người dùng hoặc giới hạn bộ nhớ chắc chắn. |
| A11. Toàn bộ quy trình có chạy từ dịch vụ trực tiếp đến tệp xuất không? | `tests/test_pipeline_integration.py`, `tests/test_ui_smoke.py`, bản xuất Bảo An và JSON hiệu năng | Kiểm tra raster sang thống kê vùng, LISA và CSV bằng đầu vào có kiểm soát; tách riêng việc đọc CSV thật và profiler từng bước. | Lượt Bảo An đã lưu ghi thành công ở cả 13 công đoạn. Hai bản xuất có 7.148 dòng và mọi giá trị trong 32 cột chung đều khớp. | Bộ kiểm thử không đăng nhập Earth Engine. Profiler và CSV chưa tạo thành phép thử có thể lặp đầy đủ từ Earth Engine qua Streamlit đến tệp xuất kèm lỗi được chủ động tạo. |
| A12. Tài liệu được duy trì có khớp mã và bằng chứng không? | [Chương trình kiểm tra tài liệu](../check_docs.mjs), sáu cặp README Anh và Việt cùng ma trận này | Kiểm tra đủ cặp hướng dẫn, liên kết nội bộ, dấu công thức và dấu câu bị cấm. Mọi số liệu phải liên kết tới tệp đã lưu hoặc nêu rõ bằng chứng còn thiếu. | Bộ tài liệu duy trì có 12 hướng dẫn trong sáu cặp song ngữ và đạt chương trình kiểm tra trên nhánh này. | Kiểm tra liên kết và định dạng không chứng minh bản dịch tương đương hoặc kết luận khoa học đúng. Vẫn cần đọc thủ công khi bằng chứng hoặc mã thay đổi. |
| V11. Trích xuất VIIRS độc lập có khớp ở các địa bàn khác nhau không? | [Quy trình nhiều địa bàn](../cross_location/README-vi.md), báo cáo V11 đã hoàn tất và manifest phục hồi | So tích phân raster Earth Engine độc lập với ô của ứng dụng ở lưới 500 m. Ô đầy đủ dùng dung sai làm tròn CSV bốn chữ số; ô cắt biên vẫn được giữ và báo cáo. Queen cùng BH-FDR được tính lại với giới hạn về hạt hoán vị. | Thượng Hải 886 ô, Bảo An 7.148 và Kỳ Môn 9.143, tổng 17.177. Toàn bộ 15.330 ô đầy đủ đạt. Trong 1.847 ô cắt biên, 1.846 ô nằm trong 0,00005 và toàn bộ nằm trong 0,0000501. | Manifest ghi đầu vào tương ứng và kết quả từng ô biên, nhưng không phải mọi tệp nhị phân lưu trữ đều được bung trong checkout. Đa giác cắt biên lấy từ bản xuất ứng dụng, không được dựng lại độc lập hoàn toàn. |
| GADM. Ranh giới Trung Quốc đã biên tập có khớp bản nguồn được chọn không? | [Hướng dẫn dữ liệu và phương pháp](../../docs/README-vi.md) cùng tệp dưới `data/` | So mã định danh được giữ lại và các trường hành chính đã ánh xạ với GADM 4.1 ở độ chính xác đã nêu; nối dữ liệu theo GID thay vì tên hiển thị. | 2.420 đơn vị đã biên tập được đối chiếu. Một bản ghi nguồn thiếu trường hành chính bị loại; `CHN.14.10.2_1` được xác định là Nam, còn tên tệp cũ giữ lại để tương thích. | Đây là đối chiếu với một bản phát hành nguồn, không xác nhận ranh giới pháp lý hiện nay hoặc mọi quốc gia. |

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

## Kiểm tra VIIRS và LISA tại ba địa bàn

**Câu hỏi và lý do.** Kết quả ở một địa bàn thí điểm có thể phụ thuộc hình học, phân bố độ sáng hoặc tỷ lệ ô biên. Thượng Hải, Bảo An và Kỳ Môn được chọn để đại diện cho nội đô, quận đô thị-công nghiệp có hình học nhiều phần và huyện ít đô thị hóa hơn.

**Bằng chứng.** Repo có ba ranh giới GADM, chương trình đối chiếu độc lập và hướng dẫn xuất Earth Engine trong [`validation/cross_location/`](../cross_location/). Manifest kiểm toán phục hồi còn ghi các CSV ứng dụng, raster VIIRS Thượng Hải và Kỳ Môn, bảng kết quả từng ô biên cùng các gói kiểm chứng có mã băm. Kết hợp với báo cáo đã giữ, đây là phép kiểm đã hoàn tất; checkout hiện tại chỉ không bung trực tiếp mọi tệp nhị phân.

**Cách kiểm tra và dung sai.** Raster tham chiếu được tích phân độc lập trên đa giác ô của ứng dụng. Ô đầy đủ phải khớp trong giới hạn làm tròn CSV bốn chữ số là 0,00005. Ô cắt biên không bị loại; ngưỡng phụ 0,0000501 giúp phân biệt ngưỡng đúng nghĩa với nhiễu số dấu phẩy động. Phần LISA dựng lại láng giềng Queen, Local I và BH-FDR, đồng thời giữ rõ tác động của NTL đã làm tròn và quy ước hạt Monte Carlo.

| Địa bàn | Toàn bộ ô | Ô đầy đủ | Ô cắt biên |
| --- | ---: | ---: | ---: |
| Thượng Hải | 886 | 706 | 180 |
| Bảo An | 7.148 | 6.131 | 1.017 |
| Kỳ Môn | 9.143 | 8.493 | 650 |
| Tổng | 17.177 | 15.330 | 1.847 |

Toàn bộ 15.330 ô đầy đủ đạt ngưỡng CSV. Trong số ô cắt biên, 1.846/1.847 ô đạt 0,00005. Tại Bảo An, `grid_id=628` so giá trị 18,8768 với 18,876850039; sai khác chỉ vượt ngưỡng đúng nghĩa $3,93\times10^{-8}$ và vẫn nằm trong 0,0000501.

**Giới hạn.** Đa giác cắt biên do ứng dụng xuất được dùng lại, nên phép so không tự dựng mọi ô từ ranh giới nguồn. Kết quả không xác nhận GHSL hoặc giá trị đại diện kinh tế. Bung lại toàn bộ đầu vào lưu trữ sẽ cải thiện khả năng chạy bằng một lệnh nhưng không thay đổi kết luận V11 đã hoàn tất.

## Kiểm tra GHSL tại Thượng Hải

**Câu hỏi và lý do.** Các dải diện tích xây dựng và dân số GHSL lưu lượng trên từng điểm ảnh nguồn. Nếu tái chiếu sang lưới khác rồi cộng như thể đó là lượng của điểm ảnh mới, tổng lượng có thể không được bảo toàn. Phép tính cũng có thể thất bại hoàn toàn nếu raster và đa giác không cùng hệ tọa độ.

**Bằng chứng.** Repo có cách tính đã sửa trên lưới gốc và các kiểm thử hồi quy nhân tạo. Manifest phục hồi lập danh mục gói Thượng Hải độc lập gồm raster GHSL lưới gốc và kiểu ứng dụng, JSON kiểm chứng từng ô, bản ghi SHA-256, chương trình kiểm chứng và báo cáo sau triển khai. Đây là kiểm chứng thực địa đã hoàn tất, dù checkout hiện tại không bung đầy đủ gói nhị phân.

**Cách kiểm tra.** Giữ raster GHSL 100 m trên lưới ESRI:54009, chuyển đa giác 500 m sang hệ tọa độ đó rồi cộng `lượng điểm ảnh × diện tích giao / 10.000 m²`. Chỉ dùng ô lõi có ít nhất 99% diện tích danh nghĩa. Phần tương quan dùng thứ hạng trung bình khi hòa, 200 lượt bootstrap theo khối 5 nhân 5 ô với hạt 42 và AUC một phần tư cao nhất theo Mann-Whitney.

Trước khi sửa bảo toàn lượng, vùng lõi chung tại Thượng Hải có 36.234 điểm ảnh nguồn nhưng 42.244 điểm ảnh đích. Tổng theo cách cũ làm diện tích xây dựng tăng từ 118.319.940 lên 137.859.621 m², sai 16,51428%; dân số tăng từ 11.674.618,205 lên 13.612.238,308, sai 16,59686%.

Sau khi sửa lưới gốc và hệ tọa độ, phép tính tổng hợp độc lập dùng 715 trong 886 ô:

| Chỉ tiêu | Diện tích xây dựng | Dân số |
| --- | ---: | ---: |
| Ô đủ điều kiện có proxy dương | 715 | 715 |
| Spearman rho | -0,0794533 | 0,1358105 |
| Khoảng bootstrap 95% | [-0,220123; 0,086086] | [-0,029628; 0,271008] |
| AUC một phần tư cao nhất | 0,394636 | 0,576274 |
| Mật độ GHSL trung vị | 353.036 m²/km² | 33.799 người/km² |

Rho, hai đầu khoảng và AUC tái lập các giá trị hiển thị của ứng dụng ở đúng mức làm tròn. Cả hai khoảng rho đều chứa 0, nên mẫu này chưa chứng minh mối liên hệ đơn điệu khác 0 một cách tin cậy.

**Giới hạn.** Kết quả độc lập xác nhận đúng gói và chỉ số Thượng Hải đã nêu; nó không làm hai đường Earth Engine Drive và `computePixels` đồng nhất cho mọi lượt chạy có thể có. Kết quả Thượng Hải không xác nhận Bảo An, Kỳ Môn hoặc epoch GHSL khác. GHSL không phải biến kết quả kinh tế trực tiếp.

## Kiểm tra G10/G18 tại Kỳ Môn 2016: số 0 có quan sát

**Câu hỏi:** ô NTL bằng 0 có thực sự không có ánh sáng quan sát, hay do trung vị radiance **âm** được cắt về 0? Đây là câu hỏi đo lường, khác với câu hỏi ô **không có dữ liệu** được xử lý ra sao.

**Nguồn và cấp độ độc lập:** CSV và GeoJSON ứng dụng gồm 9.143 `grid_id` năm 2016; raster nguồn GEE gồm ba band `raw_median`, `clipped_median`, `cf_cvg_total`; và GeoTIFF VIIRS 2020 chỉ cung cấp **hệ tọa độ pixel tham chiếu**. Hai đường xử lý cùng sử dụng sản phẩm NOAA `VCMSLCFG`; đây là đối chiếu xử lý nguồn, **không phải** phép đo cảm biến độc lập. Chương trình `reproduce_qimen_2016.py`, báo cáo, `metrics.json` và bảng theo ô thuộc gói dữ liệu chủ sở hữu lưu giữ, **chưa nằm trong checkout repo**; vì thế kết quả này chưa có khả năng chạy lại từ repo đơn lẻ.

**Cách tính và lý do chọn:**

1. Ở pixel nguồn, kiểm tra `clipped_median = max(raw_median, 0)` và `cf_cvg_total > 0` trên pixel hữu hạn. Cách này trực tiếp phân biệt **âm bị cắt**, **số 0 đúng bằng 0** và **không có quan sát**.
2. Dùng `rasterio.warp.reproject` với **nearest** đưa raster 2016 sang lưới pixel tọa độ tham chiếu 2020; không dùng ánh sáng năm 2020 trong phép tính. Đây là thử nghiệm **căn chỉnh gián tiếp**, không phải chứng minh lưới tải ảnh nội bộ của app năm 2016.
3. Chồng raster đã căn lên **polygon `grid_id` thực**; tính trung bình `max(raw_median,0)` và tỷ lệ pixel có `raw_median < 0` bằng diện tích giao pixel-đa giác. Báo sai số tuyệt đối, Spearman, số ô trong dung sai làm tròn `0.00005`; tách ô đầy đủ khỏi ô biên.
4. Kiểm tra `ntl_class` để phân biệt số 0 thật với giá trị NTL dương rất nhỏ bị CSV làm tròn thành `0.0000`. Dùng `dq_observed_fraction` và `dq_negative_fraction` để đối chiếu ngữ nghĩa hỗ trợ.

**Kết quả có thể phát biểu:** 12.202 pixel nguồn hợp lệ, trong đó 1.079 pixel trung vị âm, không pixel nào trung vị đúng bằng 0; các pixel hợp lệ đều có `cf_cvg_total > 0`. App có **49 ô** được phân loại NTL thật sự bằng 0, đều có `dq_observed_fraction=1` và `dq_negative_fraction=1`; thêm **7 ô** dương rất nhỏ bị làm tròn thành `0.0000`. Sau căn chỉnh, đối chiếu được **9.120/9.143** ô (Spearman **0,9988467**, MAE **0,00007570**), trong đó **8.532** ô đầy đủ có MAE **0,00002711**. Có **47/49** ô số 0 app đủ phủ raster; **47/47** cho kết quả nguồn bằng 0. **23 ô biên** không phủ bởi raster nguồn đã cắt ROI; **8 ô biên** có kết quả số 0 khác nhau.

**Điều chưa chứng minh:** không có file raster sáu band do chính app nhận trong lần chạy 2016 để xác nhận geotransform tuyệt đối; thiếu phủ ROI khác thiếu quan sát VIIRS; không có `no_observation` ở các ô app; và chưa đo sai lệch LISA do chính sách thiếu-versus-zero trên một cảnh thực thiếu quan sát. Do đó kết quả hỗ trợ **cơ chế số 0 do cắt radiance âm**, không đóng G10/G18 hoặc hiệu chuẩn FDR.

**Danh tính nguồn (SHA-256):** raster 2016 `28c8db4486455a6df1aa2f120ff1ff1d39f61336c80b90b0432e58cd79b4358e`; lưới raster 2020 `c3a209ff1e800b960f69a986b425941e958fe368fd421858bcf4405004d83f0f`; CSV app `447690688e1f648eee5b57e38eda0c82edc81680086a475baed5c224b7607e64`; GeoJSON app `4758265ca72ba9540ccb55bab1d179590e87f63c77c410cdc4a26b4940daf2c0`.

## Kiểm tra số học và tích hợp

**Lý do.** Đối chiếu thực địa có thể phát hiện lỗi đầu vào và hình học, còn chuẩn tham chiếu nhỏ giúp cô lập công thức cùng đường xử lý lỗi. Dự án cần cả hai loại.

Bộ kiểm thử số học gồm Global Moran Queen nhị phân tính tay bằng $1/3$, Local I $[0,45;0,15;0,15;0,45]$, láng giềng Queen trên lưới 2 nhân 2, Gini đối chiếu với định nghĩa sai khác tuyệt đối theo cặp, biên BH-FDR, đuôi hoán vị có điều kiện, giá trị hòa, xử lý thiếu một năm của Không gian và Thời gian cùng vòng xuất rồi đọc lại CSV. Phần raster kiểm tra đa giác cắt biên, mặt nạ, NoData, giá trị không hữu hạn và sự khác nhau giữa giữ thiếu với điền 0.

Các ca dùng kỳ vọng chính xác hoặc dung sai riêng được ghi trong tệp kiểm thử. Kiểm thử Monte Carlo đánh giá phân phối trong dung sai đã nêu, không buộc dùng cùng chuỗi số ngẫu nhiên với thư viện khác. Toàn bộ kiểm thử đạt chỉ có nghĩa các hợp đồng đã khai báo được chạy thành công, không có nghĩa mọi dữ liệu trực tiếp hoặc diễn giải khoa học đều đúng.

## Độ nhạy đặc tả đã ghi tại Diên Khánh

Danh mục kiểm toán đã khôi phục ghi nhận các báo cáo và tệp kết quả đầy đủ cho độ nhạy theo phép tổng hợp tháng, phép biến đổi, loại trọng số và kích thước lưới. Phần tóm tắt được giữ lại ở đây vì chúng trả lời câu hỏi diễn giải khoa học khác với kiểm tra mã cơ bản. Chương trình gốc và toàn bộ bảng từng ô chưa nằm trong repo hiện tại, nên đây là kết quả đã ghi nhưng chưa thể chạy lại công khai đầy đủ, không phải phép tính mới của nhánh này.

### Trung vị năm và trung bình năm

Với cùng 8.333 ô, hình học và quy tắc LISA, thay tổng hợp tháng năm 2020 từ trung vị năm sang trung bình năm làm NTL trung bình không trọng số tăng từ 1,4137188 lên 1,4754449, tương đương 4,366%. Gini đổi từ 0,6809244 lên 0,6861015 và Global Moran Queen nhị phân từ 0,914128499 lên 0,914558970. Số ô HH có ý nghĩa đổi từ 370 lên 385 và LL từ 2.510 xuống 2.499; Jaccard HH và LL lần lượt là 0,96104 và 0,96201. Trung vị giữ mặt nạ và trung vị điền 0 giống nhau tại toàn bộ 30.814 điểm ảnh của raster này, nên mẫu không có dữ liệu thiếu cần thiết để kiểm tra A02 ngoài thực địa.

### Dữ liệu thô, chặn P99 và log

Mọi đặc tả dùng cùng 7.733 ô tham gia, trọng số Queen, 999 hoán vị có điều kiện không hoàn lại, hạt 42, p-value hai đuôi tính cả trường hợp hòa và BH-FDR ở mức 0,05.

| Kết quả | NTL thô | Chặn P99 | Log NTL |
| --- | ---: | ---: | ---: |
| Số ô HH | 370 | 457 | 1.050 |
| Số ô LL | 2.510 | 2.510 | 2.441 |
| Toàn bộ ô có ý nghĩa sau FDR | 2.880 | 2.967 | 3.491 |
| Tỷ lệ diện tích HH | 4,617% | 5,702% | 13,102% |
| Độ lệch đầu vào | 6,312 | 4,905 | 1,928 |

Jaccard HH giữa dữ liệu thô và P99 là 0,809628; giữa dữ liệu thô và log là 0,352381. Cả 370 ô HH thô vẫn là HH ở hai đặc tả thay thế, vì vậy mức chồng lấn thô-log thấp là do log bổ sung 680 ô sáng vừa phải, không phải thay thế lõi ban đầu. Phép biến đổi làm đổi thang phân tích; nó không chỉ là lựa chọn hiển thị, và kết quả này chưa quyết định thang nào dự báo tốt nhất một biến kinh tế độc lập.

### Queen, Rook và độ phân giải lưới

| Đặc tả | Số ô lưới | Số ô kiểm định | HH | LL | Tỷ lệ diện tích HH |
| --- | ---: | ---: | ---: | ---: | ---: |
| Queen 500 m | 8.333 | 7.733 | 370 | 2.510 | 4,6169% |
| Rook 500 m | 8.333 | 7.733 | 187 | 906 | 2,3334% |
| Queen 1.000 m | 2.162 | 1.865 | 92 | 562 | 4,5919% |
| Rook 1.000 m | 2.162 | 1.865 | 46 | 210 | 2,2960% |

Tại 500 m, Jaccard HH giữa Queen và Rook là 0,5054. Giữa lưới 500 m và lưới 1.000 m được dựng mới, Jaccard theo diện tích HH là 0,6547 với Queen và 0,6864 với Rook. Vì vậy tổng diện tích HH gần nhau không đồng nghĩa ranh giới điểm nóng ổn định. Các số liệu này thuộc phép dựng lưới thô độc lập trong nghiên cứu lưu trữ; chúng không chứng minh chẩn đoán gộp khối riêng của ứng dụng tương đương về số học.

Danh tính báo cáo và tệp kết quả nằm trong [danh mục 118 bản ghi](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_FILE_MANIFEST_2026-11-15.csv). Muốn công bố rộng hơn cần khôi phục đúng chương trình, tệp chỉ số và đầu vào đã nêu, không chỉ sao chép các số tóm tắt này.

## Cách kiểm tra
Chạy từ thư mục gốc của repo:

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/check_docs.mjs
python -m pytest -q tests
```

Lệnh đầu kiểm tra CSV Bảo An, bản tóm tắt hiệu năng và các danh mục bằng chứng đã lưu. Lệnh tài liệu kiểm tra các cặp hướng dẫn Anh–Việt cùng liên kết. Bộ Python kiểm tra hợp đồng của ứng dụng; không tải dữ liệu vệ tinh mới.
