# Evidence inventory

[English](README.md) · [Tiếng Việt](README-vi.md) · [Validation status](../README.md) · [Data and methods](../../docs/README.md)

This is the only English guide for the evidence folder. It records what is deposited, what each item can support and where the original source bytes are kept.

| Evidence | Deposited material | Scope |
| --- | --- | --- |
| Bao'an 2020 | 7,148-cell CSV, performance JSON, manifests and verified summary in [the audit deposit](audit-2026-11-15/) | Directly checks the deposited schema, values, IDs and hashes. It does not rerun Earth Engine or raster extraction. |
| Yanqing 2014 and 2020 | Cell exports, raster reference, independent comparisons and metrics in the [Yanqing folder](yanqing/README.md) | Supports the recorded VIIRS, LISA and two-date calculations for this location. |
| A02 after PR #27 | Cell CSV and performance JSON in [the A02 deposit](a02_post_pr27/) | Supports the recorded observed-data case and timing. It does not cover a real missing-support case. |
| Synthetic controls | Test outputs in [the A02 control folder](a02/) | Checks specific numerical and schema contracts only. |

## Original source records

Three large records are retained as plain text so GitHub does not present mixed-language historical material as current documentation:

- [Consolidated field record](CONSOLIDATED_FIELD_EVIDENCE_2026-11.txt)
- [Thirteen-document historical archive](historical_document_sources_2026-11-15.txt), with its [byte index](historical_document_sources_index.json)
- [Seventy-eight recovered reports](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.txt), with the original JSON and CSV manifests in the same folder

These files preserve the received languages, punctuation, formulas and line endings because their SHA-256 values and byte ranges are audit evidence. Current conclusions are maintained in the English and Vietnamese README pairs, rather than duplicated as separate reading editions.

## Verification

Run from the repository root:

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/audit_docs_archive.mjs
node validation/check_docs.mjs
```

The first two commands verify deposited bytes and indexes. The documentation check enforces the active README pairs, links, language-specific headings, punctuation and basic math delimiters.
