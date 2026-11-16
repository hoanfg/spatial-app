# Bilingual evidence edition quality check

The checks inspect **editorial reading editions only**; they do not change, translate or rewrite the SHA-256-protected archives.

```sh
node validation/check_evidence_language_editions.mjs --strict
node validation/audit_bilingual_editions.mjs
node validation/audit_public_evidence.mjs --check-result
```

The manifest at `validation/evidence/reading-editions/translation_manifest.json` maps **78 recovered report sections** (35 distinct SHA-256 bodies) and **13 historical document sources** (11 bilingual topic pairs) to one complete English and one complete Vietnamese reading edition per unique text. The consolidated field report is a separate bilingual pair.

**Logical coverage:** 78 × 2 + 13 × 2 + 2 = **184 source-language references**, resolved to **94 content files** (70 report files, 22 historical files and 2 consolidated reports). Shared original report hashes are deliberately translated once, rather than writing dozens of duplicate full texts.

`check_evidence_language_editions.mjs` validates the original inventory, manifest associations, source SHA citations in editions, Unicode em dashes, basic placeholders, minimum edition length and Vietnamese diacritics. `--strict` fails on missing mappings; CI runs strict mode. `audit_bilingual_editions.mjs` independently cross-checks every recovered source entry and historical manifest record, verifies canonical pair presence and basic editorial navigation.

Historical sources 01/02 and 03/04 originally constitute separate English and Vietnamese source documents with **different original SHA-256 hashes**. The source-language edition cites the corresponding original hash. Every original remains in the protected archival file.

**Limitations:** automated coverage, file-level formatting and source-hash referencing do not certify that every translation is linguistically perfect, that all section-level details are equivalent, or that scientific computations have been rerun. A bilingual domain reviewer should compare formulas, all numbers, caveats, historical status dates and tables against each original. The archived original bytes and hashes remain authoritative.

No additional GeoTIFF, GeoJSON, raw Cloud logs or private source binaries are published by this documentation work.
