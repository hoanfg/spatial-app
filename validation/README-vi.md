<a id="top"></a>

# Tình trạng kiểm chứng

[English](README.md) · [Tiếng Việt](README-vi.md) · [Sổ tay ứng dụng](../README-vi.md) · [Hướng dẫn bằng chứng](evidence/README-vi.md)

Mỗi kết quả chỉ áp dụng cho đúng địa bàn, năm, dữ liệu và độ chính xác đã nêu. Bảng dưới tách kết quả có bằng chứng khỏi phần vẫn cần thêm dữ liệu.

## Cách đọc một phép kiểm toán khoa học

Một phép kiểm toán chỉ đủ rõ khi trả lời được sáu câu hỏi: **đầu vào và đơn vị quan sát là gì; đại lượng nào được tính; chuẩn đối chiếu là gì; vì sao chọn phép kiểm; sai số hoặc độ nhạy được đánh giá như thế nào; và kết luận tối đa được phép phát biểu là gì**. Mã nguồn thực thi, kiểm thử nhân tạo, phép đối chiếu hai quy trình xử lý cùng sản phẩm, và dữ liệu thực độc lập là **bốn tầng chứng cứ khác nhau**. Kết quả ở tầng trước không tự động thay thế tầng sau.

- **Chuẩn số học:** kiểm thử công thức bằng mẫu có đáp án biết trước; hữu ích để phát hiện lỗi tính toán, không kiểm chứng hiện tượng ngoài thực địa.
- **Kiểm chứng triển khai:** so mã đầu ra, schema, hình học, mặt nạ và quy trình; xác nhận hợp đồng phần mềm cho đúng ca kiểm tra.
- **Đối chiếu nguồn trên ô thực:** tính lại trên raster, polygon hoặc sản phẩm đối chứng; phải ghi mức độc lập của nguồn và sai số làm tròn/lấy mẫu.
- **Mô phỏng có sự thật đã gán:** thử độ nhạy hoặc sai số kiểm định khi biết trước dữ liệu sinh ra thế nào; không mặc nhiên suy rộng thành hiệu năng thực địa.
- **Kiểm chứng giá trị cấu trúc kinh tế và suy luận:** cần biến kinh tế độc lập, thiết kế nhận dạng hoặc giả thuyết không hiệu chuẩn phù hợp; các bảng tương quan chỉ có thể cung cấp bằng chứng liên hệ mô tả.

### G01-G18: câu hỏi, phép tính, lý do và phạm vi kết luận

Bảng này mô tả **phép kiểm đang tồn tại**, không đề xuất thay thuật toán. Trạng thái chuẩn vẫn ở [sổ G01-G18](scientific_closure_register.json); bằng chứng định lượng chi tiết và tệp chương trình nằm trong các mục phía dưới hoặc [hướng dẫn bằng chứng](evidence/README-vi.md).

| Mã | Kiểm tra và cách tính | Vì sao dùng phương pháp đó | Cách diễn giải và giới hạn |
| --- | --- | --- | --- |
| G01 | Từ các ô High-High (HH), lấy khoảng cách Euclid giữa **tâm ô** và phân nhóm vòng khoảng cách như 0-2, 2-5, 5-10 km. | Kiểm tra tính nhất quán của chỉ số lan tỏa theo khoảng cách đã có mà không giả định có can thiệp ngoại sinh. | Đó là phân bố theo khoảng cách quanh HH, **không phải hiệu ứng lan tỏa nhân quả hoặc RDD**; cần ranh giới/can thiệp độc lập mới kiểm định nhân quả. |
| G02 | Chuẩn hóa NTL thành `z`, tính độ trễ không gian `Wz`, báo `Corr(z, Wz)` trên một lát cắt. | Tách tương quan đồng thời giữa ô và hàng xóm khỏi động học theo thời gian. | Không phải hệ số AR(1), tham số tự hồi quy không gian ước lượng hay kiểm định nghiệm đơn vị. |
| G03 | Áp ngưỡng bức xạ cố định 5/15/40 vào các giá trị NTL, đối chiếu quy tắc phân lớp. | Ngưỡng quyết định nhóm có thể tái lập ngay cả khi chưa có nhãn kinh tế chuẩn. | Nhóm bức xạ mô tả, **không tự mang nghĩa** khu việc làm, CBD hay mức phát triển kinh tế. |
| G04 | Tính `SOL_j = NTL_j × area_j`; cộng `SOL_j × exp(-tau × distance_ij)` trong bán kính đặt trước; so thay đổi thứ hạng/Jaccard top 10% theo bán kính, `tau` và hoán vị vị trí NTL. | Thử xem kết quả phụ thuộc vào hạt nhân khoảng cách và sự trùng vị trí sáng hay không; dữ liệu nhân tạo cho biết quy mô việc làm để kiểm tra tính nhạy cấu trúc. | Đây là **tiềm năng ánh sáng**, không đo thời gian đi lại hoặc tiếp cận thị trường thực; phép trừ kỳ vọng hoán vị không tạo biến ngoại sinh. |
| G05 | Chọn tâm từ cụm HH có ý nghĩa lớn nhất, theo trọng số `SOL`; hồi quy WLS theo diện tích của `log1p(NTL)` lên khoảng cách tâm; so độ dốc và R² với tâm biết trước trong dữ liệu nhân tạo và tâm thay thế. | Phát hiện độ nhạy nội sinh khi chính NTL vừa chọn tâm vừa là biến được giải thích. | R² cao **không xác nhận tâm CBD kinh tế**; Bảo An thiếu tâm việc làm độc lập, còn tâm chuẩn chỉ tồn tại trong mô phỏng. |
| G06 | Lấy bốn tỷ lệ đuôi dương 5/10/15/20%, ước lượng Hill, KS; dùng 399 lần bootstrap Pareto có **ước lượng lại alpha nhưng giữ ngưỡng u và k**; so AICc với đuôi mũ và lognormal bị cắt tại cùng `u`. | Phân biệt phép tính KS xấp xỉ, độ phù hợp có điều kiện và lựa chọn giữa các mô hình đuôi cạnh tranh. | Không bác bỏ KS hoặc AICc thấp nhất **không chứng minh quy luật Pareto không gian**; bootstrap giả định iid và chưa tái chọn ngưỡng. |
| G07 | Khoảng cách dấu `signed_dist_hh_km` được tính từ tâm ô tới tâm HH gần nhất theo quy tắc mã. | Chỉ rõ đại lượng hình học thực được tính, tránh dùng từ “biên cụm” sai nghĩa. | Không được dùng như khoảng cách tới đường biên polygon HH nếu chưa tính khoảng cách hình học biên. |
| G08 | Ràng buộc `year_t0 < year_t1`; thử các trường hợp năm đảo và bằng nhau phải bị từ chối. | Bảo đảm hướng thời gian của so sánh hai mốc. | Kiểm tra hợp đồng thời gian, không nhận dạng nhân quả hay xu hướng giữa hai năm. |
| G09 | Lập ma trận chuyển nhóm tứ phân vị, tính Shorrocks `(4 - trace(P))/3` **chỉ khi đủ hàng xác suất nguồn**; trả NaN nếu phân vị nguồn rỗng. | Tránh biến hàng toàn 0 thành phân phối chuyển tiếp giả, vốn có thể tạo chỉ số chuyển dịch dương khi mọi ô bất động. | Hai mốc có thể mô tả chuyển nhóm; chưa đủ kiểm chứng tính dừng hoặc Markov dài hạn. |
| G10 | Phân biệt `dq_mean_valid_months` (số tháng hợp lệ) với `cf_cvg_total` (tổng lượt quan sát); so `dq_observed_fraction`, mặt nạ và raster nguồn theo `grid_id`. | Một tháng có thể chứa nhiều lượt quan sát; số tháng, số lượt và tỷ lệ diện tích có quan sát trả lời ba câu hỏi khác nhau. | Bảo An/Kỳ Môn có quan sát ở tất cả ô chưa kiểm nghiệm chính sách cho một ô **không có quan sát thực**; không chứng minh trọng số số lượt là tối ưu. |
| G11 | Kiểm tra phạm vi vĩ độ, đường đổi ngày và tính phù hợp của một vùng UTM; đối chiếu với khoảng cách/diện tích trắc địa khi cần. | Khoảng cách và diện tích phẳng có thể sai ở vùng cực, xuyên múi hoặc đường đổi ngày. | Cảnh báo phạm vi không phải chứng nhận sai số hình học toàn cầu; cần chuẩn trắc địa ở ca cực đoan. |
| G12 | Phân biệt chỉ số Moran phần dư mô tả với suy luận từ hoán vị/phân phối tham chiếu; không coi ngưỡng `I > 0.3` là giá trị p. | Quy mô hoặc độ lớn thống kê không tự xác định mức ý nghĩa thống kê. | Chỉ nói “có tự tương quan mô tả” khi chưa có phép kiểm suy luận hợp lệ. |
| G13 | Ghi mốc năm GHSL thực dùng và độ lệch so với năm VIIRS. | GHSL theo epoch cách quãng; phép đối chiếu khác mốc có thể mang sai lệch thời gian. | Tương quan không phải bằng chứng cùng năm nếu hai nguồn không đồng thời; cần proxy cùng mốc nếu khẳng định đồng thời. |
| G14 | Tính Jaccard hai tập HH, độ dao động theo seed, dịch tâm và các ngưỡng nhạy; so cùng tập ô và thông số. | Đếm số ô HH giống nhau chưa đủ để biết **vị trí** điểm nóng có ổn định hay không. | Mốc Jaccard/SD/cự ly là ngưỡng kinh nghiệm, không có p-value hay tính phổ quát được xác nhận. |
| G15 | Kiểm tra nhãn `moran_I_lit` bằng thống kê trung bình Local I và phân biệt với Global Moran I. | Local và Global Moran có chuẩn hóa, tập ô và mục tiêu thống kê khác nhau. | Không gọi trung bình Local I là hệ số Global Moran, kể cả khi cùng phản ánh cấu trúc lân cận. |
| G16 | Đối chiếu ID sản phẩm NOAA `VCMSLCFG` trong tài liệu, đường mã Earth Engine và kiểm thử hợp đồng nguồn. | Đổi sản phẩm có thể đổi xử lý ánh sáng lạc, mask và khả năng so sánh theo thời gian. | Chứng nhận **nhận dạng nguồn được sử dụng**, không chứng nhận độ chính xác vật lý của cảm biến. |
| G17 | Trên lưới nhân tạo 64 ô, sinh p Gaussian có giả thuyết đúng/sai biết trước (400 lần/cấu hình) và mô phỏng LISA riêng (24 lần/cấu hình, 999 hoán vị); so không hiệu chỉnh, BH, BY bằng `FDP = V/max(R,1)`. | Muốn ước lượng FDR mô phỏng phải biết giả thuyết nào thực sự đúng; thử nhiều cấu trúc phụ thuộc để xem ranh giới phương pháp. | FDR trung bình của **mô hình Gaussian có p hợp lệ** không chứng minh p hoán vị Local Moran ngoài thực địa hợp lệ hay thỏa PRDS. |
| G18 | Tạo 144 ô với 106 ô dương, 28 ô quan sát bằng 0 và 10 ô thiếu; chạy LISA ba chính sách (chỉ dương, gồm số 0 có quan sát, điền 0 cả ô thiếu), trước/sau BH. | Cô lập hệ quả của đổi tập ô, láng giềng, chuẩn hóa và họ kiểm định khi nhầm thiếu dữ liệu với bóng tối. | Chênh nhãn HH/LL là **độ nhạy trong dữ liệu nhân tạo**, không phải độ lớn sai lệch thực địa. Phải có ô thiếu thực và nguồn quan sát độc lập để kiểm chứng phần này. |

