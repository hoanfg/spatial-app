<a id="top"></a>

# Validation status

[English](README.md) · [Tiếng Việt](README-vi.md) · [Application manual](../README.md) · [Evidence guide](evidence/README.md)

A result applies only to the stated location, year, input and precision. The table separates results supported by deposited evidence from work that still needs additional data.

## Results

| Topic | Result | Limit |
| --- | --- | --- |
| GADM China | 2,420 curated units matched the full-resolution GADM 4.1 source at the documented precision. | This does not verify current official boundaries or every country. |
| Yanqing VIIRS and LISA | The deposited 2020 polygon table has 8,332/8,333 cells within 0.00005; the single exceedance is a border cell at 0.0000643242. The independent LISA table matches 8,154/8,333 final classes and records all 179 differences. | LISA uses rounded exported NTL and an independent permutation seed, so label differences must be reported rather than treated as exact arithmetic failures. Two dates do not establish an annual trend. |
| Shanghai, Bao'an and Qimen | The completed V11 validation found 15,330/15,330 full cells within the four-decimal CSV bound; 1,846/1,847 clipped cells were within 0.00005 and all were within 0.0000501. The recovered manifest inventories the source rasters, application CSVs and edge-cell outputs used. | The current checkout preserves the report, inventory and hashes rather than every expanded binary input, so this completed result should not be confused with a fresh rerun from the checkout alone. |
| A02 observation metadata | The 7,148-cell Bao'an CSV has observed status and five finite quality fields in every row. Across the earlier and later exports, all values in the 32 shared columns match; the later file adds LISA columns. | No real missing or low-support field case has been checked. |
| GHSL Shanghai | The completed independent validation inventories native-grid and application-style rasters, a cell-validation JSON, hashes, script and report. The native-grid calculation reproduced the displayed rho, bootstrap interval and AUC rounding on 715 eligible cells. | Both rho intervals include zero, so the verified result is an inconclusive association for this sample, not proof of general GHSL agreement or economic validity. |
| A02 performance | The later Bao'an run records 37.6479 s for the pipeline and 26.4623 s for A02, compared with 46.6687 s and 25.0028 s in the earlier run. | The total run was shorter, but A02 itself was not faster. Repeated comparable runs are needed. |

File locations, hashes and runnable checks are listed in the [evidence guide](evidence/README.md).

The evidence guide's [scientific claim audit](evidence/README.md#scientific-claim-audit) distinguishes literature support, implementation tests and field comparisons. A citation can justify a method or interpretation, but it does not establish that this application's output passed a field check.

## Audit coverage register

