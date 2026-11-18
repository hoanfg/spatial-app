# Evidence guide

[English](README.md) · [Tiếng Việt](README-vi.md) · [Validation status](../README.md) · [Data and methods](../../docs/README.md)

This folder contains the datasets and outputs used to check the application. Each result applies only to the stated location, year, grid and input files.

## How evidence is classified

The repository contains several kinds of checks. They answer different questions and must not be combined into one general PASS.

| Level | Meaning | Examples |
| --- | --- | --- |
| Deposited and runnable | The input or result table is in this repository and a local command can inspect it. | Bao'an A02, Yanqing comparison tables, synthetic regression tests |
| Completed archived validation | The verification was completed and its report, inventory, hashes and named input/result artifacts are preserved, although the current checkout does not expand every binary artifact for a fresh rerun. | Three-location V11 and Shanghai GHSL |
| Contract test | A small controlled case checks a formula, schema, mask or failure path. | Gini, Moran, FDR, NoData and cache tests |
| Open question | The repository does not contain enough evidence to decide the scientific or operational claim. | Real missing-support A02 case, multi-session Cloud capacity, economic construct validity |

## Scientific claim audit

A citation, a code test and a field comparison are different forms of support. The table below records which form is available for the main scientific claims used across the maintained guides. It does not turn a literature-backed method into a field-validated result for this application.

