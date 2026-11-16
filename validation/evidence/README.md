# Evidence inventory

[English](README.md) | [Tiếng Việt](README-vi.md)

The **original evidence archives remain byte-preserved**. Use separate editorial reading editions for English or Vietnamese. See the [language coverage audit](LANGUAGE_COVERAGE.md) and the [complete source-to-translation manifest](reading-editions/translation_manifest.json).

| Evidence | English reading edition | Vietnamese reading edition | Original source |
| --- | --- | --- | --- |
| Consolidated field audit, including six historical sections | [English](CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md) | [Vietnamese](CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md) | [Original](CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) |
| Thirteen historical sources in eleven bilingual topic pairs | [English index](reading-editions/historical/README.md) | [Vietnamese index](reading-editions/historical/README-vi.md) | [Original archive](historical_document_sources_2026-11-15.md) |
| Seventy-eight recovered reports representing thirty-five unique content hashes | [English index](reading-editions/recovered/README.md) | [Vietnamese index](reading-editions/recovered/README-vi.md) | [Original archive](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md) |
| Bao'an CSV, profiler, hashes and recovered inventory | [Audit deposit](audit-2026-11-15/) | Same source data | [Audit deposit](audit-2026-11-15/) |
| Yanqing raster and cell comparisons | [Yanqing guide](yanqing/README.md) | [Yanqing guide in Vietnamese](yanqing/README-vi.md) | [Evidence folder](yanqing/) |

The reading editions have normalized punctuation and separate languages. Archived source texts intentionally preserve their received language, punctuation, line endings, dates, formulas and SHA-256 records. Neither a translation nor a successful repository integrity check counts as a new independent scientific rerun.

From the repository root, run:

```sh
node validation/check_evidence_language_editions.mjs --strict
node validation/audit_bilingual_editions.mjs
node validation/audit_public_evidence.mjs --check-result
node validation/check_docs.mjs
```

Read the [validation guide](../README.md) for supported results, limitations and open work, and the [data guide](../../docs/README.md) for GADM and analysis methods.
