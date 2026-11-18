<a id="top"></a>

# Tình trạng kiểm chứng

[English](README.md) · [Tiếng Việt](README-vi.md) · [Sổ tay ứng dụng](../README-vi.md) · [Hướng dẫn bằng chứng](evidence/README-vi.md)

Mỗi kết quả chỉ áp dụng cho đúng địa bàn, năm, dữ liệu và độ chính xác đã nêu. Bảng dưới tách kết quả có bằng chứng khỏi phần vẫn cần thêm dữ liệu.

## Kết quả

| Hạng mục | Kết quả | Giới hạn |
| --- | --- | --- |
| GADM Trung Quốc | 2.420 đơn vị biên tập khớp nguồn GADM 4.1 đầy đủ trong sai số đã ghi. | Không xác nhận ranh giới pháp lý hiện nay hoặc mọi quốc gia. |
| VIIRS và LISA tại Diên Khánh | Bảng đối chiếu đa giác năm 2020 có 8.332/8.333 ô trong ngưỡng 0,00005; ô vượt ngưỡng duy nhất là ô biên với sai số 0,0000643242. Bảng LISA độc lập khớp 8.154/8.333 nhãn cuối và ghi đủ 179 trường hợp khác. | Phép LISA dùng NTL đã làm tròn trong CSV và hạt hoán vị độc lập, nên phải báo cáo khác biệt thay vì coi mọi nhãn khác là lỗi số học. Hai mốc năm không chứng minh xu thế hằng năm. |
| Thượng Hải, Bảo An và Kỳ Môn | Kiểm chứng V11 đã hoàn tất với 15.330/15.330 ô đầy đủ trong giới hạn làm tròn CSV bốn chữ số; 1.846/1.847 ô cắt biên trong ngưỡng 0,00005 và toàn bộ trong 0,0000501. Manifest phục hồi ghi danh mục raster nguồn, CSV ứng dụng và kết quả ô biên đã dùng. | Checkout hiện tại giữ báo cáo, danh mục và mã băm thay vì bung toàn bộ đầu vào nhị phân; không được nhầm giới hạn chạy lại này với việc kết quả chưa được kiểm chứng. |
| Siêu dữ liệu A02 | CSV Bảo An 7.148 ô có trạng thái đã quan sát và năm trường chất lượng hữu hạn ở mọi dòng. Mọi giá trị trong 32 cột chung của hai lần xuất đều khớp; tệp sau có thêm các cột LISA. | Chưa kiểm tra ca thực địa thật sự thiếu hoặc ít quan sát. |
| GHSL tại Thượng Hải | Kiểm chứng độc lập đã hoàn tất và ghi trong danh mục bằng chứng các raster lưới gốc và kiểu ứng dụng, JSON kiểm chứng theo ô, mã băm, chương trình cùng báo cáo. Phép tính lưới gốc tái lập mức làm tròn rho, khoảng bootstrap và AUC trên 715 ô đủ điều kiện. | Cả hai khoảng rho đều chứa 0, nên kết quả đã kiểm chứng là quan hệ chưa rõ trong mẫu này, không phải bằng chứng về đồng thuận GHSL nói chung hay giá trị kinh tế. |
| Hiệu năng A02 | Lượt Bảo An sau ghi 37,6479 giây cho toàn quy trình và 26,4623 giây cho A02, so với 46,6687 giây và 25,0028 giây ở lượt trước. | Tổng thời gian ngắn hơn nhưng riêng A02 không nhanh hơn; cần nhiều lượt chạy cùng cấu hình. |

Vị trí tệp, mã băm và các phép kiểm có thể chạy nằm trong [hướng dẫn bằng chứng](evidence/README-vi.md).