| Claim family | External basis | Repository check | Audited conclusion |
| --- | --- | --- | --- |
| VIIRS measurement and observation support | The [Earth Engine VIIRS catalog](https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_MONTHLY_V1_VCMCFG) documents `avg_rad`, `cf_cvg`, 463.83 m pixels, possible negative radiance, incomplete monthly coverage and unscreened temporary lights in the Version 1 series. | A02 schema tests and the Bao'an export check the fields produced by the application. | Source characteristics and application fields are supported. Bao'an is an all-observed case; real missing support and contamination from temporary lights remain untested. |
| Fractional raster extraction | Baston (2023), [DOI 10.5281/zenodo.11396419](https://doi.org/10.5281/zenodo.11396419), specifies coverage-aware raster and polygon summaries. | Deterministic zonal tests and the deposited Yanqing raster comparison check the implemented path. | Fractional weighting is implemented and has one deposited field comparison. No universal error magnitude is claimed for a center-point alternative. |
| MAUP and grid support | Openshaw (1984) and Fotheringham and Wong (1991), [DOI 10.1068/a231025](https://doi.org/10.1068/a231025), establish sensitivity to scale and zoning. | A07 tests the application's block-aggregation robustness path. | A regular grid standardizes spatial support but does not eliminate MAUP. The current field evidence does not establish equivalence to a fresh coarse-grid raster extraction. |
| Moran, LISA and multiple testing | Moran (1950), [DOI 10.1093/biomet/37.1-2.17](https://doi.org/10.1093/biomet/37.1-2.17); Anselin (1995), [DOI 10.1111/j.1538-4632.1995.tb00338.x](https://doi.org/10.1111/j.1538-4632.1995.tb00338.x); and Benjamini and Hochberg (1995), [DOI 10.1111/j.2517-6161.1995.tb02031.x](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x), provide the statistical basis. | Hand oracles, enumerated null cases, regression tests and the Yanqing independent comparison check selected implementations. | The tested formulas and stated rules are supported. A significant cluster remains descriptive of spatial association, not a causal effect or official urban boundary. |
| Nighttime light as an economic proxy | Henderson et al. (2012), [DOI 10.1257/aer.102.2.994](https://doi.org/10.1257/aer.102.2.994), and Gibson et al. (2021), [DOI 10.1016/j.jdeveco.2020.102602](https://doi.org/10.1016/j.jdeveco.2020.102602), show both potential and context-dependent measurement limits. | The repository has no matched GDP, income, price or household outcome for the deposited places. | The application measures and describes radiance. Economic construct validity remains open and no README result should equate NTL with GDP, welfare or causal economic activity. |
| GHSL external agreement | The JRC technical records define [GHS-BUILT-S](https://doi.org/10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA) and [GHS-POP](https://doi.org/10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE). | Native-grid conservation tests are runnable; the completed Shanghai package is indexed with its rasters, per-cell validation JSON, script, hashes and report. | GHSL is a separate settlement proxy, not ground truth for NTL or an economic outcome. The verified Shanghai result is inconclusive because both rho intervals contain zero. |

## Available evidence
| Evidence | Files | Supported result | Limit |
| --- | --- | --- | --- |
| Bao'an 2020 | [7,148-cell CSV, performance JSON and verified summary](audit-2026-11-15/) | Cell IDs are unique; every row has observed status and five finite A02 quality fields. The recorded pipeline took 46.6687 s, including 25.0028 s for A02. | One observed-data run. It does not cover genuine missing or low-support observations. |
| A02 after the multiband change | [Cell CSV and performance JSON](a02_post_pr27/) | All values in the 32 shared columns match the earlier 7,148-row export; the later file adds LISA columns. The recorded pipeline took 37.6479 s, including 26.4623 s for A02. | A02 was not faster in this single run. More comparable runs are required. |
| Yanqing 2014 and 2020 | [Cell exports, reference raster, independent comparisons and metrics](yanqing/README.md) | Supports the recorded VIIRS, LISA and two-date calculations for 8,333 cells. | Two dates do not establish a continuous annual trend. Some source rasters from the larger campaign are not deposited. |
| Shanghai, Bao'an and Qimen | [Boundaries and independent comparison workflow](../cross_location/README.md) plus the recovered manifest | Completed V11 results cover 17,177 cells; the manifest names the matched rasters, application CSVs and per-edge-cell artifacts and preserves their hashes. | Not every archived binary is expanded in the current checkout, so a fresh local rerun is a packaging question rather than an unfinished scientific verification. |
| Synthetic controls | [A02 test outputs](a02/) and the repository test suite | Checks numerical, masking, schema and failure-handling contracts. | Synthetic tests do not replace a field comparison. |

## Why these checks are needed

| Question | Why it matters | Evidence used |
| --- | --- | --- |
| Can a measured zero be separated from missing observation support? | The legacy output fills missing annual NTL with zero. Without separate support fields, zero light and missing data can be confused. | Bao'an A02 columns, synthetic missingness case and schema tests |
| Did the multiband change alter existing output values? | A performance change is acceptable only if values and cell identity remain stable. | The earlier 32-column Bao'an export and the later export with added LISA columns |
| Did the change make A02 faster? | A shorter total pipeline does not prove that the targeted A02 stage improved. | Stage-level performance JSON before and after the change |
| Does raster extraction agree with an independent reference? | Correct code can still use the wrong raster, projection, mask or cell geometry. | Yanqing raster-to-polygon comparison and the three-location workflow |
| Do Local Moran and FDR results survive an independent calculation? | Neighbor construction, rounding, permutation seed and tail counting can change significance labels. | Yanqing per-cell LISA comparison and repository regression tests |

## Complete audit question matrix

This matrix consolidates the A01 to A12 review and the later field checks. The result column states only what the named evidence supports.

| ID and scientific question | Evidence used | Method and acceptance rule | Quantitative result | Limit |
| --- | --- | --- | --- | --- |
| A01. Does CI execute every maintained test file? | [Workflow](../../.github/workflows/tests.yml) and [test suite](../../tests/) | The core job runs the two lightweight statistical files. The second job runs the remaining `tests/` tree, excluding only those two files already run by the core job. Both jobs must finish successfully. | The original gap was closed after the Space-Time file was added to CI. Current branch checks are the execution record; the historical 54 to 61 count is not used as a current total because the suite has grown. | CI confirms checked code paths on its installed environment. It is not a live Earth Engine, field-data or Cloud-load test. |
| A02. Can measured zero be separated from missing observation support? | [Bao'an CSV and verified summary](audit-2026-11-15/), [synthetic sensitivity JSON](a02/synthetic_sensitivity.json), `tests/test_data_semantics.py` and `tests/test_a02_field_schema.py` | Require unique cell IDs, explicit status and policy, finite quality fields and valid ranges. Use a controlled missingness case to test whether zero filling can change downstream statistics. | Bao'an: 7,148/7,148 rows are observed; mean valid months 10 to 12, mean 11.9880599727. Synthetic six-cell mask changes mean, zero share, Gini, Global Moran, six LISA labels and 33 Space-Time regimes. | Bao'an contains no genuine missing-support row. The synthetic case demonstrates sensitivity, not field bias. |
| A03. Are the statistical formulas consistent with independent oracles? | `tests/test_numerical_validation_a03.py`, `tests/test_advanced_statistics_a03b.py`, `tests/test_audit_regressions.py` and [Yanqing evidence](yanqing/README.md) | Compare Gini with the pairwise definition; binary Global Moran with a hand-calculated four-cell chain; Local I and Queen neighbors with explicit small grids; BH-FDR with fixed p-values; conditional permutations with enumerated null cases. | The hand oracle for Global Moran is $1/3$; Local I is $[0.45,0.15,0.15,0.45]$; BH-FDR at 5% rejects the second and fourth values in $[0.2,0.01,0.04,0.001]$. Yanqing reports 8,154/8,333 matching final LISA classes. | Small deterministic tests do not validate every morphology or a complete conditional permutation distribution on field data. Yanqing uses rounded NTL and an independent seed. |
| A04. Do both Gini implementations have the same input contract? | `app.py::gini`, `ntl/lisa_core.py::gini` and numerical tests | Inspect handling of nonfinite and negative inputs, then compare valid nonnegative arrays with the same reference formula. | Both formulas agree on valid nonnegative test inputs. `ntl/lisa_core.py` removes nonfinite and negative values; `app.py` does not. | The invalid-input contract remains unresolved. Do not silently change the estimator until the intended scientific rule is chosen. |
| A05. Can the software environment be reproduced? | `requirements.txt`, `requirements-test.txt` and the workflow | Record Python and dependency versions used by CI and evidence generation; require a repeated run under a declared environment. | Test dependencies pin ESDA 2.10.0 and libpysal 4.15.1. Most production packages remain unpinned; CI uses Python 3.11 and 3.13 in separate jobs. | A complete lock file and cross-version equivalence result are not deposited. A passing CI run is not long-term environment reproducibility. |
| A06. Is application coupling controlled well enough for safe changes? | `app.py`, modular `ntl/` files and the integration suite | Use integration and schema regressions to detect changes across raster, grid, statistics, UI and CSV boundaries. | Core numerical and many UI paths have regression coverage, and statistical modules are separated under `ntl/`. | Much orchestration still resides in `app.py`. No metric proves that future refactoring is behavior-preserving beyond the covered tests. |
| A07. Does block aggregation represent a direct coarse-grid raster extraction? | `ntl/robustness.py`, `tests/test_robustness.py` and the cross-location method | Distinguish aggregation of 500 m cell means into blocks from rebuilding a 1,000 m grid and extracting the raster again. Only a matched comparison can establish equivalence. | The application calculates the aggregation path and its HH overlap measures. No deposited field comparison establishes equality with direct coarse-grid extraction. | MAUP outputs are robustness diagnostics for the implemented aggregation, not a universal result for another grid-construction method. |
| A08. Are GHSL quantities conserved and aligned with the grid? | `ntl/ghsl_native.py`, `tests/test_ghsl_native_grid.py`, `tests/test_ghsl_computepixels.py` and the completed Shanghai package indexed by the recovered manifest | Keep GHSL quantities on the native 100 m Mollweide lattice, reproject polygons, weight each pixel quantity by intersection fraction, reject absent coverage, then compare rho, block-bootstrap interval and AUC on eligible core cells. | The old Shanghai reprojection inflated built surface by 16.51428% and population by 16.59686%. After the fix, 715 eligible cells gave built rho -0.0794533, CI [-0.220123, 0.086086], AUC 0.394636; population rho 0.1358105, CI [-0.029628, 0.271008], AUC 0.576274. | The archived package is not fully expanded in the current checkout. The completed Shanghai result does not generalize to Bao'an, Qimen or another epoch. |
| A09. Are interpretation thresholds scientific acceptance criteria? | `ntl/validation.py` and Shanghai GHSL results | Compute rho, a spatial block-bootstrap interval and top-quartile AUC. Treat the 0.4 and 0.6 labels as display conventions, not universal hypothesis-test thresholds. | Both Shanghai rho intervals contain zero. The evidence therefore does not establish a nonzero monotonic association in this urban-core sample. | GHSL is a contextual proxy, not nighttime-light ground truth or an independent economic outcome. AUC is descriptive here. |
| A10. Are cache and runtime behavior bounded? | `ntl/lisa_ui.py`, performance JSON files and runtime tests | Bound in-session caches, record stage wall time and sampled process RSS, and compare like-for-like runs. A capacity claim requires repeated multi-session measurements. | LISA cache is capped at five parameter sets. Bao'an sampled peaks were 728.531 and 688.941 MiB; pipeline times were 46.6687 and 37.6479 s. | RSS is sampled for the server process, not isolated by user. No concurrent-user capacity or hard memory limit has been measured. |
| A11. Does the full pipeline work from live service to export? | `tests/test_pipeline_integration.py`, `tests/test_ui_smoke.py`, Bao'an exports and performance JSON | Test raster to zonal values to LISA to CSV with controlled inputs; separately inspect a real exported CSV and stage profiler. | The stored Bao'an run reports success for all 13 recorded stages. The two Bao'an exports have 7,148 rows and identical values in all 32 shared columns. | The test suite does not authenticate to Earth Engine. The profiler and CSV do not constitute a repeatable live Earth Engine to Streamlit to export test with injected failures. |
| A12. Do maintained documents agree with code and evidence? | [Documentation checker](../check_docs.mjs), six English/Vietnamese README pairs and this matrix | Check expected guide pairs, internal links, math delimiters and prohibited punctuation. Link every quantitative claim to a deposited file or state the missing evidence. | The maintained documentation set contains 12 guides in six bilingual pairs and passes the documentation check on this branch. | Link and formatting checks cannot prove translation equivalence or scientific truth. Manual review remains necessary when evidence or code changes. |
| V11. Does independent VIIRS extraction agree across contrasting places? | [Cross-location workflow](../cross_location/README.md), completed V11 report and recovered manifest | Compare independent Earth Engine raster integration with application cells at 500 m. Full cells use the four-decimal CSV tolerance; clipped cells are retained and reported. Recompute Queen and BH-FDR with stated seed qualifications. | Shanghai 886 cells, Bao'an 7,148 and Qimen 9,143, total 17,177. All 15,330 full cells pass. Of 1,847 clipped cells, 1,846 are within 0.00005; all are within 0.0000501. | The manifest records matched inputs and per-edge-cell outputs, but not every archived binary is expanded in the checkout. The clipped polygons came from the application export, not an independent reconstruction. |
| GADM. Do curated Chinese boundaries correspond to the selected source release? | [Data and methods guide](../../docs/README.md) and curated files under `data/` | Match preserved identifiers and mapped administrative fields to GADM 4.1 at the documented precision; use GID rather than display names for joins. | 2,420 curated units were matched. One source record with missing administrative fields was omitted; `CHN.14.10.2_1` is identified as Nan while its legacy filename remains for compatibility. | This is source-release correspondence, not verification of current legal boundaries or all countries. |

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

## Three-location VIIRS and LISA check

**Question and reason.** A result from one pilot location may depend on its geometry, brightness distribution or boundary share. Shanghai, Bao'an and Qimen were selected to cover an urban core, a multipart urban-industrial district and a less urbanized county.

**Evidence.** The repository contains the three GADM boundaries, the independent comparison program and the Earth Engine export recipe in [`validation/cross_location/`](../cross_location/). The recovered audit manifest also inventories the matched application CSVs, Shanghai and Qimen VIIRS rasters, per-edge-cell result tables and archived verification packages with hashes. Together with the preserved report, this records a completed validation; not every binary artifact is expanded as a direct file in the current checkout.

**Method and tolerance.** The reference raster is integrated independently over the application cell polygons. Full cells must agree within the four-decimal CSV rounding bound of 0.00005. Clipped cells remain in the result; a second 0.0000501 guard distinguishes the literal threshold from floating-point noise. The LISA review reconstructs Queen neighbors, Local I and BH-FDR, while retaining the effect of rounded NTL and Monte Carlo seed conventions.

| Location | All cells | Full cells | Clipped cells |
| --- | ---: | ---: | ---: |
| Shanghai | 886 | 706 | 180 |
| Bao'an | 7,148 | 6,131 | 1,017 |
| Qimen | 9,143 | 8,493 | 650 |
| Total | 17,177 | 15,330 | 1,847 |

All 15,330 full cells met the CSV bound. Among clipped cells, 1,846/1,847 met 0.00005. Bao'an `grid_id=628` compared 18.8768 with 18.876850039; it exceeded the literal bound by $3.93\times10^{-8}$ and remained within 0.0000501.

**Limit.** The application-exported clipped polygons were reused, so the comparison does not independently reconstruct every cell from the source boundary. The result does not establish GHSL agreement or economic validity. Re-expanding every archived input would improve one-command reproducibility but would not change the completed V11 finding.

## Shanghai GHSL check

**Question and reason.** GHSL built-surface and population bands store quantities per source pixel. Reprojecting those values to another lattice and summing them as new pixel quantities can violate conservation and can also fail completely when raster and vector CRS do not overlap.

**Evidence.** The repository contains the corrected native-grid implementation and synthetic regression tests. The recovered manifest indexes the independent Shanghai package, including native and application-style GHSL rasters, the cell-validation JSON, SHA-256 record, validation script and post-deployment report. This is a completed field validation whose binary package is not expanded in full in the current checkout.

**Method.** Keep the 100 m GHSL raster on its ESRI:54009 source grid, transform the 500 m polygons to that CRS and sum `pixel quantity × intersection area / 10,000 m²`. Use core cells with at least 99% of nominal area. For association, calculate average-tie Spearman rho, a 200-draw 5 by 5 cell block bootstrap with seed 42, and Mann-Whitney top-quartile AUC.

Before the conservation fix, the common Shanghai core contained 36,234 source pixels but 42,244 destination pixels. The application-style sum inflated built surface from 118,319,940 to 137,859,621 m², or 16.51428%, and population from 11,674,618.205 to 13,612,238.308, or 16.59686%.

After the native-grid and CRS corrections, the independent aggregate calculation used 715 of 886 core cells:

| Metric | Built surface | Population |
| --- | ---: | ---: |
| Positive-proxy eligible cells | 715 | 715 |
| Spearman rho | -0.0794533 | 0.1358105 |
| Block-bootstrap 95% interval | [-0.220123, 0.086086] | [-0.029628, 0.271008] |
| Top-quartile AUC | 0.394636 | 0.576274 |
| Median GHSL density | 353,036 m²/km² | 33,799 people/km² |

The rho, interval endpoints and AUC reproduce the displayed application values at their shown precision. Both intervals include zero, so this sample does not establish a reliably nonzero monotonic association.

**Limit.** The independent result verifies the stated Shanghai package and metrics; it does not make the Earth Engine Drive and live `computePixels` paths identical for every possible run. Shanghai does not establish behavior for Bao'an, Qimen or another GHSL epoch. GHSL is not a direct economic outcome.

## Numerical and integration checks

**Reason.** Field comparisons can reveal input and geometry errors, while small independent oracles isolate formula and failure-path behavior. Both are needed.

The numerical suite covers a hand-calculated binary Global Moran value of $1/3$, Local I values $[0.45,0.15,0.15,0.45]$, Queen adjacency on a 2 by 2 grid, Gini against the pairwise absolute-difference definition, BH-FDR boundaries, conditional permutation tails, ties, missing-year Space-Time behavior and CSV round trips. Raster tests cover clipped polygons, masks, NoData, nonfinite values and the choice between preserving missing values and filling zero.

These checks use exact expectations or case-specific tolerances defined in the test files. Monte Carlo tests assess a distribution within their stated tolerance; they do not require the same random stream as another library. A complete passing suite means the declared contracts ran successfully, not that every live dataset or scientific interpretation is valid.

## Recorded Yanqing specification sensitivity

The recovered audit inventory identifies complete reports and result files for measurement, transformation, weights and grid sensitivity. Their summaries are retained here because they answer scientific interpretation questions that are different from basic code correctness. The original scripts and all derived cell tables are not in the current repository, so these are recorded results with incomplete public rerun, not new computations from this branch.

### Annual median versus annual mean

Using the same 8,333 cells, geometry and LISA rules, changing the 2020 monthly composite from annual median to annual mean changed unweighted mean NTL from 1.4137188 to 1.4754449, or 4.366%. Gini changed from 0.6809244 to 0.6861015 and binary-Queen Global Moran from 0.914128499 to 0.914558970. Significant HH cells changed from 370 to 385 and LL from 2,510 to 2,499; HH and LL Jaccard were 0.96104 and 0.96201. The masked and zero-filled median were identical for all 30,814 pixels in that particular raster, so this sample did not contain the missingness needed to test A02 in the field.

### Raw, P99 and log transformation

All specifications used the same 7,733 active cells, Queen weights, 999 conditional permutations without replacement, seed 42, inclusive two-sided p-values and BH-FDR at 0.05.

| Result | Raw NTL | P99 capped | Log NTL |
| --- | ---: | ---: | ---: |
| HH cells | 370 | 457 | 1,050 |
| LL cells | 2,510 | 2,510 | 2,441 |
| All FDR-significant cells | 2,880 | 2,967 | 3,491 |
| HH area share | 4.617% | 5.702% | 13.102% |
| Input skewness | 6.312 | 4.905 | 1.928 |

Raw versus P99 HH Jaccard was 0.809628; raw versus log was 0.352381. All 370 raw HH cells remained HH under both alternatives, so the low raw-log overlap resulted from 680 additional moderately bright log-HH cells, not displacement of the original core. The transformation changes the analysis scale; it is not a harmless display choice, and no result here decides which scale best predicts an independent economic outcome.

### Queen, Rook and grid resolution

| Specification | Grid cells | Tested | HH | LL | HH area share |
| --- | ---: | ---: | ---: | ---: | ---: |
| Queen 500 m | 8,333 | 7,733 | 370 | 2,510 | 4.6169% |
| Rook 500 m | 8,333 | 7,733 | 187 | 906 | 2.3334% |
| Queen 1,000 m | 2,162 | 1,865 | 92 | 562 | 4.5919% |
| Rook 1,000 m | 2,162 | 1,865 | 46 | 210 | 2.2960% |

At 500 m, Queen versus Rook HH Jaccard was 0.5054. Across 500 m and a newly constructed 1,000 m grid, the geographic HH Jaccard was 0.6547 for Queen and 0.6864 for Rook. Similar total HH area therefore did not imply stable hotspot boundaries. These results concern the independently reconstructed coarse grid in that archived study; they do not establish that the application's separate block-aggregation diagnostic is numerically equivalent.

The report and result-file identities are recorded in the [118-record audit inventory](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_FILE_MANIFEST_2026-11-15.csv). Wider publication requires restoring the named scripts, metrics and source inputs rather than copying only these summary numbers.
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
