# Evidence guide

[English](README.md) · [Tiếng Việt](README-vi.md) · [Validation status](../README.md) · [Data and methods](../../docs/README.md)

This folder contains the datasets and outputs used to check the application. Each result applies only to the stated location, year, grid and input files.

## Available evidence

| Evidence | Files | Supported result | Limit |
| --- | --- | --- | --- |
| Bao'an 2020 | [7,148-cell CSV, performance JSON and verified summary](audit-2026-11-15/) | Cell IDs are unique; every row has observed status and five finite A02 quality fields. The recorded pipeline took 46.6687 s, including 25.0028 s for A02. | One observed-data run. It does not cover genuine missing or low-support observations. |
| A02 after the multiband change | [Cell CSV and performance JSON](a02_post_pr27/) | The NTL CSV matches the deposited Bao'an reference byte for byte. The recorded pipeline took 37.6479 s, including 26.4623 s for A02. | A02 was not faster in this single run. More comparable runs are required. |
| Yanqing 2014 and 2020 | [Cell exports, reference raster, independent comparisons and metrics](yanqing/README.md) | Supports the recorded VIIRS, LISA and two-date calculations for 8,333 cells. | Two dates do not establish a continuous annual trend. Some source rasters from the larger campaign are not deposited. |
| Shanghai, Bao'an and Qimen | [Boundaries and independent comparison workflow](../cross_location/README.md) | Recorded V11 results cover 17,177 cells and state the accepted full-cell and edge-cell tolerances. | The complete source-raster pairs, cellwise comparison outputs and plots are not deposited. |
| Synthetic controls | [A02 test outputs](a02/) and the repository test suite | Checks numerical, masking, schema and failure-handling contracts. | Synthetic tests do not replace a field comparison. |

## Checks

Run from the repository root:

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/check_docs.mjs
python -m pytest -q tests
```

The first command checks the deposited Bao'an CSV, performance summary and evidence inventories. The documentation check verifies the maintained English/Vietnamese guides and their links. The Python suite checks application contracts; it does not download new satellite data.

## Evidence still needed

- one real A02 case with missing or low observation support;
- complete source-raster pairs and per-cell outputs for the three-location V11 comparison;
- a live per-cell GHSL export for independent comparison;
- repeated performance measurements using the same deployed revision and settings;
- a continuous multi-year VIIRS series and an independently sourced economic outcome for broader interpretation.
