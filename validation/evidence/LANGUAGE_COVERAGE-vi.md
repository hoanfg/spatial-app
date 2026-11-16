# Kiểm kê ngôn ngữ và bảo toàn bằng chứng

[English](LANGUAGE_COVERAGE.md) | [Tiếng Việt](LANGUAGE_COVERAGE-vi.md) | [Tổng quan bản đọc](reading-editions/README-vi.md)

Trạng thái ngày 16/11/2026: **mọi nguồn có chỉ mục đã có bản đọc tương ứng bằng cả tiếng Anh và tiếng Việt**. Đây là kết quả kiểm kê sự hiện diện và nhất quán cơ học của tệp, chưa phải chứng nhận độc lập về chất lượng dịch thuật.

## Các hướng dẫn hiện hành

Sáu vị trí có cặp `README.md` tiếng Anh và `README-vi.md` tiếng Việt: thư mục gốc repository, `docs/`, `validation/`, `validation/evidence/`, `validation/cross_location/` và `validation/evidence/yanqing/`. Công cụ `validation/check_docs.mjs` không cho phép dấu gạch ngang dài Unicode trong các hướng dẫn đang sử dụng.

## Các bản đọc kiểm toán

| Bằng chứng gốc | Phạm vi các bản đọc | Chỉ mục truy cập |
| --- | --- | --- |
| Báo cáo thực địa tổng hợp với sáu phần lịch sử | Một tệp tiếng Anh đầy đủ và một tệp tiếng Việt đầy đủ | [Tiếng Anh](CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md) và [Tiếng Việt](CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md) |
| Mười ba nguồn lịch sử có chỉ mục | Mười một cặp theo chủ đề; các nguồn 01/02 và 03/04 vốn là cặp Anh/Việt trong bản gốc | [Chỉ mục tiếng Anh](reading-editions/historical/README.md) và [chỉ mục tiếng Việt](reading-editions/historical/README-vi.md) |
| Bảy mươi tám mục báo cáo gốc được khôi phục | Ba mươi lăm nội dung không trùng nhau theo SHA-256, mỗi nội dung có bản đọc tiếng Anh và tiếng Việt; mục trùng dùng chung bản dịch | [Chỉ mục tiếng Anh](reading-editions/recovered/README.md) và [chỉ mục tiếng Việt](reading-editions/recovered/README-vi.md) |

[Manifest đối chiếu](reading-editions/translation_manifest.json) ghi đủ đường dẫn, mã SHA-256 và bản dịch của từng nguồn. Tổng cộng **184 ánh xạ nguồn và ngôn ngữ** được giải quyết bằng **94 tệp nội dung**: 70 bản đọc báo cáo khôi phục, 22 bản đọc lịch sử và 2 bản đọc báo cáo tổng hợp. Các nguồn trùng byte không cần nhân đôi tệp nội dung.

## Giữ nguyên kho gốc

Ba tập bằng chứng gốc là **kho lưu trữ phục vụ kiểm toán**. Chúng cố ý bảo tồn ngôn ngữ, công thức, ngày tháng, dấu gạch ngang dài và byte nguyên gốc. Không sửa dấu câu, dịch trực tiếp hay đổi kiểu xuống dòng trong các kho này vì vị trí byte cùng mã băm là một phần bằng chứng. Khi cần đối chiếu nguồn gốc và giới hạn khoa học, phải ưu tiên văn bản gốc.

## Kiểm tra và những việc cần rà soát

```sh
node validation/check_docs.mjs
node validation/check_evidence_language_editions.mjs --strict
node validation/audit_bilingual_editions.mjs
node validation/audit_public_evidence.mjs --check-result
```

Các lệnh kiểm tra sự tồn tại của bản đọc, quan hệ nguồn và bản dịch, độ dài tối thiểu, mã băm, dấu gạch ngang dài trong bản biên tập và liên kết điều hướng. Chúng **không** chứng nhận từng câu dịch đều đúng, các phát biểu lịch sử đều chính xác, kết quả khoa học tương đương hay Earth Engine/Cloud vừa được chạy lại. Trước khi công bố nghiên cứu, người rà soát chuyên môn thông thạo cả hai ngôn ngữ cần đối chiếu số liệu, ngày tháng, các giới hạn và kết luận trong từng bản dịch với kho gốc. Không thêm GeoTIFF, GeoJSON hoặc nhật ký Cloud thô riêng vào tập bản đọc.