### Quy tắc tính, báo sai số và lý do chọn chuẩn

- **Đối chiếu VIIRS theo ô:** trên đúng polygon `grid_id`, so `NTL_app` và trung bình pixel raster có trọng số giao diện tích; báo độ lệch tuyệt đối từng ô và các ngoại lệ. CSV xuất bốn chữ số thập phân nên `0.00005` là **dung sai làm tròn**, không phải sai số đo của cảm biến. Tương quan Spearman gần 1 chỉ bảo đảm **thứ hạng**, không bảo đảm hai giá trị bằng nhau.
- **Đối chiếu GHSL:** GHSL lưu lượng/diện tích ở pixel gốc; cộng `quantity_pixel × intersection_area/pixel_area` trong hệ diện tích phù hợp để tránh tạo hoặc mất lượng do tái lấy mẫu. Sau đó chia diện tích ô để ra mật độ; đối chiếu rho/AUC với khoảng bootstrap khối. Nếu khoảng rho chứa 0 thì không được khẳng định quan hệ đơn điệu khác 0 từ mẫu đó.
- **Hoán vị và đa kiểm định:** hạt ngẫu nhiên cố định phục vụ tái lập **cùng cài đặt**, không bảo đảm kết quả p trùng giữa hai bộ mã độc lập. BH so p đã sắp thứ tự với `i × alpha/m`; BY còn điều chỉnh bằng tổng điều hòa. Việc chia một họ kiểm định hay thay số ô tham gia làm thay đổi ngưỡng và cách đọc p.
- **Không gian phụ thuộc:** các ô kề nhau không thể mặc nhiên xem là quan sát iid. Spearman dùng để mô tả quan hệ đơn điệu; các khoảng lấy lại mẫu theo khối mô tả **độ nhạy đối với đơn vị lấy mẫu**, không tự tạo ra CI đã hiệu chuẩn hoặc kết quả nhân quả.
- **Tái lập và độc lập:** SHA-256 xác nhận đúng phiên bản byte chứ không xác nhận phép đo khoa học đúng. Cùng VIIRS nhưng khác tuyến xử lý là đối chiếu triển khai nguồn, không phải cảm biến đối chứng độc lập. Tệp đầu vào không lưu trong repo phải được ghi rõ là giới hạn chạy lại, không lấp bằng đầu vào mô phỏng.

## Kết quả

