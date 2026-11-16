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

## Bilingual reading edition coverage

| Original evidence | Source records | Reading editions |
| --- | ---: | --- |
| [Consolidated field evidence](CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) | Six indexed historic sections plus contemporary commentary | [English](CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md) and [Vietnamese](CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md) |
| [Historical document sources](historical_document_sources_2026-11-15.md) | Thirteen source records representing eleven topics | [English index](reading-editions/historical/README.md) and [Vietnamese index](reading-editions/historical/README-vi.md) |
| [Recovered original reports](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md) | Seventy-eight entries representing thirty-five distinct SHA-256 report bodies | [English index](reading-editions/recovered/README.md) and [Vietnamese index](reading-editions/recovered/README-vi.md) |

All 35 unique recovered report bodies have an English and a Vietnamese reading edition. Repeated archival entries reuse the same edition only when original SHA-256 is identical. The thirteen historical documents are indexed in eleven topic groups. Two topics already had separate English and Vietnamese source documents; **same-topic grouping does not certify that those historical versions are exact line-by-line translations.** The [translation manifest](reading-editions/translation_manifest.json) explicitly maps each original source record to its reading editions.

**These original source entries are forensic archives, not normalized editorial documents.** Their punctuation, original languages, formulas, CRLF/LF and byte lengths must remain unchanged, including historical Unicode em dashes. Only the new reading editions use editorial punctuation and language normalization. Historical dates, qualifications and the originals' SHA-256 remain authoritative.

### Remaining quality review

- Compare every reading edition with its linked original for complete preservation of numerical values, tables, equations, caveats, original status dates and claims.
- Where a historical topic has two independent language-specific originals, check differences between those original versions instead of assuming perfect correspondence.
- Retain any original code identifiers, file names, hashes and proper nouns as written; they are not language mixing in editorial prose.
- Use both `node validation/check_evidence_language_editions.mjs --strict` and `node validation/audit_bilingual_editions.mjs` to check canonical coverage, source association, navigation and punctuation. Automated checks do not establish semantic translation equivalence.

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
