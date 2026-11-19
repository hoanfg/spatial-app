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
| G04 | P1 | A bounded synthetic jobs-construct stress test and observed Bao'an 2020 NTL kernel sensitivity now have complete archived evidence. **Economic market-access validation and exogeneity remain open.** | Compare with genuinely independent georeferenced employment, population, transport friction or observed market outcomes, with predeclared measures and spatial uncertainty. |
| G05 | P1 | Production LISA-selected center sensitivity has archived evidence: synthetic known-center tests, 80-replicate proxy stress and Bao'an 2020 comparisons. **An independently verified real economic CBD is still absent.** | Use independently geocoded employment/POI or official activity-center evidence with matched spatial and temporal support; distinguish true center validity from in-sample gradient fit. |
| G06 | P1 | Fixed-cutoff conditional KS parametric bootstrap with alpha re-estimation, 4 cutoffs, 3 synthetic known distributions and Bao'an 2020, plus conditional AICc rivals now archived. **A spatially calibrated field Pareto law remains unverified.** | Refit data-dependent cutoff under a full null simulation; handle spatial dependence, temporal aggregation and alternative localities before any field-law inference. |
| G07 | P1 | The UI and handbook now clarify signed **cell-center** distance; geometric hotspot-border distance remains **unverified**. | Compare with polygon-boundary distances for complex HH shapes and grids. |
| G08 | P1 | Chronological comparison is guarded: `year_t0 < year_t1` in core and UI; new regression tests cover invalid years. | Existing two-year observational validation remains intact; no repeat required. |
| G09 | P1 | Guard added: four-state Shorrocks is now `NaN` when an initial quartile is empty (or fewer than 12 cells qualify). Two-period transitions remain descriptive, not an established long-run Markov process. | Still open: multi-year panel, rank-tie sensitivity, transition stability and real-world dynamics. |
| G10 | P1 | Optional cloud-free OBSERVATION-count raster now sums monthly `cf_cvg`, separately from valid-month count; the A02 support screen reports unknown/low support. This is not evidence that observation-count weighting is optimal. | Still needs genuine low-support VIIRS scene, independent monthly counts and an observed-data sensitivity study. |
| G11 | P1 | Single UTM zone from bbox center may distort wide, polar or antimeridian regions. | Geodesic control and projected-area/distance comparison at geographic extremes. |
| G12 | P2 | Fixed: large-grid residual Moran no longer sets an inferential flag from I > 0.3; descriptive-high-I and permutation-performed are separate. | A large-grid significance claim still needs a valid test and reference distribution. |
| G13 | P2 | When GHSL epoch differs from the VIIRS year the UI now warns and exports the year gap. The completed Shanghai validation is unaffected. | Contemporaneous economic agreement still requires an independently dated comparison or temporal sensitivity analysis. |
| G14 | P2 | Jaccard, core-frequency, seed SD and space-time movement thresholds are descriptive rules of thumb. | Empirical sensitivity plots rather than universal scientific cutoffs. |
| G15 | P2 | `moran_I_lit` is a mean of local statistics, not Global Moran I. | Ensure all current CSV/UI explanations preserve that distinction. |
| G16 | P2 | The evidence guide's VIIRS catalog link must match the application's `VCMSLCFG` product. | Check source/version provenance; no V11 rerun. |
| G17 | P1 | Archived synthetic Gaussian and actual-LISA permutation stress tests remain authoritative. The UI now explicitly disclaims unvalidated field FDR guarantees. **Formal field guarantee remains open.** | Validate null p-values, tested family and dependence/PRDS assumptions with a suitable spatial reference; do not infer validity merely from BH arithmetic. |
| G18 | P1 | Existing synthetic zero-vs-missing support sensitivity stands. The new guarded field runner refuses all-observed cases and unknown support; **no new real low-support field result is claimed**. | Use a real incomplete-support VIIRS A02 CSV and independent observation-support reference. |

