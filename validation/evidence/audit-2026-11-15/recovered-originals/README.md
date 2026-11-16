# Recovered audit inventory

[English](README.md) · [Tiếng Việt](README-vi.md) · [Evidence inventory](../../README.md)

This folder records the recoverable inventory from the 15 November 2026 audit. It replaces a 5,340-line verbatim compilation that repeated staging notes, pull-request instructions and several copies of the same reports. Those editorial records were not scientific outputs and are not retained as current documentation.

## Material retained

| File | Purpose | What it proves |
| --- | --- | --- |
| [JSON inventory](SPATIAL_APP_AUDIT_EVIDENCE_MANIFEST_2026-11-15.json) | Metadata for 118 direct files and 271 members recorded inside historical ZIP files | Names, recorded sizes, hashes and provenance statements from the supplied inventory |
| [CSV inventory](SPATIAL_APP_AUDIT_FILE_MANIFEST_2026-11-15.csv) | Tabular view of the same 118 direct-file records | Machine-checkable agreement with the JSON inventory |
| [Original verifier](verify_spatial_app_audit_archive.py) | Checker supplied with the private archive | Can verify the full package only when the original ZIP and byte-range index are available |
| [Historical recovery receipt](recovery_receipt.json) | Size and hash record for the originally supplied recovery files | Preserved as provenance metadata; its removed verbatim compilation is no longer verified in this repository |

The repository does not contain every raster, script, screenshot, plot or ZIP member listed in the inventory. An inventory record is not evidence that the corresponding bytes are publicly available here.

## Findings retained from the recovered reports

| Topic | Supported statement | Limit |
| --- | --- | --- |
| V11 cross-location check | Historical reports record 17,177 cells for Shanghai core, Bao'an and Qimen. Full cells met the stated four-decimal CSV tolerance; 1,846 of 1,847 clipped cells met the strict 0.00005 tolerance and all met 0.0000501. | Source raster pairs, complete cellwise comparison files and plots are not deposited in this repository. |
| Bao'an A02 metadata | The published 7,148-row CSV contains unique cell IDs, observed status in every row and finite values for all five quality fields. | This covers an observed-data case only. It does not test genuine missing or low-support observations. |
| A02 performance | The historical baseline records 46.6687 seconds for the pipeline, 25.0028 seconds for A02 and a sampled process peak of 728.531 MiB. | It is one pre-optimization run without commit identity, not a capacity guarantee or proof of a speedup. |
| Shanghai GHSL | Historical reports record the native-grid quantity correction and an independent aggregate comparison that reproduced the deployed UI rounding on 715 eligible core cells. | There is no public live per-cell GHSL export. Bao'an and Qimen UI charts are not independent cellwise validation. |
| Yanqing | Recovered reports cover VIIRS, LISA, measurement, transformation, spatial and two-date temporal checks. | The reusable public files and their present limits are documented in the [Yanqing evidence guide](../../yanqing/README.md). |

Current acceptance status is maintained in the [validation guide](../../../README.md). Later evidence overrides older staging statements when it uses the same input and scope. A historical proposal, command list or pull-request instruction is not treated as a result.

## Reproducible checks

From the repository root:

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/check_docs.mjs
```

The first command checks the published Bao'an data and cross-checks the JSON and CSV inventories. It does not recreate absent private files or run Earth Engine.
