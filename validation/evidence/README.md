# Evidence inventory

[English](README.md) · [Tiếng Việt](README-vi.md) · [Validation status](../README.md) · [Data and methods](../../docs/README.md)

This is the English guide for the evidence folder. It records what is deposited and what each item can support.

| Evidence | Deposited material | Scope |
| --- | --- | --- |
| Bao'an 2020 | 7,148-cell CSV, performance JSON, manifests and verified summary in [the audit deposit](audit-2026-11-15/) | Directly checks the deposited schema, values, IDs and hashes. It does not rerun Earth Engine or raster extraction. |
| Yanqing 2014 and 2020 | Cell exports, raster reference, independent comparisons and metrics in the [Yanqing folder](yanqing/README.md) | Supports the recorded VIIRS, LISA and two-date calculations for this location. |
| A02 after PR #27 | Cell CSV and performance JSON in [the A02 deposit](a02_post_pr27/) | Supports the recorded observed-data case and timing. It does not cover a real missing-support case. |
| Synthetic controls | Test outputs in [the A02 control folder](a02/) | Checks specific numerical and schema contracts only. |

## Recovered source records

The earlier plain-text compilations repeated superseded reports, mixed languages and retained pull-request staging instructions that were not scientific evidence. Their useful conclusions are now integrated into this README pair, the validation guide and the new [recovered audit inventory](audit-2026-11-15/recovered-originals/README.md).

The original JSON and CSV inventories, recovery receipt and byte indexes remain available as provenance metadata. Selected CSV, JSON, raster and ZIP evidence remains in its subject folder. The repository does not claim to hold all private files named by the historical inventory, and a retained byte index is not presented as runnable without its former compilation.

## Verification

Run from the repository root:

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/check_docs.mjs
```

The evidence command checks the deposited Bao'an data and cross-checks the recovered JSON and CSV inventories. The documentation check enforces the maintained README pairs, links, language-specific headings, punctuation and basic math delimiters.
