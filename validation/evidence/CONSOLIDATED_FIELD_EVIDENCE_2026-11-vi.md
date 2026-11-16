# Cập nhật khôi phục: đã cung cấp danh mục gốc và nội dung của 78 báo cáo

Bản cập nhật này thay thế danh mục tài liệu còn thiếu được ghi nhận trước đó ở phần dưới. Chủ dự án đã cung cấp [manifest JSON lịch sử](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_EVIDENCE_MANIFEST_2026-11-15.json), [chương trình xác minh kho lưu trữ](audit-2026-11-15/recovered-originals/verify_spatial_app_audit_archive.py), [danh mục CSV gồm 118 bản ghi](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_FILE_MANIFEST_2026-11-15.csv) và [toàn bộ nội dung 78 báo cáo Markdown](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md). Tất cả được bảo tồn nguyên byte; bản tái dựng tạo trước đó không được dùng để thay thế.

SHA-256 của toàn bộ Markdown khôi phục khớp chính xác với manifest JSON. Cả 118 bản ghi CSV đều khớp JSON; nội dung từng báo cáo khớp độ dài, mã băm và mục tệp trực tiếp hoặc thành viên bên trong tệp nén tương ứng. CSV Bao'an và JSON đo hiệu năng đã công bố cũng khớp các mã băm lịch sử. Chương trình xác minh kho lưu trữ mới chỉ được kiểm tra cú pháp: để chạy đầy đủ vẫn cần tệp ZIP nguyên gốc và JSON chỉ mục khoảng byte, hiện chưa có. Manifest khôi phục liệt kê 271 tệp nằm trong các kho nén, nhưng byte của chúng chưa được khôi phục hoặc kiểm tra tại đây. Không có phép tính khoa học độc lập nào được chạy lại.

78 báo cáo hiện cung cấp bằng chứng lịch sử về kiểm chứng ô rìa V11, kiểm chứng GHSL tại Thượng Hải sau triển khai và A02 tại Bao'an, bao gồm các điều kiện và giới hạn. Đây là những phát biểu gốc được khôi phục, không phải kết quả tính toán lại, cũng không thay thế các kết quả theo từng ô, raster, biểu đồ và chương trình còn thiếu. Việc công bố toàn bộ dữ liệu thô và đo hiệu năng Cloud sau PR #27 vẫn chưa hoàn tất.

README bằng chứng và mốc hiệu năng tiếp theo do chủ dự án cung cấp được chèn đầy đủ ở cuối tài liệu. Các nội dung trước đó, kể cả phát biểu gắn với thời điểm lịch sử, được giữ lại. Có thể tái lập các kiểm tra cục bộ bằng `node validation/audit_public_evidence.mjs --check-result`; xem [biên nhận khôi phục](audit-2026-11-15/recovered-originals/recovery_receipt.json).

---

# Bằng chứng kiểm toán tổng hợp: ngày 15 tháng 11 năm 2026

## Bằng chứng hiện có và giới hạn

