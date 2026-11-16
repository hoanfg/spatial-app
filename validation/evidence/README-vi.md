# Danh mục bằng chứng

[English](README.md) · [Tiếng Việt](README-vi.md)

Trước khi sử dụng văn bản nguồn, đọc [kiểm kê ngôn ngữ](LANGUAGE_COVERAGE-vi.md) và [các bản đọc song ngữ](reading-editions/README-vi.md). Đọc [hướng dẫn kiểm chứng](../README-vi.md) để xem kết quả có bằng chứng, giới hạn và việc còn mở. [Hướng dẫn dữ liệu](../../docs/README-vi.md) trình bày GADM và phương pháp phân tích.

| Bằng chứng | Vị trí |
| --- | --- |
| CSV Bao'an, hồ sơ thời gian chạy và mã băm | [Bộ dữ liệu kiểm chứng](audit-2026-11-15/) |
| Raster và đối chiếu từng ô Diên Khánh | [Hướng dẫn Diên Khánh](yanqing/README-vi.md) |
| Hồ sơ kiểm chứng thực địa tổng hợp gốc | [Văn bản nguồn](CONSOLIDATED_FIELD_EVIDENCE_2026-11.md); [tiếng Anh](CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md); [tiếng Việt](CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md) |
| Mười ba tài liệu đã thay thế | [Văn bản nguồn](historical_document_sources_2026-11-15.md); [chỉ mục byte](historical_document_sources_index.json); [tiếng Anh](reading-editions/historical/README.md); [tiếng Việt](reading-editions/historical/README-vi.md) |
| Bảy mươi tám báo cáo khôi phục | [Văn bản nguồn](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md); [tiếng Anh](reading-editions/recovered/README.md); [tiếng Việt](reading-editions/recovered/README-vi.md) |

Các tệp văn bản nguồn giữ ngôn ngữ, dấu câu và công thức đã nhận để đối chiếu lịch sử. Đây là dữ liệu nguồn, chưa phải bản dịch biên tập đầy đủ. Nội dung byte và mã băm được giữ nguyên. Các hướng dẫn hiện hành đã có bản tiếng Anh và tiếng Việt riêng tại các liên kết phía trên.

Chạy `node validation/audit_public_evidence.mjs --check-result` và `node validation/audit_docs_archive.mjs` tại thư mục gốc repo để kiểm tra bằng chứng đã lưu.
