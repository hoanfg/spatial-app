<a id="top"></a>

# Validation guide and evidence register

[English](README.md) · [Tiếng Việt](README-vi.md) · [Application manual](../README.md) · [GADM and methods](../docs/README.md)

The result of a test applies to its stated location, year, input and precision. A successful CI run does not reproduce an Earth Engine raster, and an observed correlation does not validate an economic outcome.

| Read this for… | Location |
| --- | --- |
| Current status and remaining work | [Status below](#current-status) |
| Evidence inventory, source records and limitations | [Evidence guide](evidence/README.md) |
| Reusable datasets and checks | [Yanqing](evidence/yanqing/README.md), [Bao'an](evidence/audit-2026-11-15/), [cross-location protocol](cross_location/README.md) |

## Current status

| Topic | Supported result | Remaining boundary |
| --- | --- | --- |
| GADM China | 2,420 curated units matched the full-resolution GADM 4.1 source at documented precision; source label Nan corrected in PR #10 | This does not verify current official boundaries or all countries |
| Yanqing VIIRS and LISA | Independent 2014 and 2020 raster comparisons cover 8,333 cells each; formulas, FDR and 2014→2020 calculations checked in their recorded scope | A two-year result is not a continuous annual trend |
| V11 Shanghai / Bao'an / Qimen | Historical 2020 NTL comparison: 15,330/15,330 full cells within the four-decimal CSV bound; 1,846/1,847 clipped cells within strict 0.00005, all within 0.0000501. Queen/FDR comparisons are recorded with rounding and seed limits | Clipped cell geometry came from app GeoJSON; source rasters, detailed comparisons and plots are not deposited here |
| A02 observation metadata | Original 7,148-cell Bao'an CSV has all observed status and finite five quality fields; NTL CSV after PR #27 is byte-identical to the archived version | No real missing/low-support case; raw live download schema is not archived |
| GHSL Shanghai | Native-grid quantity conservation defect corrected in PRs #24–26. Independent Shanghai core rho, bootstrap interval and AUC reproduce deployed UI rounding on 715 eligible cells | No live per-cell GHSL export; Qimen/Bao'an UI charts are not independent cellwise validation |
| A02 performance | One post-PR-27 Bao'an profiler records A02 at 26.4623 s versus the earlier 25.0028 s; PR #29 added substep timings and `source_commit` | A02 speedup is not established; new comparable Cloud runs are needed |

See the [evidence guide](evidence/README.md) for deposited inputs, source records and SHA-256 checks. The recovered inventory indexes 118 direct files and 271 ZIP members. The repository holds a curated audit summary and selected CSV/JSON evidence, **not** every indexed original report, raster, script, plot or ZIP member.

## Audit findings and work still open

| ID | Action or decision | Evidence needed before closure |
| --- | --- | --- |
| S01–S03 | Preserve independent-checker safeguards for GHSL coverage/resolution and A02 reference footprint when original staged scripts can be recovered | The reports describe synthetic negative controls; checker source files and field inputs are absent from this repository |
| S04 | Match every reconstructed polygon to exported UTM/WGS84 centroid by `grid_id`; area alone misses equal-area swaps | Implemented in `main` with a negative control in `tests/test_cross_location_identity.py` |
| S05 | Reject fractional monthly valid-observation counts in independent checks | Production A02 schema already enforces integral counts; staged checker source is absent |
| A02 | Test a genuine no-observation/low-month field case without silently changing `legacy_zero_fill` | Aligned real raster support and app CSV from the same run |
| A03, A07, A09 | Keep Global/Local Moran samples and weights distinct; label block-aggregated MAUP correctly; treat rho thresholds as heuristics | A direct coarse-grid field comparison remains open; no numerical defect is inferred from the terminology alone |
| A04 | Decide the NaN/negative-input rule for two Gini implementations before aligning them | Scientific data contract and focused regression |
| A05, A06, A12 | Record a tested dependency matrix; gradually split coupled app code after end-to-end coverage; keep bilingual documents in sync | No lockfile, broad refactor or global document audit is claimed here |
| A08, A10, A11 | Check other GHSL epochs/masks, live Earth Engine→app→CSV execution, repeated Cloud runtime/RSS and multiple sessions | Authenticated service and measured runs with deployed commit |
| V12, V13 | Examine a continuous annual VIIRS series and compare with independently sourced, aligned economic outcomes | Neither two-year dynamics nor GHSL agreement proves these claims |

A01 CI discovery was fixed in PR #19. PR #10 corrected Local Moran's conditional sampling, observed-I normalization, explicit NoData masks and one GADM source label. PRs #20–22 added A02 and numerical controls; #24–27 addressed A02/GHSL production issues and the multiband reducer; #28 published recoverable audit evidence; #29 added A02 diagnostics; #31 added the S04 grid-identity guard. The [recovered audit inventory](evidence/audit-2026-11-15/recovered-originals/README.md) separates retained findings from duplicated staging notes.

## Methods and reproducibility

| Question | Method / limit |
| --- | --- |
| NTL per cell | Fractional pixel coverage mean of valid VIIRS annual median radiance; valid negative radiance is clipped to zero for the legacy output. Missing annual radiance is filled to zero upstream, with separate A02 support fields. |
| Local Moran | Eligible core/lit cells, row-standardized Queen or selected Rook weights, distinct non-focal conditional draws without replacement, inclusive tails and BH-FDR. Global Moran uses all cells and binary Queen weights. |
| GHSL | Sum native source-pixel quantities by polygon intersection fraction, then divide by cell area for density. Reproject polygons to the source CRS; do not sum resampled per-pixel amounts as if they were independent source amounts. |
| Evidence levels | CI and synthetic oracles, archival numeric consistency, independent field raster comparisons, and live operational checks answer different questions. Preserve the input hash, source revision, location, year, grid and tolerance with each claim. |

The root [technical manual](../README.md) gives the formulas and CSV dictionary. The [GADM and method guide](../docs/README.md) gives extraction rules and the interpretation of Space-Time regimes. Original detailed validation calculations remain available in the indexed historical documents; trimming their presentation here does not change the application formula or the reported numerical results.

### Checks available in this repository

```sh
node validation/audit_public_evidence.mjs --check-result
node validation/check_docs.mjs
python -m pytest -q tests
```

The evidence command checks the deposited data and public CSV summary; `check_docs.mjs` checks active links and basic math delimiters. The Python suite checks code contracts; it does not perform a fresh Earth Engine, GHSL field or Cloud benchmark. Do not mark a command as passed without its actual run result.
