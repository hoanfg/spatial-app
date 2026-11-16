# Kiểm kê ngôn ngữ và bảo toàn bằng chứng

[English](LANGUAGE_COVERAGE.md) | [Tiếng Việt](LANGUAGE_COVERAGE-vi.md)

Phạm vi: tài liệu của repository và bằng chứng lịch sử, ngày 16 tháng 11 năm 2026.

## Hướng dẫn đang sử dụng

Sáu vị trí sau có hai bản hướng dẫn riêng: bản tiếng Anh `README.md` và bản tiếng Việt `README-vi.md`:

1. Thư mục gốc của repository
2. `docs/`
3. `validation/`
4. `validation/evidence/`
5. `validation/cross_location/`
6. `validation/evidence/yanqing/`

Đây là các bản hướng dẫn dành cho người đọc. Lệnh `validation/check_docs.mjs` hiện từ chối ký tự gạch ngang dài Unicode trong những bản hướng dẫn đang sử dụng. Việc tồn tại hai tên tệp chưa đủ để khẳng định hai bản dịch hoàn toàn tương đương.

## Phạm vi bản đọc tiếng Anh và tiếng Việt

| Bằng chứng gốc | Số bản ghi nguồn | Bản đọc |
| --- | ---: | --- |
| [Bằng chứng thực địa tổng hợp](CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) | Sáu phần lịch sử có chỉ mục và phần giải thích kiểm toán | [Tiếng Anh](CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md) và [tiếng Việt](CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md) |
| [Nguồn tài liệu lịch sử](historical_document_sources_2026-11-15.md) | Mười ba tài liệu gốc, thuộc mười một nhóm chủ đề | [Chỉ mục tiếng Anh](reading-editions/historical/README.md) và [chỉ mục tiếng Việt](reading-editions/historical/README-vi.md) |
| [Báo cáo gốc khôi phục](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md) | Bảy mươi tám bản ghi, tương ứng ba mươi lăm nội dung khác nhau theo SHA-256 | [Chỉ mục tiếng Anh](reading-editions/recovered/README.md) và [chỉ mục tiếng Việt](reading-editions/recovered/README-vi.md) |

Cả 35 nội dung báo cáo khôi phục khác nhau đều có bản đọc riêng bằng tiếng Anh và tiếng Việt. Các bản ghi trong kho lưu trữ chỉ dùng chung bản đọc khi mã băm SHA-256 của nội dung gốc giống hệt nhau. Mười ba tài liệu lịch sử được xếp thành mười một nhóm chủ đề. Hai chủ đề vốn đã có tài liệu nguồn tiếng Anh và tiếng Việt riêng. **Cùng chủ đề không chứng minh hai văn bản lịch sử tương đương từng câu.** [Manifest bản dịch](reading-editions/translation_manifest.json) cho phép tra cứu từng bản ghi nguồn và cặp bản đọc tương ứng.

**Các tệp nguồn là kho bằng chứng pháp chứng, không phải tài liệu biên tập.** Không thay dấu câu, ngôn ngữ nguồn, công thức, kiểu xuống dòng CRLF/LF hay độ dài byte của chúng, kể cả dấu gạch ngang dài lịch sử. Chỉ các bản đọc mới được chuẩn hóa ngôn ngữ và dấu câu. Thời điểm kết luận, điều kiện kiểm chứng và SHA-256 của nguồn gốc vẫn có giá trị ưu tiên.

### Việc kiểm tra chất lượng còn lại

- Đối chiếu toàn bộ bản đọc với nguồn về giá trị số, bảng, công thức, giới hạn, ngày tháng và các phát biểu kiểm chứng; không lược bỏ nội dung.
- Với chủ đề lịch sử có hai văn bản nguồn ở hai ngôn ngữ, cần xác định khác biệt giữa hai nguồn thay vì mặc nhiên coi là bản dịch khớp từng câu.
- Giữ nguyên tên tệp, mã định danh, mã băm và địa danh gốc; các yếu tố kỹ thuật này không được xem là văn xuôi pha tạp ngôn ngữ.
- Chạy `node validation/check_evidence_language_editions.mjs --strict` và `node validation/audit_bilingual_editions.mjs` để kiểm tra phạm vi, liên kết nguồn, điều hướng và dấu câu. Các phép kiểm tra tự động không chứng minh bản dịch tương đương hoàn toàn về ý nghĩa.

## Tính toàn vẹn bằng chứng

Các tệp Markdown lưu trữ có chỉ mục vị trí byte hoặc mã băm:

- `historical_document_sources_index.json` dùng để kiểm tra mười ba phần nguồn gốc.
- `audit-2026-11-15/consolidation_index.json` dùng để kiểm tra sáu phần của báo cáo tổng hợp.
- `audit-2026-11-15/recovered-originals/recovery_receipt.json` cùng manifest khôi phục dùng để kiểm tra byte của báo cáo gốc và danh mục dữ liệu.
- Các quy tắc `.gitattributes` đánh dấu tệp bằng chứng là `-text` nhằm ngăn Git tự động thay kiểu xuống dòng.

Chạy các lệnh sau từ thư mục gốc:

```sh
node validation/check_docs.mjs
node validation/audit_docs_archive.mjs
node validation/audit_public_evidence.mjs --check-result
```

Lệnh cuối cũng chạy các bước đối chiếu báo cáo khôi phục và nguồn lịch sử. Chúng kiểm tra bằng chứng đã lưu, không thay thế việc tái lập độc lập dữ liệu Earth Engine hay các kiểm chứng khoa học trực tiếp. Mọi kết luận gốc và giới hạn gắn với thời điểm lịch sử đều được giữ nguyên.