**G09 bounded correction (19 November 2026).** The previous four-state Shorrocks calculation used `(4 - trace(P)) / 3` even when one or more initial quartiles had no cells, represented as all-zero rows in the exported transition table. Such rows are not probability distributions. For a 4×4 full-cell grid with eight zero-radiance cells and eight equally bright cells, all unchanged across two periods, the previous expression gave **0.6667** despite zero observed transitions. The corrected function returns `NaN` with status `undefined_empty_initial_quartile` and lists the missing source quartiles; a fully populated four-quartile identity transition still gives **0**. For backward compatibility, existing Markov tables retain zero rows for missing source classes, now explicitly labeled as undefined by the UI. This is a numerical invariant test, **not** a new field validation or confirmation of long-run Markov assumptions.

### Consolidated G01-G18 release decision (19 November 2026)

**One authoritative queue, not a series of new gaps:** [machine-readable 18-item disposition register](scientific_closure_register.json). The register separates *numerical completion*, *descriptively bounded indicators* and *claims that require unavailable independent real-world data*. A documented scientific limit is not a newly discovered code bug; do not open a follow-up PR merely to repeat an established result.

- **Implemented in one review branch:** G10 source observation counts from monthly `cf_cvg` are available as an optional additional Data Quality check, alongside (not instead of) valid-month counts. G10/G18 source-support screening and field-ready comparison runner, G12 inferential/descriptive residual-Moran separation, G13 GHSL-VIIRS year-gap warning, and G17 field-FDR interpretation warning. These additions do **not** change the legacy VIIRS composite, Local Moran, Gini, G17 simulations or historical V11 evidence.
- **G10/G18 reproducible command, once genuine sparse-coverage input exists:** `python validation/g10_g18_field_audit.py --input <REAL_A02_CELLS.csv> --out-dir <OUTPUT_DIR> --independent-reference <SEPARATE_SOURCE_SUPPORT.csv>`. The script requires 30–20,000 grid cells, a matching projected centroid pair, at least one unobserved cell and one supported post-clipping zero; it explicitly rejects all-observed or unknown-support files. The independent reference must contain `grid_id`, `ref_observed_fraction` and `ref_mean_valid_months`. It outputs a hashed cell-comparison CSV and JSON with fixed seed, policy, conditional LISA comparisons and limitations. It does **not** validate the identity of the upstream independent data source or the optimal monthly weight rule.
- **Cannot be scientifically closed without external evidence:** G04 economic market access, G05 economic CBD, G06 spatial Pareto law, G10/G18 real low-support bias, G17 a formally calibrated field null/FDR claim, G11 extreme-geography precision, G09 stationary multi-year Markov assumptions. These are blocked **claims**, not a request to rerun prior completed A02/V11/GHSL numerical checks. If data are unavailable, use bounded descriptive wording and retain the blocked status.
- **Safe stopping boundary:** for a research result, document the input raster revision, location-year, A02 support status, grid/CRS, zero policy, permutation/tested family, spatial sensitivity and the estimand actually computed. A green CI run or synthetic test alone is insufficient evidence of economic validity, causality or empirical FDR control. No archived validation is superseded here.

This is a consolidated closure of the **code-level safeguards and evidence bookkeeping that can be completed without new field data**, not an assertion that all 18 scientific questions have been resolved.

### G04: Distance-weighted NTL potential, construct stress and field sensitivity (19 November 2026)

**What is actually used, and what is not.** The production calculation uses only the archived VIIRS NTL, cell area, projected grid coordinates and user-selected distance-kernel settings. `SOL = NTL × cell area`; Euclidean distance is a proxy for proximity, not a measured trip time or transport cost. The production app does **not** ingest employment, population, household income, purchasing power, external market outcomes or transport networks for this index. The synthetic jobs values below are generated solely inside the audit script to challenge its interpretation. They are not observed jobs and are never read by the app. Therefore the computation works without economic data, but its **economic market-access interpretation is not established**.

**Scientific object.** The code computes $P_i=\sum_{j\ne i}w_{ij}SOL_j$ and $\widetilde P_i=P_i-\overline{SOL}_{core}\sum_{j\ne i}w_{ij}$ with $w_{ij}=\exp(-\tau d_{ij})$ truncated at a fixed Euclidean grid radius. At the production baseline, $\tau=0.5$ per kilometre and the five-step radius on a 500 m grid is **2.5 km** (the exponential half-distance is about 1.386 km). This transformation subtracts the **location-specific expectation under an unrestricted permutation of core-cell SOL**, not an estimated economic travel cost or the shock-assignment counterfactuals needed for causal exposure recentering. The previous T07 mathematical-expectation test is already closed and was not rerun.

