# Bilingual evidence edition quality check

This check inspects **reading editions only**. It never changes, translates, reformats or reparses the archived evidence bytes.

```sh
node validation/check_evidence_language_editions.mjs
node validation/check_evidence_language_editions.mjs --strict
```

The default command reports missing translations without failing on absence, making it suitable during incremental translation. `--strict` exits unsuccessfully if any expected edition is missing or a detected file-level problem exists.

Expected layout:

- `validation/evidence/CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md` and `-vi.md`.
- `validation/evidence/reading-editions/historical/001-en.md` through `013-vi.md`, indexed by `historical_document_sources_index.json`.
- `validation/evidence/reading-editions/recovered/001-en.md` through `078-vi.md`, numbered in the verbatim source archive.

The report checks the existence of both languages, original SHA-256 citations for each indexed report, selected manifest relationships, Unicode em dashes, obvious placeholders and minimal document length. A Vietnamese edition must contain Vietnamese diacritics. Names, quoted source data, code blocks and technical terms may legitimately appear in their original language.

**Important limitation:** a passing report only confirms file coverage and basic mechanical consistency. It does not certify translation accuracy, completeness of every paragraph, methodological equivalence, or independent reproduction of reported scientific results. A bilingual domain reviewer must compare each full edition against the original, with particular attention to limitations, status dates, numerical values, tables and formulas. Preserved originals remain the evidential authority.

No original evidence hashes or source binaries are modified by these checks.
