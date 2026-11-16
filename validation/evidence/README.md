# Evidence inventory

[English](README.md) · [Tiếng Việt](README-vi.md)

Read the [language coverage and translation backlog](LANGUAGE_COVERAGE.md) before using archived source text. Read the [validation guide](../README.md) for supported results, limits and remaining work. The [data guide](../../docs/README.md) describes GADM and the analysis methods.

| Evidence | Location |
| --- | --- |
| Bao'an CSV, profiler and hashes | [Audit deposit](audit-2026-11-15/) |
| Yanqing raster and cell comparisons | [Yanqing guide](yanqing/README.md) |
| Original consolidated field record | [Source text](CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) |
| Thirteen superseded documents | [Source text](historical_document_sources_2026-11-15.md) and [byte index](historical_document_sources_index.json) |
| Seventy-eight recovered reports | [Source text](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md) |

The source text files preserve the received languages, punctuation and formulas as historical data. They are not translated reading editions. Their bytes and hashes remain unchanged. Current instructions are available separately in English and Vietnamese through the guides above.

Run `node validation/audit_public_evidence.mjs --check-result` and `node validation/audit_docs_archive.mjs` from the repository root to verify the deposited evidence.
