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
| G04 | P1 | Đã lưu bằng chứng về độ nhạy chỉ số NTL theo khoảng cách trên Bảo An 2020 và thí nghiệm nhân tạo có quy mô việc làm biết trước. **Hiệu chuẩn tiếp cận thị trường kinh tế và ngoại sinh vẫn mở.** | Đối chiếu dữ liệu việc làm, dân số, chi phí đi lại hoặc kết quả thị trường độc lập, đồng bộ địa bàn, thời gian và đơn vị không gian. |
| G05 | P1 | Đã lưu bằng chứng về độ nhạy theo tâm chọn bằng LISA: thử nghiệm nhân tạo biết trước tâm, 80 lần lặp của các tâm thay thế và so sánh Bảo An 2020. **Vẫn chưa có tâm kinh tế thực được xác minh độc lập.** | Ghép tâm việc làm/POI hoặc trung tâm hoạt động được xác minh độc lập, có vị trí và năm phù hợp; không đồng nhất R² nội mẫu với độ đúng của tâm kinh tế. |
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
| G17 | P1 | Đã lưu mô phỏng FDR/lực kiểm định với p-value Gaussian hợp lệ và phép thử độ nhạy bằng hoán vị LISA thực tế. **Bảo đảm FDR cho địa bàn thực vẫn còn mở.** | Phải kiểm tra giả thuyết hoán vị, sự phụ thuộc giữa p-value và trường hợp thực phù hợp trước khi công bố FDR danh nghĩa. |
| G18 | P1 | Đã lưu bằng chứng độ nhạy tổng hợp có cờ quan sát: đưa ô 0 vào và điền 0 sai làm đổi nhãn, láng giềng và p-value LISA. **Kiểm chứng thực địa thiếu hỗ trợ vẫn mở.** | Lặp lại trên ca thực có hỗ trợ A02 được xác minh; không coi mô phỏng là kiểm chứng ngoài. |

### G04: Tiềm năng NTL có trọng số khoảng cách và kiểm chứng độ nhạy (19/11/2026)

**Dữ liệu thực sự được dùng và dữ liệu không có trong phép tính.** Ứng dụng đang sử dụng NTL VIIRS, diện tích ô, tọa độ ô trên lưới chiếu và tham số hàm suy giảm theo khoảng cách. `SOL = NTL × diện tích ô`; khoảng cách Euclid chỉ thể hiện độ gần nhau về địa lý, không phải thời gian đi lại hay chi phí vận tải được quan sát. **Ứng dụng không nạp dữ liệu việc làm, dân số, thu nhập, sức mua, kết quả thị trường hoặc mạng giao thông để tính chỉ số này.** Số "việc làm" bên dưới hoàn toàn do mã kiểm chứng tạo ra để thử ý nghĩa của chỉ số: không phải việc làm khảo sát thực, và không được ứng dụng dùng làm đầu vào. Vì vậy **không cần dữ liệu kinh tế để tính chỉ số NTL**, nhưng chưa thể khẳng định nó đo tiếp cận thị trường kinh tế.

**Đại lượng được kiểm tra.** Mã hiện hành tính $P_i=\sum_{j\ne i}w_{ij}SOL_j$ và $$
\widetilde{P}_i=P_i-\overline{SOL}_{core}\sum_{j\ne i}w_{ij}
$$, với $w_{ij}=\exp(-\tau d_{ij})$ trong bán kính Euclid cố định trên lưới. Cấu hình mặc định dùng $\tau=0,5$ mỗi km và bán kính năm bước tại lưới 500 m, tức **2,5 km**; khoảng cách làm trọng số còn một nửa xấp xỉ 1,386 km. Phép biến đổi chỉ trừ **kỳ vọng theo hoán vị không hạn chế các giá trị SOL giữa ô lõi**, không phải phép đo chi phí vận tải thực tế hoặc phép tái định tâm theo một cơ chế phân bổ cú sốc ngoại sinh phục vụ nhận dạng nhân quả. Đẳng thức kỳ vọng đã được kiểm trong T07 trước đây và **không được chạy lại**.

