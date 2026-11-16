# Danh mục bằng chứng

[English](README.md) | [Tiếng Việt](README-vi.md)

**Các kho bằng chứng gốc vẫn được bảo tồn nguyên byte.** Hãy sử dụng các bản đọc biên tập riêng tiếng Anh và tiếng Việt. Xem [kiểm kê ngôn ngữ](LANGUAGE_COVERAGE-vi.md) và [manifest đối chiếu đầy đủ nguồn với bản dịch](reading-editions/translation_manifest.json).

| Nhóm bằng chứng | Bản tiếng Anh | Bản tiếng Việt | Nguồn gốc |
| --- | --- | --- | --- |
| Kiểm toán thực địa tổng hợp, gồm sáu phần lịch sử | [Bản tiếng Anh](CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md) | [Bản tiếng Việt](CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md) | [Văn bản gốc](CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) |
| Mười ba nguồn lịch sử được tổ chức thành mười một cặp theo chủ đề | [Chỉ mục tiếng Anh](reading-editions/historical/README.md) | [Chỉ mục tiếng Việt](reading-editions/historical/README-vi.md) | [Kho gốc](historical_document_sources_2026-11-15.md) |
| Bảy mươi tám báo cáo khôi phục, tương ứng ba mươi lăm nội dung có mã băm khác nhau | [Chỉ mục tiếng Anh](reading-editions/recovered/README.md) | [Chỉ mục tiếng Việt](reading-editions/recovered/README-vi.md) | [Kho gốc](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md) |
| CSV Bao'an, tệp đo hiệu năng, mã băm và danh mục khôi phục | [Tập bằng chứng](audit-2026-11-15/) | Dùng chung dữ liệu gốc | [Tập bằng chứng](audit-2026-11-15/) |
| Raster và đối chiếu từng ô Diên Khánh | [Hướng dẫn tiếng Anh](yanqing/README.md) | [Hướng dẫn tiếng Việt](yanqing/README-vi.md) | [Thư mục bằng chứng](yanqing/) |

Các bản đọc đã được tách theo ngôn ngữ và chuẩn hóa dấu câu. Nội dung nguồn lưu trữ chủ ý giữ nguyên ngôn ngữ, dấu câu, kiểu xuống dòng, ngày tháng, công thức và mã SHA-256. Bản dịch và phép kiểm toàn vẹn repository đều không phải phép tính kiểm chứng khoa học độc lập mới.

Chạy các lệnh sau tại thư mục gốc repository:

```sh
node validation/check_evidence_language_editions.mjs --strict
node validation/audit_bilingual_editions.mjs
node validation/audit_public_evidence.mjs --check-result
node validation/check_docs.mjs
```

Xem [hướng dẫn kiểm chứng](../README-vi.md) để biết giới hạn và việc còn mở, cùng [hướng dẫn dữ liệu](../../docs/README-vi.md) về GADM và phương pháp phân tích.