Mốc repository: `349612530fe118820831af610f67015636981bde` (nhánh main sau khi hợp nhất PR #27). Lần cập nhật này công bố hai tệp đính kèm có thể truy xuất của chủ dự án và đối chiếu các báo cáo lịch sử. Nó không chứng nhận toàn bộ đợt kiểm toán.

- [CSV ô gốc của Bao'an](audit-2026-11-15/baoan_ntl_2020_500m.csv): 7.148 dòng, năm 2020, kích thước ô 500 m. [JSON đo hiệu năng gốc](audit-2026-11-15/spatial_app_performance.json). Số byte và SHA-256 được ghi trong [manifest](audit-2026-11-15/manifest.json).
- [Bản tổng hợp công khai đã tính lại](audit-2026-11-15/verified_summary.json). Tái lập bằng `node validation/audit_public_evidence.mjs --check-result`. Lệnh này kiểm tra toàn bộ dòng, lược đồ, tính hữu hạn và miền giá trị của các trường chất lượng, ID duy nhất và mã băm; không tính lại bước trích xuất raster hay các chỉ số khoa học.
- Bằng chứng tổng hợp V11 bên dưới ghi nhận 17.177 ô của khu vực lõi Thượng Hải, Bao'an và Qimen. Repository được rà soát chưa chứa kết quả đối chiếu từng ô, cặp raster nguồn, kết quả LISA và biểu đồ kiểm chứng ngoài cho cả ba địa điểm. Do đó, trạng thái V11 là **đã ghi nhận bằng chứng tổng hợp / chưa thể tái lập đầy đủ từ dữ liệu công khai**, không phải một lần PASS mới.
- Siêu dữ liệu Bao'an có thể kiểm tra trực tiếp trong CSV đính kèm. CSV phiên bản trước không hiện diện tại đây; chưa thể xác minh lại phát biểu trong cuộc trò chuyện rằng NTL không thay đổi trước và sau. Mẫu này chưa kiểm chứng các trường hợp thật sự không có dữ liệu quan trắc hỗ trợ.
- Bộ đo hiệu năng: pipeline 46,6687 giây; A02 25,0028 giây; RSS của tiến trình máy chủ được lấy mẫu 728,531 MiB. Tạo lúc 12:48:20 UTC ngày 15/11/2026, trước PR #27; không chứa mã commit nguồn. Chưa xác lập mức tăng tốc sau tối ưu hóa. Tổng thời gian các giai đoạn bao gồm cả LISA/GHSL chạy sau đó, không được xem là thời gian riêng của pipeline.
- Cuộc trò chuyện ghi nhận GHSL hoạt động trở lại ở ba nơi, nhưng các tệp nhận được không chứa kết quả GHSL từng ô, giá trị rho/AUC hoặc biểu đồ. Trạng thái thành công của một giai đoạn trong bộ đo hiệu năng chỉ là bằng chứng vận hành, không phải kiểm chứng độc lập về mức khớp số học GHSL.

## Gói dữ liệu do chủ dự án lưu giữ, chưa có đầy đủ

Cuộc trò chuyện được truy xuất mô tả `SPATIAL_APP_FULL_AUDIT_EVIDENCE_2026-11-15.zip` (118 tệp nguồn, 271 thành viên giải nén lịch sử, 78 báo cáo Markdown), `SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md`, các manifest CSV/JSON, chỉ mục khoảng byte, `verify_spatial_app_audit_archive.py` và `SPATIAL_APP_NEXT_PERFORMANCE_BASELINE_2026-11-15.md` tại `/Spatial-App/audit-evidence-2026-11-15/` trong Library. Đối với lần cập nhật lịch sử được mô tả tại đây, đây là **danh mục được thuật lại trong cuộc trò chuyện, không phải các tệp đã khôi phục và xác minh ở chính lần cập nhật đó**. Thư mục nguồn dự án cục bộ khi ấy rỗng. Các trang cuộc trò chuyện được truy xuất không trả về con trỏ cũ hơn. Không tự tạo mã băm cho gói dữ liệu hay liên kết tệp chưa có như thể đã xuất bản trong repository.

Điểm bắt đầu hiện hành là [hướng dẫn kiểm chứng](../README-vi.md). Các báo cáo A02, A03, A03-B và phạm vi kiểm chứng gốc được bảo tồn trong [kho tài liệu có chỉ mục](historical_document_sources_2026-11-15.md); [bằng chứng Diên Khánh](yanqing/README-vi.md) và [công cụ kiểm chứng chéo địa điểm](../cross_location/README-vi.md) có đường dẫn riêng. Tập con được khôi phục tại mốc lịch sử này khác với gói đầy đủ khi đó chưa có.

## Những báo cáo lịch sử được bảo tồn

Bốn báo cáo bên dưới được nhúng bằng byte gốc trong **tệp lưu trữ nguồn**, không bỏ các điều kiện lịch sử hay thay trạng thái được ghi vào thời điểm trước đó. Báo cáo thực địa tổng hợp gốc được theo sau bởi ba báo cáo ngắn đã hợp nhất. Đường dẫn cũ và mã băm tại commit mốc được ghi ở [chỉ mục khoảng byte](audit-2026-11-15/consolidation_index.json). Hãy đọc bằng chứng hiện hành ở trên trước khi áp dụng các chỉ dẫn lịch sử về việc chờ hoặc hợp nhất.

Bản tiếng Việt này là **bản đọc dịch**, không phải vật chứng nguyên byte. Mọi mã định danh, thông số, kết quả và giới hạn sau đây được giữ theo nguồn.

---

## Nguồn: `validation/CONSOLIDATED_FIELD_EVIDENCE_2026-11.md`

# Bằng chứng thực địa độc lập tổng hợp: tháng 11 năm 2026

Báo cáo ghi lại những phép kiểm tra có phạm vi giới hạn liên quan đến chỉnh sửa A02/GHSL/thời gian chạy. GeoTIFF nguồn, CSV từng ô do chủ dự án cung cấp và GeoJSON vẫn nằm ngoài repository công khai; tại đây chỉ công bố kết quả tổng hợp và giá trị SHA-256. Những kết quả này **không đồng nghĩa với chấp nhận cuối cùng trên Cloud đang hoạt động**.

## V11 đối chiếu giữa các địa điểm, VIIRS năm 2020

Ba địa phương theo GADM 4.1: lõi Thượng Hải (`CHN.24.1.10_1`), Bao'an thuộc Thâm Quyến (`CHN.6.15.1_1`) và Qimen thuộc An Huy (`CHN.1.11.1_1`). Raster trung vị tham chiếu năm 2020, raster số tháng hợp lệ và raster trung vị đã áp mặt nạ được xuất độc lập từ Google Earth Engine. Giá trị từng ô được so sánh với CSV/GeoJSON đầu ra thực tế của ứng dụng ở độ phân giải 500 m.

| Khu vực | Tổng số ô của ứng dụng | Ô 500 m nguyên vẹn | Ô bị cắt bởi ranh giới |
|---|---:|---:|---:|
| Thượng Hải | 886 | 706 | 180 |
| Bao'an | 7.148 | 6.131 | 1.017 |
| Qimen | 9.143 | 8.493 | 650 |
| **Tổng** | **17.177** | **15.330** | **1.847** |

Cả 15.330 ô nguyên vẹn đều đạt phép so sánh giá trị bức xạ tham chiếu tích phân độc lập sau làm tròn CSV đến bốn chữ số thập phân. Trong 1.847 ô bị cắt, 1.846 ô đáp ứng trực tiếp ngưỡng sai số tuyệt đối `5e-5`. Với ô Bao'an `grid_id=628`, giá trị CSV là `18.8768`, giá trị độc lập là `18.876850039`, chỉ vượt ngưỡng `3.93e-8`; toàn bộ ô bị cắt đạt `5.01e-5` khi tính thêm phần dự phòng sai số số học `1e-7`. Đa giác bị cắt trong phép kiểm tra này là hình học GeoJSON do ứng dụng xuất, không phải đa giác được dựng lại hoàn toàn độc lập từ dữ liệu GADM gốc. Kiểm tra láng giềng Queen và BH-FDR trên kết quả CSV của ứng dụng không phát hiện sai khác, với các lưu ý về hạt giống mô phỏng Monte Carlo và làm tròn giá trị trong bằng chứng lưu riêng.

Đây là bằng chứng tham chiếu khoa học, không thể dùng việc chạy lại nó để thay cho kiểm thử những thay đổi mã A02 hoặc GHSL trong môi trường vận hành.

## Sai lệch bảo toàn đại lượng GHSL, Thượng Hải năm 2020

Sản phẩm: `JRC/GHSL/P2023A` trên lưới Mollweide gốc 100 m (`ESRI:54009`), các đại lượng theo pixel gốc, so với dạng dữ liệu ứng dụng dùng `EPSG:4326` ở độ phân giải danh nghĩa 100 m. Hộp giới hạn nội vùng dùng chung (`121.35899,31.17207,121.57093,31.33289`) giúp tránh ảnh hưởng do độ bao phủ ở rìa. Mọi tọa độ mẫu nguồn và đích đều được chuyển hệ tọa độ độc lập.

| Đại lượng | Tổng trên lưới gốc | Tổng chưa hiệu chỉnh theo lưới ứng dụng | Độ lệch |
|---|---:|---:|---:|
| Diện tích xây dựng (m²) | 118.319.940 | 137.859.621 | +16,51428% |
| Dân số (người) | 11.674.618,205 | 13.612.238,308 | +16,59686% |

Vùng lõi tham chiếu gốc có 36.234 pixel nguồn, so với 42.244 pixel đích. Phép biến đổi lưới theo láng giềng gần nhất được thực hiện độc lập tái tạo chính xác **42.244/42.244** giá trị đích cho cả hai sản phẩm. Do đó, độ lệch phát sinh khi cộng các *đại lượng trên từng pixel nguồn sau tái chiếu* như thể chúng là các đại lượng độc lập trên pixel đích. Cách sửa là tổng có trọng số theo phần bao phủ và bảo toàn lưới nguồn, **không phải** hiệu chuẩn bằng một hệ số vô hướng chung. Sai số quan sát khoảng 16,5% chỉ được xác lập cho trường hợp Thượng Hải này; tác động tại thành phố khác, cũng như đến Spearman/AUC, cần đánh giá sau khi triển khai bản sửa.

SHA-256 tệp đầu vào (lưới gốc sang dạng ứng dụng):

- Diện tích xây dựng: `cb72bc30727e89c43daecee6276b242ee141d8d1c971adde85f409020151cee6` sang `93fbe303ed47c6276689409b53a05118e41f8a12a9f8aca3bf85223c84983244`.
- Dân số: `3f20333936035fefc208a42cfdf8ab63414afc8f1c4f2ccad6c6294497fbf0b6` sang `31d75bb8be7a5641281ed6e516e1fbc9f7480f9cc25af30034127b5c5fca4b8f`.

## Các băng chất lượng A02, Bao'an năm 2020

GeoTIFF sáu băng độc lập từ `Export.image.toDrive` có tên băng như dự kiến và giá trị `float32`. Băng thứ nhất khớp chính xác trung vị VIIRS độc lập trên 26.786 pixel hữu hạn chung. Cả 27.013 pixel raster chất lượng đều có quan trắc, với số tháng hợp lệ từ chín đến mười hai. Mẫu thực địa này không có pixel nào thật sự không có quan trắc hỗ trợ hoặc có mức hỗ trợ thấp. Đường tải về khác của ứng dụng thực tế bằng `getDownloadURL` vẫn chưa được xác minh. Toàn bộ 17.177 dòng CSV theo ô được xuất trước đó đều có `dq_status=unknown` và các trường chất lượng trống. Bản sửa trong môi trường vận hành cần ghi lại số lượng băng và mô tả băng, đồng thời từ chối xử lý khi không thể tin cậy lược đồ. Không khẳng định nguyên nhân gốc đã được chứng minh trước khi quan sát bản tải xuống thật trên Cloud.

SHA-256 của đầu vào sáu băng: `5569fd153784dfee99d28d6a2413982f16fe9613691e9e62baeb937313b4f4c1`.

## Điều kiện nghiệm thu trên Cloud và thời gian chạy

Một nhật ký Streamlit Cloud (nguồn được lưu ngoài repository này) cho thấy lỗi nhập mô-đun `ntl.semantics` vào ngày 12/11 trong lịch sử, sau đó là các lần cập nhật ứng dụng; khi chạy ngày 14/11 có thông báo API giao diện sắp ngừng hỗ trợ và cảnh báo tile CartoDB. Nhật ký không xác lập thời gian thực thi hay RSS cho từng lượt phân tích, cũng không chứng minh đã xảy ra hết bộ nhớ hay vượt thời gian. PR bổ sung khả năng ghi hiệu năng JSON/CSV cho người dùng; cần đo một lần chạy Cloud có xác thực trước khi hợp nhất. Điều kiện nghiệm thu tương tự phải kiểm tra tổng GHSL trên lưới gốc, siêu dữ liệu chất lượng A02 từ lần truyền `getDownloadURL` thật, đồng thời lưu kết quả hồi quy và CI. Không công bố thông tin xác thực hay dữ liệu địa lý gốc của chủ dự án.

---

## Nguồn: `validation/CLOUD_RUNTIME_LOG_REVIEW_2026-11-14.md`

# Rà soát nhật ký chạy Streamlit Cloud: ngày 14 tháng 11 năm 2026

**Nguồn:** nhật ký triển khai Streamlit do chủ dự án cung cấp, tải ngày 14/11/2026, có bản ghi từ 11 đến 14/11/2026 (UTC). SHA-256: `92d1b8829288fbc50458989e4d0fcda1ec4b2486b10b77469352902d4799f873`. Nhật ký gốc đầy đủ được lưu riêng, **không commit**. Báo cáo này diễn giải nhật ký, không phải phép đo hiệu năng Cloud từ đầu đến cuối.

## Các sự kiện quan sát được

- Cloud khởi động với **Python 3.14.10** và **Streamlit 1.67.0**; quá trình cài gói hoàn tất và máy chủ web đã chạy (dòng nguồn 128–129, 245–246, 295–296).
- Quá trình cài phụ thuộc ban đầu chọn PyArrow 26.0.1, sau đó nền tảng tự thay bằng 24.0.0 do lo ngại lỗi phân đoạn bộ nhớ đã được biết đến (dòng 247–257). **Không quan sát thấy lỗi phân đoạn bộ nhớ** trong nhật ký.
- Hai lần thất bại khi nhập mô-đun, `ModuleNotFoundError: No module named 'ntl.semantics'`, xuất hiện ngày **12/11** trong lúc kéo mã GitHub (dòng 419–455). Thông báo `Updated app!` xuất hiện ở dòng 458 và ứng dụng tiếp tục được dùng những ngày sau. Lỗi lịch sử này **không phải bằng chứng mô-đun hiện nay bị thiếu**. Mô-đun có trong nhánh `main` được rà soát.
- Có 99 thông báo yêu cầu thay `st.components.v1.html` đã lỗi thời bằng `st.iframe`, và 107 thông báo yêu cầu thay `use_container_width` bằng `width`. Đây là thông báo API sắp ngừng hỗ trợ, **không phải ngoại lệ**; việc dùng iframe cũ có thể đến từ mã bên thứ ba và cần truy ra nơi gọi trước khi sửa hành vi.
- Có 34 cảnh báo rằng nguồn tile CartoDB đang chọn có thể yêu cầu khóa API. Đây là nguy cơ thiếu bản đồ nền, tách biệt với các phép tính raster/NTL/LISA. Cần xác minh trực quan lựa chọn bản đồ nền dự phòng, thay vì thay kiểu bản đồ một cách máy móc.
- Có 19 thông báo `Updated app!` trong khoảng nhật ký. Lần checkout Git đầu tiên xử lý khoảng 20.023 tệp; điều này có thể góp phần kéo dài khởi động nguội, nhưng riêng nhật ký không tách được thời gian checkout khỏi biến động mạng và máy chủ.
- Không thấy `MemoryError`, thông báo tiến trình bị hủy do hết bộ nhớ, chấm dứt tiến trình hoặc quá thời gian thực thi trong tệp này. **Sự vắng mặt của chúng không xác lập giới hạn trên về bộ nhớ hoặc độ trễ của từng lượt phân tích.**

## Quyết định và điều kiện phát hành

1. Đưa **bộ đo hiệu năng truy cập được trong phiên ứng dụng** vào PR dự thảo tổng hợp duy nhất: thời gian từ đầu đến cuối và của từng giai đoạn, RSS tiến trình được lấy mẫu, loại thành công/lỗi và xuất JSON/CSV. Bộ đo không tuyên bố đo chính xác bộ nhớ riêng cho từng người dùng hay cực đại vật lý.
2. Đưa chẩn đoán lược đồ sáu băng A02 theo nguyên tắc từ chối khi không đủ tin cậy và bản sửa bảo toàn đại lượng GHSL trên lưới gốc vào **cùng PR**. Chúng xử lý vấn đề được phát hiện từ đối chiếu CSV/raster; nhật ký triển khai không trực tiếp chẩn đoán riêng từng vấn đề.
3. Trước khi hợp nhất, chạy CI và một lần đối chiếu thực địa trên Cloud có xác thực. Xác nhận siêu dữ liệu băng chất lượng VIIRS từ `getDownloadURL` được điền hoặc hiển thị lý do lỗi rõ ràng; đối chiếu tổng diện tích xây dựng/dân số GHSL trên từng ô với tham chiếu lưới gốc. Kiểm tra JSON hiệu năng với số ô đại diện và tình trạng chạy đồng thời trên Cloud.
4. Xem thông báo tương thích là việc bảo trì cần theo dõi trong rà soát; chỉ cập nhật tham số chiều rộng do mã dự án gọi khi đã kiểm tra phiên bản Streamlit hỗ trợ, xác định nguồn gọi iframe và xác minh trực quan bản đồ nền không cần khóa. Không đánh đồng cảnh báo giao diện với sai hỏng khoa học.

**Trạng thái:** đã phân loại nhật ký; kiểm chứng trên môi trường vận hành còn chờ. Báo cáo bằng chứng này không chứa định danh người dùng, thông tin xác thực, toàn bộ nhật ký thô hay bí mật Cloud.
