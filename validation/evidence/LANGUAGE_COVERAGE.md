# Evidence language coverage and preservation

[English](LANGUAGE_COVERAGE.md) | [Tiếng Việt](LANGUAGE_COVERAGE-vi.md) | [Reading-edition overview](reading-editions/README.md)

Status at 16 November 2026: **paired reading editions have been deposited for every indexed source**. This records edition availability and mechanical consistency, not an independently certified translation-quality review.

## Separate active guides

Six locations have English `README.md` and Vietnamese `README-vi.md` pairs: repository root, `docs/`, `validation/`, `validation/evidence/`, `validation/cross_location/`, and `validation/evidence/yanqing/`. The `validation/check_docs.mjs` check rejects Unicode em dashes in these active guides.

## Audit reading editions

| Original evidence | Coverage of reading editions | Navigable editions |
| --- | --- | --- |
| Consolidated field evidence with six historical sections | One complete English and one complete Vietnamese reading file | [English](CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md) and [Vietnamese](CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md) |
| Thirteen indexed historical sources | Eleven English/Vietnamese topic pairs; source 01/02 and 03/04 were pre-existing language counterparts | [English index](reading-editions/historical/README.md) and [Vietnamese index](reading-editions/historical/README-vi.md) |
| Seventy-eight recovered original report records | Thirty-five distinct report bodies identified by SHA-256, each with full English and Vietnamese reading editions; repeated bodies share a pair | [English index](reading-editions/recovered/README.md) and [Vietnamese index](reading-editions/recovered/README-vi.md) |

The [mapping manifest](reading-editions/translation_manifest.json) records every original path, SHA-256 and language-edition path. The total is **184 source-language mappings** resolved by **94 content files**: 70 recovered-report editions, 22 historical editions and 2 consolidated-report editions. Multiple source entries with identical content do not require duplicate text files.

## Source preservation

The three original evidence collections are **forensic archives**. They intentionally retain original languages, formulas, dates, em dashes and byte sequences. Do not change original punctuation, translate paragraphs in place, or normalize line endings: the original byte offsets and hashes are evidence. They remain authoritative for provenance and original scientific qualifications.

## Checks and remaining review

```sh
node validation/check_docs.mjs
node validation/check_evidence_language_editions.mjs --strict
node validation/audit_bilingual_editions.mjs
node validation/audit_public_evidence.mjs --check-result
```

These checks target edition presence, source-to-edition relationships, minimum length, source hashes, editorial em dashes and navigation. They **do not** certify sentence-level translation fidelity, scientific equivalence, correctness of historical claims or new Earth Engine/Cloud reproducibility. A bilingual subject reviewer should inspect quantitative details, historical status and qualifications against each protected original before scientific publication. No GeoTIFF, GeoJSON or private raw Cloud logs have been added to the reading-edition set.