**Thí nghiệm nhân tạo có quy mô việc làm biết trước.** Trên lưới không đều gồm 335 ô, nguồn việc làm nhân tạo được dựng trước; sau đó mới sinh ánh sáng tương quan với việc làm kèm nhiễu, thêm một nguồn sáng mạnh không gắn với việc làm, hoặc xáo vị trí ánh sáng một lần theo seed (đối chứng mô tả, không phải kiểm định hoán vị). Ở cấu hình mặc định, tương quan thứ hạng Spearman giữa **tiềm năng NTL đã trừ kỳ vọng** và **tiềm năng việc làm nhân tạo** như sau:

| Kịch bản NTL nhân tạo | Tương quan với tiềm năng việc làm nhân tạo |
| --- | ---: |
| Ánh sáng được sinh có liên hệ trực tiếp với việc làm | 0,9361 |
| Thêm nguồn chiếu sáng mạnh không đại diện việc làm | 0,4393 |
| Xáo vị trí NTL một lần theo seed | -0,2513 |

Các con số thể hiện độ nhạy theo **cơ chế tạo dữ liệu nhân tạo**, không xác nhận độ chính xác kinh tế trên thực địa. Nguồn việc làm được giả lập và trường ánh sáng khớp được **sinh trực tiếp từ nguồn đó**, không phải dữ liệu việc làm thực tế được đo độc lập. Trường xáo vị trí chỉ là một hiện thực đối chứng, không có p-value.

**Độ nhạy bức xạ thực tại Bảo An (2020, 500 m).** Tái sử dụng đúng CSV gốc **7.148 ô** đã được kiểm tra A02. Có **6.186 ô lõi đầy đủ** đủ điều kiện để tính trọng số khoảng cách; 962 ô biên vẫn nằm trong tệp kết quả theo ID nhưng các chỉ số tiềm năng để trống. Cả 7.148 dòng nguồn đều có trạng thái đã quan sát. Một dòng không thuộc lõi có trường dữ liệu không hợp lệ được loại khỏi phép tính, không tự điền tọa độ hoặc NTL. Không thay đổi hay trích xuất lại CSV nguồn. Khi đối chiếu cùng tập ô lõi và cấu hình mặc định:

| Bán kính (bước lưới) | Bán kính tối đa | Khoảng tương quan Spearman theo $\tau$ | Khoảng Jaccard của nhóm 10% cao nhất |
| --- | --- | --- | --- |
| 3 | 1,5 km | 0,9855 đến 0,9891 | 0,7813 đến 0,8152 |
| 5 | 2,5 km | 0,9984 đến 1,0000 | 0,9344 đến 1,0000 |
| 8 | 4,0 km | 0,9733 đến 0,9985 | 0,7839 đến 0,9527 |

Các mức $\tau$ được thử là 0,25; 0,5 và 1,0 mỗi km. Thứ hạng tổng thể tương đối gần nhau, nhưng tập ô thuộc 10% cao nhất có thể thay đổi. Ở cấu hình mặc định, tương quan thứ hạng giữa tiềm năng NTL thô và thành phần kỳ vọng chỉ do hình học là **0,4085**; giữa tiềm năng đã trừ kỳ vọng và thành phần hình học là **0,1758**. Đây **không phải kiểm định độc lập thống kê** và tiềm năng đã trừ kỳ vọng không nhất thiết mất mọi tương quan không gian. Giá trị âm (50,73% ô đủ điều kiện ở cấu hình mặc định) chỉ có nghĩa là **thấp hơn kỳ vọng tham chiếu theo hoán vị**, không hàm ý việc làm hay thị trường có giá trị âm.

**Bằng chứng lưu trữ đầy đủ:** [chương trình có thể tái lập](g04_ntl_potential_experiment.py), [CSV đầu vào nhân tạo 335 ô có quy mô việc làm](evidence/g04_ntl_potential/synthetic_input.csv), [1.005 kết quả cấp ô nhân tạo ở cấu hình mặc định](evidence/g04_ntl_potential/synthetic_cell_results.csv), [kết quả cấp ô theo 7.148 ID Bảo An](evidence/g04_ntl_potential/baoan_cell_results.csv), [bảng 36 trường hợp độ nhạy](evidence/g04_ntl_potential/sensitivity.csv) và [JSON gồm mã băm SHA-256 nguồn, phiên bản thư viện, định nghĩa và giới hạn](evidence/g04_ntl_potential/summary.json). CSV gốc Bảo An đã được bảo quản ở `validation/evidence/a02_post_pr27/`. CI sẽ đối chiếu đúng cả năm tệp mới bằng cách chạy lại chương trình, giữ nguyên đầu vào lịch sử.