**Synthetic construct stress with known, engineered job mass.** An irregular 335-cell grid contains a synthetic employment surface generated first. Light intensity is then deliberately constructed to match it with noise, to contain a bright *nonemployment* artifact, or to be spatially shuffled (one negative-control realization, not a randomization test). At the baseline, Spearman's correlation of **centered NTL potential** with the known synthetic **jobs-distance potential** was:

| Synthetic NTL scenario | Spearman correlation with constructed jobs-distance potential |
| --- | ---: |
| NTL deliberately linked to simulated jobs | 0.9361 |
| Same NTL with a strong unrelated lighting source | 0.4393 |
| Single seeded spatial shuffle of NTL | -0.2513 |

These values show sensitivity to the **constructed data-generating mechanism**, not empirical economic accuracy. The benchmark jobs surface is synthetic and the aligned light field is **generated directly from it**, so it is not an independent external employment observation. The single shuffled case does not supply a p-value.

**Observed radiance sensitivity in Bao'an (2020, 500 m).** Reuse exactly the existing, A02-checked, **7,148-row** archived cell CSV; **6,186 full core cells** enter the distance kernel and 962 clipped border cells remain in the exported join table with blank potentials. All 7,148 source records have observed A02 status. One noncore row has an invalid field and is excluded, not filled or assigned a fabricated coordinate. The source CSV is not edited or re-extracted. Against the same baseline on the same eligible core cells:

| Radius in grid steps | Max radius | Spearman range across $\tau$ | Top-decile Jaccard range across $\tau$ |
| --- | --- | --- | --- |
| 3 | 1.5 km | 0.9855 to 0.9891 | 0.7813 to 0.8152 |
| 5 | 2.5 km | 0.9984 to 1.0000 | 0.9344 to 1.0000 |
| 8 | 4.0 km | 0.9733 to 0.9985 | 0.7839 to 0.9527 |

Here $\tau\in\{0.25,0.5,1.0\}$ per km. Overall cell ranks remain similar, while identity of the highest-ranked 10% changes more. At baseline, raw potential has rank correlation **0.4085** with the geometry-only expected-exposure term, while the centered potential has **0.1758** with that term. Neither is an independence test and the centered quantity need not be spatially uncorrelated with geometry in realized, spatially structured data. Negative centered values (50.73% of eligible cells at baseline) mean *below the spatial-permutation reference expectation*, not negative employment or negative market access.

