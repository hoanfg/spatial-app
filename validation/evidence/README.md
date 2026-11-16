# Evidence guide

[English](README.md) · [Tiếng Việt](README-vi.md) · [Validation status](../README.md) · [Data and methods](../../docs/README.md)

This folder contains the datasets and outputs used to check the application. Each result applies only to the stated location, year, grid and input files.

## Available evidence
| Evidence | Files | Supported result | Limit |
| --- | --- | --- | --- |
| Bao'an 2020 | [7,148-cell CSV, performance JSON and verified summary](audit-2026-11-15/) | Cell IDs are unique; every row has observed status and five finite A02 quality fields. The recorded pipeline took 46.6687 s, including 25.0028 s for A02. | One observed-data run. It does not cover genuine missing or low-support observations. |
| A02 after the multiband change | [Cell CSV and performance JSON](a02_post_pr27/) | All values in the 32 shared columns match the earlier 7,148-row export; the later file adds LISA columns. The recorded pipeline took 37.6479 s, including 26.4623 s for A02. | A02 was not faster in this single run. More comparable runs are required. |
| Yanqing 2014 and 2020 | [Cell exports, reference raster, independent comparisons and metrics](yanqing/README.md) | Supports the recorded VIIRS, LISA and two-date calculations for 8,333 cells. | Two dates do not establish a continuous annual trend. Some source rasters from the larger campaign are not deposited. |
| Shanghai, Bao'an and Qimen | [Boundaries and independent comparison workflow](../cross_location/README.md) | Recorded V11 results cover 17,177 cells and state the accepted full-cell and edge-cell tolerances. | The complete source-raster pairs, cellwise comparison outputs and plots are not deposited. |
| Synthetic controls | [A02 test outputs](a02/) and the repository test suite | Checks numerical, masking, schema and failure-handling contracts. | Synthetic tests do not replace a field comparison. |

## Why these checks are needed

| Question | Why it matters | Evidence used |
| --- | --- | --- |
| Can a measured zero be separated from missing observation support? | The legacy output fills missing annual NTL with zero. Without separate support fields, zero light and missing data can be confused. | Bao'an A02 columns, synthetic missingness case and schema tests |
| Did the multiband change alter existing output values? | A performance change is acceptable only if values and cell identity remain stable. | The earlier 32-column Bao'an export and the later export with added LISA columns |
| Did the change make A02 faster? | A shorter total pipeline does not prove that the targeted A02 stage improved. | Stage-level performance JSON before and after the change |
| Does raster extraction agree with an independent reference? | Correct code can still use the wrong raster, projection, mask or cell geometry. | Yanqing raster-to-polygon comparison and the three-location workflow |
| Do Local Moran and FDR results survive an independent calculation? | Neighbor construction, rounding, permutation seed and tail counting can change significance labels. | Yanqing per-cell LISA comparison and repository regression tests |

## Bao'an observation-support check

**Reason.** A02 was added so researchers can distinguish a measured NTL value of zero from a value produced when observation support is absent.

**Method.** The evidence command reads every row of the deposited 2020, 500 m CSV. It requires 7,148 unique `grid_id` values, `dq_status=observed`, `dq_stat_missing=false`, the `legacy_zero_fill` policy and finite values in all five quality fields. Fractions must stay in $[0,1]$ and the mean valid-month count in $[0,12]$.

**Result.**

- 7,148/7,148 rows pass the structural checks.
- `dq_observed_fraction` is 1 for every row.
- Negative, measured-zero and low-month fractions are 0 for every row.
- Mean valid months range from 10 to 12, with mean 11.9880599727.
- The later export has the same 7,148 rows. All values in the 32 columns shared with the earlier export match exactly; its additional fields are LISA outputs.

**Limit.** This is an all-observed case. It confirms that A02 fields can be populated, but not that a real missing or low-support pixel is classified correctly.

## Performance comparison

**Reason.** The multiband implementation targets repeated A02 raster traversal. Total runtime must therefore be separated from the A02 stage and from unrelated grid or NTL work.

| Measurement | Earlier run | Later run | Interpretation |
| --- | ---: | ---: | --- |
| Full pipeline | 46.6687 s | 37.6479 s | Later total is 9.0208 s shorter |
| Grid build | 9.7399 s | 5.0124 s | Different stage also became shorter |
| NTL zonal mean | 9.6193 s | 4.4589 s | Different stage also became shorter |
| A02 cell quality | 25.0028 s | 26.4623 s | Target stage is 1.4595 s longer in this run |
| Sampled process peak | 728.531 MiB | 688.941 MiB | Lower sampled peak, not a hard memory maximum |

Both runs report success, but they are single measurements and the earlier profiler has no commit identity. The evidence therefore supports “no A02 speedup demonstrated”, not a general performance regression or capacity guarantee.

## Synthetic missingness sensitivity

**Reason.** The Bao'an field file contains no missing-support rows, so it cannot show the statistical effect of treating missing observations as zero.

The deposited 36-cell synthetic case masks six cells. Relative to the complete baseline, legacy zero filling changes mean NTL from 10.9444 to 9.1944, zero-cell share from 0.0278 to 0.1944, Gini from 0.3054 to 0.4289 and binary-Queen Global Moran from 0.7319 to 0.6210. Six LISA labels and 33 Space-Time regimes change in the constructed example.

This is a diagnostic counterexample, not an estimate of field bias. It explains why observation support must be exported and why a real missing-support case remains a next step.
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