**Phần đã hoàn tất và phần còn mở:** Bộ G04 đã kiểm tra độ nhạy trên dữ liệu nhân tạo và bức xạ VIIRS thực; nó không chứng minh ý nghĩa kinh tế. **Chưa đóng G04 về giá trị diễn giải kinh tế, không phải vì thiếu dữ liệu để chạy công thức.** Để hiệu chuẩn như thước đo tiếp cận thị trường kinh tế, cần số liệu việc làm hoặc dân số được thu thập độc lập, có vị trí và cùng khoảng thời gian, kết hợp với chi phí giao thông hoặc đi lại có cơ sở, tốt nhất thêm kết quả thị trường quan sát thực tế. Việc làm nhân tạo không đóng được khoảng trống này; kiểm tra độ nhạy thuần NTL tại một địa bàn không nhận dạng tác động ngoại sinh. Trong [Donaldson và Hornbeck (2016)](https://doi.org/10.1093/qje/qjw002), tiếp cận thị trường liên quan quy mô thị trường và chi phí vận tải; còn phép tái định tâm phục vụ nhận dạng trong [Borusyak và Hull (2023)](https://doi.org/10.3982/ECTA19367) cần quy tắc về các cú sốc phản thực được xác định rõ.

### G05: Độ nhạy khi chọn tâm từ NTL để ước lượng độ dốc và R² (19/11/2026)

**Phạm vi của chỉ số.** Ứng dụng tính \`urban_gradient_decay\` và \`monocentric_r2\` trên **cùng tập NTL đã dùng để chọn tâm**. Tâm được xác định bằng trọng tâm SOL của cụm HH có ý nghĩa lớn nhất đủ điều kiện; nếu không tồn tại cụm đủ điều kiện, chương trình chọn ô có điểm kết hợp NTL và NTL trung bình láng giềng cao nhất. Sau đó ứng dụng hồi quy có trọng số diện tích giữa \(\log(1+\mathrm{NTL}_i)\) và khoảng cách Euclid từ tâm. Đây là **độ dốc mô tả khớp trong mẫu**, không tự xác nhận CBD kinh tế, cấu trúc đơn tâm hoặc tác động nhân quả. Công thức WLS hiện hành và cấu trúc CSV cũ không bị thay đổi.

**Phần A: mô phỏng có tâm được xác định trước.** Trên lưới 25 × 25 ô, tâm của cơ chế sinh dữ liệu được cố định **trước khi tạo ánh sáng**. Nó được biết đúng nhờ thiết kế nhân tạo, **không phải CBD thực địa được quan sát độc lập**. Ba trường dùng chung nhiễu nền: bức xạ quanh tâm gốc, sau đó bổ sung một nguồn sáng không đại diện trung tâm hoạt động, với biên độ 60 hoặc 170. Trên mỗi trường, chương trình gọi chính \`run_lisa\` để chọn tâm, dùng Queen, 999 hoán vị, BH-FDR mức 0,05, cụm tối thiểu bốn ô. Tâm lấy từ khoảng cách đã được làm tròn trong kết quả được kiểm tra lại bằng độ dốc ứng dụng. Số cụm HH đủ điều kiện lần lượt là một, hai và một.

| Bề mặt NTL nhân tạo | Khoảng lệch giữa tâm LISA và tâm sinh dữ liệu | R² theo tâm đã biết | R² theo tâm LISA | Độ dốc \(\gamma\) theo tâm LISA, mỗi km |
| --- | ---: | ---: | ---: | ---: |
| Không có nguồn sáng gây nhiễu | 0,025 km | 0,874 | 0,874 | 0,3752 |
| Nguồn sáng không đại diện hoạt động, biên độ 60 | 0,090 km | 0,533 | 0,541 | 0,3067 |
| Nguồn sáng gây nhiễu mạnh, biên độ 170 | 6,335 km | 0,304 | 0,128 | 0,1059 |

Ở kịch bản nhiễu mạnh, tâm chọn từ NTL dịch chuyển khỏi tâm gốc và độ dốc thay đổi từ 0,2579 xuống 0,1059 mỗi km. **Chọn tâm theo NTL không nhất thiết làm R² tăng**: trong ví dụ này R² giảm khoảng 0,176, còn kịch bản nhiễu vừa làm R² tăng khoảng 0,008. Các kết quả là phản ứng dưới một cơ chế mô phỏng đã nêu, không phải ước lượng thiên lệch phổ quát.

Ngoài ra, có 80 lần lặp theo seed cho mỗi trường, so tâm gốc với trọng tâm hình học, tâm trọng số NTL và ô sáng nhất. **960 quan sát cấp lần chạy** đã được lưu. Khoảng phân bố mô phỏng này chỉ áp dụng cho các cách chọn tâm thay thế tính nhanh; tâm production dùng cụm HH chỉ được chạy trên ba trường NTL được lưu đầy đủ, **không được tính lại trong cả 240 lần lặp**. Không được lấy độ bất định của các tâm thay thế để suy ra độ bất định của thuật toán chọn tâm HH.

**Phần B: NTL thực tại Bảo An 2020, chưa có CBD kinh tế độc lập.** Dùng lại đúng CSV VIIRS 7.148 ô đã kiểm tra A02, ước lượng cùng phương trình \(\log(1+\mathrm{NTL})\) và cùng trọng số diện tích cho **6.186 ô lõi đầy đủ**. Không trích xuất lại VIIRS hoặc chạy lại A03/LISA. Tâm đã chọn trong kết quả lịch sử được tái dựng hình học từ \`dist_to_core_km\` lưu trong CSV, làm tròn đến 0,001 km; độ lệch tuyệt đối trung vị giữa khoảng cách tái dựng và khoảng cách nguồn là **0,254 m**, phân vị 99% là **0,505 m**. Đây là **tâm suy ra từ NTL trong lần chạy cũ**, không phải CBD được xác định bên ngoài.

| Quy tắc chọn tâm Bảo An 2020 | Khoảng cách tới tâm NTL lịch sử | Độ dốc \(\gamma\), mỗi km | R² nội mẫu |
| --- | ---: | ---: | ---: |
| Tâm NTL được chọn từ kết quả trước đây | 0 km | 0,02601 | 0,37988 |
| Trọng tâm hình học có trọng số diện tích | 33,000 km | 0,02736 | 0,10613 |
| Tâm theo trọng số NTL cùng năm | 22,833 km | 0,04070 | 0,34348 |
| Ô NTL sáng nhất cùng năm | 9,326 km | 0,02677 | 0,37505 |

Đây chỉ là **độ nhạy khi đổi tâm trong cùng vùng và cùng năm**, không phải bảng xếp hạng mức độ chính xác CBD kinh tế. Trọng tâm hình học không dùng NTL khi tính, nhưng **không được xác nhận là tâm việc làm**; hai cách chọn tâm còn lại cũng phụ thuộc NTL. Tất cả hồi quy cùng dùng 6.186 ô và cùng biến phụ thuộc, nên khác biệt xuất phát từ quy tắc chọn tâm chứ không phải do thay đổi mẫu. Chênh lệch R² tới khoảng 0,274 là dấu hiệu cần diễn giải thận trọng \`monocentric_r2\`, không dùng nó làm phép kiểm đô thị đơn tâm trong kinh tế học.

**Bằng chứng đầy đủ có thể chạy lại:** [mã chương trình](g05_ntl_center_experiment.py); [đầu vào nhân tạo 625 ô và ba trường ánh sáng](evidence/g05_ntl_center/synthetic_input.csv); [1.875 dòng kết quả cấp ô nhân tạo và khoảng cách](evidence/g05_ntl_center/synthetic_cell_results.csv); [960 dòng mô phỏng chọn tâm thay thế](evidence/g05_ntl_center/synthetic_replications.csv); [7.148 ID Bảo An có lưu khoảng cách từng cách chọn tâm và trạng thái ô biên](evidence/g05_ntl_center/baoan_cell_results.csv); [19 phép so sánh độ dốc và R²](evidence/g05_ntl_center/center_comparison.csv); và [JSON ghi nhận nguồn, chất lượng tái dựng, kết quả mô phỏng, SHA-256 và giới hạn](evidence/g05_ntl_center/summary.json). CI khóa phiên bản thư viện khoa học và đối chiếu đúng cả sáu tệp. CSV nguồn Bảo An cùng các bằng chứng G04, G17, G18, A02, A03, V11, GHSL được bảo lưu.

**Kiểm chứng G05 về ý nghĩa kinh tế vẫn mở:** Cần tâm CBD, tâm việc làm hoặc trung tâm hoạt động được quan sát độc lập tại khoảng năm 2020, có tọa độ, nguồn gốc và phạm vi không gian phù hợp để đánh giá mức lệch chọn tâm **theo nghĩa kinh tế**. Tâm do mô hình nhân tạo đặt trước hay trọng tâm hình học của vùng thật không thay thế được nguồn đó. Một số đô thị còn có cấu trúc đa tâm hoặc độ dốc không tuyến tính, nên phương trình một tâm có thể mô tả không phù hợp bất kể chọn tâm nào. Tham khảo [nghiên cứu về độ dốc bức xạ ban đêm và mật độ đô thị](https://doi.org/10.1057/s41599-023-01884-8).

### Kiểm chứng G17 dưới phụ thuộc không gian (phạm vi mô phỏng, 19/11/2026)

Đây là **hai thí nghiệm nhân tạo tách biệt**, không phải kiểm chứng thực địa VIIRS mới và không làm lại số học BH đã đóng trong A03. p-value hợp lệ dưới giả thuyết không, phụ thuộc giữa các p-value và việc lập trình công thức BH chính xác là ba vấn đề khác nhau.

**Phần A, biết chính xác giả thuyết nào đúng và đo lực kiểm định:** Trên lưới nhân tạo 64 ô (8×8), lập đồ thị Queen hoặc Rook chuẩn hóa từng hàng, rồi tạo trường Gaussian theo $z=D^{-1/2}(I-\rho W)^{-1}\epsilon$. Chuẩn hóa theo độ lệch chuẩn lý thuyết giúp mỗi điểm kiểm định dưới giả thuyết không có phân phối chuẩn tắc, nên p-value Gaussian hai phía hợp lệ về phân phối biên ngay cả khi giữa các điểm có phụ thuộc không gian. Dùng $\rho\in\{0;0,5;0,8;-0,5\}$, 400 lần lặp cho mỗi cấu hình và $\alpha=0,05$. Trong kịch bản có tín hiệu, tăng kỳ vọng cố định 2,75 độ lệch chuẩn tại chín ô giữa lưới xác định trước; 55 ô còn lại có giả thuyết H₀ đúng theo thiết kế. **FDR thực nghiệm** là trung bình tỷ lệ phát hiện sai trên tổng số bác bỏ (quy ước mẫu không bác bỏ có tỷ lệ 0); **lực kiểm định** là phần chín ô tín hiệu được nhận diện. BY áp dụng BH tại mức $\alpha/H_{64}$ với $H_{64}=\sum_{i=1}^{64}1/i$.

| Kết quả phần A qua 8 cấu hình không gian | BH | BY |
| --- | ---: | ---: |
| FDR khi toàn bộ giả thuyết H₀ đều đúng | 0,0475 đến 0,0575 | 0,0075 đến 0,0175 |
| FDR khi có cụm chín ô tín hiệu | 0,0353 đến 0,0483 | 0,0087 đến 0,0164 |
| Lực nhận diện cụm chín ô | 0,4222 đến 0,4467 | 0,2194 đến 0,2544 |

Đây là ước lượng từ số lần mô phỏng hữu hạn; sai số Monte Carlo và khoảng 95% nằm trong [JSON tổng hợp](evidence/g17_spatial_fdr/summary.json). Chẳng hạn 0,0575 ở một cấu hình với 400 lần lặp **không đủ** chứng minh đã vi phạm ngưỡng danh nghĩa 0,05. Hệ số $\rho$ là tham số tạo trường, không phải giá trị `spatial_ar1_persistence` của ứng dụng. Mức đánh đổi lực kiểm định của BY chỉ đúng trong các cấu hình đã thử.

**Phần B, sử dụng trực tiếp thuật toán hoán vị Local Moran:** Tạo trường NTL lognormal dương trên cùng lưới, chạy chính hàm `local_moran`, `bh_reject` của app và ngưỡng BY, với Queen/Rook, 999 hoán vị có điều kiện, $\alpha=0,05$, 24 lần lặp cho mỗi cặp trọng số và $\rho\in\{0;0,8;-0,5\}$. Khi $\rho=0$, dữ liệu độc lập cùng phân phối, giả thuyết hoán vị không gian hợp lệ và tất cả giả thuyết H₀ đều đúng. Trong 24/24 lượt cho mỗi đồ thị, BH lẫn BY không bác bỏ ô nào. Số lần lặp nhỏ này **không chứng minh** khả năng kiểm soát FDR chính xác.

Với trường có tương quan $\rho=0,8$ nhưng không tự thêm cụm tín hiệu, BH có ít nhất một ô bị bác bỏ ở 16/24 lượt Queen và 1/24 lượt Rook, trong khi BY không bác bỏ ở các nhóm 24 lượt này. **Đây không phải số phát hiện sai:** phụ thuộc không gian vốn đã vi phạm giả thuyết phân bổ ngẫu nhiên của phép hoán vị và có thể tạo liên hệ cục bộ thật. Không có tập nhãn giả thuyết không đúng/sai cấp ô đã được xác minh, do đó JSON cố ý ghi FDR của các trường này là `null`.

**Độ phân giải p-value:** Với 999 hoán vị hai phía, p-value nhỏ nhất bằng 0,002. Khi có 64 phép kiểm định, không thể có bác bỏ ở hạng đầu theo BH/BY. Hạng có khả năng đạt ngưỡng sớm nhất là 3 đối với BH và 13 đối với BY. Giới hạn rời rạc này ảnh hưởng mạnh đến khả năng phát hiện trong phép thử LISA, phải được báo khi diễn giải.

**Bằng chứng có thể tái lập:** [design.csv](evidence/g17_spatial_fdr/design.csv) chứa lưới và mặt nạ tín hiệu định trước; [replicates.csv](evidence/g17_spatial_fdr/replicates.csv) chứa **6.544 bản ghi cấp lượt chạy**; [summary.json](evidence/g17_spatial_fdr/summary.json) chứa kết quả từng cấu hình, độ bất định, giả định và mã băm SHA-256. [Chương trình tạo phép kiểm](g17_spatial_fdr_experiment.py) dùng seed cố định và phiên bản NumPy, pandas, SciPy được khóa trong CI. Chạy `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python validation/g17_spatial_fdr_experiment.py --verify` tại thư mục gốc để so sánh toàn bộ tệp lưu trữ.

**G17 thực địa vẫn mở:** Phụ thuộc không gian dương không tự chứng minh điều kiện PRDS cho p-value LISA. Định lý BY dưới phụ thuộc bất kỳ vẫn **đòi hỏi p-value hợp lệ theo giả thuyết không**, không thể chữa sai lệch do hoán vị không hợp lệ. Cần định nghĩa giả thuyết khoa học, tập phép kiểm định, mô hình nhiễu không gian và nguồn chuẩn để kiểm tra khả năng kiểm soát FDR trước khi áp dụng khẳng định định lượng cho vùng thực. Tham khảo [Benjamini và Yekutieli (2001)](https://doi.org/10.1214/aos/1013699998) và [hướng dẫn Local Spatial Autocorrelation của GeoDa](https://geodacenter.github.io/workbook/6a_local_auto/lab6a.html).

### Bằng chứng tổng hợp G18 (phạm vi giới hạn, 18/11/2026)

Đây là thí nghiệm **dữ liệu nhân tạo có kiểm soát** trên lưới 12×12 ô, cạnh 500 m, không phải dữ liệu VIIRS thực hoặc ca kiểm chứng A02. Mặt nạ quan sát được xác định trước, gồm 106 ô có NTL dương đã quan sát, 28 ô có NTL bằng 0 thực đo và 10 ô không có quan sát nhưng bị điền 0 theo chính sách cũ. Ba lần chạy dùng cùng Queen, 999 hoán vị có điều kiện, seed 42, alpha 0,05; bảng dưới dùng BH-FDR.

| Chính sách tập mẫu và xử lý ô 0 | Ô kiểm định | HH | LL |
| --- | ---: | ---: | ---: |
| Chỉ ô NTL dương thuộc vùng có quan sát | 106 | 22 | 21 |
| Đưa thêm ô 0 thực đo trong vùng có quan sát | 134 | 21 | 17 |
| Đưa cả ô thiếu quan sát bị điền 0 vào như ô thực đo | 144 | 18 | 13 |

Khi đưa các ô 0 thực đo vào, **50/134 ô có dữ liệu** đổi nhãn (trong đó có 28 ô trước đó là `DARK`), 45/134 ô đổi số láng giềng và 92/106 p-value so sánh được thay đổi. Khi coi nhầm 10 ô thiếu quan sát thành ô 0 thực đo, 9/134 ô có dữ liệu đổi nhãn, 28/134 ô đổi số láng giềng và 112/134 p-value so sánh được thay đổi **ngay trong phần có quan sát thực sự**. Cả 10 ô thiếu quan sát đã đi vào họ kiểm định của lần chạy sai. CSV bằng chứng còn lưu kết quả chưa hiệu chỉnh FDR.

**Giới hạn:** Dùng cùng seed không bảo đảm các lần chạy với số ô kiểm định khác nhau dùng đúng cùng mẫu hoán vị; vì vậy chênh lệch p-value có thể gồm cả biến thiên Monte Carlo ngoài thay đổi quần thể. Đây chỉ là độ nhạy trên một trường nhân tạo, **không** phải mức thiên lệch đo được tại địa phương thực, không xác định chính sách nào đúng cho mọi nghiên cứu và không chứng minh kiểm soát FDR thực nghiệm. Những lần chạy có kiểm soát loại vị trí thiếu quan sát khỏi hình học phân tích thay vì đưa NaN vào `run_lisa`, bởi tính Gini trong hàm hiện bác bỏ NaN. Việc này đồng thời thay đổi quần thể chuẩn hóa và tập phép kiểm định. Các bằng chứng V11/GHSL/A02/A03/A04 được bảo lưu; chính sách vận hành mặc định vẫn loại ô NTL bằng 0 khỏi LISA.

**Bằng chứng lưu trữ:** [chương trình tạo kết quả](g18_zero_support_experiment.py), [đầu vào và mặt nạ quan sát](evidence/g18_zero_support/synthetic_input.csv), [kết quả cấp ô toàn bộ](evidence/g18_zero_support/cell_comparison.csv) và [JSON tóm tắt, phiên bản thư viện, mã băm SHA-256](evidence/g18_zero_support/summary.json). CI chạy chương trình và đối chiếu cả ba tệp lưu trữ để bảo đảm tái lập đúng kết quả.

**G18 thực địa còn mở:** Cần ca thực có siêu dữ liệu hỗ trợ quan sát được kiểm tra độc lập, phân biệt số 0 thực đo và thiếu dữ liệu, rồi thực hiện so độ nhạy với tiêu chí diễn giải và ngưỡng chất lượng định trước.

### Tiêu chí nghiệm thu kiểm chứng mới

- **G04/G05/G06:** lưu nguồn dữ liệu độc lập, đơn vị không gian, công thức, seed, chỉ số so sánh, kết quả cấp ô và các bảng độ nhạy. Tách tính đúng của đẳng thức khỏi giá trị diễn giải kinh tế.
- **G17:** định trước cách sinh dữ liệu null và alpha danh nghĩa; báo số phát hiện sai, FDR thực nghiệm, lực kiểm định và độ bất định qua các lần mô phỏng. BH tính đúng không tự chứng minh kiểm soát FDR cho mọi cấu trúc không gian. Tham khảo [Benjamini và Yekutieli (2001)](https://doi.org/10.1214/aos/1013699998).
- **G18:** phân biệt số 0 thực đo và không có quan sát bằng dải hỗ trợ A02 đã xác nhận; chỉ chạy đặc tả thêm ô 0, không lặp lại chuẩn A03 đã hoàn thành.
- **Phần còn mở của A02/A07:** kiểm tra ca thiếu quan sát thực tế và lưới thô trích xuất trực tiếp từ raster. Không mở lại ca Bảo An đủ quan sát hoặc V11 chỉ vì còn câu hỏi lân cận.

**Ranh giới thay đổi trong lần này:** thay đổi mô tả chuyên môn và ràng buộc thứ tự năm; không đổi ngưỡng NTL, công thức trích xuất VIIRS/GHSL, công thức hoán vị Local Moran, BH, Gini, dữ liệu lưu trữ hay mã phân nhóm số học. Cột nhãn chữ `ntl_class_label` chuyển sang mô tả nhóm bức xạ, không còn gán loại hình kinh tế chưa hiệu chuẩn.
