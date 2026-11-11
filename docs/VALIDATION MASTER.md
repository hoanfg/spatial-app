<a id="top"></a>

# Spatial-app: Validation specification and evidence register

| Field | Description |
|:---|:---|
| Project | Spatial econometrics and VIIRS nighttime-lights extraction |
| Repository | `hoanfg/spatial-app` |
| Document | Validation specification |
| Version | 1.0: 11 November 2026 |
| Reference implementation | Main branch, following pull requests #10, #11, #12 and #13 |
| Reference study | Yanqing District, Beijing, China, 2014–2020 |
| Scope | Methods, numerical findings, acceptance criteria, limitations and future verification |
| Maintenance | This document is revised through pull requests; previous findings remain traceable |

> **Scope of assurance.** The principal raster extraction and spatial statistics have been reproduced for the specified Yanqing study. This does not establish universal validity for other locations, years, economic interpretations or the production hosting environment. This document records both successful tests and material sensitivities.

## Contents

1. [Purpose and validation standards](#s1)
2. [Reference datasets and reproducibility](#s2)
3. [GADM boundary audit](#s3)
4. [Statistical implementation and Local Moran validation](#s4)
5. [Independent VIIRS extraction - 2020](#s5)
6. [Independent VIIRS extraction - 2014](#s6)
7. [Measurement sensitivity](#s7)
8. [Transformation sensitivity](#s8)
9. [Spatial robustness](#s9)
10. [Temporal validation and Spatial Markov](#s10)
11. [GHSL convergent validation](#s11)
12. [Regression tests and corrective changes](#s12)
13. [Validation status and remaining work](#s13)
14. [Evidence register](#s14)
15. [Update protocol and change log](#s15)

---

<a id="s1"></a>
## 1. Purpose and validation standards

### 1.1. Research objective

The application integrates GADM 4.1 administrative boundaries, VIIRS Day/Night band radiance, regularly spaced analytical grids, zonal statistics, spatial autocorrelation, Local Indicators of Spatial Association (LISA), GHSL reference variables, and two-period spatial dynamics. Verification must distinguish **numerical correctness** from **sensitivity to methodological choices**, **validity of a proxy for economic activity**, and **operational reliability**.

The verification programme uses the following categories:

| Category | Meaning | What it does not imply |
|---|---|---|
| PASS: tested scope | Independent calculation agrees with the specified implementation within a prespecified numerical tolerance | General performance in all locations |
| SENSITIVITY CHARACTERIZED | Effects of alternative definitions have been quantified | All specifications are interchangeable |
| FIXED | A documented defect or interpretation problem was corrected and regression-tested | Every possible downstream use is validated |
| PARTIAL | Relevant results exist, but part of the independent comparison is missing | End-to-end verification |
| PENDING | No sufficient independent evidence is currently recorded | Failure or lack of scientific utility |

### 1.2. Evidence hierarchy

The assessment distinguishes (1) deterministic formula and geometry checks, (2) independent recomputation of Monte Carlo procedures, (3) independent raster-to-polygon benchmarks on actual Earth Engine products, (4) external comparisons with independent datasets, and (5) production execution tests. Agreement in one category must not be substituted for another.

The validation reports were generated on 11 November 2026 and consolidated into this specification. Their original CSVs, GeoTIFFs, Python scripts and evidence packages are identified in Section 14. Unless explicitly stated, those binary files are **not committed to this repository**. A clone of the repository alone does not reproduce all reported numbers.

<a id="s2"></a>
## 2. Reference datasets and reproducibility

### 2.1. Golden reference case

| Parameter | Value |
|---|---|
| Country and administrative district | China - Beijing - Yanqing |
| GADM identifier | `GID_2 = CHN.2.1.11_1` |
| Boundary source | `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Beijing/CHN_Beijing_Yanqing_District.geojson` |
| VIIRS source | `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` |
| VIIRS radiance and coverage bands | `avg_rad` and `cf_cvg` |
| Calendar years | 2014 and 2020 |
| Annual aggregation | Median of monthly composites after masking `cf_cvg == 0` |
| Application raster export | EPSG:4326, nominal scale **463.83 metres** |
| Grid projection | UTM zone 50N, EPSG:32650 |
| Baseline analytical grid | 500 m × 500 m, clipped to the district boundary |
| Number of clipped cells | **8,333** |
| Total grid area | Approximately **2,003.51 km²** |
| Border-cell exclusion rule | Area < 99% × 0.25 km² |
| Excluded border cells | **600** |
| Cells tested by LISA | **7,733** |
| Local Moran weights | Row-standardized binary Queen adjacency, with eligible neighbors |
| Monte Carlo parameters | 999 permutations, seed 42 for baseline |
| Inference | Conditional permutations without replacement; app-specific inclusive two-sided pseudo-p; Benjamini–Hochberg FDR at 5% |

### 2.2. Provenance and alignment

The application fetches a bounding-box annual GeoTIFF from Earth Engine. It converts radiance values into floating-point raster data, preserves invalid raster masks, clips negative **valid** radiance to zero and computes a coverage-weighted zonal mean for each actual grid polygon using `exactextract`.

The 500 m analytical grid is **not** the original VIIRS grid. Its UTM polygon boundaries intersect multiple pixels from the EPSG:4326 Earth Engine image. Therefore a center-pixel sample, a point extraction, or a grid overlay without a common raster affine transform is **not** a valid substitute for the original zonal mean.

Both the GADM polygon coordinates and the raster geotransform must be reproduced at full available precision. Early verification of border cells used rounded geometry, causing a slight discrepancy. Reconstructing the exact polygon eliminated it.

### 2.3. Reported source files

The primary CSVs were:

- `dien_khanh_NTL_2020_500m.csv`;
- `CHN_beijing_yanqing_2020_500m_lisa_cells.csv`;
- `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv`.

Earth Engine reference files were `yanqing_viirs_2020_reference.tif`, `yanqing_valid_months_2020.tif`, `yanqing_viirs_2020_annual_mean.tif`, `yanqing_viirs_2020_masked_median.tif`, `yanqing_viirs_2014_reference.tif`, `yanqing_valid_months_2014.tif` and `yanqing_viirs_2014_masked_median.tif`.

Because CSV radiance is exported to four decimal places, `5×10⁻⁵ nW/cm²/sr` is the natural absolute tolerance for a raster benchmark when comparing the unrounded reference mean to exported cell-level values.

<a id="s3"></a>
## 3. GADM boundary audit

### 3.1. Audit design

The audited China collection contains **2,420 curated GeoJSON files**. Each was compared against an official full-resolution GADM 4.1 China GeoPackage using administrative identifiers and geometry. Checks covered missing/invalid polygons, duplicate identifiers, topology agreement and measurable overlaps above the adopted 1 m² screening threshold.

### 3.2. Findings

- All **2,420** curated geometries and identifiers matched their GADM counterparts within the tested tolerance.
- No invalid geometry, duplicate GID or overlap exceeding the screening threshold was found in the audited set.
- **2,419/2,420** name values matched the source; the exceptional record was investigated.
- `GID_2 = CHN.14.10.2_1` had an incorrect curated name (`Yiyang`) where source data specified `Nan`. Pull request #10 corrected the metadata while retaining the geometry and file identity.
- One source GADM unit with an `NA` name was not represented by the curated export. Accordingly, a geometrically accurate curated dataset is not necessarily a one-to-one enumeration of every record in the source GeoPackage.

### 3.3. Resource-aware unit selection

Administrative subdivisions of major municipalities are intentionally analysed at district level. Beijing, Shanghai, Tianjin and Chongqing were split into manageable curated units to protect the Streamlit Community Cloud memory budget. This is a deliberate safeguard, **not** evidence of a missing city-level calculation. Studies requiring citywide estimates must specify an aggregation method across district units.

### 3.4. Verdict

**PASS for geometry and identifier consistency within the audited China export.** Cross-country GADM harmonization, naming conventions and socioeconomic comparability remain broader research questions outside this specific audit.

<a id="s4"></a>
## 4. Statistical implementation and independent Local Moran verification

### 4.1. Analysis sample and spatial adjacency

The baseline computes the lit-cell standardized score on non-edge analysis cells. A Queen adjacency relation includes neighbors sharing an edge **or** corner. Eligible cells constitute the membership pool for lag and conditional permutations; edge-masked or otherwise ineligible cells are not valid members of the neighbor graph.

For a focal cell \(i\) and valid set of neighbors \(N_i\), the row-standardized spatial lag is

\[
(Wz)_i = \frac{1}{|N_i|}\sum_{j\in N_i}z_j.
\]

The local Moran statistic follows the ESDA-style denominator:

\[
I_i = \frac{z_i(Wz)_i}{\sum_{j\in M}z_j^2/(|M|-1)},
\]

where \(M\) is the common set of eligible analysis cells. Raw values and transformed values are standardized separately when conducting sensitivity analyses.

### 4.2. Conditional Monte Carlo inference

The corrected algorithm samples **distinct non-focal member cells without replacement** for each permutation, keeping the focal standardized score fixed. This corrects an earlier with-replacement issue documented in PR #10.

The application uses a **two-sided, inclusive-tail Monte Carlo convention**: counts from simulated statistics at or beyond the observed statistic in either tail are converted into a pseudo-p with the +1 correction and twice the smaller tail, capped at one. For 999 simulations, the nominal smallest two-sided p-value is `2/(999+1) = 0.002`. Its tie handling and two-sided definition need not equal the default one-tail `esda.Moran_Local.p_sim`; comparisons must align conventions first.

Benjamini–Hochberg is then applied over the eligible focal cells at \(\alpha=0.05\). Quadrants are defined by the signs of the focal z-score and neighbor lag, and final HH/LL/HL/LH labels require statistical significance.

### 4.3. Deterministic audit

| Test | Observed result |
|---|---|
| Total cell rows | 8,333 |
| Excluded border cells | 600 |
| Eligible focal cells | 7,733 |
| Queen neighbor count per cell | **8,333/8,333 agreement** |
| Raw HH/LL/HL/LH quadrant assignments | **7,733/7,733 agreement** |
| Maximum absolute Local Moran I difference | Approximately **0.00016805** using rounded CSV inputs |
| FDR decisions reconstructed from exported `lisa_p_sim` | **100% agreement** |
| Significant HH | **370** |
| Significant LL | **2,510** |
| Not significant | **4,853** |
| Edge masked | **600** |

The small Local Moran difference should not be interpreted as a numerical defect because exported `ntl_mean` and `lisa_I` were rounded.

### 4.4. Independent seed and repeatability

A separate 999-permutation run with seed `20261111` produced pseudo-p Pearson correlation **~0.9967** with the exported values. The alternative seed yielded **2,879** significant cells versus **2,880** in the application, **375 HH** versus **370** (Jaccard **~0.935**) and **2,504 LL** versus **2,510** (Jaccard **~0.940**). These differences are consistent with Monte Carlo variability close to FDR thresholds; identical seed and permutation order are needed to demand exact p-value equality.

Later sensitivity work, using the original seed and matching algorithm, reproduced all baseline LISA labels and exported p-values. The independent-seed results and exact same-seed replication are complementary, not contradictory.

### 4.5. Verdict and limitations

**PASS within the reference configuration** for grid adjacency, deterministic Local Moran, permutation and BH-FDR behavior. This does not make the local hotspot map invariant to weights, transformations, grid sizes or the inference convention.

<a id="s5"></a>
## 5. Independent VIIRS extraction: 2020

### 5.1. Independent Earth Engine reference

The validation reproduced the annual median by selecting all monthly images between `2020-01-01` and `2021-01-01`, masking `avg_rad` where `cf_cvg <= 0`, taking the median and applying the same zero-fill policy as the application. A separate GeoTIFF was exported from Earth Engine for the common Yanqing bounding box.

### 5.2. Polygon reconstruction and raster benchmark

The complete GADM district polygon was projected into EPSG:32650 and intersected with the aligned 500 m grid. That reconstruction yielded exactly **8,333 polygons** with an area sum agreeing with the application's exported grid to within the geometry/CSV rounding tolerance. Each polygon's coverage-weighted mean was computed from the independent raster using pixel intersection area.

An interim check had validated **7,703 full cells**, with approximately **30 lightly clipped cells** and **600 border cells** requiring exact polygons. A single remaining apparent outlier at `grid_id=349` disappeared once unrounded GADM coordinates were used. The final result supersedes the earlier partial checks.

### 5.3. Final results

| Metric | Result |
|---|---:|
| Compared cells | **8,333** |
| Cells within exported-precision tolerance | **8,333/8,333** |
| Absolute tolerance | **0.00005 nW/cm²/sr** |
| Mean absolute error | Approximately **0.000025 nW/cm²/sr** |
| Maximum absolute error | Approximately **0.000050 nW/cm²/sr** |
| Pearson correlation | Approximately **0.99999999997** |
| Border-masked cells included in raster verification | **600/600** |
| Raster size | 217 × 142 = **30,814 pixels** |

The separate valid-month raster indicated **12 months with `cf_cvg > 0` at every exported pixel**. This counts monthly composites meeting the criterion, **not** the total number of satellite observations. The masked annual median contained no missing pixels in this bounding-box export.

### 5.4. Verdict

**PASS:** the complete 2020 VIIRS raster-to-cell extraction pipeline was independently reproduced at CSV output precision, including all clipped border polygons. No inference is made about missing data or calibration in other years or regions.

<a id="s6"></a>
## 6. Independent VIIRS extraction: 2014

### 6.1. Reference image and quality control

A separate 2014 annual median was built with the same Earth Engine collection, `cf_cvg > 0` mask, median aggregation, spatial bounds, raster scale and zonal-statistic rule.

The 2014 reference, masked median and valid-month rasters were all **217 × 142 pixels**, aligned with the 2020 reference. The coverage raster again indicated **12 valid monthly composites at all 30,814 exported pixels** and no missing annual-median pixels.

One 2014 VIIRS pixel had a **slightly negative radiance**. Two analytical cells intersected that pixel. The application clips **valid negative values to zero** before `exactextract`; reproducing this step resolved their discrepancies.

### 6.2. Results

| Metric | Result |
|---|---:|
| Compared grid cells | **8,333** |
| Cells within CSV rounding tolerance | **8,333/8,333** |
| Mean absolute error | Approximately **0.00002505 nW/cm²/sr** |
| Maximum absolute error | Approximately **0.00004999 nW/cm²/sr** |
| Pearson correlation | Approximately **0.9999999998** |
| Border cells successfully compared | **600/600** |
| Negative-radiance source pixels | **1** |
| Affected grid cells | **2** |

### 6.3. Two-year interpretation

The unweighted mean NTL across the common grid rose from **~0.4452 (2014)** to **~1.4137 (2020)**, or roughly **3.18 times** the 2014 level. Across 8,333 cells, **8,221 increased** and **112 decreased** in absolute radiance.

**PASS for 2014 raster extraction and the two-year radiance comparison.** An increase in absolute nighttime radiance should not automatically be described as economic or GDP growth.

<a id="s7"></a>
## 7. Measurement sensitivity: annual aggregation and missingness

### 7.1. Experimental design

The baseline takes the median of valid monthly radiance composites. Two alternatives were computed independently from Earth Engine: (a) an **unweighted mean of the monthly composites**, and (b) the **annual median with missing pixels preserved** rather than zero-filled. The same polygon grid, baseline inference parameters, and raster-to-cell extraction procedure were retained.

This annual mean is not an observation-count-weighted mean of raw satellite acquisitions; it is a mean of the valid monthly composite values.

### 7.2. Results

| Statistic | Annual median | Annual mean | Masked median |
|---|---:|---:|---:|
| Mean cell radiance | **1.4137** | **1.4754** | **1.4137** |
| Gini coefficient | **0.6809** | **0.6861** | **0.6809** |
| Global Moran I (binary Queen, same 8,333-cell sample) | **0.91413** | **0.91456** | **0.91413** |
| Significant HH | **370** | **385** | **370** |
| Significant LL | **2,510** | **2,499** | **2,510** |
| HH share of district area | **4.617%** | **4.804%** | **4.617%** |

The annual mean raised mean radiance by approximately **4.37%** relative to the median. Yet the geographical HH and LL sets remained similar: Jaccard **~0.961 (HH)** and **~0.962 (LL)**.

The masked and zero-filled medians agreed exactly over this pilot because the validated raster had no missing pixels. Therefore the comparison **does not test the impact of filling genuine missing pixels in a dataset with coverage gaps**.

### 7.3. Interpretation

The choice of annual aggregation influences radiance magnitude and inequality modestly, while preserving the main local clusters for this pilot. The application retains **annual median as the specified baseline**. Annual mean remains a sensitivity specification rather than a replacement.

<a id="s8"></a>
## 8. Transformation sensitivity: raw, P99 and log

### 8.1. Specifications

The tests used the 2020 annual median, 500 m grid, Queen neighbors, 999 permutations, seed 42 and FDR 5%. P99 caps positive NTL values at the **99th percentile of lit cells** before z-standardization. The log alternative applies the natural logarithm **on positive NTL values** in the lit-cell LISA computation. It is **not** the `log1p(NTL)` transform employed in the two-period dynamics module.

### 8.2. Results

| Statistic | Raw | P99 | Natural log |
|---|---:|---:|---:|
| Significant HH | **370** | **457** | **1,050** |
| Significant LL | **2,510** | **2,510** | **2,441** |
| Total significant cells | **2,880** | **2,967** | **3,491** |
| HH district area share | **~4.62%** | **~5.70%** | **~13.10%** |
| Raw-quadrant HH before significance | **1,072** | **1,135** | **2,517** |

**HH Jaccard:** raw–P99 **0.810**, raw–log **0.352**, P99–log **0.435**.

All **370 raw HH cells** also remained HH under the logarithmic specification, while the log alternative identified **680 additional HH cells**. The median untransformed NTL was approximately **13.259** among original raw HH cells and **2.731** among the additional log HH cells. Around **20.38%** of tested cells changed their raw-quadrant classification between the raw and log specifications.

### 8.3. Statistical interpretation

The NTL distribution is heavily right-skewed. Extremely bright cells strongly influence the raw mean and standard deviation. Logging compresses the upper tail and changes which cells have positive relative scores; it also affects the spatial lag signs and the resulting quadrants. The low Jaccard thus reflects a material **change in the underlying statistical definition**, not simply sampling noise or an implementation error.

### 8.4. Decision

Retain **raw NTL** as the baseline for absolute radiance concentration, **P99** as a robustness measure against extreme values, and **log NTL** as an alternative representation of relative light intensity. A specification must not be selected solely because it identifies more or fewer HH clusters. Findings sensitive to transformation should be reported as such.

<a id="s9"></a>
## 9. Spatial robustness: Queen/Rook and 500/1,000 m

### 9.1. Study design

Queen weights include edge- and corner-sharing cells; Rook weights include edge-sharing cells only. The 1,000 m grid was reconstructed from the original GADM geometry and the **source VIIRS raster**, not estimated by simply averaging 500 m CSV cells. All variants used raw annual median, 999 permutations, seed 42 and FDR 5%.

### 9.2. Comparison

| Spatial configuration | Tested cells | HH | LL | HH area share |
|---|---:|---:|---:|---:|
| Queen 500 m (baseline) | **7,733** | **370** | **2,510** | **4.62%** |
| Rook 500 m | **7,733** | **187** | **906** | **2.33%** |
| Queen 1,000 m | **1,865** | **92** | **562** | **4.59%** |
| Rook 1,000 m | **1,865** | **46** | **210** | **2.30%** |

The complete clipped 1,000 m grid contains **2,162 polygons**; the **1,865** figures are the eligible focal cells after edge masking.

At 500 m, all **187 Rook HH cells** belonged to the Queen HH set. Changing neighbor definition approximately halved HH area.

Between 500 m and 1,000 m, the Queen HH area was approximately **92.5 km² → 92.0 km²** and the Rook HH area **46.75 km² → 46.0 km²**. Similar totals do not imply identical locations. Direct polygon intersection gave **spatial Jaccard 0.655** for Queen (about **73.0 km²** shared HH area) and **0.686** for Rook (about **37.75 km²** shared HH area).

### 9.3. Verdict

**SENSITIVITY CHARACTERIZED.** HH area is relatively stable across these cell scales but the boundaries change materially; results are more sensitive to Queen versus Rook adjacency. Neither weight system is universally correct. Scientific use must specify the chosen neighborhood definition and report robustness where that choice matters.

<a id="s10"></a>
## 10. Temporal validation and Spatial Markov from 2014 to 2020

### 10.1. Temporal transform and directional vector

The module first computes

\[
v_{it} = \log(1+\max(\mathrm{NTL}_{it},0))
\]

and standardizes values **separately within each year**, across valid, non-edge cells:

\[
z_{it}=\frac{v_{it}-\bar v_{t}}{s_{v,t}}.
\]

It then calculates year-specific Queen neighbor means and movement components:

\[
\Delta z_i=z_{i,2020}-z_{i,2014},\qquad
\Delta Wz_i=(Wz)_{i,2020}-(Wz)_{i,2014},
\]

\[
m_i=\sqrt{(\Delta z_i)^2+(\Delta Wz_i)^2}.
\]

A directional regime is assigned only to eligible cells with **\(m_i\geq 0.05\)**. This number is a **descriptive movement threshold**, **not** a p-value or FDR significance threshold.

### 10.2. Regime definitions

| Stored CSV code (retained for compatibility) | Display interpretation | Sign rule |
|---|---|---|
| `1_Synergistic_Growth` | Synergistic Relative Growth | Δz ≥ 0, ΔWz ≥ 0 |
| `2_Agglomeration_Shadow` | Focal Relative Decline / Neighbor Relative Growth | Δz < 0, ΔWz ≥ 0 |
| `3_Emergent_Pioneer` | Focal Relative Growth / Neighbor Relative Decline | Δz ≥ 0, ΔWz < 0 |
| `4_Synchronized_Decline` | **Synchronized Relative Decline** | Δz < 0, ΔWz < 0 |
| `Excluded_or_Static` | Excluded or movement below threshold | Ineligible or m < 0.05 |

### 10.3. Observed outcomes

| Regime | Cells | Absolute radiance increased | Absolute radiance decreased |
|---|---:|---:|---:|
| Synergistic Relative Growth | **1,456** | 1,456 | 0 |
| Neighbor Relative Growth / Focal Relative Decline | **75** | 75 | 0 |
| Focal Relative Growth / Neighbor Relative Decline | **194** | 194 | 0 |
| **Synchronized Relative Decline** | **4,711** | **4,624** | **87** |
| Excluded / Static | **1,897** | 1,872 | 25 |
| **Total** | **8,333** | **8,221** | **112** |

**4,624 of 4,711 cells (approximately 98.15%)** in the stored `4_Synchronized_Decline` category experienced **positive absolute radiance growth**. There is no contradiction: their position in the **separately standardized within-year distribution** declined relative to their comparison population, as did that of their neighbors.

### 10.4. Threshold sensitivity

| Descriptive movement cutoff | Cells in synchronized relative decline |
|---|---:|
| 0.025 | **5,242** |
| 0.050 | **4,711** |
| 0.100 | **2,949** |
| 0.200 | **1,111** |

The classification is substantially sensitive to cutoff. It must not be described as independently statistically significant merely because a regime was assigned.

### 10.5. Spatial Markov

The module ranks cells into year-specific quartiles of `log1p(NTL)` and estimates transition matrices, including subsets conditioned on above- and below-median initial neighboring z-scores. Approximately **74.90%** of analyzed cells remained in their same radiance **quartile** from 2014 to 2020. This indicates persistence in relative spatial position, **not** unchanged absolute brightness.

### 10.6. Reproducibility and rounding

The Space-Time formulas, directional labels and Markov statistics were independently reconstructed from the exported CSV. One cell (`grid_id=3922`) sat very near the **0.05** threshold; recomputing from four-decimal-place NTL values could change its category. Using the application-exported movement information recovered all **8,333/8,333** regime labels. The discrepancy is attributable to export precision rather than evidence of a new algorithm defect.

### 10.7. Corrective interpretation

The initial interface term “Synchronized Decline” was ambiguous and could be misconstrued as economic or absolute light decline. **PR #11**, now merged, updates the bilingual UI wording and documents the relative nature of the method while preserving legacy machine-readable CSV identifiers and all numerical computations.

### 10.8. Remaining temporal questions

Independent raster benchmarks currently cover **two endpoint years (2014 and 2020)**, not a fully audited annual time series. Effects of interannual coverage, sensor calibration, background radiance and compositing policy across all years remain outside the completed tests.

<a id="s11"></a>
## 11. GHSL convergent validation

### 11.1. Reported pilot findings

The application's quality panel compared NTL with two GHSL measures at Yanqing in 2020.

| External reference | Spearman correlation | Spatial block-bootstrap 95% CI | AUC for top quartile |
|---|---:|---|---:|
| GHSL built-up surface | **0.629** | **~0.59–0.68** | **0.867** |
| GHSL population | **0.616** | **~0.58–0.66** | **0.851** |

Approximately **63%** of GHSL grid-level measurements in the displayed pilot were zero, depending on the layer and definition. The correlations are positive and informative as a preliminary convergent check.

### 11.2. Validation status

**PARTIAL.** Independent reconstruction of the exact GHSL source rasters, resampling/grid alignment, zero handling, Spearman, AUC and spatial block-bootstrap was **not** completed. The figures above are **application-reported**, not independently benchmarked in the same way as VIIRS extraction. GHSL built-up area and population are not substitutes for independent local GDP or economic activity.

### 11.3. Required benchmark

Use identical grid polygons, GHSL product versions, epoch, source projection and aggregation logic; report the number of zero cells; recompute rank correlations and AUC using explicit positive labels; reproduce block definitions, bootstrap draws and confidence-interval procedure. Assess spatial resolution mismatch and uncertainty.

<a id="s12"></a>
## 12. Regression tests and corrective changes

### 12.1. Source-level audit

The initial code audit found that the former conditional Local Moran routine sampled neighbors with replacement rather than from a distinct non-focal pool. It also identified a possible loss of finite NoData sentinel masks during raster conversion and the above GADM metadata naming issue.

**[Pull request #10](https://github.com/hoanfg/spatial-app/pull/10)** implemented the conditional without-replacement sampling, ESDA Local Moran scale convention, preservation of valid raster masks, metadata correction, documentation and regression coverage.

### 12.2. CI outcomes

After PR #10 was merged, two GitHub Actions test groups reported **32 passed** and **22 passed**, for **54 passed tests** in the associated CI runs. This establishes regression behavior for the covered code paths; it is not an Earth Engine execution benchmark.

**[Pull request #11](https://github.com/hoanfg/spatial-app/pull/11)** clarified Space-Time regime presentation, the `0.05` descriptive threshold, and retained CSV compatibility. Its GitHub Actions run completed successfully. The changes were display/documentation-only and did not modify numerical classifications.

### 12.3. Reproducibility caveats

Static fixtures alone cannot confirm performance on all source data, and agreement with a single implementation can propagate shared design assumptions. The independent raster-to-polygon comparisons at Yanqing supply a separate and stronger check of real data extraction. Both levels of evidence are retained.

<a id="s13"></a>
## 13. Validation status and outstanding programme

| ID | Topic | Current status | Principal outstanding requirement |
|---|---|---|---|
| V01 | Curated China GADM geometry/GIDs | PASS: audited China set | Extend scope when adding other countries |
| V02 | Automated tests / regression fixes | PASS: covered CI runs | Continuous verification on future commits |
| V03 | Independent LISA and BH-FDR | PASS: Yanqing 2020 | Additional geographies and Monte Carlo stability |
| V04 | VIIRS 2020 raster-to-polygon | PASS: all 8,333 cells | Geographic transferability |
| V05 | VIIRS 2014 raster-to-polygon | PASS: all 8,333 cells | Longer series and varying coverage |
| V06 | Aggregation and missingness | SENSITIVITY CHARACTERIZED | Cases containing genuine missing pixels |
| V07 | Raw/P99/log transformations | SENSITIVITY CHARACTERIZED | Interpretation across locations |
| V08 | Queen/Rook and cell size | SENSITIVITY CHARACTERIZED | Other morphologies, resolutions and weights |
| V09 | Two-period dynamics / Markov | PASS computation; interpretation FIXED | Broader temporal tests |
| V10 | GHSL comparison | PARTIAL | Independent GHSL benchmark |
| V11 | Cross-location validation | PENDING | At least 2–3 contrasting locations |
| V12 | Continuous multi-year stability | PARTIAL | Annual reference series and quality flags |
| V13 | External economic construct validity | PENDING | Comparable independently published economic indicators |
| V14 | Streamlit Cloud operational checks | PENDING | RAM, runtime, failure modes and export tests |

### 13.1. Recommended priority sequence

1. **Cross-location validation:** a bright urban core, an industrial/peri-urban area, and a low-light rural area. Document selection rationale and use available administrative subdivisions without overriding RAM safeguards.
2. **Independent GHSL pipeline:** align GHSL to the exact tested cells and independently reproduce the quality-panel diagnostics.
3. **Continuous multi-year series:** apply a stable geometry/grid while auditing missingness, anomalous changes and annual composites.
4. **Operational benchmark:** document peak memory, execution time, Earth Engine failures/retries, and output reproducibility on Streamlit Community Cloud.
5. **Economic construct validation:** compare radiance and hotspot measures against suitable independent economic indicators with explicit limitations and without causal claims.

A scientifically useful validation programme does not require all correlations to be high. It requires correct computation, transparent methodology, defined scope, meaningful uncertainty checks and clear disclosure where indicators respond to modeling choices.

<a id="s14"></a>
## 14. Evidence register and custody

### 14.1. Primary results

| Work package | Original Markdown report | Additional evidence names |
|---|---|---|
| Repository audit | `verification-report.md`; `Báo cáo kiểm chứng NTL spatial econometrics.md` | `spatial-app-audit-evidence.zip` |
| Local Moran/FDR | `yanqing_validation_report.md` | `yanqing_validation_evidence.zip`; `yanqing_lisa_independent_cell_comparison.csv` |
| VIIRS 2020 preliminary | `yanqing_viirs_validation_report.md` | `yanqing_viirs_validation_evidence.zip`; `yanqing_viirs_reference_interior_comparison.csv` |
| VIIRS 2020 final | `yanqing_viirs_all_cells_validation_report.md` | `yanqing_viirs_all_cells_validation_evidence.zip`; `yanqing_viirs_all_8333_polygon_comparison.csv` |
| VIIRS 2014 | `yanqing_2014_temporal_raster_validation_report.md` | `yanqing_2014_temporal_raster_validation_evidence.zip`; `yanqing_2014_viirs_cell_validation.csv` |
| Measurement sensitivity | `yanqing_2020_measurement_sensitivity_report.md` | `yanqing_2020_measurement_sensitivity_evidence.zip`; `yanqing_2020_measurement_sensitivity_cells.csv` |
| Transformation sensitivity | `yanqing_2020_transformation_sensitivity_report.md` | `yanqing_2020_transformation_sensitivity_evidence.zip`; `yanqing_2020_transformation_sensitivity_cells.csv` |
| Spatial robustness | `yanqing_spatial_robustness_validation_report.md` | `yanqing_spatial_robustness_evidence.zip`; `yanqing_spatial_robustness_500m_cells.csv`; `yanqing_spatial_robustness_1000m_cells.csv` |
| Temporal validation | `yanqing_temporal_validation_report.md` | `yanqing_temporal_validation_evidence.zip`; `yanqing_temporal_validation_by_cell.csv`; `yanqing_temporal_regime_summary.csv`; `yanqing_temporal_markov_counts.csv` |

### 14.2. What is and is not stored

The present specification records method details and reported numeric results, while the binary evidence bundles remain outside this documentation PR. Those filenames identify work products of the validation campaign **but are not hyperlinks to repository-hosted copies**. There is no claim that all comparisons can be executed from the Git repository without additional input data. For formal peer review, preserve source GeoTIFF/CSV, script versions, environment information and immutable file hashes in a stable evidence deposit.

### 14.3. Historical interim results

A preliminary 2020 raster check initially covered whole cells and only approximated border polygons. It was **superseded** by the full-precision GADM reconstruction covering **8,333/8,333** cells. Both stages may be retained in external evidence archives, but the latter is the current authoritative 2020 verdict. Likewise, a different permutation seed gives expected stochastic differences; it does not contradict identical-seed reproducibility.

<a id="s15"></a>
## 15. Updating this specification

### 15.1. Requirements for a new validation entry

Every new campaign must record:

1. Date, repository commit/PR, validation identifier and scientific question.
2. Administrative location/GID, years, source product, imagery bands, spatial scale and CRS.
3. Data masks, zero/negative treatment, original and alternative specifications.
4. Grid construction, edge rules, neighbor weights, seeds, number of permutations, p-value/FDR conventions.
5. Numerical acceptance criteria, per-cell/sample counts, errors, overlap, exceptions and uncertainties.
6. Reproducible method/script locator, input manifest and immutable hashes when available.
7. Result status with **scope-limited** conclusion, limitations and further actions.

Update the status table in Section 13, add the detailed findings to the relevant section (or create a numbered section) and append an entry to the change log. Do not silently delete contradictory or superseded findings; explain the replacement.

### 15.2. Entry template

```markdown
### YYYY-MM-DD - Vxx: Study name
- Repository commit / pull request:
- Study area (GID), years, satellite products:
- Source rasters, masks, grids, projection:
- Baseline / sensitivity configurations:
- Reproduction script, input hashes, evidence location:
- Seed, permutations, significance method:
- Acceptance criterion:
- Detailed results and exceptions:
- Interpretation and unresolved limitations:
- Status change and next action:
```

### 15.3. Revision log

| Date | Change | Reference |
|---|---|---|
| 2026-11-11 | China boundary audit, Local Moran/NoData implementation corrections | [PR #10](https://github.com/hoanfg/spatial-app/pull/10) |
| 2026-11-11 | Yanqing VIIRS 2014/2020 and spatial, statistical and temporal benchmarks | Study evidence register above |
| 2026-11-11 | Clarified relative Space-Time regimes and descriptive cutoff | [PR #11](https://github.com/hoanfg/spatial-app/pull/11) |
| 2026-11-11 | Established a single validation register | [PR #12](https://github.com/hoanfg/spatial-app/pull/12) |
| 2026-11-11 | Expanded the register into a full technical compilation | [PR #13](https://github.com/hoanfg/spatial-app/pull/13) |
| 2026-11-11 | Separated complete English and Vietnamese validation specifications | Current documentation revision |

---

**Overall conclusion:** VIIRS extraction, Local Moran inference and the two-year directional calculations are supported by strong independent evidence for the specified Yanqing pilot. Important sensitivity to transformation, spatial weights and temporal threshold is documented. General validity across cities, independently extracted GHSL variables, continuous multi-year data, economic proxies and production Cloud runtime **remains unverified**.

[Return to top](#top)
