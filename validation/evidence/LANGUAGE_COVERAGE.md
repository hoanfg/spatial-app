# Evidence language and preservation audit

[English](LANGUAGE_COVERAGE.md) | [Tiếng Việt](LANGUAGE_COVERAGE-vi.md)

Audit scope: repository documentation and historical evidence, 16 November 2026.

## Editorial guides

The following six active guide pairs have an English `README.md` and a Vietnamese `README-vi.md`:

1. Repository root
2. `docs/`
3. `validation/`
4. `validation/evidence/`
5. `validation/cross_location/`
6. `validation/evidence/yanqing/`

These guides are separate reading editions. Their existing `validation/check_docs.mjs` check rejects the Unicode em dash in active guides. A filename pair is not itself proof of perfect translation equivalence.

## Historical evidence requiring separate reading translations

| Original evidence | Scope | Translation status |
| --- | --- | --- |
| [Consolidated field evidence](CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) | Six indexed historical sections plus current audit commentary | No complete Vietnamese reading edition |
| [Historical document sources](historical_document_sources_2026-11-15.md) | Thirteen indexed original documents, including English and Vietnamese source material | Mixed-language source archive; no complete paired English/Vietnamese reading editions |
| [Recovered original reports](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md) | Seventy-eight original report bodies | Original languages retained; no complete paired translations |

**These three entries are archives, not normalized editorial documents.** Do not replace original punctuation, remove the Unicode em dash, translate paragraphs in place, normalize CRLF/LF, or change source-text metadata. Doing so would invalidate byte offsets and/or recorded SHA-256 values. Use new English/Vietnamese reading editions for any future translations, preserving unchanged technical values, paths, hashes, qualifiers and status dates.

### Remaining work

- Translate the full consolidated field report into a separately named Vietnamese reading edition.
- Produce a source-by-source translation ledger for all thirteen historical documents and complete missing English or Vietnamese reading editions.
- Produce a report-by-report translation ledger for all seventy-eight recovered originals and translate missing reading editions without changing the archive.
- Review editorial wording for mixed-language prose and replace Unicode em dashes contextually in those *new reading editions*, not in the originals.
- Verify translation completeness, every referenced file, and data provenance before marking any edition complete.

## Forensic consistency

The archival Markdown files have byte-offset or checksum records:

- `historical_document_sources_index.json` checks the thirteen original segments.
- `audit-2026-11-15/consolidation_index.json` checks six consolidated sections.
- `audit-2026-11-15/recovered-originals/recovery_receipt.json` and the recovered manifest check original report bytes and inventory.
- The `.gitattributes` rules mark these evidence files as `-text` to prevent automatic newline rewriting.

Run these checks from the repository root:

```sh
node validation/check_docs.mjs
node validation/audit_docs_archive.mjs
node validation/audit_public_evidence.mjs --check-result
```

The last command also runs the recovered-originals and historical-source verifiers. These checks validate deposited evidence, not independent Earth Engine extraction or live scientific replication. Original source claims and their time-specific limitations remain unchanged.