[Kiểm toán phát biểu khoa học](evidence/README-vi.md#kiểm-toán-phát-biểu-khoa-học) trong hướng dẫn bằng chứng tách cơ sở tài liệu, kiểm thử triển khai và đối chiếu thực địa. Trích dẫn có thể biện minh cho phương pháp hoặc cách diễn giải, nhưng không chứng minh rằng đầu ra của ứng dụng đã vượt qua một phép kiểm thực địa.

## Sổ theo dõi phạm vi kiểm toán

Đợt rà soát mã nguồn ban đầu dùng các mã A01 đến A12. Bảng dưới ghi trạng thái hiện nay; [ma trận câu hỏi kiểm toán đầy đủ](evidence/README-vi.md#ma-trận-câu-hỏi-kiểm-toán-đầy-đủ) nêu câu hỏi, lý do, tệp bằng chứng, cách kiểm tra, kết quả định lượng hoặc điều kiện chấp nhận, dung sai và giới hạn của từng mục.

| Mã | Trạng thái hiện nay |
| --- | --- |
| A01 | Khoảng trống tìm kiểm thử trong CI đã đóng. Quy trình hiện tại chạy toàn bộ cây kiểm thử đang được duy trì qua hai tác vụ. |
| A02 | Các trường hỗ trợ quan sát đã được xác nhận cho ca Bảo An có đủ quan sát; độ nhạy nhân tạo đã được định lượng; ca thiếu hỗ trợ thật vẫn còn mở. |
| A03 | Có chuẩn số học độc lập và đối chiếu thực địa tại Diên Khánh; các dạng không gian rộng hơn cùng chuỗi năm liên tục vẫn chưa đủ. |
| A04 | Đã đóng. Một hàm Gini chung trả 0,000000 cho `[5,5,5,5]`, 0,500000 cho `[0,0,10,10]`, 0,250000 cho `[1,2,3,4]` và 0 cho mẫu rỗng/toàn 0, khớp công thức cặp đôi độc lập trong sai số $10^{-12}$. Ba ca số âm, NaN và vô cực đều gây lỗi thay vì đổi mẫu. |
| A05 | Một phần phiên bản kiểm thử đã cố định, nhưng thư viện vận hành và tệp khóa tái lập đầy đủ chưa hoàn thiện. |
| A06 | Kiểm thử tích hợp và mô-đun thống kê tách riêng đã giảm rủi ro; phần điều phối ứng dụng vẫn liên kết chặt. |
| A07 | MAUP theo cách gộp khối đã được kiểm tra đúng theo triển khai; chưa chứng minh tương đương với trích xuất raster trực tiếp trên lưới thô. |
| A08 | Bảo toàn lượng trên lưới GHSL gốc và hệ tọa độ đã được sửa cùng kiểm thử; kiểm chứng thực địa độc lập tại Thượng Hải đã hoàn tất, còn đầu vào, kết quả theo ô, chương trình và mã băm được ghi trong manifest bằng chứng phục hồi. |
| A09 | Nhãn rho chỉ là quy ước mô tả. Khoảng tin cậy tại Thượng Hải chứa 0 nên chưa chứng minh quan hệ khác 0. |
| A10 | Bộ nhớ đệm trong phiên có giới hạn và có hai hồ sơ đo thực địa; chưa kiểm tra năng lực Cloud nhiều người dùng. |
| A11 | Kiểm thử tích hợp nhân tạo và một lượt Bảo An đã lưu bao phủ nhiều công đoạn; vẫn thiếu phép thử trực tiếp có đăng nhập và có thể lặp từ dịch vụ đến tệp xuất. |
| A12 | Có sáu cặp hướng dẫn song ngữ cùng kiểm tra tự động cho liên kết và công thức; việc đối chiếu ngữ nghĩa và khoa học vẫn cần đọc thủ công. |

## Phần có thể tái lập từ repo

| Phép kiểm | Lệnh hoặc dữ liệu | Phạm vi |
| --- | --- | --- |
| Bằng chứng Bảo An | `node validation/audit_public_evidence.mjs --check-result` | Kiểm tra số dòng, ID, trường A02, bản tóm tắt và danh mục tệp đã lưu. |
| Tài liệu | `node validation/check_docs.mjs` | Kiểm tra các cặp hướng dẫn Anh–Việt, liên kết và dấu công thức. |
| Hợp đồng của ứng dụng | `python -m pytest -q tests` | Kiểm tra số học, cấu trúc dữ liệu, mặt nạ và giao diện bằng đầu vào đã lưu hoặc nhân tạo. |
| Đối chiếu raster ba địa bàn | [Quy trình nhiều địa bàn](cross_location/README-vi.md) và manifest kiểm toán phục hồi | Ghi phương pháp V11 đã hoàn tất, đầu vào, tệp ô biên, dung sai và kết quả. Checkout hiện tại không phải gói đầu vào nhị phân đã bung để chạy mới. |

## Giới hạn phương pháp

- NTL mỗi ô là trung bình bức xạ VIIRS hợp lệ theo tỷ lệ phủ điểm ảnh. Giá trị âm hợp lệ được chặn về 0 ở đầu ra cũ; các trường hỗ trợ quan sát được giữ riêng.
- Local Moran dùng các ô lõi hoặc ô sáng đủ điều kiện và trọng số chuẩn hóa theo hàng. Global Moran dùng toàn bộ ô và trọng số Queen nhị phân; hai thống kê không thể thay thế nhau.
- Lượng trên từng điểm ảnh GHSL được cộng theo tỷ lệ giao với đa giác ngay trên lưới nguồn, sau đó chia diện tích ô để lấy mật độ.
- Kiểm thử tự động, đối chiếu số liệu đã lưu và phép kiểm dịch vụ trực tiếp trả lời những câu hỏi khác nhau. Mỗi kết quả công bố cần nêu đầu vào, phiên bản mã, địa bàn, năm, lưới và dung sai.

## Các khoảng trống khoa học còn lại: G01-G18 (18/11/2026)

Sổ này tiếp nối các kết quả A01-A12, V11, Diên Khánh, Bảo An và GHSL Thượng Hải đã ghi ở trên. Sửa nhãn diễn giải **không phải** kiểm chứng thực địa mới. Các bằng chứng số học, manifest lưu trữ, dữ liệu và hợp đồng CSV lịch sử được giữ nguyên trong phạm vi đã xác nhận. Các mã cột như `spatial_ar1_persistence`, `signed_dist_hh_km` và `0_Treated_HH` được giữ để tương thích, không hàm ý đã nhận dạng mô hình.

| Khoảng trống | Ưu tiên | Trạng thái và rủi ro khoa học | Bằng chứng cần bổ sung |
| --- | --- | --- | --- |
| G01 | P0 | Đã đổi nhãn lan tỏa nhân quả/RDD thành mô tả khoảng cách HH. Tác động nhân quả vẫn **chưa kiểm chứng**. | Thiết kế can thiệp hoặc ranh giới độc lập, kiểm tra tính liên tục và nhóm so sánh hợp lệ. |
| G02 | P0 | Giao diện nêu đúng `spatial_ar1_persistence` là `Corr(z, Wz)` cùng một năm, **không phải** hệ số AR hay kiểm định nghiệm đơn vị. | Mô hình không gian tường minh và phép kiểm tính dừng riêng nếu cần. |
| G03 | P1 | Các ngưỡng NTL 5/15/40 đã được gọi là nhóm bức xạ mô tả; hiệu chuẩn ý nghĩa kinh tế vẫn **mở**. | Dữ liệu sử dụng đất và biến kinh tế độc lập tại nhiều địa bàn. |
| G04 | P1 | Đẳng thức NTL có trọng số khoảng cách trừ kỳ vọng hoán vị đã có kiểm thử; ý nghĩa tiếp cận thị trường và tính ngoại sinh còn **mở**. | Đối chiếu việc làm, dân số hoặc khả năng tiếp cận độc lập; thử độ nhạy hệ số suy giảm khoảng cách. |
| G05 | P1 | Tâm CBD lấy từ NTL có thể gây thiên lệch lựa chọn tâm khi đánh giá độ dốc và R². | Tâm hoạt động xác định độc lập, so độ dốc và R² theo từng cách chọn tâm. |
| G06 | P1 | Số học Hill/KS đã kiểm thử nhưng chưa xác nhận dữ liệu thực sự theo Pareto. | Bootstrap có ước lượng lại tham số, so ngưỡng đuôi và các phân phối thay thế. |
| G07 | P1 | Giao diện và sổ tay đã ghi đúng khoảng cách **giữa tâm ô**; khoảng cách tới biên đa giác thực vẫn **chưa kiểm chứng**. | Đối chiếu với khoảng cách đến biên đa giác tại cụm HH phức tạp và nhiều lưới. |
| G08 | P1 | Đã chặn năm ngược: `year_t0 < year_t1` trong hàm lõi và giao diện; có kiểm thử hồi quy mới. | Giữ nguyên bằng chứng hai kỳ đã hoàn tất, không chạy lại chỉ vì bổ sung ràng buộc. |
| G09 | P1 | Bảng chuyển phân vị hai kỳ chỉ mô tả, chưa chứng minh quá trình Markov dài hạn ổn định. | Panel nhiều năm liên tục, kiểm tra đồng hạng, phân vị và độ ổn định xác suất chuyển. |
| G10 | P1 | Đếm tháng có dữ liệu không đồng nghĩa trọng số theo số lần quan sát. Bảo An A02 đủ quan sát vẫn được bảo lưu. | Ca thiếu hỗ trợ thật, `cf_cvg` tháng không đồng đều và phép thử nhạy theo tháng. |
| G11 | P1 | Chọn một UTM theo tâm bbox có thể gây sai lệch ở vùng rộng, cực hoặc qua kinh tuyến 180°. | Chuẩn trắc địa và sai số diện tích/khoảng cách ở các trường hợp địa lý khó. |
| G12 | P2 | Cờ Moran phần dư chuyển từ p-value hoán vị sang ngưỡng I cố định khi lưới quá lớn. | Tách trạng thái suy luận khỏi cảnh báo mô tả hoặc kiểm chứng ngưỡng. |
| G13 | P2 | Mốc năm GHSL có thể khác năm VIIRS, không ảnh hưởng kết luận kiểm chứng Thượng Hải đã lưu. | Thử độ nhạy lệch thời gian với biến đối chiếu có năm độc lập. |
| G14 | P2 | Các ngưỡng Jaccard, tần suất lõi, SD theo seed và độ dịch chuyển là quy ước. | Đường độ nhạy thực nghiệm, không xem là mốc khoa học phổ quát. |
| G15 | P2 | `moran_I_lit` là trung bình Local Moran, không phải Global Moran I. | Bảo đảm mọi giải thích trên giao diện và CSV phân biệt hai đại lượng. |
| G16 | P2 | Liên kết danh mục VIIRS trong hướng dẫn bằng chứng phải đúng mã `VCMSLCFG` đang chạy. | Đối chiếu nguồn và phiên bản; không chạy lại V11. |
| G17 | P1 | Số học BH đã kiểm thử, nhưng phụ thuộc không gian không bảo đảm FDR danh nghĩa trong mọi cấu trúc. | Mô phỏng null không gian: FDR thực nghiệm và lực kiểm định của BH so với BY theo W và mức tương quan. |
| G18 | P1 | LISA mặc định loại ô NTL bằng 0 khỏi cả kiểm định lẫn đồ thị láng giềng. | So HH/LL khi đưa ô 0 vào, đồng thời tách số 0 thực đo khỏi thiếu quan sát. |

### Tiêu chí nghiệm thu kiểm chứng mới

- **G04/G05/G06:** lưu nguồn dữ liệu độc lập, đơn vị không gian, công thức, seed, chỉ số so sánh, kết quả cấp ô và các bảng độ nhạy. Tách tính đúng của đẳng thức khỏi giá trị diễn giải kinh tế.
- **G17:** định trước cách sinh dữ liệu null và alpha danh nghĩa; báo số phát hiện sai, FDR thực nghiệm, lực kiểm định và độ bất định qua các lần mô phỏng. BH tính đúng không tự chứng minh kiểm soát FDR cho mọi cấu trúc không gian. Tham khảo [Benjamini và Yekutieli (2001)](https://doi.org/10.1214/aos/1013699998).
- **G18:** phân biệt số 0 thực đo và không có quan sát bằng dải hỗ trợ A02 đã xác nhận; chỉ chạy đặc tả thêm ô 0, không lặp lại chuẩn A03 đã hoàn thành.
- **Phần còn mở của A02/A07:** kiểm tra ca thiếu quan sát thực tế và lưới thô trích xuất trực tiếp từ raster. Không mở lại ca Bảo An đủ quan sát hoặc V11 chỉ vì còn câu hỏi lân cận.

**Ranh giới thay đổi trong lần này:** thay đổi mô tả chuyên môn và ràng buộc thứ tự năm; không đổi ngưỡng NTL, công thức trích xuất VIIRS/GHSL, công thức hoán vị Local Moran, BH, Gini, dữ liệu lưu trữ hay mã phân nhóm số học. Cột nhãn chữ `ntl_class_label` chuyển sang mô tả nhóm bức xạ, không còn gán loại hình kinh tế chưa hiệu chuẩn.
