# Bilingual evidence edition quality check

This check inspects **reading editions only**. It never changes, translates, reformats or reparses the archived evidence bytes.

```sh
node validation/check_evidence_language_editions.mjs
node validation/check_evidence_language_editions.mjs --strict
node validation/audit_bilingual_editions.mjs
```

The default command reports missing translations without failing on absence. `--strict` exits unsuccessfully if any canonical reading edition is missing or a detected file-level problem exists. The independent manifest audit also checks source records and reading-edition navigation.

Expected layout:

- `validation/evidence/CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md` and `-vi.md`.
- 11 canonical historical source topic pairs under `validation/evidence/reading-editions/historical/`, mapped from all 13 archival source records by `translation_manifest.json`.
- 35 canonical recovered report pairs under `validation/evidence/reading-editions/recovered/`, mapped from all 78 source entries. Repeated source content is deduplicated **only** when its original SHA-256 is identical.

The checks cover 94 canonical reading editions, link all 78 recovered and 13 historical source records, and check source SHA-256 citations, selected manifest relationships, Unicode em dashes, navigation links and minimal document length. A Vietnamese edition must contain Vietnamese diacritics. Names, quoted source data, code blocks and technical terms may legitimately appear in their original language.

**Important limitation:** a passing report only confirms file coverage and basic mechanical consistency. It does not certify translation accuracy, completeness of every paragraph, methodological equivalence, or independent reproduction of reported scientific results. A bilingual domain reviewer must compare each full edition against the original, with particular attention to limitations, status dates, numerical values, tables and formulas. Preserved originals remain the evidential authority.

No original evidence hashes or source binaries are modified by these checks.