| Hạng mục | Kết quả | Giới hạn |
| --- | --- | --- |
| GADM Trung Quốc | 2.420 đơn vị biên tập khớp nguồn GADM 4.1 đầy đủ trong sai số đã ghi. | Không xác nhận ranh giới pháp lý hiện nay hoặc mọi quốc gia. |
| VIIRS và LISA tại Diên Khánh | Bảng đối chiếu đa giác năm 2020 có 8.332/8.333 ô trong ngưỡng 0,00005; ô vượt ngưỡng duy nhất là ô biên với sai số 0,0000643242. Bảng LISA độc lập khớp 8.154/8.333 nhãn cuối và ghi đủ 179 trường hợp khác. | Phép LISA dùng NTL đã làm tròn trong CSV và hạt hoán vị độc lập, nên phải báo cáo khác biệt thay vì coi mọi nhãn khác là lỗi số học. Hai mốc năm không chứng minh xu thế hằng năm. |
| Thượng Hải, Bảo An và Kỳ Môn | Kiểm chứng V11 đã hoàn tất với 15.330/15.330 ô đầy đủ trong giới hạn làm tròn CSV bốn chữ số; 1.846/1.847 ô cắt biên trong ngưỡng 0,00005 và toàn bộ trong 0,0000501. Manifest phục hồi ghi danh mục raster nguồn, CSV ứng dụng và kết quả ô biên đã dùng. | Checkout hiện tại giữ báo cáo, danh mục và mã băm thay vì bung toàn bộ đầu vào nhị phân; không được nhầm giới hạn chạy lại này với việc kết quả chưa được kiểm chứng. |
| Siêu dữ liệu A02 | CSV Bảo An 7.148 ô có trạng thái đã quan sát và năm trường chất lượng hữu hạn ở mọi dòng. Mọi giá trị trong 32 cột chung của hai lần xuất đều khớp; tệp sau có thêm các cột LISA. | Chưa có ca ô hoàn toàn không quan sát ngoài thực địa. |
| Kỳ Môn 2016: radiance âm và số 0 có quan sát | 1.079/12.202 pixel nguồn hợp lệ có trung vị âm và bị cắt về 0; 49 ô app NTL bằng 0 theo lớp gốc, 47/47 ô đủ phủ đối chiếu khớp số 0 sau căn chỉnh. Chi tiết về công thức, căn chỉnh và sai số ở [hướng dẫn bằng chứng](evidence/README-vi.md#kiểm-tra-g10g18-tại-kỳ-môn-2016-số-0-có-quan-sát). | Căn chỉnh bằng lưới tham chiếu 2020 gián tiếp; 23 ô biên bị cắt khỏi nguồn; không có ô `no_observation` thực và chưa đối chiếu được raster app nội bộ 2016. |
| GHSL tại Thượng Hải | Kiểm chứng độc lập đã hoàn tất và ghi trong danh mục bằng chứng các raster lưới gốc và kiểu ứng dụng, JSON kiểm chứng theo ô, mã băm, chương trình cùng báo cáo. Phép tính lưới gốc tái lập mức làm tròn rho, khoảng bootstrap và AUC trên 715 ô đủ điều kiện. | Cả hai khoảng rho đều chứa 0, nên kết quả đã kiểm chứng là quan hệ chưa rõ trong mẫu này, không phải bằng chứng về đồng thuận GHSL nói chung hay giá trị kinh tế. |
| Hiệu năng A02 | Lượt Bảo An sau ghi 37,6479 giây cho toàn quy trình và 26,4623 giây cho A02, so với 46,6687 giây và 25,0028 giây ở lượt trước. | Tổng thời gian ngắn hơn nhưng riêng A02 không nhanh hơn; cần nhiều lượt chạy cùng cấu hình. |

Vị trí tệp, mã băm và các phép kiểm có thể chạy nằm trong [hướng dẫn bằng chứng](evidence/README-vi.md).

[Kiểm toán phát biểu khoa học](evidence/README-vi.md#kiểm-toán-phát-biểu-khoa-học) trong hướng dẫn bằng chứng tách cơ sở tài liệu, kiểm thử triển khai và đối chiếu thực địa. Trích dẫn có thể biện minh cho phương pháp hoặc cách diễn giải, nhưng không chứng minh rằng đầu ra của ứng dụng đã vượt qua một phép kiểm thực địa.

## Sổ theo dõi phạm vi kiểm toán

Đợt rà soát mã nguồn ban đầu dùng các mã A01 đến A12. Bảng dưới ghi trạng thái hiện nay; [ma trận câu hỏi kiểm toán đầy đủ](evidence/README-vi.md#ma-trận-câu-hỏi-kiểm-toán-đầy-đủ) nêu câu hỏi, lý do, tệp bằng chứng, cách kiểm tra, kết quả định lượng hoặc điều kiện chấp nhận, dung sai và giới hạn của từng mục.

| Mã | Trạng thái hiện nay |
| --- | --- |
| A01 | Khoảng trống tìm kiểm thử trong CI đã đóng. Quy trình hiện tại chạy toàn bộ cây kiểm thử đang được duy trì qua hai tác vụ. |
| A02 | Các trường hỗ trợ quan sát đã được xác nhận cho ca Bảo An có đủ quan sát; độ nhạy nhân tạo đã được định lượng. Tại Kỳ Môn 2016 đã đối chiếu được số 0 có quan sát do trung vị radiance âm; ca ô hoàn toàn thiếu hỗ trợ thật vẫn còn mở. |
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
| G06 | P1 | Giữ nguyên bootstrap ước lượng lại alpha và so sánh AICc đã lưu; không còn đánh dấu thành công xanh chỉ vì KS xấp xỉ không bác bỏ. **Chưa xác nhận quy luật Pareto thực địa có phụ thuộc không gian.** | Cần tái chọn ngưỡng trong mô phỏng giả thuyết không có cấu trúc không gian phù hợp và so sánh địa bàn độc lập. |
| G07 | P1 | Giao diện và sổ tay đã ghi đúng khoảng cách **giữa tâm ô**; khoảng cách tới biên đa giác thực vẫn **chưa kiểm chứng**. | Đối chiếu với khoảng cách đến biên đa giác tại cụm HH phức tạp và nhiều lưới. |
| G08 | P1 | Đã chặn năm ngược: `year_t0 < year_t1` trong hàm lõi và giao diện; có kiểm thử hồi quy mới. | Giữ nguyên bằng chứng hai kỳ đã hoàn tất, không chạy lại chỉ vì bổ sung ràng buộc. |
| G09 | P1 | Đã chặn phép tính Shorrocks bốn nhóm khi thiếu một phân vị ban đầu (hoặc dưới 12 ô đủ điều kiện): kết quả là `NaN`. Chuyển tiếp hai kỳ vẫn chỉ mang tính mô tả, không xác nhận chuỗi Markov dài hạn. | Còn mở: panel nhiều năm, độ nhạy khi đồng hạng, độ ổn định xác suất chuyển và ý nghĩa động học thực địa. |
| G10 | P1 | Đã bổ sung phép kiểm tùy chọn cộng **số lượt quan sát** `cf_cvg` theo tháng (khác đếm số tháng hợp lệ) và sàng lọc metadata A02. Chưa chứng minh được quy tắc trọng số theo số lần quan sát là tối ưu. | Cần cảnh VIIRS thực thiếu hỗ trợ, số lượt `cf_cvg` được trích xuất độc lập và so độ nhạy theo tháng. |
| G11 | P1 | Đã bổ sung kiểm tra phạm vi: từ chối vùng cực/đường đổi ngày không phù hợp một UTM và cảnh báo vùng rộng phải đối chiếu trắc địa. Chưa tự xác nhận độ đúng UTM cho mọi địa phương. | Cần so diện tích/khoảng cách với chuẩn trắc địa độc lập để khẳng định độ chính xác ở vùng rộng/đặc biệt. |
| G12 | P2 | Đã sửa: lưới lớn không dùng ngưỡng I > 0,3 để tạo cờ kết luận suy luận; chỉ số I mô tả và việc có chạy hoán vị được tách riêng. | Muốn kết luận có ý nghĩa ở lưới lớn cần phép kiểm và phân phối tham chiếu hợp lệ. |
| G13 | P2 | Giao diện đã cảnh báo và xuất khoảng cách năm GHSL–VIIRS nếu hai mốc khác nhau. Kết quả Thượng Hải đã xác minh được giữ nguyên. | Suy luận đồng thời theo năm cần proxy có ngày độc lập hoặc kiểm chứng độ nhạy thời gian. |
| G14 | P2 | Các ngưỡng Jaccard/tần suất lõi/SD/độ dịch chuyển là quy ước; UI nay gọi trùng cao là mức heuristic, không phải kết luận thống kê xanh. | Cần đường nhạy thực nghiệm nếu muốn khẳng định ngưỡng có giá trị phổ quát. |
| G15 | P2 | `moran_I_lit` là trung bình Local Moran, không phải Global Moran I. | Bảo đảm mọi giải thích trên giao diện và CSV phân biệt hai đại lượng. |
| G16 | Đóng trong phạm vi nhận dạng nguồn | Link tài liệu bằng chứng đã dùng `VCMSLCFG` đúng với `GEE_DATASET` vận hành; thêm kiểm thử hồi quy nhận dạng nguồn. | Chỉ cần đối chiếu lại nếu thay mã sản phẩm VIIRS; không chạy lại V11. |
| G17 | P1 | Giữ nguyên mô phỏng Gaussian/LISA đã lưu; giao diện nay nói rõ chưa xác minh bảo đảm FDR thực địa. **Bảo đảm FDR thực vẫn mở.** | Xác minh giả thuyết không, họ kiểm định và điều kiện phụ thuộc/PRDS theo tham chiếu không gian phù hợp. |
| G18 | P1 | Giữ bằng chứng mô phỏng zero/thiếu quan sát. Trình kiểm tra thực địa mới từ chối cảnh đủ quan sát hoặc metadata không rõ; **chưa khẳng định đã kiểm chứng thực địa**. | Phải dùng cảnh VIIRS thật có thiếu hỗ trợ A02 và bảng đối chiếu quan sát nguồn độc lập. |

**G09: Sửa có giới hạn (19/11/2026).** Công thức Shorrocks bốn nhóm trước đây dùng `(4 - trace(P)) / 3` ngay cả khi một hoặc nhiều phân vị ban đầu không có ô, được lưu dưới dạng hàng toàn 0 trong bảng chuyển tiếp. Những hàng này không phải phân phối xác suất. Với lưới 4×4 ô đầy đủ, tám ô NTL bằng 0 và tám ô có cùng mức sáng, tất cả giữ nguyên giữa hai kỳ, công thức cũ trả **0,6667** dù không có ô nào chuyển nhóm. Hàm đã sửa trả `NaN`, trạng thái `undefined_empty_initial_quartile` và danh sách phân vị nguồn bị rỗng; trường hợp đủ bốn nhóm và không có chuyển dịch vẫn trả **0**. Để giữ tương thích, các bảng Markov cũ vẫn để hàng 0 đối với nhóm nguồn rỗng, nhưng giao diện cảnh báo đây là giá trị chưa xác định. Đây là phép kiểm bất biến số học, **không phải** kiểm chứng thực địa mới hay xác nhận giả định Markov dài hạn.

### Chốt kiểm toán G01-G18 trong một đợt (19/11/2026)

**Một sổ theo dõi, không phát sinh thêm danh sách gap:** [Bảng trạng thái 18 mục có cấu trúc máy đọc được](scientific_closure_register.json). Phân biệt *đã sửa và kiểm thử số học*, *đại lượng mô tả có giới hạn phát biểu* và *kết luận còn đòi hỏi dữ liệu thực độc lập*. Giới hạn diễn giải đã được ghi nhận không tự nó chứng minh có lỗi triển khai mới.

- **Các biện pháp đã triển khai:** G10 có phép kiểm bổ sung cộng **số lượt quan sát** từ `cf_cvg` theo tháng, phân biệt với số tháng hợp lệ. G10/G18 có sàng lọc metadata và chương trình so sánh trên một cảnh thực có hỗ trợ quan sát không đầy đủ; G12 đã tách cờ suy luận Moran phần dư khỏi ngưỡng mô tả; G13 cảnh báo chênh mốc GHSL–VIIRS; G17 cảnh báo giới hạn đảm bảo FDR thực địa. Không đổi trung vị VIIRS vận hành, Local Moran, Gini, mô phỏng G17 hay bằng chứng V11.
- **Quy trình thu thập bằng chứng thực địa G10/G18, chỉ khi tìm được cảnh thiếu hỗ trợ thật:** (1) Lưu CSV A02 thực và GeoJSON đa giác ô của **cùng** địa phương, lưới và năm; không dùng lại Bảo An đã quan sát đủ. (2) Trích xuất độc lập ba lớp `ref_observed_fraction`, `ref_mean_valid_months`, `ref_cf_cvg_total` trên lưới pixel nguồn bằng [script Earth Engine](g10_independent_support_gee.js); phải chọn năm và vẽ/import đúng geometry nghiên cứu. (3) Chạy `python validation/g10_reference_zonal.py --source-raster SOURCE.tif --grid-geojson CELLS.geojson --year YEAR --trusted-gee-export --out REFERENCE.csv` ([mã nguồn](g10_reference_zonal.py)), đối chiếu hash và xuất xứ tác vụ. (4) Chạy `python validation/g10_g18_field_audit.py --input REAL_A02_CELLS.csv --out-dir OUTPUT_DIR --independent-reference REFERENCE.csv` ([mã nguồn](g10_g18_field_audit.py)). Chương trình yêu cầu 30–20.000 ô, tọa độ chiếu cùng EPSG, có ít nhất một ô không quan sát và một ô NTL sau cắt bằng 0 nhưng có hỗ trợ, đồng thời từ chối metadata không rõ/cảnh đủ quan sát. Kết quả gồm CSV theo ô và JSON có hash, seed, các quy tắc so sánh. Đối chiếu số học nguồn độc lập **không tự chứng minh provenance nguồn hoặc mô hình trọng số theo cf_cvg là đúng**.
- **Chưa thể đóng về mặt khoa học nếu chưa có bằng chứng ngoài:** G04 tiếp cận thị trường kinh tế, G05 CBD thực, G06 quy luật Pareto có phụ thuộc không gian, G10/G18 sai lệch ở cảnh VIIRS thực thiếu dữ liệu, G17 hiệu chuẩn FDR thực địa, G11 độ chính xác vùng địa lý cực đoan và G09 Markov dài hạn. Đây là các **kết luận phải giới hạn**, không phải yêu cầu chạy lại kiểm chứng số học A02/V11/GHSL đã hoàn tất.
- **Điểm dừng hợp lệ:** báo rõ phiên bản raster, vùng-năm, hỗ trợ A02, CRS/lưới, chính sách số 0, hoán vị và họ kiểm định, độ nhạy không gian, cùng đại lượng thực sự tính. CI xanh hoặc test nhân tạo không phải chứng cứ tự động cho tính đúng kinh tế, quan hệ nhân quả hoặc kiểm soát FDR thực địa.

Đây là lần chốt **phần sửa code và sổ bằng chứng có thể hoàn thành khi chưa có dữ liệu thực mới**; không đồng nghĩa cả 18 vấn đề đã được xác minh toàn diện.

### G04: Tiềm năng NTL có trọng số khoảng cách và kiểm chứng độ nhạy (19/11/2026)

**Dữ liệu thực sự được dùng và dữ liệu không có trong phép tính.** Ứng dụng đang sử dụng NTL VIIRS, diện tích ô, tọa độ ô trên lưới chiếu và tham số hàm suy giảm theo khoảng cách. `SOL = NTL × diện tích ô`; khoảng cách Euclid chỉ thể hiện độ gần nhau về địa lý, không phải thời gian đi lại hay chi phí vận tải được quan sát. **Ứng dụng không nạp dữ liệu việc làm, dân số, thu nhập, sức mua, kết quả thị trường hoặc mạng giao thông để tính chỉ số này.** Số "việc làm" bên dưới hoàn toàn do mã kiểm chứng tạo ra để thử ý nghĩa của chỉ số: không phải việc làm khảo sát thực, và không được ứng dụng dùng làm đầu vào. Vì vậy **không cần dữ liệu kinh tế để tính chỉ số NTL**, nhưng chưa thể khẳng định nó đo tiếp cận thị trường kinh tế.

**Đại lượng được kiểm tra.** Mã hiện hành tính $P_i=\sum_{j\ne i}w_{ij}SOL_j$ và $`\widetilde{P}_i = P_i - \overline{SOL}_{core}\sum_{j \ne i} w_{ij}`$, với $w_{ij}=\exp(-\tau d_{ij})$ trong bán kính Euclid cố định trên lưới. Cấu hình mặc định dùng $\tau=0,5$ mỗi km và bán kính năm bước tại lưới 500 m, tức **2,5 km**; khoảng cách làm trọng số còn một nửa xấp xỉ 1,386 km. Phép biến đổi chỉ trừ **kỳ vọng theo hoán vị không hạn chế các giá trị SOL giữa ô lõi**, không phải phép đo chi phí vận tải thực tế hoặc phép tái định tâm theo một cơ chế phân bổ cú sốc ngoại sinh phục vụ nhận dạng nhân quả. Đẳng thức kỳ vọng đã được kiểm trong T07 trước đây và **không được chạy lại**.

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

### G06: Kiểm chứng đuôi Pareto bằng bootstrap có điều kiện (19/11/2026)

**Ước lượng Hill không đồng nghĩa xác nhận phân phối Pareto.** Ứng dụng hiện tính hệ số Hill cho 10% ô lõi có NTL dương sáng nhất. Hàm `ntl.lisa_diagnostics.ks_pareto` vẫn xuất **p-value KS xấp xỉ tiệm cận** sau khi hệ số alpha đã được ước lượng từ chính tập mẫu dùng kiểm định. T09 đã xác nhận phép tính số học trong trường hợp kiểm soát, **không đồng nghĩa đã hiệu chuẩn phép kiểm độ phù hợp phân phối**. G06 không tính lại kiểm chứng ảnh vệ tinh hoặc thay đổi hàm ước lượng vận hành, các khóa CSV và giá trị kết quả.

**Thiết kế kiểm chứng.** Chọn trước bốn tỷ lệ đuôi: 5%, 10%, 15% và 20% các ô lõi có NTL dương. Ở mỗi mức, ngưỡng `u` bằng giá trị sáng thứ `k+1`, đúng quy tắc hiện hành của Hill; `k` ô sáng nhất tạo thành tập quan sát đuôi. Tính $\widehat\alpha=1/\overline{\log(x/u)}$ và thống kê KS theo hàm phân phối Pareto có điều kiện đã khớp alpha. Sau đó tạo **399 mẫu bootstrap Pareto cho mỗi tổ hợp**, giữ cố định ngưỡng `u` và kích thước mẫu đuôi `k`. **Mỗi mẫu bootstrap đều được ước lượng lại alpha**, rồi tính lại KS theo tham số mới. p-value tham chiếu bằng $`(1+\#{D^{*}\ge D_{\mathrm{obs}}})/(399+1)`$. Vì vậy, p nhỏ nhất có thể ghi là **0,0025**, không phải bằng 0; khoảng tin cậy 95% phản ánh bất định hữu hạn từ số lượt mô phỏng.

**Giới hạn quan trọng:** Bootstrap này **giữ nguyên `u`, `k` và giả định các giá trị vượt ngưỡng độc lập cùng phân phối**. Nó **không chọn lại ngưỡng thấp nhất trong từng lần mô phỏng**, nên chưa phải đầy đủ quy trình của Clauset, Shalizi và Newman (2009). Với NTL VIIRS thực, các ô kế nhau có phụ thuộc không gian; do đó p-value trên Bảo An chỉ là **chuẩn tham chiếu theo giả định độc lập có điều kiện**, **không phải p-value thực địa đã được hiệu chuẩn phụ thuộc không gian**.

**Ba trường nhân tạo, mỗi trường 5.000 quan sát độc lập.** Chương trình có seed cố định tạo một phân phối Pareto với hệ số đúng bằng 2,5, một phân phối lognormal và một phân phối exponential có dịch gốc. Bảng CSV lưu toàn bộ giá trị đầu vào. Qua bốn ngưỡng:

| Phân phối sinh dữ liệu biết trước | Khoảng p-value KS bootstrap | So sánh ứng viên bằng AICc |
| --- | ---: | --- |
| Pareto, alpha thật bằng 2,5 | 0,4050 đến 0,8075 | Pareto có AICc thấp nhất ở 3/4 trường hợp, lognormal ở 1/4 |
| Lognormal | 0,0025 đến 0,0850 | Lognormal cắt ngưỡng có AICc thấp nhất ở 4/4 |
| Exponential có dịch gốc | 0,0025 đến 0,0500 | Exponential có AICc thấp nhất ở 3/4, lognormal cắt ngưỡng ở 1/4 |

Việc không bác bỏ ở một ngưỡng ngắn, chẳng hạn 5% với dữ liệu lognormal (p = 0,085), **không chứng minh có quy luật Pareto**. Khi chỉ giữ số ít giá trị lớn nhất, phép thử có thể thiếu sức phân biệt.

**NTL thực Bảo An năm 2020, chỉ kiểm chứng giả định độc lập có điều kiện.** Dùng đúng CSV VIIRS 7.148 ô đã kiểm tra A02. **6.186 ô lõi có NTL dương** đi vào phân tích; 962 ô biên vẫn hiện diện trong bảng nối theo mã ô nhưng không vào phép khớp. Không lấy thêm biến kinh tế hoặc dữ liệu ảnh vệ tinh mới.

| Nhóm ô lõi sáng nhất | Số ô đuôi `k` | Hệ số Hill | p-value KS cũ | p-value KS bootstrap ước lượng lại alpha | AICc nhỏ nhất |
| --- | ---: | ---: | ---: | ---: | --- |
| 5% | 309 | 5,6726 | 0,00665 | 0,0025 | Pareto |
| 10% (mặc định ứng dụng) | 618 | 5,5904 | 0,09511 | 0,0225 | Pareto |
| 15% | 927 | 4,6953 | 0,000009 | 0,0025 | Lognormal cắt ngưỡng |
| 20% | 1.237 | 4,0730 | Rất gần 0 ở độ chính xác hiển thị | 0,0025 | Lognormal cắt ngưỡng |

**Diễn giải:** Ở ngưỡng 10% ứng dụng thường dùng, p-value xấp xỉ cũ bằng 0,09511, còn bootstrap **theo giả định độc lập có điều kiện** bằng 0,0225 trên cùng 618 ô. Hai phương pháp có thể dẫn tới đánh giá khác nhau ở mức 5%. Nhưng **không được kết luận đã bác bỏ Pareto cho toàn bộ trường NTL Bảo An** theo tiêu chuẩn thống kê thực địa, vì bootstrap này chưa điều chỉnh tự tương quan không gian và cố định ngưỡng thứ tự từ mẫu. Với 399 lượt bootstrap, p = 0,0025 nghĩa là không lượt nào có KS sau tái ước lượng lớn hơn hoặc bằng KS quan sát, trong giới hạn Monte Carlo. Đồng thời, **AICc là so sánh tương đối**: Pareto thắng ở 5% và 10% dù phép KS bootstrap theo giả định độc lập không ủng hộ ở ngưỡng 5%. Không có mâu thuẫn, bởi mô hình tốt nhất trong ba ứng viên chưa chắc phù hợp tuyệt đối với dữ liệu.

**Phân phối đối chiếu:** Mô hình exponential của phần vượt ngưỡng và lognormal **được cắt trái tại cùng ngưỡng `u`** đều được ước lượng riêng trên **cùng `k` quan sát đuôi**, rồi so với Pareto bằng AICc và chênh lệch KS mô tả. Cách này tránh so likelihood vô điều kiện của lognormal với likelihood có điều kiện của Pareto. Đây không phải phép kiểm tỷ số likelihood có p-value; tham số lognormal sau khớp được lưu riêng.

**Bằng chứng đầy đủ có thể tái lập:** [chương trình sinh phép kiểm](g06_pareto_tail_experiment.py), [5.000 đầu vào nhân tạo](evidence/g06_pareto_tail/synthetic_input.csv), [7.148 ô Bảo An gốc có cờ lõi, quan sát dương và thứ hạng](evidence/g06_pareto_tail/baoan_tail_observations.csv), [16 trường hợp phân phối/ngưỡng](evidence/g06_pareto_tail/tail_cases.csv), [6.384 lần bootstrap có hệ số alpha và KS sau ước lượng lại](evidence/g06_pareto_tail/bootstrap_replications.csv), [JSON tổng hợp, phiên bản thư viện, mã băm SHA-256 và giới hạn](evidence/g06_pareto_tail/summary.json). CSV gốc Bảo An đã nằm tại `validation/evidence/a02_post_pr27/`. CI sẽ chạy và đối chiếu **đúng từng byte của cả năm tệp mới** bằng các thư viện khóa phiên bản.

**G06 thực địa còn mở:** Kết quả **không chứng nhận NTL có quy luật Pareto**, không xác lập quan hệ kinh tế hoặc nhân quả. Cần mô phỏng giả thuyết không có cấu trúc phụ thuộc không gian hoặc bootstrap theo khối địa lý, kiểm tra tính khác biệt của quá trình đo theo thời gian và quy trình chọn ngưỡng đã đăng ký trước hoặc được bootstrap cùng bước tối ưu ngưỡng. Tham khảo [Clauset, Shalizi và Newman (2009)](https://doi.org/10.1137/070710111). Cờ `power_law_ok` cũ chỉ là **phép sàng lọc KS xấp xỉ**, không phải kết luận đã xác thực quy luật ở thực địa; phần diễn giải trên giao diện đã được bổ sung cảnh báo.

### G05: Độ nhạy khi chọn tâm từ NTL để ước lượng độ dốc và R² (19/11/2026)

**Phạm vi của chỉ số.** Ứng dụng tính `urban_gradient_decay` và `monocentric_r2` trên **cùng tập NTL đã dùng để chọn tâm**. Tâm được xác định bằng trọng tâm SOL của cụm HH có ý nghĩa lớn nhất đủ điều kiện; nếu không tồn tại cụm đủ điều kiện, chương trình chọn ô có điểm kết hợp NTL và NTL trung bình láng giềng cao nhất. Sau đó ứng dụng hồi quy có trọng số diện tích giữa $\log(1+\mathrm{NTL}_i)$ và khoảng cách Euclid từ tâm. Đây là **độ dốc mô tả khớp trong mẫu**, không tự xác nhận CBD kinh tế, cấu trúc đơn tâm hoặc tác động nhân quả. Công thức WLS hiện hành và cấu trúc CSV cũ không bị thay đổi.

**Phần A: mô phỏng có tâm được xác định trước.** Trên lưới 25 × 25 ô, tâm của cơ chế sinh dữ liệu được cố định **trước khi tạo ánh sáng**. Nó được biết đúng nhờ thiết kế nhân tạo, **không phải CBD thực địa được quan sát độc lập**. Ba trường dùng chung nhiễu nền: bức xạ quanh tâm gốc, sau đó bổ sung một nguồn sáng không đại diện trung tâm hoạt động, với biên độ 60 hoặc 170. Trên mỗi trường, chương trình gọi chính `run_lisa` để chọn tâm, dùng Queen, 999 hoán vị, BH-FDR mức 0,05, cụm tối thiểu bốn ô. Tâm lấy từ khoảng cách đã được làm tròn trong kết quả được kiểm tra lại bằng độ dốc ứng dụng. Số cụm HH đủ điều kiện lần lượt là một, hai và một.

| Bề mặt NTL nhân tạo | Khoảng lệch giữa tâm LISA và tâm sinh dữ liệu | R² theo tâm đã biết | R² theo tâm LISA | Độ dốc $\gamma$ theo tâm LISA, mỗi km |
| --- | ---: | ---: | ---: | ---: |
| Không có nguồn sáng gây nhiễu | 0,025 km | 0,874 | 0,874 | 0,3752 |
| Nguồn sáng không đại diện hoạt động, biên độ 60 | 0,090 km | 0,533 | 0,541 | 0,3067 |
| Nguồn sáng gây nhiễu mạnh, biên độ 170 | 6,335 km | 0,304 | 0,128 | 0,1059 |

Ở kịch bản nhiễu mạnh, tâm chọn từ NTL dịch chuyển khỏi tâm gốc và độ dốc thay đổi từ 0,2579 xuống 0,1059 mỗi km. **Chọn tâm theo NTL không nhất thiết làm R² tăng**: trong ví dụ này R² giảm khoảng 0,176, còn kịch bản nhiễu vừa làm R² tăng khoảng 0,008. Các kết quả là phản ứng dưới một cơ chế mô phỏng đã nêu, không phải ước lượng thiên lệch phổ quát.

Ngoài ra, có 80 lần lặp theo seed cho mỗi trường, so tâm gốc với trọng tâm hình học, tâm trọng số NTL và ô sáng nhất. **960 quan sát cấp lần chạy** đã được lưu. Khoảng phân bố mô phỏng này chỉ áp dụng cho các cách chọn tâm thay thế tính nhanh; tâm production dùng cụm HH chỉ được chạy trên ba trường NTL được lưu đầy đủ, **không được tính lại trong cả 240 lần lặp**. Không được lấy độ bất định của các tâm thay thế để suy ra độ bất định của thuật toán chọn tâm HH.

**Phần B: NTL thực tại Bảo An 2020, chưa có CBD kinh tế độc lập.** Dùng lại đúng CSV VIIRS 7.148 ô đã kiểm tra A02, ước lượng cùng phương trình $\log(1+\mathrm{NTL})$ và cùng trọng số diện tích cho **6.186 ô lõi đầy đủ**. Không trích xuất lại VIIRS hoặc chạy lại A03/LISA. Tâm đã chọn trong kết quả lịch sử được tái dựng hình học từ `dist_to_core_km` lưu trong CSV, làm tròn đến 0,001 km; độ lệch tuyệt đối trung vị giữa khoảng cách tái dựng và khoảng cách nguồn là **0,254 m**, phân vị 99% là **0,505 m**. Đây là **tâm suy ra từ NTL trong lần chạy cũ**, không phải CBD được xác định bên ngoài.

| Quy tắc chọn tâm Bảo An 2020 | Khoảng cách tới tâm NTL lịch sử | Độ dốc $\gamma$, mỗi km | R² nội mẫu |
| --- | ---: | ---: | ---: |
| Tâm NTL được chọn từ kết quả trước đây | 0 km | 0,02601 | 0,37988 |
| Trọng tâm hình học có trọng số diện tích | 33,000 km | 0,02736 | 0,10613 |
| Tâm theo trọng số NTL cùng năm | 22,833 km | 0,04070 | 0,34348 |
| Ô NTL sáng nhất cùng năm | 9,326 km | 0,02677 | 0,37505 |

Đây chỉ là **độ nhạy khi đổi tâm trong cùng vùng và cùng năm**, không phải bảng xếp hạng mức độ chính xác CBD kinh tế. Trọng tâm hình học không dùng NTL khi tính, nhưng **không được xác nhận là tâm việc làm**; hai cách chọn tâm còn lại cũng phụ thuộc NTL. Tất cả hồi quy cùng dùng 6.186 ô và cùng biến phụ thuộc, nên khác biệt xuất phát từ quy tắc chọn tâm chứ không phải do thay đổi mẫu. Chênh lệch R² tới khoảng 0,274 là dấu hiệu cần diễn giải thận trọng `monocentric_r2`, không dùng nó làm phép kiểm đô thị đơn tâm trong kinh tế học.

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

#### G17: Hiệu chuẩn giả thuyết không cấp nguồn trên hình học raster thực

**Đại lượng và lý do kiểm chứng.** Hoán vị cấp ô kiểm định phân bổ ngẫu nhiên của các giá trị ô. Null cấp pixel độc lập là giả thuyết khác khi ô dùng chung pixel (G23). Cần phân biệt độ hợp lệ của p-value theo null đã chọn với công thức hiệu chỉnh BH/BY.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Chọn cửa sổ 8×8 hoàn chỉnh đầu tiên theo thứ tự chỉ số lưới Bảo An (64 ô, 102 pixel), giữ nguyên trọng số giao đã chuẩn hóa. Sinh 999 trường tham chiếu và 400 trường thử độc lập từ pixel Gaussian độc lập, seed 171723. Tính Local I trên giá trị ô chuẩn hóa bằng độ lệch chuẩn mẫu và lag Queen trung bình. Một phân phối tham chiếu lấy trực tiếp từ các trường nguồn; phân phối còn lại lấy mẫu láng giềng cấp ô không hoàn lại, giữ giá trị ô trung tâm. Dùng p hai phía nhân đôi đuôi nhỏ hơn có hiệu chỉnh +1, giới hạn 1; áp dụng raw, BH, BY tại alpha 0,05.

**Kết quả.**

| Chỉ tiêu (400 trường thử, 25.600 phép kiểm cấp ô) | Hoán vị cấp ô | Tham chiếu cấp nguồn |
| --- | ---: | ---: |
| Tỷ lệ p ≤ 0,05 | 10,5547% | 5,1836% |
| Raw: số lượt có ít nhất một bác bỏ | 394 | 385 |
| BH: số lượt có ít nhất một bác bỏ | 21 | 2 |
| BY: số lượt có ít nhất một bác bỏ | 0 | 0 |
| Tỷ lệ có bác bỏ BH dưới null cấp nguồn | 5,25% | 0,5% |

Tỷ lệ p biên và tỷ lệ trường có bác bỏ là hai đại lượng khác nhau. Trong thiết kế toàn-null cấp nguồn, tỷ lệ có ít nhất một bác bỏ là FDR thực nghiệm theo null đó.

**Bằng chứng lưu trữ.** [Chương trình null cấp nguồn](g17_source_support_null.py), [JSON kết quả và SHA-256 dữ liệu nguồn](evidence/g20_g23_g17_raster_summary.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Một cửa sổ, một mô hình pixel iid và bảng tham chiếu dùng chung giữa các trường thử; các tỷ lệ phụ thuộc thiết kế này. P nhỏ nhất 0,002 hạn chế đáng kể BH/BY, nhất là BY. Kết quả không chứng minh BH sai theo null random placement cấp ô và không xác nhận kiểm soát FDR thực địa. Cần thử nhiều hình học, độ phân giải, mô hình covariance nguồn và số lượt tham chiếu; định nghĩa null trước khi diễn giải.

### Bằng chứng tổng hợp G18 (phạm vi giới hạn, 18/11/2026)

**Bằng chứng thực bổ sung cho G18 tại Kỳ Môn 2016:** 49 ô app được phân loại NTL bằng 0 đều có metadata đã quan sát và tỷ lệ nguồn radiance âm 1; 47/47 ô có raster tham chiếu giao phủ cũng cho NTL bằng 0 sau căn chỉnh. Trong 9.143 ô, **không có `no_observation`**. Đây là kiểm chứng **nguồn gốc số 0 do cắt âm**, không phải mô phỏng missing-versus-zero trên ca thiếu quan sát thật. Đường căn chỉnh dùng lưới pixel 2020 và còn 23 ô biên chưa phủ, nên không thể gọi là khớp geotransform app 2016 tuyệt đối. Xem [phương pháp và mã băm nguồn](evidence/README-vi.md#kiểm-tra-g10g18-tại-kỳ-môn-2016-số-0-có-quan-sát).

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

#### G10/G18: Phân biệt số 0, bức xạ âm và hỗ trợ quan sát thực tế

**Đại lượng và lý do kiểm chứng.** Các trường chất lượng A02 phân biệt bức xạ có quan sát với giá trị thiếu và các giá trị bị cắt về 0. Một ô có NTL xuất bằng 0 không nhất thiết là ô tối thực đo; cần kiểm tra đồng thời hỗ trợ quan sát và nguồn gốc radiance.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Đối chiếu năm CSV cấp ô (Kỳ Môn 2014, 2016, 2020; Bảo An 2020; Thượng Hải 2020), đếm riêng `dq_status`, `dq_observed_fraction`, `dq_mean_valid_months`, `dq_stat_missing`, `dq_negative_fraction` và NTL bằng 0. Kiểm tra bổ sung `cf_cvg` tại các pixel hữu hạn trong raster hỗ trợ Bảo An 2020 và Kỳ Môn 2016. Không suy từ pixel ngoài mặt nạ AOI rằng nguồn VIIRS không có quan sát.

**Kết quả.**

| Địa bàn và năm | Số bản ghi CSV | Tỷ lệ hỗ trợ đầy đủ |
| --- | ---: | ---: |
| Kỳ Môn 2014 | 9.143 | 100% |
| Kỳ Môn 2016 | 9.143 | 100% |
| Kỳ Môn 2020 | 9.143 | 100% |
| Bảo An 2020 | 7.148 | 100% |
| Thượng Hải 2020 | 886 | 100% |
| Tổng | 35.463 | 100% |

Không có cờ thiếu thống kê hoặc ô có số tháng hợp lệ dưới ba. Trong các raster hỗ trợ, 8.909 pixel hữu hạn Bảo An và 12.202 pixel hữu hạn Kỳ Môn đều có `cf_cvg` dương. Kỳ Môn 2016 có 56 giá trị NTL bằng 0 trong CSV và 2.487 ô có tỷ lệ radiance âm lớn hơn 0. Con số 56 bao gồm khả năng làm tròn và không thay thế 49 ô zero đã xác nhận trong phép đối chiếu nguồn G18 ở trên.

**Bằng chứng lưu trữ.** [Chương trình đối chiếu CSV và mô phỏng số học](g19_g29_independent_audit.mjs), [JSON kết quả](evidence/g19_g29_independent_audit.json); [Chương trình đối chiếu raster và hình học](g20_g23_raster_audit.py), [JSON kết quả và SHA-256 dữ liệu nguồn](evidence/g20_g23_g17_raster_summary.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Các mẫu này xác nhận trạng thái hỗ trợ của dữ liệu đã xuất, không cung cấp trường hợp thiếu quan sát thực sự. Không thể dùng chúng để định lượng ảnh hưởng thực địa của zero-fill. Cần một cảnh có pixel hoặc ô thiếu hỗ trợ được xác minh độc lập từ số lượt quan sát nguồn, sau đó so chính sách xử lý trên đúng hình học.

### G19: Ảnh hưởng của dữ liệu thiếu và zero-fill lên thống kê NTL

**Đại lượng và lý do kiểm chứng.** Tại tầng tạo raster và thống kê vùng, `median.unmask(0.0)` và `fillna(0.0)` có thể biến giá trị chưa quan sát thành số 0. Cờ chất lượng không tự thay đổi các chỉ số sử dụng NTL đã điền. Cần kiểm chứng liệu chính sách này có làm thay đổi đại lượng đo, ngay cả khi các giá trị quan sát được không đổi.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Dùng bốn ô bằng diện tích, trong đó ô thứ ba thiếu quan sát. Tập legacy là [10, 20, 0, 30], tập có hỗ trợ là [10, 20, 30]. Trung bình là tổng các giá trị chia số ô; Gini tính từ tổng chênh lệch tuyệt đối giữa mọi cặp, chia hai lần bình phương số ô nhân trung bình. Hai phép tính chỉ khác tập mẫu, không khác giá trị ở các vị trí quan sát được.

**Kết quả.**

| Chính sách | Số ô | NTL trung bình | Gini |
| --- | ---: | ---: | ---: |
| Điền 0 vào ô thiếu | 4 | 15 | 0,416666667 |
| Chỉ xét ô có quan sát | 3 | 20 | 0,222222222 |

Trung bình trên tập quan sát cao hơn 5 đơn vị; Gini cũng thay đổi dù không chỉnh sửa ba quan sát dương.

**Bằng chứng lưu trữ.** [Chương trình đối chiếu CSV và mô phỏng số học](g19_g29_independent_audit.mjs), [JSON kết quả](evidence/g19_g29_independent_audit.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Phản ví dụ xác nhận độ nhạy của mean và Gini, không xác định giá trị thật của ô thiếu, mean thật toàn vùng hay hướng sai lệch phổ quát. Để đánh giá production, cần đối chiếu SOL, mean, Gini, tỷ lệ sáng, Global/Local Moran và diện tích hỗ trợ dưới các chính sách legacy, tập quan sát và ngưỡng hỗ trợ định trước trên cảnh thiếu quan sát thực. G10/G18 cung cấp điều kiện dữ liệu cho phép kiểm đó.

### G20: Tính toàn vẹn của lưới pixel khi ghép tile VIIRS

**Đại lượng và lý do kiểm chứng.** Cùng CRS và kích thước pixel chưa bảo đảm các tile có chung điểm gốc. Nếu affine transform, mask hoặc giá trị tại đường nối khác nhau, thao tác ghép có thể làm thay đổi raster đầu vào của zonal statistics. Phép kiểm offline cô lập riêng bước ghép, không kiểm định dịch vụ tải ảnh.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Chia đúng raster VIIRS Median Bảo An 2020 thành bốn cửa sổ hàng/cột nguyên, lấy affine transform từng cửa sổ từ raster gốc. Ghép bằng `rasterio.merge(method='first')`. So kích thước, transform, mask hữu hạn và sai khác tuyệt đối trên từng pixel hữu hạn; khi so mảng thô, hai NaN tương ứng được coi là cùng trạng thái không có giá trị.

**Kết quả.**

| Đại lượng so sánh | Kết quả |
| --- | --- |
| Kích thước mosaic (hàng × cột) | 109 × 217 |
| Affine transform và mask hữu hạn | Trùng khớp |
| Pixel hữu hạn được so | 8.909 |
| Sai khác tuyệt đối lớn nhất | 0 |
| Số pixel sai khác sau khi đồng nhất NaN | 0 |

**Bằng chứng lưu trữ.** [Chương trình đối chiếu raster và hình học](g20_g23_raster_audit.py), [JSON kết quả và SHA-256 dữ liệu nguồn](evidence/g20_g23_g17_raster_summary.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Xác nhận phép ghép bốn tile đã căn chỉnh đúng giữ nguyên raster trong điều kiện thử. Chưa xác nhận các tile Earth Engine tải độc lập tự có chung lattice. Phép kiểm còn lại phải giữ cố định AOI, năm, sản phẩm và affine transform native; so single-tile, multi-tile và bản native-aligned ở tất cả band, mask, mép nối và kết quả theo polygon. Tham khảo [hướng dẫn export ảnh của Earth Engine](https://developers.google.com/earth-engine/guides/exporting_images).

### G26: Hỗ trợ quan sát chung trong phân tích không gian và thời gian

**Đại lượng và lý do kiểm chứng.** Biến động extensive margin, Markov và spatial lag chỉ có thể diễn giải trên các vị trí có phép đo so sánh được. Nếu năm đầu thiếu quan sát nhưng được điền 0, một giá trị dương năm sau có thể bị gọi là chuyển từ tối sang sáng mà không có bằng chứng.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Đối chứng hai kỳ với t0=[10,0,0,5], t1=[10,8,0,5]. Zero thứ nhất của t0 là giá trị thiếu, zero thứ hai là quan sát thực. Tỷ lệ entry bằng số ô zero đầu kỳ chuyển sang dương chia số ô zero đầu kỳ trong tập được xét. Với dữ liệu thực, ghép từng cặp năm Kỳ Môn 2014, 2016, 2020 theo `grid_id` và kiểm tra bằng nhau của tọa độ tâm chiếu, tâm địa lý và diện tích đã xuất.

**Kết quả.**

| Tập mẫu nhân tạo | Entry / số ô zero đầu kỳ | Tỷ lệ entry |
| --- | ---: | ---: |
| Legacy zero-fill | 1/2 | 50% |
| Có hỗ trợ ở cả hai kỳ | 0/1 | 0% |

| Cặp năm Kỳ Môn | ID khớp | Tâm và diện tích xuất khớp | Dương sang zero CSV | Zero CSV sang dương |
| --- | ---: | ---: | ---: | ---: |
| 2014–2016 | 9.143 | 9.143 | 56 | 0 |
| 2014–2020 | 9.143 | 9.143 | 0 | 0 |
| 2016–2020 | 9.143 | 9.143 | 0 | 56 |

Tất cả các cặp có hỗ trợ quan sát đầy đủ theo metadata. Zero trong bảng là giá trị xuất, không phải nhãn kinh tế.

**Bằng chứng lưu trữ.** [Chương trình đối chiếu CSV và mô phỏng số học](g19_g29_independent_audit.mjs), [JSON kết quả](evidence/g19_g29_independent_audit.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Ví dụ nhân tạo xác nhận cơ chế entry giả; kết quả Kỳ Môn xác nhận tính nhất quán của thuộc tính lưới xuất chứ không xác nhận polygon giống hệt, không phải bằng chứng missingness và không đo chuyển đổi kinh tế. Cần cảnh thiếu thực qua hai kỳ, giữ tập hỗ trợ chung, kiểm tra Markov, lag và extensive margin; báo rõ số ô/diện tích bị loại.

### G11: Độ chính xác diện tích UTM so với diện tích ellipsoid

**Đại lượng và lý do kiểm chứng.** Ứng dụng tính diện tích trong CRS chiếu để xác định ô biên, trọng số diện tích và SOL. UTM có độ biến dạng diện tích không bằng 0; cần đo trực tiếp trên polygon thay vì suy từ kích thước lưới danh nghĩa.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Dùng toàn bộ polygon xuất tại Bảo An và Kỳ Môn. Tính diện tích phẳng sau khi chuyển sang UTM được khai báo trong thuộc tính tọa độ; tính diện tích ellipsoid WGS84 bằng `pyproj.Geod`, với các đoạn trắc địa giữa đỉnh. Sai lệch tương đối tuyệt đối mỗi ô là abs(A_UTM/A_geod - 1); thống kê trung bình và cực đại trên toàn bộ tập polygon.

**Kết quả.**

| Địa bàn | Số ô | Sai lệch tương đối trung bình | Sai lệch tương đối lớn nhất |
| --- | ---: | ---: | ---: |
| Bảo An | 7.148 | 0,13057% | 0,19250% |
| Kỳ Môn | 9.143 | 0,07141% | 0,07907% |

**Bằng chứng lưu trữ.** [Chương trình đối chiếu raster và hình học](g20_g23_raster_audit.py), [JSON kết quả và SHA-256 dữ liệu nguồn](evidence/g20_g23_g17_raster_summary.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Định lượng sai khác diện tích tại hai địa bàn; không phải chuẩn dung sai áp dụng cho mọi vùng. Chưa đo sai số khoảng cách, miền qua nhiều múi UTM, cực hoặc đường đổi ngày. Sai lệch diện tích UTM khác câu hỏi về trọng số giao raster trong G21.

### G21: Trung bình raster theo diện tích góc và diện tích vật lý

**Đại lượng và lý do kiểm chứng.** Trong raster EPSG:4326 có pixel cùng kích thước góc, trọng số tỷ lệ phủ tương đương trọng số diện tích góc. Diện tích vật lý của pixel thay đổi theo vị trí, vì vậy hai đại lượng trung bình không đồng nhất một cách toán học.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Tạo polygon pixel bằng affine transform nguồn, giao với polygon đúng ID của app và loại pixel không hữu hạn. Với mỗi ô, lấy tổng radiance nhân diện tích giao chia tổng diện tích giao; tính một lần với diện tích góc và một lần với diện tích ellipsoid WGS84. So sai khác tuyệt đối theo ô, tương quan thứ hạng Spearman và SOL tính bằng mean nhân diện tích thực được hỗ trợ (km²). Bảo An dùng VIIRS Median 2020, Kỳ Môn dùng band `clipped_median` của RAW_SUPPORT 2016. Phép giao sử dụng make_valid, buffer(0) và precision 1e-11 độ; diện tích ellipsoid tính theo đoạn trắc địa giữa đỉnh.

**Kết quả.**

| Chỉ tiêu | Bảo An 2020 | Kỳ Môn 2016 |
| --- | ---: | ---: |
| Ô có kết quả hữu hạn để so | 7.147 | 9.143 |
| Ô có hỗ trợ hình học ≥ 0,999 | 7.103 | 9.117 |
| Mean sai khác tuyệt đối | 0,000009862 | 0,000000114 |
| Phân vị sai khác 95% | 0,000034017 | 0,000000225 |
| Sai khác lớn nhất | 0,000299313 | 0,000018815 |
| Spearman rho | 0,9999999998 | 0,9999999993 |
| SOL dùng mean theo diện tích góc | 34.196,306051 | 115,380656 |
| SOL dùng mean theo diện tích vật lý | 34.196,307125 | 115,380622 |

Ngưỡng 0,999 chỉ phân tầng hỗ trợ hình học trong phép đối chiếu; không phải chuẩn chất lượng quan sát VIIRS.

**Bằng chứng lưu trữ.** [Chương trình đối chiếu raster và hình học](g20_g23_raster_audit.py), [JSON kết quả và SHA-256 dữ liệu nguồn](evidence/g20_g23_g17_raster_summary.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Sai khác nhỏ trên hai raster tham chiếu cụ thể, không phải sai số cảm biến, không phải phép chạy lại V11 và không bảo đảm tương đương toàn cầu. Diện tích giao raster hữu hạn không thay thế `cf_cvg`; SOL trên diện tích được hỗ trợ không đồng nghĩa SOL production. Cần mở rộng nếu nghiên cứu khác vĩ độ hoặc dùng AOI rộng. Tham khảo [exactextract operations](https://isciences.github.io/exactextract/operations.html).

### G22/A07: Trích xuất trực tiếp, gộp ô và hiệu ứng phân vùng MAUP

**Đại lượng và lý do kiểm chứng.** Thay đổi độ phân giải và điểm gốc lưới có thể đổi các đơn vị quan sát (MAUP). Gộp mean từ các ô 500 m chỉ tương đương trích xuất trực tiếp khi hình học và trọng số phù hợp. Bảo toàn SOL toàn vùng không đồng nghĩa bảo toàn hotspot.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Dùng hợp các polygon xuất Bảo An làm AOI (không phải ranh giới hành chính dựng độc lập). Dựng lưới UTM 1.000, 1.500 và 2.000 m với điểm gốc 0 hoặc dịch nửa cạnh ở cả X và Y; cắt theo AOI, bỏ mảnh có diện tích ≤ 0,0001 m², trích trực tiếp cùng raster. Tại gốc 0, gộp mean của ô 500 m bằng diện tích raster hữu hạn được hỗ trợ và so với coarse mean trực tiếp. So SOL và mean toàn vùng qua sáu cấu hình. Phép tính này không dùng trọng số block production.

**Kết quả.**

| Cạnh ô (m) | Dịch gốc (m) | Số ô | Ô có raster hữu hạn |
| --- | ---: | ---: | ---: |
| 1.000 | 0 | 1.921 | 1.920 |
| 1.000 | 500 | 1.912 | 1.912 |
| 1.500 | 0 | 913 | 913 |
| 1.500 | 750 | 902 | 902 |
| 2.000 | 0 | 539 | 539 |
| 2.000 | 1.000 | 540 | 540 |

| Cạnh ô tại gốc 0 | Mean sai khác tuyệt đối (direct vs aggregate) | Max sai khác |
| --- | ---: | ---: |
| 1.000 m | 0,000022939 | 0,000279087 |
| 1.500 m | 0,000049633 | 0,000540609 |
| 2.000 m | 0,000074602 | 0,000415689 |

SOL sáu cấu hình từ 34.196,307188 đến 34.196,307441; mean từ 20,733703468 đến 20,733703659. Với chỉ số `coarse_covered_by_fine`, một block bốn ô bằng diện tích chứa đúng một ô HH cho tỷ lệ block có giao 100% nhưng tỷ lệ diện tích giao thực chỉ 25%. Hai tỷ lệ không cùng định nghĩa.

**Bằng chứng lưu trữ.** [Chương trình đối chiếu CSV và mô phỏng số học](g19_g29_independent_audit.mjs), [JSON kết quả](evidence/g19_g29_independent_audit.json); [Chương trình đối chiếu raster và hình học](g20_g23_raster_audit.py), [JSON kết quả và SHA-256 dữ liệu nguồn](evidence/g20_g23_g17_raster_summary.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Xác nhận gần bảo toàn tích phân trên AOI và phương pháp đối chứng này. Chưa đối chiếu phép gộp production, chưa chạy LISA trên sáu lưới và chưa đo tính ổn định HH. Phép kiểm tiếp theo phải so cùng raster, cùng hỗ trợ, cấu hình LISA tương thích và giao polygon HH để tính Jaccard diện tích; không dùng tỷ lệ block bất kỳ giao thay cho diện tích giao thực.

### G23: Phụ thuộc không gian do các ô phân tích dùng chung pixel

**Đại lượng và lý do kiểm chứng.** Các ô lưới 500 m không phải là các phép đo cảm biến độc lập chỉ vì lưới có độ phân giải danh nghĩa 500 m. Khi hai ô nhận trọng số từ cùng pixel, quá trình tích hợp có thể tạo hiệp phương sai ngay cả khi pixel nguồn độc lập.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Từ phần giao diện tích góc của polygon và pixel, lập ma trận W với mỗi hàng chuẩn hóa tổng bằng 1. Nếu vector pixel x có phương sai đơn vị và độc lập, y=Wx có hiệp phương sai WWᵀ; tương quan giữa hai ô là tích vô hướng hai hàng chia tích chuẩn Euclid. Đối chứng lý tưởng dùng 400 raster uniform độc lập 25×25, lấy lưới 24×24 thẳng hàng hoặc dịch nửa pixel theo cả hai trục. Đối chứng hình học thực dùng 6.185 ô lõi Bảo An (diện tích ít nhất 99% danh nghĩa, hỗ trợ hình học ≥ 0,999), 400 trường pixel Gaussian độc lập, seed 20261125. Tính Global Moran nhị phân Rook sau phép tích hợp, với trung bình trường đầu ra được trừ trước.

**Kết quả.**

| Cấu hình | Moran trung bình | Phân vị thực nghiệm 2,5% | Phân vị thực nghiệm 97,5% |
| --- | ---: | ---: | ---: |
| Lưới lý tưởng thẳng hàng | -0,001514 | -0,060801 | 0,056433 |
| Lưới lý tưởng dịch nửa pixel | 0,496455 | 0,441207 | 0,550105 |
| Hình học thực Bảo An | 0,209232 | 0,190961 | 0,228331 |

Trên hình học Bảo An, toàn bộ 23.900 liên kết Rook có hướng dùng chung ít nhất một pixel nguồn. Tương quan cặp kỳ vọng trung bình là 0,230268; phân vị 95% là 0,415925. Trong lưới lý tưởng dịch nửa pixel, hai ô kề nhau chia sẻ hai trong bốn pixel nên tương quan dương là hệ quả của trọng số giao.

**Bằng chứng lưu trữ.** [Chương trình đối chiếu CSV và mô phỏng số học](g19_g29_independent_audit.mjs), [JSON kết quả](evidence/g19_g29_independent_audit.json); [Chương trình đối chiếu raster và hình học](g20_g23_raster_audit.py), [JSON kết quả và SHA-256 dữ liệu nguồn](evidence/g20_g23_g17_raster_summary.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Xác nhận cơ chế tạo phụ thuộc trên hình học raster tham chiếu thực, với radiance giả lập; không phải số đo sai lệch Moran thực địa, PSF VIIRS hoặc hệ số được phép trừ khỏi Moran quan sát. Khoảng phân vị là phân bố các lượt mô phỏng, không phải CI cho trường NTL thật. G17 mở rộng câu hỏi này sang phân phối null cho Local Moran.

### G24: Đối chiếu Global Moran và độ dốc Moran scatterplot

**Đại lượng và lý do kiểm chứng.** Độ dốc Moran scatterplot chỉ tương ứng Global Moran khi tập ô, biến đổi và chuẩn hóa trọng số phù hợp. Global Moran toàn ô raw và scatterplot LISA trên ô lõi dương không mặc nhiên là một đại lượng.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Tái dựng Queen từ tọa độ tâm chiếu CSV bằng floor(tọa độ/500). Tính Global Moran nhị phân trên toàn bộ ô với NTL gốc; tính độ dốc hồi quy OLS có intercept của spatial lag trung bình lên độ lệch NTL trên focal lõi dương, tối thiểu một láng giềng; lặp với log NTL. So kết quả theo từng địa bàn-năm.

**Kết quả.**

| Địa bàn 2020 | Global I toàn ô raw | Slope lõi dương raw | Slope lõi dương log |
| --- | ---: | ---: | ---: |
| Kỳ Môn | 0,817250 | 0,800781 | 0,866488 |
| Bảo An | 0,903654 | 0,921101 | 0,962057 |
| Thượng Hải | 0,810675 | 0,802565 | 0,830273 |

**Bằng chứng lưu trữ.** [Chương trình đối chiếu CSV và mô phỏng số học](g19_g29_independent_audit.mjs), [JSON kết quả](evidence/g19_g29_independent_audit.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Xác nhận khác biệt trên CSV đã làm tròn; chưa phải phép đối chiếu trực tiếp đường trend UI. Cần đồng nhất tập ô, trọng số, biến đổi, xử lý đảo và sample hiển thị. Cột chẩn đoán row-standardized trong JSON ở minK=4 đặt các hàng dưới ngưỡng bằng 0, không phải Global Moran chuẩn trên đồ thị cảm sinh focal.

### G25: Mẫu số diện tích của tỷ trọng High-High trên tập được kiểm định

**Đại lượng và lý do kiểm chứng.** `members` là tập đủ điều kiện tham gia đồ thị; `focal` là tập thực sự được kiểm định sau điều kiện số láng giềng. Nếu tên `hh_area_share_of_tested` mang nghĩa diện tích HH chia diện tích được kiểm định, mẫu số members có thể không đúng với tên biến.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Dựng Queen trên ô lõi dương từ CSV và áp điều kiện minK=1 hoặc minK=4. So số ô và tổng diện tích members, focal. Với cùng tử số diện tích HH, tỷ số dùng focal và tỷ số dùng members chỉ bằng nhau khi hai tổng diện tích bằng nhau.

**Kết quả.**

| Địa bàn 2020 | Members | Focal (minK=4) |
| --- | ---: | ---: |
| Kỳ Môn | 8.532 | 8.513 |
| Bảo An | 6.186 | 6.158 |
| Thượng Hải | 715 | 712 |

Bảo An ngay cả ở minK=1 có 6.186 members nhưng 6.185 focal, chênh 0,25 km². Tại minK=4, tỷ lệ diện tích focal/members là 0,995482857.

**Bằng chứng lưu trữ.** [Chương trình đối chiếu CSV và mô phỏng số học](g19_g29_independent_audit.mjs), [JSON kết quả](evidence/g19_g29_independent_audit.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Xác nhận mẫu số khác nhau trên dữ liệu thực, không tính tỷ trọng HH mới vì CSV không có nhãn HH. Cần test production với đảo và minK thay đổi, xác định rõ tên hoặc mẫu số trước khi sửa thuật toán.

### G27: Tính đồng nhất đặc tả phân tích trong panel vùng-năm

**Đại lượng và lý do kiểm chứng.** Hai bản ghi cùng vùng, năm và cạnh lưới có thể dùng các đặc tả LISA khác nhau. So sánh panel khi cấu hình thay đổi có thể nhầm thay đổi phép đo với thay đổi hiện tượng.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Đối chiếu `KEY_COLS` và đường thay thế dòng cùng khóa trong `ntl/lisa_ui.py`. Thiết kế định danh đặc tả từ weights, log, alpha, FDR, số hoán vị, seed, chính sách hỗ trợ, phiên bản thuật toán và định danh ranh giới. Phép kiểm cần tạo hai cấu hình khác nhau cùng khóa để phát hiện xung đột; kiểm tra cả ID/hình học nguồn qua năm.

**Kết quả.**

Kiểm tra tĩnh xác nhận dòng cùng khóa có thể bị thay thế dù cấu hình khác. G26 xác nhận thuộc tính tọa độ và diện tích CSV của Kỳ Môn khớp qua năm, không xác nhận hash polygon hoặc cùng đặc tả toàn panel.

**Bằng chứng lưu trữ.** [Chương trình đối chiếu CSV và mô phỏng số học](g19_g29_independent_audit.mjs), [JSON kết quả](evidence/g19_g29_independent_audit.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Rủi ro từ hợp đồng dữ liệu đã được nhận diện, chưa có kiểm thử UI/production với các cấu hình xung đột. Cần xác minh fingerprint và ngăn gộp các chuỗi khác đặc tả; không được coi panel hiện có đã đồng nhất.

### G28: Kích thước block và độ bao phủ spatial bootstrap

**Đại lượng và lý do kiểm chứng.** Block năm ô và 200 lần lấy mẫu lại là lựa chọn thuật toán, không phải bằng chứng khoảng tin cậy có độ bao phủ danh nghĩa 95%. Cấu trúc phụ thuộc của nội đô và nông thôn có thể khác nhau.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Ước lượng phạm vi phụ thuộc bằng correlogram hoặc variogram, thử nhiều cỡ block và số lượt lặp; báo số block, số lượt hợp lệ, phân vị và độ nhạy khoảng ước lượng. Trên trường mô phỏng có tham số thật biết trước, độ bao phủ thực nghiệm là số khoảng chứa tham số thật chia số lần mô phỏng hợp lệ. Dùng độ bao phủ và độ bất định Monte Carlo, không chọn block chỉ vì CI hẹp.

**Kết quả.**

Chưa có kết quả hiệu chuẩn độ bao phủ mới. Các kết quả spatial block resampling đã lưu trước đây vẫn là bằng chứng độ nhạy, không phải bằng chứng 95% coverage.

**Phạm vi đã kiểm chứng và phần còn mở.** Giữ phạm vi mô tả của các khoảng hiện có; chỉ đưa ra khẳng định độ bao phủ khi có thí nghiệm hiệu chuẩn phù hợp với thiết kế lấy mẫu và phụ thuộc.

### G29: Tính tương đương của quy ước p-value trong tài liệu và production

**Đại lượng và lý do kiểm chứng.** So trị tuyệt đối của thống kê quan sát và mô phỏng khác với nhân đôi xác suất đuôi nhỏ hơn khi phân phối tham chiếu bất đối xứng. Cần phân biệt công thức minh họa tổng quát và thuật toán thực sự được triển khai.

**Dữ liệu, phương pháp và chuẩn đối chiếu.** Đặt Local I quan sát bằng 2 và chín giá trị mô phỏng [-5,-4,-3,-2,-1,0,1,2,3]. Phương pháp trị tuyệt đối đếm sáu giá trị có độ lớn ≥ 2, cộng 1 rồi chia 10. Phương pháp hai đuôi lấy số giá trị ở đuôi nhỏ hơn (hai giá trị ≥ 2), cộng 1, chia 10 và nhân đôi, giới hạn trên 1.

**Kết quả.**

| Quy ước | p-value |
| --- | ---: |
| Trị tuyệt đối, hiệu chỉnh +1 | 0,7 |
| Nhân đôi đuôi nhỏ hơn, hiệu chỉnh +1 | 0,6 |

**Bằng chứng lưu trữ.** [Chương trình đối chiếu CSV và mô phỏng số học](g19_g29_independent_audit.mjs), [JSON kết quả](evidence/g19_g29_independent_audit.json).

**Phạm vi đã kiểm chứng và phần còn mở.** Phản ví dụ xác nhận không tương đương số học; không chứng minh quy ước nào có hiệu chuẩn null tốt hơn. Cần đối chiếu tất cả estimand và quy ước tài liệu với production. Các công thức hiện hữu được giữ nguyên.

### Tiêu chí nghiệm thu kiểm chứng mới

- **G04/G05/G06:** lưu nguồn dữ liệu độc lập, đơn vị không gian, công thức, seed, chỉ số so sánh, kết quả cấp ô và các bảng độ nhạy. Tách tính đúng của đẳng thức khỏi giá trị diễn giải kinh tế.
- **G17:** định trước cách sinh dữ liệu null và alpha danh nghĩa; báo số phát hiện sai, FDR thực nghiệm, lực kiểm định và độ bất định qua các lần mô phỏng. BH tính đúng không tự chứng minh kiểm soát FDR cho mọi cấu trúc không gian. Tham khảo [Benjamini và Yekutieli (2001)](https://doi.org/10.1214/aos/1013699998).
- **G18:** phân biệt số 0 thực đo và không có quan sát bằng dải hỗ trợ A02 đã xác nhận; chỉ chạy đặc tả thêm ô 0, không lặp lại chuẩn A03 đã hoàn thành.
- **Phần còn mở của A02/A07:** kiểm tra ca thiếu quan sát thực tế và lưới thô trích xuất trực tiếp từ raster. Không mở lại ca Bảo An đủ quan sát hoặc V11 chỉ vì còn câu hỏi lân cận.

- **G06:** khi mở rộng từ bootstrap có điều kiện sang null không gian, chọn lại cutoff và ước lượng alpha trong mỗi lượt; so các phân phối cạnh tranh trên cùng miền và đo tần suất bác bỏ.
- **G04/G05:** đối chiếu chuẩn kinh tế độc lập cùng thời điểm và hỗ trợ không gian; OSM 2026 không phải ground truth kinh tế 2020. Kiểm tra potential dân số/việc làm, ma sát giao thông, top-decile và tâm hoạt động ngoài mẫu.
- **G03/G09/G13/G14:** giữ điều kiện kiểm chứng ngưỡng bức xạ, Markov đa kỳ, chênh lệch epoch và ngưỡng robustness trong [sổ kiểm chứng](scientific_closure_register.json).

