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

## Bằng chứng lịch sử còn thiếu bản dịch riêng

| Bằng chứng gốc | Phạm vi | Tình trạng bản dịch |
| --- | --- | --- |
| [Bằng chứng thực địa tổng hợp](CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) | Sáu phần lịch sử có chỉ mục cùng phần giải thích kiểm toán hiện hành | Chưa có bản đọc tiếng Việt đầy đủ |
| [Nguồn tài liệu lịch sử](historical_document_sources_2026-11-15.md) | Mười ba tài liệu gốc có chỉ mục, gồm nguồn tiếng Anh và tiếng Việt | Kho lưu trữ chứa cả hai ngôn ngữ; chưa có đầy đủ bản đọc tách riêng theo từng ngôn ngữ |
| [Các báo cáo gốc được khôi phục](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md) | Bảy mươi tám báo cáo gốc | Giữ ngôn ngữ nguồn; chưa có đầy đủ hai bộ bản dịch |

**Ba tệp trên là kho bằng chứng gốc, không phải tài liệu biên tập đã chuẩn hóa.** Không sửa trực tiếp dấu câu, loại bỏ dấu gạch ngang dài, dịch đoạn văn, đổi kiểu xuống dòng CRLF/LF hoặc thay thông tin về nguồn. Những thay đổi đó có thể làm sai vị trí byte hay mã băm SHA-256. Bản dịch phục vụ người đọc cần là tệp mới tách riêng tiếng Anh và tiếng Việt, đồng thời giữ nguyên thông số, đường dẫn, mã băm, điều kiện kiểm chứng và ngày tháng kết luận.

### Công việc còn lại

- Dịch toàn bộ báo cáo thực địa tổng hợp thành bản đọc tiếng Việt độc lập.
- Lập bảng đối chiếu bản dịch cho đủ mười ba tài liệu lịch sử; bổ sung các bản tiếng Anh hoặc tiếng Việt còn thiếu.
- Lập bảng đối chiếu cho đủ bảy mươi tám báo cáo gốc; dịch các bản đọc còn thiếu mà không sửa kho lưu trữ.
- Rà soát văn phong pha trộn ngôn ngữ, thay dấu gạch ngang dài bằng dấu câu phù hợp trong *các bản đọc mới*, không thay trong bản gốc.
- Kiểm tra độ đầy đủ của từng bản dịch, đường dẫn tham chiếu và nguồn dữ liệu trước khi công bố là hoàn tất.

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