The original source review used identifiers A01 to A12. Their current status is summarized here; the [complete audit question matrix](evidence/README.md#complete-audit-question-matrix) records the question, reason, evidence file, method, quantitative result or acceptance rule, tolerance and limit for each item.

| IDs | Current status |
| --- | --- |
| A01 | CI discovery gap closed. Current workflow runs the full maintained test tree across two jobs. |
| A02 | Observation fields verified for an all-observed Bao'an case; synthetic sensitivity quantified; a real missing-support case remains open. |
| A03 | Independent numerical oracles and Yanqing field comparisons are recorded; broader morphologies and continuous annual data remain open. |
| A04 | Closed. One Gini implementation returns 0.000000 for `[5,5,5,5]`, 0.500000 for `[0,0,10,10]`, 0.250000 for `[1,2,3,4]` and 0 for empty/all-zero samples, matching the independent pairwise formula within $10^{-12}$. Negative, NaN and infinite cases all raise an error instead of changing the sample. |
| A05 | Test versions are partly pinned, but production dependencies and a full reproducible lock remain incomplete. |
| A06 | Integration coverage and modular statistical code reduce risk; application orchestration remains coupled. |
| A07 | Block-aggregation MAUP is tested as implemented; equivalence to direct coarse-grid raster extraction is not established. |
| A08 | Native-grid GHSL conservation and CRS handling are fixed and tested; the independent Shanghai field validation is complete, with its inputs, cell-validation result, script and hashes recorded in the recovered evidence manifest. |
| A09 | Rho labels are descriptive conventions. Shanghai confidence intervals include zero and do not establish a nonzero association. |
| A10 | In-session caches are bounded and two field profiler files are deposited; concurrent Cloud capacity is untested. |
| A11 | Synthetic integration and one stored Bao'an execution cover many stages; a repeatable authenticated live-service end-to-end test is still absent. |
| A12 | Six maintained bilingual guide pairs and automated link/math checks are in place; semantic and scientific review remains manual. |

## What can be reproduced from this repository

| Check | Command or material | Scope |
| --- | --- | --- |
| Bao'an evidence | `node validation/audit_public_evidence.mjs --check-result` | Checks rows, IDs, A02 fields, stored summary and file inventories. |
| Documentation | `node validation/check_docs.mjs` | Checks the maintained English/Vietnamese guides, links and math delimiters. |
| Application contracts | `python -m pytest -q tests` | Checks numerical, schema, masking and interface behavior with deposited or synthetic inputs. |
| Three-location raster comparison | [Cross-location workflow](cross_location/README.md) and recovered audit manifest | Records the completed V11 method, inputs, edge-cell artifacts, tolerances and results. The current checkout is not a newly expanded binary rerun bundle. |

## Method boundaries

- NTL per cell is the fractional-coverage mean of valid VIIRS radiance. Negative valid radiance is clipped to zero for the legacy output; observation-support fields remain separate.
- Local Moran uses eligible core or lit cells and row-standardized weights. Global Moran uses all cells and binary Queen weights; the two statistics are not interchangeable.
- GHSL source-pixel quantities are summed by polygon intersection fraction on the native grid, then divided by cell area for density.
- Automated tests, stored numeric comparisons and live service checks answer different questions. Each published result should state its input, revision, location, year, grid and tolerance.

## Remaining scientific gaps: G01-G18 (18 November 2026)

This register follows the completed A01-A12, V11, Yanqing, Bao'an and Shanghai GHSL records above. A corrected label is **not** a new external validation. Existing numerical evidence, archival manifests, data and historic CSV schemas remain authoritative within their recorded scope. Codes such as `spatial_ar1_persistence`, `signed_dist_hh_km` and `0_Treated_HH` are preserved for downstream compatibility; their original names do not establish model identification.

| Gap | Priority | Current status and scientific risk | Next evidence required |
| --- | --- | --- | --- |
| G01 | P0 | Causal spillover/RDD claims replaced with descriptive HH-distance wording. Causality remains **unverified**. | External intervention or boundary identification, continuity checks and credible comparison design. |
| G02 | P0 | The UI now identifies `spatial_ar1_persistence` as cross-sectional `Corr(z, Wz)`. It is **not** a spatial AR estimate or unit-root test. | Estimate an explicit spatial model and define a separate stationarity test if needed. |
| G03 | P1 | Fixed NTL thresholds 5/15/40 now have descriptive radiance labels; economic calibration is **open**. | Cross-location land-use and independent socioeconomic calibration. |
| G04 | P1 | Permutation-centered NTL access identity is tested; its economic market-access meaning and exogeneity are **open**. | Compare with independent jobs, population or accessibility measures and sensitivity to distance decay. |
| G05 | P1 | The NTL-derived CBD can bias the estimated distance gradient and fit. | Compare against independently located activity centers; quantify slope and R² shifts. |
| G06 | P1 | Hill/KS arithmetic is tested; a fitted Pareto law is not independently established. | Bootstrap fit after re-estimating parameters; compare tail cutoffs and rival distributions. |
| G07 | P1 | The UI and handbook now clarify signed **cell-center** distance; geometric hotspot-border distance remains **unverified**. | Compare with polygon-boundary distances for complex HH shapes and grids. |
| G08 | P1 | Chronological comparison is guarded: `year_t0 < year_t1` in core and UI; new regression tests cover invalid years. | Existing two-year observational validation remains intact; no repeat required. |
| G09 | P1 | Two-period quartile transitions are descriptive, not a stationary long-run Markov process. | Multi-year continuous panel, ties/quantile sensitivity and transition stability. |
| G10 | P1 | Observed-month count is not observation-count weighting. A02's observed Bao'an result remains closed within scope. | Real low-support case with monthly `cf_cvg` heterogeneity and month-wise sensitivity. |
| G11 | P1 | Single UTM zone from bbox center may distort wide, polar or antimeridian regions. | Geodesic control and projected-area/distance comparison at geographic extremes. |
| G12 | P2 | Residual Moran flag changes from permutation p-value to a fixed I cutoff on large grids. | Align inference statuses or label the noninferential shortcut explicitly. |
| G13 | P2 | GHSL epoch may differ from VIIRS target year; Shanghai validation is unaffected. | Time-lag sensitivity with independently dated proxy data. |
| G14 | P2 | Jaccard, core-frequency, seed SD and space-time movement thresholds are descriptive rules of thumb. | Empirical sensitivity plots rather than universal scientific cutoffs. |
| G15 | P2 | `moran_I_lit` is a mean of local statistics, not Global Moran I. | Ensure all current CSV/UI explanations preserve that distinction. |
| G16 | P2 | The evidence guide's VIIRS catalog link must match the application's `VCMSLCFG` product. | Check source/version provenance; no V11 rerun. |
| G17 | P1 | BH arithmetic is tested, but spatial dependence does not guarantee nominal FDR in every setting. | Simulated spatial nulls: empirical FDR and power for BH versus BY, across weights and autocorrelation levels. |
| G18 | P1 | Synthetic support-aware sensitivity is now deposited: zero inclusion and false zero-fill change LISA labels, neighbors and p-values. **Real incomplete-support validation stays open.** | Repeat with a genuine A02-verified low-support scene; do not treat the synthetic result as external validation. |

### G18 synthetic evidence (bounded result, 18 November 2026)

This experiment is based on a fully specified **synthetic** 12×12 grid at 500 m, not a real VIIRS or A02 scene. The controlled support mask has 106 observed-positive cells, 28 genuinely observed zeros and 10 unobserved cells that carry legacy filled zeros. All three runs use Queen neighbors, 999 conditional permutations, seed 42, alpha 0.05; the following outputs use BH-FDR.

| Analysis population and zero policy | Tested cells | HH | LL |
| --- | ---: | ---: | ---: |
| Known-support locations, positive NTL only | 106 | 22 | 21 |
| Known-support locations, including observed zero | 134 | 21 | 17 |
| All locations, naively treating unknown-support zeros as observed | 144 | 18 | 13 |

Including observed zeros changed 50/134 classes on the common known-support domain (including 28 formerly DARK cells); 45/134 neighbor counts and 92/106 comparable pseudo p-values also changed. Inappropriately including the 10 unknown-support cells changed 9/134 classes, 28/134 neighbor counts and 112/134 comparable pseudo p-values **among the truly supported locations**. In the naive run, all 10 unknown-support cells entered the local test family. Separate unadjusted results are stored in the evidence CSV.

**Scope restriction:** This demonstrates possible specification sensitivity under one controlled synthetic field, **not** a measured bias magnitude in a real locality, proof of which policy is universally correct, or empirical FDR control. The safe audit runs subset the observed geography instead of feeding NaNs to the existing `run_lisa` (whose full Gini calculation rejects NaN). Consequently, the normalization population and tested family also change. Existing V11/GHSL/A02/A03/A04 validations are untouched, and the production default still excludes zero NTL cells from LISA.

**Retained evidence:** [generator](g18_zero_support_experiment.py), [input and support mask](evidence/g18_zero_support/synthetic_input.csv), [all cell-level results](evidence/g18_zero_support/cell_comparison.csv) and [machine-readable summary, software versions and SHA-256 identities](evidence/g18_zero_support/summary.json). The CI job runs the generator and checks all three archived outputs for exact reproducibility.

**G18 field validation remains open:** Select a genuine locality with independently verified observation-support metadata, distinguish measured zeros and missing coverage, and repeat a sensitivity comparison with preregistered interpretation and coverage thresholds.

### New validation acceptance criteria

- **G04/G05/G06:** retain independent input sources, spatial units, model definitions, seed, comparison metrics, cell-level results and sensitivity tables. Distinguish mathematical identity from economic construct validation.
- **G17:** preregister null-generating processes and nominal alpha; report empirical false discoveries, realized FDR, power and uncertainty over simulations. Do not treat a correct BH function as proof of FDR control for all spatial dependence structures. Background: [Benjamini and Yekutieli (2001)](https://doi.org/10.1214/aos/1013699998).
- **G18:** distinguish truly observed zero from no observation using verified A02 support fields; repeat only the alternative zero-inclusion specification, not the previously completed A03 reference tests.
- **A02/A07 remaining:** test a real incomplete-coverage scene and directly extracted coarse-grid raster respectively. Never re-open the completed Bao'an observed case or V11 raster comparison merely because a neighboring question remains.

**Change boundary for this update:** code changes affect scientific descriptions and chronology validation; the radiance thresholds, VIIRS/ GHSL extraction formulas, Local Moran permutation mathematics, BH step-up logic, Gini, historical files and numeric cell-class codes remain unchanged. The human-readable `ntl_class_label` now describes radiance rather than uncalibrated economic land-use categories.
