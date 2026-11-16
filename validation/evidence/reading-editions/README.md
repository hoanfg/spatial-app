# Bilingual reading editions of preserved audit evidence

[English](README.md) | [Tiếng Việt](README-vi.md) | [Original evidence inventory](../README.md)

This directory contains editorial reading editions in **separate English and Vietnamese files**, not replacements for protected forensic originals.

| Evidence group | English reading edition | Vietnamese reading edition | Source |
|---|---|---|---|
| Consolidated field evidence and all six historical sections | [English report](../CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md) | [Vietnamese report](../CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md) | [Original consolidated file](../CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) |
| Thirteen historical document sources, eleven bilingual topic pairs | [English index](historical/README.md) | [Vietnamese index](historical/README-vi.md) | [Historical source archive](../historical_document_sources_2026-11-15.md) |
| Seventy-eight recovered report records, thirty-five unique report bodies | [English index](recovered/README.md) | [Vietnamese index](recovered/README-vi.md) | [Verbatim recovered archive](../audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md) |

The [machine-readable translation manifest](translation_manifest.json) maps every archival entry, original SHA-256 and canonical bilingual edition. Duplicate report content is translated once and linked repeatedly, without dropping original source records.

**Preservation rule:** editorial punctuation and language are normalized only in the reading editions. Source hashes, original byte offsets, formulas, data, historical author/provenance statements, and original archive wording remain authoritative. These editions do not imply new field validation or remeasurement.

Run `node validation/audit_bilingual_editions.mjs` to validate the translation manifest, source associations, links and edition formatting.
