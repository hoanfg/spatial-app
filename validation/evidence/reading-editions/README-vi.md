# Các bản đọc bằng chứng kiểm toán tách riêng tiếng Anh và tiếng Việt

[English](README.md) | [Tiếng Việt](README-vi.md) | [Danh mục bằng chứng gốc](../README-vi.md)

Thư mục này chứa các bản đọc biên tập **tách riêng hoàn toàn theo ngôn ngữ**, không thay thế kho chứng cứ nguyên byte được bảo vệ.

| Nhóm bằng chứng | Bản tiếng Anh | Bản tiếng Việt | Kho nguồn |
|---|---|---|---|
| Báo cáo kiểm chứng thực địa tổng hợp và đủ sáu phần lịch sử | [Bản tiếng Anh](../CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md) | [Bản tiếng Việt](../CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md) | [Tệp tổng hợp gốc](../CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) |
| Mười ba nguồn tài liệu lịch sử, mười một cặp theo chủ đề | [Chỉ mục tiếng Anh](historical/README.md) | [Chỉ mục tiếng Việt](historical/README-vi.md) | [Kho nguồn lịch sử](../historical_document_sources_2026-11-15.md) |
| Bảy mươi tám bản ghi báo cáo khôi phục, ba mươi lăm nội dung duy nhất | [Chỉ mục tiếng Anh](recovered/README.md) | [Chỉ mục tiếng Việt](recovered/README-vi.md) | [Kho báo cáo nguyên văn](../audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md) |

[Manifest bản dịch dạng JSON](translation_manifest.json) đối chiếu tất cả nguồn, mã băm SHA-256 và bản đọc song ngữ chuẩn. Báo cáo trùng byte chỉ dịch một lần rồi liên kết đến đầy đủ các mục gốc, không bỏ mất bản ghi nguồn.

**Nguyên tắc bảo tồn:** chỉ chuẩn hóa dấu câu và ngôn ngữ trong bản đọc. Mã băm, vị trí byte, công thức, dữ liệu, ghi nhận tác giả/nguồn gốc và nội dung nguyên văn lịch sử vẫn là căn cứ. Các bản dịch không đồng nghĩa có phép kiểm chứng thực địa hay đo lường mới.

Chạy `node validation/audit_bilingual_editions.mjs` để kiểm tra manifest, ánh xạ nguồn, liên kết và quy tắc trình bày.