**Archived inputs and detailed outputs:** the [reproducible program](g04_ntl_potential_experiment.py), [335-cell synthetic input with generated employment](evidence/g04_ntl_potential/synthetic_input.csv), [1,005 synthetic cell-level baseline results](evidence/g04_ntl_potential/synthetic_cell_results.csv), [all 7,148 Bao'an cell IDs and baseline results](evidence/g04_ntl_potential/baoan_cell_results.csv), [36 scenario-level comparisons](evidence/g04_ntl_potential/sensitivity.csv), and [machine-readable summary, source SHA-256, software versions, definitions and limitations](evidence/g04_ntl_potential/summary.json). The original Bao'an CSV referenced by the summary is already deposited at `validation/evidence/a02_post_pr27/`. The CI job checks exact reproducibility of all five new outputs and leaves historical inputs intact.

**What is complete vs. open:** The archived G04 tests quantify sensitivity to a synthetic jobs-generating mechanism and to distance-kernel settings on observed VIIRS radiance. They do not prove economic meaning. **Economic construct validity remains open, not the ability to calculate the index.** A scientifically defensible economic market-access validation needs a real, independent, georeferenced employment or population surface and defensible transport/commuting costs aligned by place, time and spatial units; ideally also external market outcomes. Synthetic job mass cannot close that gap, and an NTL-only real-data sensitivity cannot identify an exogenous effect. This distinction matters because structural market access is linked to transport costs and markets in [Donaldson and Hornbeck (2016)](https://doi.org/10.1093/qje/qjw002), while exposure recentering for identification uses explicitly defined counterfactual shocks in [Borusyak and Hull (2023)](https://doi.org/10.3982/ECTA19367).

### G06: Pareto tail testing and conditional bootstrap (19 November 2026)

**Distinguish a Hill estimate from a distributional claim.** The production application estimates a Hill exponent on the largest 10% of positive core-cell NTL values. The existing `ntl.lisa_diagnostics.ks_pareto` reports a **nominal asymptotic KS p-value**, even though the Pareto exponent is estimated using the same sample. T09 already verifies its arithmetic on controlled inputs; **an arithmetic check is not a goodness-of-fit calibration**. G06 does not rerun the original field-extraction tests or change the production estimator, CSV keys, or output values.

**Audit design.** Four tail fractions are **predeclared** at 5%, 10%, 15% and 20% of the positive core cells. For each fraction, the threshold `u` is the `(k+1)`st largest positive NTL value, matching the production Hill convention, and the top `k` observations define the tail sample. We calculate $\widehat\alpha = 1/\overline{\log(x/u)}$ and the KS statistic against the fitted conditional continuous Pareto CDF. Then, **399 independent parametric bootstrap tail samples** are generated conditional on that same `u` and `k`. Crucially, the exponent is **re-estimated in each bootstrap sample**, and its own KS statistic is recalculated. The one-sided upper-tail Monte Carlo GOF p-value uses $(1 + \#\{D^{*} \ge D_{\rm obs}\})/(399+1)$, so the smallest reportable result is **0.0025**, not zero. Approximate binomial 95% intervals reflect Monte Carlo variability of the replicate count.

The cutoff is **conditioned upon, not selected or re-estimated in the bootstrap**. This is a deliberately limited **fixed-k conditional iid reference**. It is **not** the complete Clauset–Shalizi–Newman (2009) pipeline that optimizes the lower cutoff and repeats that step in the null simulation. For real spatially correlated VIIRS pixels, the iid reference p-value is **not** a spatially calibrated field significance test.

**Synthetic controls, 5,000 independent observations each.** The test generates a genuine Pareto parent law with exponent 2.5, a lognormal parent and a shifted exponential parent, with recorded seeds and full 5,000-row input table. The refitted-bootstrap results over the four predeclared fractions were:

| Known synthetic parent | Bootstrap KS p-value range | Typical rival comparison |
| --- | ---: | --- |
| Pareto with true exponent 2.5 | 0.4050 to 0.8075 | Conditional AICc selects Pareto in 3/4 cases, lognormal in 1/4 |
| Lognormal | 0.0025 to 0.0850 | Conditional AICc selects the truncated lognormal in 4/4 cases |
| Shifted exponential | 0.0025 to 0.0500 | Conditional AICc selects shifted exponential in 3/4 cases, truncated lognormal in 1/4 |

Nonrejection at one short cutoff, such as 5% for lognormal (p = 0.085), **does not prove a Pareto law**. The test can lose discrimination when only the most extreme observations are available.

**Observed Bao'an 2020 NTL: bounded conditional-iid reference only.** Reuse the exact 7,148-row A02-verified VIIRS CSV already deposited. There are **6,186 full-core, strictly positive NTL cells**; 962 border cells are retained in the archive join output but excluded from tail fitting. No live data or new economic proxy is introduced.

| Positive core NTL used | Tail size `k` | Hill exponent | Existing asymptotic KS p | Conditional refit-bootstrap KS p | Best conditional AICc |
| --- | ---: | ---: | ---: | ---: | --- |
| Top 5% | 309 | 5.6726 | 0.00665 | 0.0025 | Pareto |
| Top 10% (production cutoff) | 618 | 5.5904 | 0.09511 | 0.0225 | Pareto |
| Top 15% | 927 | 4.6953 | 0.000009 | 0.0025 | Truncated lognormal |
| Top 20% | 1237 | 4.0730 | <0.000001 at displayed precision | 0.0025 | Truncated lognormal |

**Interpretation:** At the default 10% cutoff, the old nominal p-value 0.09511 exceeds 0.05 while the refitted *conditional iid* reference p-value 0.0225 falls below it. These need not support the same conclusion even though both use the same 618 observations. This **does not permit a formal conclusion about the underlying spatial VIIRS field**, because the bootstrap neglects the dependence of neighboring cells and conditions on a selected order-statistic cutoff. With 399 bootstrap replicates, p = 0.0025 means no simulated refitted KS exceeded the observed value, subject to Monte Carlo resolution. In addition, **AICc selection is relative**: at 5% and 10%, Pareto is the least penalized of three tested conditional candidates, even though the conditional bootstrap reference rejects a Pareto-style iid fit at 5% level. There is no contradiction; best among candidates does not imply an adequate absolute fit.

**Rival distributions:** Exponential excesses and lognormal values **truncated below the same `u`** are independently fitted on the **same `k` exceedances** for each case, and compared against Pareto using AICc and descriptive KS differences. This avoids comparing an unconditional lognormal likelihood against a conditional Pareto likelihood. These are not likelihood-ratio significance tests; truncated lognormal parameter estimates are archived separately.

**Complete evidence and replay:** [generator](g06_pareto_tail_experiment.py), [all 5,000 synthetic inputs](evidence/g06_pareto_tail/synthetic_input.csv), [7,148 source Bao'an IDs with full-core/positive rank flags](evidence/g06_pareto_tail/baoan_tail_observations.csv), [all 16 model/cutoff cases](evidence/g06_pareto_tail/tail_cases.csv), [all 6,384 bootstrap draws with refitted exponent and KS](evidence/g06_pareto_tail/bootstrap_replications.csv), and [machine-readable methodology, fitted rivals, full scenario results, software versions and SHA-256 hashes](evidence/g06_pareto_tail/summary.json). The original Bao'an input is retained at `validation/evidence/a02_post_pr27/`. The CI job regenerates and compares **all five new evidence files byte-for-byte** under pinned dependencies.

**Still open:** The results **do not certify NTL Pareto tails** and do not establish a spatial, economic, or causal law. Needed evidence includes a spatially appropriate null generator or correlated-resampling design, temporal measurement checks, and a prespecified or fully bootstrapped cutoff-selection procedure on independent regions. See [Clauset, Shalizi and Newman (2009)](https://doi.org/10.1137/070710111). Existing `power_law_ok` is a **legacy approximate-KS screening flag**, not a field-verified model-fit statement; the UI explanation in this PR warns against overinterpretation.

### G05: NTL-selected center and gradient sensitivity (19 November 2026)

**What G05 does and does not establish.** The app's `urban_gradient_decay` and `monocentric_r2` are fitted on the same NTL observations used to select the center. The center is the SOL-weighted centroid of the largest eligible significant HH cluster, or a maximum of a combined NTL/neighbour-NTL score when no qualifying HH cluster exists. Next, the app calculates the area-weighted regression of $\log(1+\mathrm{NTL}_i)$ on Euclidean distance from that selected point. This is an **in-sample descriptive gradient**; R² does not validate the economic CBD, prove that a city is monocentric, or establish causal spatial structure. The existing WLS function and the saved historic schema have not changed.

**Part A: known-center synthetic control.** A fixed 25 × 25 grid has a generator center selected **before** drawing any light. It is known exactly **because it was specified in the experiment**, not because a real CBD was observed independently. Three fields share the same baseline noise: a single-center light surface, then that surface plus an unrelated bright source at amplitudes 60 and 170. For each field, the audit runs the production `run_lisa` center selection with Queen weights, 999 permutations, BH-FDR at 0.05, and four-cell minimum clusters. Centers recovered from rounded output distances are checked against the original gradient fit. Every synthetic run selected an eligible largest HH cluster (one, two and one eligible clusters respectively).

| Synthetic light field | NTL-selected center displacement from generator center | R² at known generator center | R² at NTL-selected center | NTL-selected gradient $\gamma$, per km |
| --- | ---: | ---: | ---: | ---: |
| Baseline, no unrelated bright source | 0.025 km | 0.874 | 0.874 | 0.3752 |
| Added bright source, amplitude 60 | 0.090 km | 0.533 | 0.541 | 0.3067 |
| Dominant unrelated bright source, amplitude 170 | 6.335 km | 0.304 | 0.128 | 0.1059 |

In the dominant-artifact design, the selected center moves away from the known generator center and the fitted gradient changes from 0.2579 to 0.1059 per km. **Using the NTL-selected center does not uniformly inflate R²:** in this configuration it **reduces** R² by approximately 0.176, while the moderate-artifact example increases R² by about 0.008. Neither comparison is a universal estimate of estimator bias.

For additional dispersion evidence, 80 seeded replications per field compare the known generator center with the geometry-only centroid, NTL-weighted centroid and brightest cell. Those **960 individual center-fit results** are archived. Their Monte Carlo summaries cover only these fast comparison-center rules. The full production HH selection is rerun for the three deposited synthetic fields, **not** for all 240 Monte Carlo fields; do not apply the repeated-proxy uncertainty to the production HH algorithm.

**Part B: observed Bao'an 2020 NTL, no independent economic CBD.** The study reuses the existing 7,148-cell A02-checked VIIRS CSV and fits exactly the same $\log(1+\mathrm{NTL})$ and area-weighted gradient on **6,186 full core cells**. It does **not** re-extract VIIRS or rerun A03/LISA. The historical app-selected center is recovered by multilateration from archived `dist_to_core_km` rounded to 0.001 km; its reconstructed distances have a median absolute discrepancy of **0.254 m** and a 99th-percentile discrepancy of **0.505 m**. This method identifies the **NTL-selected point from a previous output**, not an externally identified CBD.

| Bao'an 2020 center rule | Distance from archived NTL-selected point | Fitted $\gamma$, per km | In-sample R² |
| --- | ---: | ---: | ---: |
| Archived production NTL-selected center | 0 km | 0.02601 | 0.37988 |
| Geometry-only area centroid | 33.000 km | 0.02736 | 0.10613 |
| Same-year NTL-weighted centroid | 22.833 km | 0.04070 | 0.34348 |
| Same-year brightest NTL cell | 9.326 km | 0.02677 | 0.37505 |

These are **sensitivity estimates conditional on one region-year**, not rankings of economic CBD accuracy. The geometry-only centroid is defined without using NTL, but **it is not a verified job center**, and the two other alternative centers are still NTL-dependent. All fits use the same 6,186 cells and outcome, so the differences reflect center definitions rather than a change in the fitted sample. Differences as large as 0.274 in R² warn against treating `monocentric_r2` as an economic monocentricity test.

**Retained, replayable evidence:** [experiment source](g05_ntl_center_experiment.py); [625-cell synthetic inputs and all three brightness fields](evidence/g05_ntl_center/synthetic_input.csv); [1,875 synthetic cell-level LISA classes and distances](evidence/g05_ntl_center/synthetic_cell_results.csv); [960 seeded fast-center replications](evidence/g05_ntl_center/synthetic_replications.csv); [7,148 Bao'an IDs and center distances, with border exclusions preserved](evidence/g05_ntl_center/baoan_cell_results.csv); [19 fixed-field center comparisons](evidence/g05_ntl_center/center_comparison.csv); and [metadata, reconstruction diagnostics, Monte Carlo distributions, hashes and limitations](evidence/g05_ntl_center/summary.json). CI pins the scientific Python libraries and verifies all six files byte-for-byte. The Bao'an source file and all prior G04, G17, G18, A02, A03, V11 and GHSL evidence are unchanged.

**G05 economic validation remains open:** A real CBD or employment/activity center independently observed in or near 2020, with declared coordinates, provenance, support and timing, is needed before interpreting the center differences as **economic** selection bias. A fixed generator point in a synthetic experiment and a geometry-only centroid in a real city are not substitutes. Some urban light profiles may also be polycentric or nonlinear, so an ordinary single-center regression can be a poor description regardless of center choice. For methodological context see [Spatial gradients of urban land density and nighttime light intensity](https://doi.org/10.1057/s41599-023-01884-8).

### G17 spatial-dependence FDR study (bounded simulation, 19 November 2026)

This is a **two-part synthetic study**, not new VIIRS field validation and not a re-check of the BH step-up arithmetic closed by A03. A valid marginal p-value distribution and dependence among p-values are distinct from the correctness of the BH implementation.

**Part A, known null truth and power:** On a 64-cell (8×8) synthetic grid, compute row-standardized Queen or Rook neighbors and Gaussian fields of the form $z=D^{-1/2}(I-\rho W)^{-1}\epsilon$. Rescaling by exact marginal standard deviations makes each null score standard normal; the two-sided Gaussian p-values remain marginally valid even when the spatial scores depend on one another. Use $\rho\in\{0,0.5,0.8,-0.5\}$, 400 replications per weight, correlation and scenario, and $\alpha=0.05$. In a separate alternative, add a fixed mean shift of 2.75 standard deviations to the same nine predeclared central cells. The 55 remaining nulls are known true by construction. Here, **empirical FDR** is the average over replicates of false rejections divided by $\max(1,\text{all rejections})$; **power** is the proportion of nine injected signals detected. BY uses BH at $\alpha/H_{64}$ where $H_{64}=\sum_{i=1}^{64}1/i$.

| Part A measure across 8 spatial settings | BH | BY |
| --- | ---: | ---: |
| All-null empirical FDR | 0.0475 to 0.0575 | 0.0075 to 0.0175 |
| Fixed nine-cell signal, empirical FDR | 0.0353 to 0.0483 | 0.0087 to 0.0164 |
| Fixed nine-cell signal, detection power | 0.4222 to 0.4467 | 0.2194 to 0.2544 |

These are finite-simulation estimates, with Monte Carlo standard errors and 95% intervals in the [summary](evidence/g17_spatial_fdr/summary.json). A value such as 0.0575 from 400 all-null replicates is **not** by itself evidence that nominal 0.05 was violated. The filter parameter $\rho$ is the generator parameter, not an estimate of the app's cross-sectional lag-correlation indicator. The observed BY power reduction is specific to this signal size and set of dependencies.

**Part B, the actual Local Moran conditional-permutation method:** Generate positive lognormal light fields on the same fixed grid; apply the production `local_moran` and `bh_reject` routines, plus the BY threshold, with 999 conditional permutations, $\alpha=0.05$, 24 replications for each combination of Queen/Rook and $\rho\in\{0,0.8,-0.5\}$. For $\rho=0$, cells are identically and independently distributed, so spatial randomization is exchangeable and all local association null hypotheses hold. Under this all-null case neither BH nor BY rejected in 24/24 replications for either weight. This limited observation **does not prove** exact FDR control.

Under a correlated background with $\rho=0.8$ and no planted mean shift, BH rejected at least one cell in 16/24 Queen runs but 1/24 Rook runs; BY rejected in none of these 24-run groups. **These are not false discovery counts:** a correlated background itself violates the random-placement null and may produce genuine local spatial association. There is no validated per-cell true-null map for these runs, so the archived summary marks their FDR as `null`.

**P-value granularity:** With 999 two-sided permutations, the minimum reported pseudo p is 0.002 for 64 tests. Even the smallest p cannot trigger the step-up threshold at rank one. The earliest potentially feasible rank is three for BH and thirteen for BY in this setup. This discrete threshold materially limits power and must be reported when interpreting the LISA stress results.

**Evidence and replay:** The full synthetic design and predeclared injection mask are in [design.csv](evidence/g17_spatial_fdr/design.csv), all **6,544 individual simulation records** in [replicates.csv](evidence/g17_spatial_fdr/replicates.csv), and scenario summaries, uncertainty, assumptions and SHA-256 digests in [summary.json](evidence/g17_spatial_fdr/summary.json). The [generator](g17_spatial_fdr_experiment.py) uses fixed seeds and pinned NumPy, pandas and SciPy in CI. Run `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python validation/g17_spatial_fdr_experiment.py --verify` from repository root to compare generated outputs with every retained artifact.

**Unresolved G17 claim:** Neither positive spatial dependence nor BH step-up correctness proves the formal PRDS condition for LISA pseudo p-values. BY's arbitrary-dependence guarantee presumes valid null p-values; it **does not repair invalid spatial permutations**. Before a real-world nominal FDR claim, define the scientific null, the full tested family, how spatial nuisance dependence is handled and what ground truth or valid null calibration supports the claim. See [Benjamini and Yekutieli (2001)](https://doi.org/10.1214/aos/1013699998) and the [GeoDa Local Spatial Autocorrelation guidance](https://geodacenter.github.io/workbook/6a_local_auto/lab6a.html).

### G18 synthetic evidence (bounded result, 18 November 2026)

This experiment is based on a fully specified **synthetic** 12×12 grid at 500 m, not a real VIIRS or A02 scene. The controlled support mask has 106 observed-positive cells, 28 genuinely observed zeros and 10 unobserved cells that carry legacy filled zeros. All three runs use Queen neighbors, 999 conditional permutations, seed 42, alpha 0.05; the following outputs use BH-FDR.

| Analysis population and zero policy | Tested cells | HH | LL |
| --- | ---: | ---: | ---: |
| Known-support locations, positive NTL only | 106 | 22 | 21 |
| Known-support locations, including observed zero | 134 | 21 | 17 |
| All locations, naively treating unknown-support zeros as observed | 144 | 18 | 13 |

Including observed zeros changed 50/134 classes on the common known-support domain (including 28 formerly DARK cells); 45/134 neighbor counts and 92/106 comparable pseudo p-values also changed. Inappropriately including the 10 unknown-support cells changed 9/134 classes, 28/134 neighbor counts and 112/134 comparable pseudo p-values **among the truly supported locations**. In the naive run, all 10 unknown-support cells entered the local test family. Separate unadjusted results are stored in the evidence CSV.

**Scope restriction:** The fixed seed does not pair identical Monte Carlo draws across runs with different tested populations, so some p-value variation may reflect permutation-stream changes as well as the altered sample. This demonstrates possible specification sensitivity under one controlled synthetic field, **not** a measured bias magnitude in a real locality, proof of which policy is universally correct, or empirical FDR control. The safe audit runs subset the observed geography instead of feeding NaNs to the existing `run_lisa` (whose full Gini calculation rejects NaN). Consequently, the normalization population and tested family also change. Existing V11/GHSL/A02/A03/A04 validations are untouched, and the production default still excludes zero NTL cells from LISA.

**Retained evidence:** [generator](g18_zero_support_experiment.py), [input and support mask](evidence/g18_zero_support/synthetic_input.csv), [all cell-level results](evidence/g18_zero_support/cell_comparison.csv) and [machine-readable summary, software versions and SHA-256 identities](evidence/g18_zero_support/summary.json). The CI job runs the generator and checks all three archived outputs for exact reproducibility.

**G18 field validation remains open:** Select a genuine locality with independently verified observation-support metadata, distinguish measured zeros and missing coverage, and repeat a sensitivity comparison with preregistered interpretation and coverage thresholds.

### New validation acceptance criteria

- **G04/G05/G06:** retain independent input sources, spatial units, model definitions, seed, comparison metrics, cell-level results and sensitivity tables. Distinguish mathematical identity from economic construct validation.
- **G17:** preregister null-generating processes and nominal alpha; report empirical false discoveries, realized FDR, power and uncertainty over simulations. Do not treat a correct BH function as proof of FDR control for all spatial dependence structures. Background: [Benjamini and Yekutieli (2001)](https://doi.org/10.1214/aos/1013699998).
- **G18:** distinguish truly observed zero from no observation using verified A02 support fields; repeat only the alternative zero-inclusion specification, not the previously completed A03 reference tests.
- **A02/A07 remaining:** test a real incomplete-coverage scene and directly extracted coarse-grid raster respectively. Never re-open the completed Bao'an observed case or V11 raster comparison merely because a neighboring question remains.

**Change boundary for this update:** code changes affect scientific descriptions and chronology validation; the radiance thresholds, VIIRS/ GHSL extraction formulas, Local Moran permutation mathematics, BH step-up logic, Gini, historical files and numeric cell-class codes remain unchanged. The human-readable `ntl_class_label` now describes radiance rather than uncalibrated economic land-use categories.
