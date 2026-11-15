# Spatial App — complete audit Markdown evidence (verbatim)

> This file concatenates complete original Markdown byte sequences. **Nothing is shortened, paraphrased, or filtered.**
> Every report is also retained in its original file or original ZIP. The `MARKDOWN_BYTE_RANGES.json` provides exact UTF-8 byte offsets, lengths, and SHA-256 for each original section.
> The consolidated file may include historical versions and duplicate reports: these are intentionally preserved.

**Original Markdown sections:** 78. **Audit date:** 2026-11-15.



---

## Source 001: `05_NOTES_REPORTS_AND_HISTORY/A02_DQ_UNKNOWN_FIELD_FINDING_2026-11-15.md`

**Original bytes:** 4,362 · **SHA-256:** `b4484af154e06a57d044c7e9ea69bfda29867de2968c625eb9eb04b0e022777b` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 001 -->
# A02 — real CSV `dq_status=unknown` field defect / root-cause investigation

Date: 15 November 2026. Repository: `hoanfg/spatial-app`. **Carry forward to the ONE consolidated Major Review PR; not a new PR.**

## Reproducible observed symptom

All 17,177 newly exported 2020 cell records across Shanghai (886), Bao'an (7,148) and Qimen (9,143) have `dq_status=unknown`. The five per-cell columns (`dq_observed_fraction`, `dq_negative_fraction`, `dq_zero_fraction`, `dq_mean_valid_months`, `dq_low_month_fraction`) are all empty. Separately, `dq_stat_missing=False`, and independent VIIRS pixel-overlap checks validate the main radiance values. No evidence suggests a forgotten UI action caused these particular empty columns.

## Exact code path / confirmed failure mode

1. `app.py:fetch_ntl_raster()` creates `annual_image_with_quality(col.map(_mask_cloud_free), roi)`, and downloads the GeoTIFF with `getDownloadUrl`. The ZIP branch selects its first `.tif` if a ZIP is returned.
2. `app.py:run_pipeline()` calls `cell_quality(tif_bytes, grid_wgs)` automatically as part of the core computation; that result is joined into `grid_utm`.
3. `ntl/semantics.py:cell_quality()` accepts the quality bands **only if** `src.count == 6` AND `tuple(src.descriptions[1:]) == QUALITY_BANDS` in exact order. When the condition is false, every `dq_*` numerical field becomes `NaN`, followed by `dq_status=unknown`, without a visible schema-error message.
4. `app.py:export_df` joins all `grid_utm` `dq_` columns; `ntl/lisa_ui.py` incorporates `export_df` into the downloadable `*_lisa_cells.csv`. The extra buttons in `ntl/quality_ui.py` (observation count, negative clipping sensitivity, GHSL validation) are optional **additional region-level diagnostics**. They do not populate these automatically generated per-cell fields.
5. `tests/test_data_semantics.py` writes a synthetic six-band GeoTIFF and explicitly assigns the expected band descriptions (`dst.set_band_description(i,name)`), so the test does NOT establish that live Earth Engine GeoTIFF delivery satisfies the description schema.

## Competing explanations to distinguish with one live capture

- The application may receive a six-band TIFF whose `src.descriptions[1:]` are absent or normalized differently.
- The application may receive fewer than six bands (e.g., download format / unexpected ZIP grouping) or an alternative schema.
- Stale deployed app version or an obsolete cached raster may also produce `unknown`; do not declare this hypothesis false without checking deployment commit and the `fetch_ntl_raster` cache/version.

**Current evidential status:** the deterministic code branch that generates `unknown` has been established, and all three field CSVs exhibit its output. The exact **live six-band `src.count` and `src.descriptions` remain unobserved** because the application-requested TIFF bytes were not captured. Therefore it is *not yet scientifically defensible* to state that Earth Engine definitely stripped the descriptions.

## Targeted corrective patch (one PR only, after confirming live raster schema)

1. Add a safe diagnostic at the network-to-raster interface: band count, descriptions, any ZIP members, and cache/deployment provenance (no credentials or raw raster upload required). Do not silently downgrade unrecognized schema to fully unknown without explaining the reason to the user.
2. Confirm band 1 exactly matches the pre-A02 legacy NTL contract at equal spatial settings.
3. Map valid six-band values to the known ordered semantic schema only if the producer provenance is established; refuse arbitrary six-band products instead of trusting band count alone. Explicitly distinguish absent label metadata from genuinely missing observation pixels.
4. Add one focused regression covering the **actual field condition** (e.g. nameless six-band geotiff) rather than increasing redundant synthetic test count, and confirm that known missing / zero / negative cases preserve intended semantics.
5. Perform field validation on an Earth Engine raster containing **genuine zero-support observations within the analysis polygon** before declaring A02 scientifically PASS.

**Decision:** retain the bug finding and scoped patch proposal in private staging for the user's single consolidated PR; do not open an isolated PR, alter NTL zero-fill policy, or claim A02 is fixed.

<!-- END ORIGINAL SOURCE 001 -->


---

## Source 002: `05_NOTES_REPORTS_AND_HISTORY/BAOAN_A02_PERFORMANCE_POST_MERGE_AUDIT_2026-11-15.md`

**Original bytes:** 4,019 · **SHA-256:** `dd96ca1716064c6a4d558d707ae555e824571a75181de2369ca06863df4056f1` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 002 -->
# Bao'an A02 & runtime post-merge audit — 2026-11-15

## Scope and provenance
- Area: Shenzhen Bao'an, 2020, 500 m; 7,148 grid cells, grid IDs 0–7147.
- Inputs: an app-exported cell-level CSV and `spatial_app_performance.json`, both user-provided on 2026-11-15.
- Baseline: pre-A02-fix Bao'an app CSV, 2020/500 m, preserved privately from V11 validation.
- CSV SHA-256: `40b76f2f0f1fec0834be16f88e4b97084986886f5edc84d8718e28bf263eaece`.
- Profiler JSON SHA-256: `04e634f07ff2816641f1fba3faa948485adeec5a4fdb3901474c0422b3dba2cf`.
- Do not upload the underlying user CSV or Cloud process log to GitHub.

## A02 field results
- Cell IDs: unique, identical ordering to baseline, 7,148/7,148.
- `dq_status`: `observed` in 7,148/7,148, `unknown` in 0.
- All five per-cell quality metrics have 7,148/7,148 non-missing values:
  `dq_observed_fraction`, `dq_negative_fraction`, `dq_zero_fraction`,
  `dq_mean_valid_months`, `dq_low_month_fraction`.
- Pre-fix baseline: all five metrics missing in 7,148 rows; `dq_status=unknown` in all rows.
- Observed fraction: all rows 1.0. Negative/zero/low-month fractions: all rows 0.0.
- Mean valid months: minimum 10.000000, mean
  11.988060, maximum 12.000000;
  observed fraction 1 does **not** imply all 12 months were valid.
- `dq_stat_missing`: false for every grid cell.
- Crucial regression: **all 24 non-DQ CSV columns exactly match the
  pre-fix baseline** (numeric tolerance absolute 1e-10, no relative tolerance).
  `ntl_mean`, `ntl_sol`, spatial IDs/geometry-derived fields, scores, ranks,
  quantiles and groups unchanged.

Conclusion: **A02 field PASS at Bao'an 2020/500 m**. Does not prove the
same schema behavior across all locales or historical VIIRS years.

## Profiler results
- `pipeline_success = true`; all 13 profiled stages have `status=ok`,
  no recorded error type.
- Main analysis pipeline wall time: **46.6687 s**.
- Sum of the 6 instrumented initial stages: 46.0708 s, with
  0.5979 s not attributed to those stages.
- A02 cell quality: **25.0028 s**, or
  **53.6%** of primary pipeline.
  Current implementation calls per-band zonal extraction repeatedly;
  batching exactextract on aligned bands is a candidate optimization,
  subject to exact numeric regression tests.
- Grid build: 9.7399 s; NTL zonal mean: 9.6193 s;
  NTL EE download: 1.4220 s; boundary load: 0.1477 s;
  Global Moran: 0.1391 s.
- Subsequent optional LISA: 3.6794 s;
  GHSL built fetch + zonal + agreement: 7.8895 s;
  GHSL population fetch + zonal + agreement: 8.0610 s.
- Sum of all stage durations including these later optional user actions:
  65.7007 s.
  `time_since_recorder_created_s=369.7477`
  is **elapsed wall-clock since recorder creation** and includes user activity
  or idle intervals; it is **not** computation time.
- Peak sampled process RSS: **728.531 MiB**,
  observed during `ntl.zonal_mean` (grid build peaked at 711.379 MiB).
  Baseline process RSS at first recorded stage: 591.270 MiB.
- Process-wide RSS, sampled every 0.1 second; may miss
  brief peaks and cannot be compared to an unknown Streamlit Cloud memory limit.
  One successful run cannot prove capacity under concurrency or other localities.

Conclusion: **profiler functional PASS**, **observed single-run pipeline success**.
Performance optimization candidate A02 (25 s) is open, but not a correctness bug.
No OOM/timeout event appears in this profiler trace, which does not prove such
events are impossible.

## Audit disposition
- A02 quality metadata at Bao'an 2020/500 m: **PASS (field)**.
- NTL regression vs baseline: **PASS (all 24 non-DQ columns unchanged)**.
- Profiling function: **PASS (instrumentation works)**.
- Single-run Cloud runtime: **observed success**; not a load/stress benchmark.
- GHSL built/pop profiler stages: **both OK**. Correlation and external
  scientific validity are independent of profiler status; refer to prior
  Shanghai field validation and user-observed Bao'an/Qimen charts.

No production modification is proposed on the basis of these two inputs.

<!-- END ORIGINAL SOURCE 002 -->


---

## Source 003: `05_NOTES_REPORTS_AND_HISTORY/GHSL_A02_REAL_FIELD_FINDINGS_2026-11-15.md`

**Original bytes:** 7,041 · **SHA-256:** `484478ad27db5b48bbce380fc8496649739326affc26d1dddf1a7f9939452562` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 003 -->
# Spatial App — field evidence: GHSL native vs app-style raster and A02 six-band intake

Date: 2026-11-15 (Asia/Ho_Chi_Minh). This document preserves **real exported data** from the user's connected Google Drive. No GitHub PR, production edit or renewed Yanqing/V11 test is included.

## Sources, spatial target and scope

GHSL 2020 JRC P2023A: `JRC/GHSL/P2023A/GHS_BUILT_S/2020` (`built_surface`, m² of built-up area per 100 m original grid cell), and `JRC/GHSL/P2023A/GHS_POP/2020` (`population_count`, persons per original grid cell). Native projection in the retrieved GeoTIFFs: `ESRI:54009` (World Mollweide), pixel spacing 100×100 projected meters. Application export: `EPSG:4326` at an Earth Engine scale of 100 nominal meters, actually ~8,515–8,530 geodesic m² per cell in this area. Google data catalogue: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S and https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP.

The five distinct raster types are present in Drive folder `1VJGX8ElFo2xavlRrD7Wcox__UwsjTOrs`; an A02 six-band copy is also in separate folder `1oEHzRYEVKNnrJv5M7PU4H8q2CrniK6fI`. The first folder's updated file listing, not a stale folder preview, supplied the two native GHSL outputs. Original source assets remain on Google Drive; not bundled in the repository.

The geographic export rectangle for GHSL is `[121.35299, 31.16607, 121.57693, 31.33889]`. To reduce nonuniform edge rasterization, a common interior rectangle `[121.35899, 31.17207, 121.57093, 31.33289]` (0.006° inset on all four sides) is used for the primary comparison. Both native/app pixels are selected by centre position, independently transformed to geographic coordinates. This is a bounded-field comparison, **not** an administrative census estimate or official total for Shanghai.

## GHSL measured impact — identical geographic core

| Quantity | Native GHSL grid total | App-style EPSG:4326 grid total | App-style overcount | Identical nearest-sampled pixel values |
|---|---:|---:|---:|---:|
| Built-up surface | 118,319,940.000 | 137,859,621.000 | +16.51428% | 42,244/42,244 |
| Residential population | 11,674,618.205 | 13,612,238.308 | +16.59686% | 42,244/42,244 |

Native core has **36,234** pixels; app-style core has **42,244** pixels. Independently warping the native raster to the destination grid with nearest-neighbour resampling reproduced **all 42,244/42,244 sampled destination pixel values exactly** for each of the two products. Therefore the error is not that a source pixel's stored value is changed: **a per-native-pixel quantity is repeated across a denser EPSG:4326 lattice, then summed as if each destination pixel were a separate 100×100 m source quantity**. This is a **confirmed quantity-conservation defect in the application GHSL validation/aggregation path** if totals are used without area conversion or native-grid integration.

Comparison over the full finite exported footprint (more sensitive to raster-edge footprint treatment): built-up surface **+17.08992%** (native 132,558,787 m²; app 155,212,982 m²), population **+17.02134%** (native 12,602,775.004 persons; app 14,747,936.687 persons). Independent repeated core insets give: built {'.003': 17.12041, '.006': 16.51428, '.010': 16.94212, '.015': 17.32608}; population {'.003': 17.1483, '.006': 16.59686, '.010': 16.9983, '.015': 17.31684}. This variation is expected from grid boundaries and source pixelization, not uncertainty about the fundamental failure mechanism.

The app-style cells cover **8514.7–8530.0 m²** physically, whereas source pixels represent quantities per 10,000 m² Mollweide cells. At least **62 of 48,500** app-style `built_surface` pixels exceed the physical area of the destination pixel, independently indicating that an intensive/area-preserving reinterpretation is required before physical interpretation.

**Production trace:** `ntl/ee_extra.py::fetch_ghsl_raster()` calls `getDownloadURL` with `scale=100, crs='EPSG:4326'`, then `ntl/quality_ui.py` calls `zonal_stat(raw, grid_wgs, 'sum', clip_negative=True, fill_missing=0.0)` with no compensation for changed destination cell size. `ntl/zonal.py` performs a pixel-footprint fraction-weighted `sum` on whatever grid is supplied. An appropriate production correction would download or otherwise aggregate in the source's native equal-area 100m lattice, transforming polygons into its CRS for coverage-weighted sums. **Do not** blindly scale EPSG:4326 pixel values by a single latitude factor: that is an approximate diagnostic, not a robust spatial integration method. Preserve the existing NTL and LISA estimators.

## A02 six-band export — verified, but no low/missing-support test case

The actual `baoan_2020_a02_six_band_reference.tif` has six `float32` bands with exact descriptions:

`avg_rad, dq_observed_fraction, dq_negative_fraction, dq_zero_fraction, dq_mean_valid_months, dq_low_month_fraction`.

Shape: 119×227 cells; CRS EPSG:4326. All 27,013 cells have observed fraction = 1, zero negative/zero median flags and zero low-month flags. Observed-month counts: {9.0: 1, 10.0: 26, 11.0: 802, 12.0: 26184}. Comparison with the previously independent 2020 Bao'an median export showed **26,786/26,786 exactly matching band-one values in their shared finite footprint**. The other 227 rows/pixels are outside the earlier export footprint, not proof of an observation gap inside the district.

These new data prove that Earth Engine `Export.image.toDrive` can preserve all six descriptions and that band one agrees with the independent NTL annual-median raster. However, **no pixels here have fewer than 9 months**, so this is not a real-field test of `no_observation` or `low_month_fraction`. Furthermore **the Streamlit app uses `getDownloadURL`, not Drive export**, and all 17,177 previous app CSV rows still showed `dq_status=unknown`. The specific live Cloud download band count/names remain unobserved, so A02's Cloud failure mechanism remains unresolved. Staged schema warnings and tests are not yet applied to production.

## Reproducibility and release gate

- The standalone comparator is `ghsl_field_compare_2020.py`; JSON with all stats and SHA-256: `GHSL_A02_SHANGHAI_BAOAN_FIELD_METRICS_2026-11-15.json`. Input file names are in that JSON.
- Native vs app two samples are on different pixel lattices; compare within the common geographic core before interpreting full-extent pixel sums.
- The field evidence **confirms GHSL overcount** in Shanghai 2020. It does not quantify the bias in other places/epochs or the impact on rank-based Spearman/AUC metrics. This is not a claim that the app's reported global NTL/LISA results are invalid.
- For the consolidated PR: correct native GHSL integration, add real-field conservation regression and fail-closed A02 schema diagnostics. Require one authenticated Cloud run with published raster schema and practical performance metrics before closure. **No extra copies of user rasters or proprietary data in GitHub.**

<!-- END ORIGINAL SOURCE 003 -->


---

## Source 004: `05_NOTES_REPORTS_AND_HISTORY/SHANGHAI_GHSL_POST_DEPLOY_EVIDENCE_2026-11-15.md`

**Original bytes:** 4,754 · **SHA-256:** `e46979acb604d88486d008e973c005eb5f89059f765e5b8cfeadfedee21b5cec` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 004 -->
# Shanghai GHSL 2020 — independent post-deployment validation

Date: 2026-11-15. Scope: Shanghai Core (`CHN.24.1.10_1`), year 2020, 500 m grid, GHSL built-surface and population. Evidence relates to the post-merge #26 application figures shown by the user; it does **not** re-run V11 or Yanqing.

## Direct observations from the deployed UI

- GHSL built surface: Spearman rho **-0.079**, 95% block-bootstrap CI **[-0.22, 0.09]**, top-quartile AUC **0.395**; scatter plot displayed.
- GHSL population: Spearman rho **0.136**, 95% block-bootstrap CI **[-0.03, 0.27]**, top-quartile AUC **0.576**; scatter plot displayed.
- The old 100%-zero proxy and `NaN` results no longer appear in this deployment output.

## Independent reference calculation

Inputs: original Earth Engine native-Mollweide 100 m GHSL TIFFs previously exported to Drive; the application's Shanghai 500 m grid GeoJSON and NTL CSV previously provided by the user (886 cells). No `ntl` app imports, no `exactextract` implementation dependency.

Algorithm:
1. Load GeoJSON and CSV, sort by `grid_id`, verify corresponding NTL values.
2. Project actual cell polygons from EPSG:4326 to the raster's ESRI:54009 using GeoPandas/PROJ. **Keep the GHSL raster on its original 100 m source grid.**
3. For each grid polygon, compute Shapely polygon overlap with each candidate GHSL pixel: `sum(pixel_amount * intersection_area / 10_000 m²)`.
4. Retain original 500 m cell area in km²; derive proxy density = GHSL sum / area.
5. Apply the same core-cell eligibility rule, `area_km2 >= 0.99 * (500 / 1000)^2`, giving **715 / 886** eligible cells.
6. Calculate Spearman ranks with average ties, Mann–Whitney top-quartile AUC, and 200 block-bootstrap Spearman draws with 5 x 5 cells, seed 42 and EPSG:32651 grid-centroid coordinates. 

## Independent results

| Metric | Built surface | Population |
|---|---:|---:|
| Eligible core cells | 715 | 715 |
| Core cells with positive GHSL proxy | 715 | 715 |
| GHSL core zero share | 0% | 0% |
| Spearman rho | -0.0794533 | 0.1358105 |
| Block-bootstrap 95% CI | [-0.220123, 0.086086] | [-0.029628, 0.271008] |
| Top-quartile AUC | 0.394636 | 0.576274 |
| Core median GHSL density | 353,036 m²/km² | 33,799 people/km² |
| Core median NTL | 41.2612 | 41.2612 |

All three key metrics (rho, CI endpoints, AUC) agree with both deployed UI screenshots to their displayed rounding precision. Thus the deployed application's metrics have been independently reproduced from the archived native-resolution GHSL field data. This is strong evidence that the previously broken raster/vector CRS alignment is now functioning correctly in Shanghai.

## Scientific interpretation and limitations

The Shanghai inner core has very weak monotonic association between VIIRS nighttime radiance and GHSL built surface (weak slightly negative rho) or GHSL population (weak slightly positive rho). Both displayed 95% Spearman confidence intervals contain zero; the observed evidence does not establish a reliably nonzero monotonic association. The AUC comparisons are descriptive, not separately tested here. GHSL counts and built surface are **not** direct nighttime light ground truth, and a dense urban core can have limited spatial differentiation in radiance, different daytime activity, commercial intensity or housing intensity. Avoid claiming that this disproves VIIRS or that the GHSL data are bad.

The independent calculation **does not** compare every post-deployment application's GHSL per-cell result one-to-one, since per-cell GHSL arrays were not exported from the live app. Metrics matching at screenshot precision do not prove pixel-for-pixel identity. It does independently reproduce the aggregate validation pipeline. The saved TIFFs were exported via Earth Engine `Export.image.toDrive`, while the deployed app now uses `ee.data.computePixels` to fetch a native grid: a matching statistical result offers corroboration but not an exhaustive byte-level equivalence proof.

No actual live Cloud RSS/runtime JSON and no post-merge A02 per-cell CSV have been assessed in this task. Separate post-deployment A02 and runtime acceptance gates remain open. Cross-location GHSL evaluation should be tested on regions with different urban/rural composition without altering the statistical estimators based solely on Shanghai's low rho.

## Included evidence

- `SHANGHAI_GHSL_INDEPENDENT_CELL_VALIDATION_2026-11-15.json`: exact summary metrics.
- `shanghai_ghsl_independent_validation_2026_11.py`: independent source-grid overlap and matching statistics, no Spatial App imports.
- `SHANGHAI_GHSL_POST_DEPLOY_EVIDENCE_2026-11-15.md`: this report.
- Source raster/CSV/GeoJSON are **not** redistributed in this ZIP; they remain user-supplied separate inputs.

<!-- END ORIGINAL SOURCE 004 -->


---

## Source 005: `05_NOTES_REPORTS_AND_HISTORY/V11_2020_REFERENCE_RASTER_INTAKE_2026-11-14.md`

**Original bytes:** 3,993 · **SHA-256:** `e894614571169faf4ece973def016b0a4994ca0809a57b62f05bdc2dee429015` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 005 -->
# V11 — Independent reference GeoTIFF intake and consistency check

**Date:** 2026-11-14.  **Input:** Nine GeoTIFF exports discovered in two separate Google Drive folders, downloaded read-only.

**Scope:** Binary readability, source metadata, CRS/transform/pixel alignment, recorded SHA-256, and inter-product raster consistency. This is *not* independent zonal LISA/app CSV validation. No prior Yanqing test was rerun.

| Region | Raster shape | Valid reference pixels | Zero-month / invalid pixels | Monthly support counts | Georeference | Consistency |
|---|---:|---:|---:|---|---|---|
| Shanghai urban core | 49 × 62 | 3,038 | 0 | 12: 3,038 | aligned | consistent |
| Shenzhen Bao'an | 119 × 227 | 26,786 | 227 | 0: 227, 9: 1, 10: 26, 11: 780, 12: 25,979 | aligned | consistent |
| Anhui Qimen | 137 × 192 | 26,304 | 0 | 10: 127, 11: 17,136, 12: 9,041 | aligned | consistent |

## Critical interpretation

- Bao'an has 227 pixels in the raster bounding rectangle with 0 valid months, and these are **exactly** pixels whose annual radiance and masked median are NaN (the full southernmost raster row). This is consistent with a raster-export edge/footprint effect, **not proof of real no-observation inside the Bao'an GADM polygon**. Verify polygon intersection before asserting any missingness inside the district.
- Qimen has valid pixels with 10, 11, and 12 monthly composites; Bao'an has pixels with 9–12. This is genuine raster variation in per-pixel monthly-composite support across the bounding rectangle; monthly `cf_cvg>0` does not count cloud-free nights.
- All three exports use EPSG:4326; each group has the same pixel geometry, and the finite annual median values match the masked reference exactly.
- The nine raster files do **not** establish app CSV agreement, LISA, six-band A02 semantics, or a GHSL field benchmark. V11 remains **PARTIAL/PENDING** until app CSV and polygon-specific cross-check are available.

## File provenance (downloaded bytes)

| Region | Product | Bytes | SHA-256 |
|---|---|---:|---|
| shanghai_core | shanghai_core_viirs_2020_reference.tif | 11,031 | `74c825a461d73bf5c60eedb0c556ae704ed8e023307c07d320c48902ad755948` |
| shanghai_core | shanghai_core_valid_months_2020.tif | 1,273 | `8e0a207e5cd237c8ceaddb97c6b1c2a58764c207568a65fbc8c3dcca1e1cf7d3` |
| shanghai_core | shanghai_core_viirs_2020_masked_median.tif | 11,051 | `5572851b5ef9d97206539e212cdb7a3e4d7ace517dc78c1187934be6db9a455b` |
| shenzhen_baoan | shenzhen_baoan_viirs_2020_reference.tif | 78,976 | `04117f799a684d3fc5c6e7d9d3fc498cc1938e57fb3ff50b15699a7059a8f705` |
| shenzhen_baoan | shenzhen_baoan_valid_months_2020.tif | 1,960 | `4a720b105a0afda20d07710d1814cec863701eb349fbf012e586031dea70d999` |
| shenzhen_baoan | shenzhen_baoan_viirs_2020_masked_median.tif | 78,996 | `87d9f47830ab48ef12fba7957be4f2117c8752c7936f7eac410aa1751c201e8d` |
| anhui_qimen | anhui_qimen_viirs_2020_reference.tif | 33,350 | `dfac4c7e663cf42261458b8c1ffe88daea7ddae63e0ed7e46230fc75552070cb` |
| anhui_qimen | anhui_qimen_valid_months_2020.tif | 3,415 | `f89f9a446b04396ff9e10aa597b8f54ecbee5ed6d5593d0214c018d16d36e14a` |
| anhui_qimen | anhui_qimen_viirs_2020_masked_median.tif | 33,370 | `c8b34d2a3f174e4cf0efcb43123dc2089285389a16ce456fbe52f38e7ee41e85` |

Source Drive folders:

- https://drive.google.com/drive/folders/1ftAUuIXRoAD25_JsX-REbQ9CLQcp2c1w (8 files)
- https://drive.google.com/drive/folders/1WKfOszMt7nUJxEXfqmNCQ9MrXp-v1FAo (1 file)

## Next evidence needed

- Obtain and align 2020 / 500m app CSV exports for Shanghai core, Shenzhen Bao'an and Anhui Qimen, including `grid_id`, `area_km2`, `ntl_mean`, and full LISA columns.
- Independently intersect the existing GADM district boundaries and reference rasters to distinguish inside-polygon missingness from bounding-rectangle padding.
- Apply pre-specified 500m raster-cell comparison and then independent local-Moran/FDR comparison. Only those operations can move V11 from reference-intake to field-validated status.

<!-- END ORIGINAL SOURCE 005 -->


---

## Source 006: `05_NOTES_REPORTS_AND_HISTORY/V11_CROSS_LOCATION_FIELD_VALIDATION_2026-11-15.md`

**Original bytes:** 6,952 · **SHA-256:** `465635eda5d2061ba1f63d86b5113419d0b3d324f24c46632d04f2ba2b89117f` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 006 -->
# V11 cross-location field validation: Shanghai, Bao'an, Qimen

Date: 15 November 2026
**Status: PARTIAL FIELD VERIFIED.** This is new evidence for the three V11 target locations, not a rerun of Yanqing.

## Scope and provenance

- Inputs: 6 CSVs exported from spatial-app (one NTL and one LISA CSV for each locality), 9 original 2020 VIIRS GeoTIFFs exported independently by the user from Google Earth Engine and retrieved from two Google Drive folders.
- Original boundaries: GADM v4.1 districts represented in the repository `hoanfg/spatial-app`; this run **did not** materialize the three boundary GeoJSON files into the analysis runtime. Consequently the exact geometry of cut/edge cells could not be reconstructed independently here.
- Validation program is separate from the production `ntl.zonal` and `ntl.lisa_core` imports. Input SHA-256 fingerprints are recorded in `V11_CROSS_LOCATION_INPUT_MANIFEST_2026-11-15.json`.
- VIIRS reference dataset: `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG`, year 2020; reference median with `cf_cvg > 0`, exported EPSG:4326 at scale 463.83 m. App CSV: year 2020, UTM 500 m cells, raw NTL.

## Independent numeric results

### NTL raster-to-cell comparison

For every **unclipped 500 m square**, the benchmark rebuilds the square in UTM from its gridded CSV centroid, transforms its polygon to EPSG:4326, intersects it with the independent reference raster pixel polygons, and recomputes an area-weighted radiance mean (clipping valid negative radiance at zero). This is not a copy of production `ntl_mean`.

| Location | App cells | Full-square cells independently compared | Pass at ±0.00005 | MAE | Max absolute error |
|---|---:|---:|---:|---:|---:|
| Shanghai | 886 | 706 | 706/706 | 0.000025472 | 0.000049957 |
| Bao'an | 7,148 | 6,131 | 6,131/6,131 | 0.000025034 | 0.000049998 |
| Qimen | 9,143 | 8,493 | 8,493/8,493 | 0.000024630 | 0.000049994 |

**Aggregate:** 15,330/15,330 full-square cells match to the four-decimal CSV rounding bound. **Not tested here:** 1,847 cut/partial polygon cells; these require the exact GADM boundary polygons. Do not report all 17,177 cells as independently raster-validated.

### LISA deterministic checks

The independent checker creates Queen adjacency with a dictionary of 500 m UTM grid indices, excludes cells below 99% of 0.25 km², recomputes z-scores from the rounded CSV NTL values, calculates local Moran observed I and spatial lag, checks raw quadrants, and applies a separately coded Benjamini–Hochberg step-up procedure to every exported p-value.

| Location | Local I checked | Queen neighbor differences | BH-FDR significant | FDR flag differences | I max abs difference | Raw quadrant differences |
|---|---:|---:|---:|---:|---:|---:|
| Shanghai | 715 | 0 | 159 | 0 | 0.0000519 | 0 |
| Bao'an | 6,185 | 0 | 2,848 | 0 | 0.0000573 | 0 |
| Qimen | 8,532 | 0 | 869 | 0 | 0.0030472 | 1 |

- All three NTL CSVs and respective LISA CSVs are identical across their common first 32 columns and match one-to-one on `grid_id`.
- All exported BH-FDR significant flags agree with the independently recomputed step-up threshold. **This is a consistency check of exported p-values; it does not itself validate Monte Carlo p-generation.**
- **One raw quadrant disagreement:** Qimen `grid_id=2070`, where NTL rounds to `0.2944` and the recomputed z-score is approximately `-0.0000828` (near zero). The export reports `High-High`, while recomputing with rounded CSV yields `Low-High`. Its `lisa_p_sim=0.182`, its final class is `Not Significant`, and **no final significance or HH/LL label is affected**. The difference is consistent with sensitivity to input rounding, not independently proof of a production error.

### Conditional Monte Carlo replication on genuinely new geographical cases

An independent NumPy RNG with 999 conditional draws per focal cell and distinct sampled nonfocal neighbors was run on a stratified sample of exported p-values in each region. Seeds intentionally differ from the app. A doubled smaller-tail inclusive p-value was compared with `lisa_p_sim` (the denominator of local I cancels in tail comparison).

| Location | Independently resimulated cells | Pearson correlation with exported p | MAE of p | Disagreement for raw p < 0.05 |
|---|---:|---:|---:|---:|
| Shanghai | 387 | 0.99624 | 0.0141 | 7 |
| Bao'an | 400 | 0.99599 | 0.0146 | 12 |
| Qimen | 400 | 0.99557 | 0.0145 | 10 |

- Total: **1,187** resimulated cells. The sample was intentionally stratified by reported p-value ranges and is not a probability sample of all cells.
- Small p-value and raw threshold differences are expected under distinct Monte Carlo draws; these are not exact fixed-seed equality tests. The BH-FDR comparisons in the previous table were performed separately on all stored p-values.

### A02 observational quality is not verified in the live exports

- **All 17,177 cells** have `dq_status=unknown`; none has finite `dq_observed_fraction`, `dq_mean_valid_months`, or the other per-cell observational quality indicators.
- This is observed in the actual spatial-app CSV exports, not inferred from synthetic tests. It demonstrates that the A02 observational metadata contract is **not usable in these six outputs**, although the primary band NTL values match.
- The cause cannot be established from the CSV alone; candidate explanations include the downloaded GeoTIFF missing expected band names or an unexpected single-band TIFF. Inspect an actual live app-downloaded TIFF with `rasterio` for band count and descriptions before changing production semantics.

## Decision and outstanding verification

- **V11: PARTIAL FIELD VERIFIED.** VIIRS NTL on 15,330 full 500 m cells and deterministic LISA (Queen/Local Moran/BH) across three new regions have strong independent support. Independent conditional Monte Carlo samples agree closely.
- **Open: 1,847 cut cells.** Their polygon geometry must be reconstructed from exact GADM source to independently verify the area-weighted means; matched full cells must not be conflated with border cells.
- **Open: A02 per-cell quality metrics.** All relevant columns are unknown in real exports; requires production output six-band TIFF metadata inspection, a minimal justified fix if necessary, and one real rerun.
- **Open: GHSL native-grid comparison and Cloud operational metrics.** No new GHSL/Cloud evidence was generated by this V11 audit; do not change their prior status.
- **No change to production code and no new PR.** Keep this evidence as a single set of inputs for the already planned consolidated Major Review.

## Reproducibility

Run `v11_field_validation_2026_11.py` and `v11_independent_permutation_sample.py` with the 6 CSVs and 9 reference TIFFs as named in the input manifest. The full-square check requires pandas, NumPy, rasterio, Shapely, and pyproj; it does not need `exactextract` or the app code. The Monte Carlo sample uses NumPy and pandas. Output JSONs record all summary metrics.


<!-- END ORIGINAL SOURCE 006 -->


---

## Source 007: `05_NOTES_REPORTS_AND_HISTORY/V11_EDGE_COMPLETION_2026-11-15.md`

**Original bytes:** 4,368 · **SHA-256:** `4cdb1b84cf0ceb2cc970560c699967971d169da568840a1a67c3892221c66896` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 007 -->
# V11 — Cross-location 2020 edge-cell validation completion

Date: 15 November 2026. Repository: `hoanfg/spatial-app`. **Private staging evidence; not a new PR.**

## Scope and evidence boundary

- **New analysis only:** 1,847 clipped/partial 500 m polygons that were excluded from the earlier 15,330-cell independent raster check. No previously verified full-cell zonal computations were rerun.
- The new polygon inputs are the **three user-exported application GeoJSONs**. Their IDs, areas, centroids and `ntl_mean` exactly agree with the corresponding user CSVs (all 17,177 IDs), and their geometries are nonempty/valid. The independent VIIRS raster source is the 2020 Earth Engine reference export; the integration routine does not import any `spatial-app` zonal code.
- Pixel-by-polygon intersections are computed in the EPSG:4326 GeoTIFF plane (as in the raster zonal coverage definition); masked/nonfinite values are skipped and valid negative median radiances clipped at zero, matching the legacy NTL policy. All new edge polygons have valid reference raster coverage.

## New numerical results (edge cells only)

| Case | Clipped cells checked | Within strict 0.00005 | Strict exceedances | Maximum absolute error | Within 0.0000501 |
|---|---:|---:|---:|---:|---:|
| Shanghai / Nội đô Thượng Hải | 180 | 180 | 0 | 0.00004959946 | 180 |
| Shenzhen / Bao'an | 1,017 | 1,016 | 1 | 0.00005003932 | 1,017 |
| Huangshan / Qimen | 650 | 650 | 0 | 0.00004993913 | 650 |
| **Total** | **1,847** | **1,846** | **1** | **0.00005003932** | **1,847** |

The **one** strict exceedance is `Bao'an grid_id=628`, area 0.010610 km², CSV `ntl_mean=18.8768`, independent raster overlay `18.876850039319148`. Difference: `0.000050039319148`, exceeding the four-decimal half-bin (`0.00005`) by `0.000000039319148` (3.93 × 10⁻⁸).

This is a **borderline numerical/rounding discrepancy**, not evidence of materially incorrect radiance extraction. It is retained explicitly. With the stated additive 0.0000001 floating-point allowance, 1,847/1,847 edge cells pass. This does not override or re-label the strict comparison: **1 strict exception remains**.

## Combined interpretation of prior and newly completed V11 checks

| Evidence component | Current interpretation |
|---|---|
| Existing 15,330 whole-cell raster comparisons | Previously verified within strict four-decimal CSV rounding, reused unchanged |
| New 1,847 boundary-clipped raster comparisons | 1,846 strict pass + 1 tiny rounding-boundary exception; all 1,847 within 0.0000501 |
| All 17,177 app cells (NTL raster consistency) | No material discrepancy detected at output precision; nuanced one-cell strict exception above |
| Prior independent Queen adjacency / Local I / BH-FDR | Preserved, not recomputed |
| A02 per-cell observation support | **Not validated:** all 17,177 `dq_status=unknown`; tracked separately |
| GHSL native-grid conservation / Cloud benchmark | **Still pending; unrelated to V11 NTL validation** |

**Important independence limitation:** the reference radiance raster is external, but the boundary-clipped polygon geometries are application-exported GeoJSON. Their aggregate geographic area and bounding box were separately checked against GADM-curated source metadata on GitHub (GIDs: `CHN.24.1.10_1`, `CHN.6.15.1_1`, `CHN.1.11.1_1`). This is not a source-boundary, vertex-by-vertex reconstruction of every polygon. Prior GADM provenance audits remain in force and are not duplicated here.

## Input provenance and reproducibility

All raw GeoJSON files stay outside the public repository; do not commit multi-megabyte polygon datasets by default. Original user CSVs and external reference TIFFs likewise remain private. The edge metrics JSON records SHA-256 for each of the nine newly used inputs (3 GeoJSONs, 3 NTL CSVs, 3 reference TIFFs). Per-cell edge residual CSVs (1,847 records combined) are included only in the private staging evidence ZIP. Independently re-run `v11_edge_only_independent.py` on those exact files to reproduce the results.

**Disposition:** V11 2020 cross-location NTL/LISA scientific numerical field validation is complete in the stated scope, with one explicit near-rounding strict exception; this is **not** an A02 or GHSL field PASS. Hold compact evidence for the next single consolidated major-review PR, rather than opening a new PR now.

<!-- END ORIGINAL SOURCE 007 -->


---

## Source 008: `05_NOTES_REPORTS_AND_HISTORY/spatial_app_cross_location_preflight_2026-11-13.md`

**Original bytes:** 3,280 · **SHA-256:** `2ab78372b5b30d47d9b9c16df5c92c4e9137aba7d83fa74bf0d897e16049648a` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 008 -->
# Spatial App — Cross-location validation preflight (Yanqing reference)

Date: 13 November 2026 · Repository: `hoanfg/spatial-app` · Commit: `05f03eccd4051c7c68fb039f6a292dea169f1d40`

## Scope and evidence level

This is a locally executed **real-raster polygon-overlay preflight**, not completion of V11 on Shanghai, Bao'an and Qimen. Inputs were extracted from the user's separately stored, historical Yanqing evidence archive. No Earth Engine call or new satellite acquisition was made. The code used was the archived Library copy of `validation/cross_location/compare_raster_cells.py`; its content (excluding one trailing newline) has Git blob SHA-1 `0beb176c6639ba401683e907ed5767f0f83e9200`, matching the current GitHub `main` file.

## Reproduced results

| Metric | Yanqing 2014 | Yanqing 2020 |
|---|---:|---:|
| Compared cells | 8333 | 8333 |
| Passing cells | 8333 | 8333 |
| Failed or missing cells | 0 | 0 |
| MAE (nW/cm²/sr) | 0.00002505402 | 0.00002502299 |
| Maximum absolute error (nW/cm²/sr) | 0.00004998959 | 0.00004999333 |
| Pearson r | 0.999999999785 | 0.999999999971 |
| Edge-masked grid cells | 600 | 600 |
| Reconstructed polygon area (km²) | 2003.50891204 | 2003.50891204 |

Tolerance: 0.00005 nW/cm²/sr, reflecting 4-decimal CSV rounding. The 2014 CSV used here is a derived three-column input generated from the archived 2014→2020 Space-Time CSV; it was not a separate raw app export.

## Source-raster inspection

| Measurement | 2014 | 2020 |
|---|---:|---:|
| Bands | 1 | 1 |
| Total source raster pixels | 30814 | 30814 |
| Masked pixels | 0 | 0 |
| Negative pixels | 1 | 0 |
| Exact zero pixels | 0 | 0 |
| Nonfinite unmasked pixels | 0 | 0 |
| Minimum monthly composite count | 12 | 12 |
| Maximum monthly composite count | 12 | 12 |

The 12-month indicator is a count of monthly composites accepted by the source script; it is **not** evidence of 12 independent cloud-free satellite observations per pixel. Neither historical raster has the five additional A02 quality bands.

## Provenance

- Evidence ZIP SHA-256: `95b3874d4253eec2269f2477b648a067fb14d1c94be54bc0ed38f8795599260c`; validated against historical recorded hash.
- 2014 reference raster SHA-256: `637661ab304986ef19befa4c7ca62d1e9cface500862803f02ad76a4b6637c31`
- 2020 reference raster SHA-256: `39d7d4789f816db6a066da4d90b022b8f4ba52abfb1e45da84c06be594090025`
- Boundary SHA-256: `3f40030b125423fa68e3350284ff79464843fa601a3bdfa7fa5ea891f9e91dbd`

## Reproduction and open dependencies

The same repository script was executed for each annual raster, with the archived GADM boundary and corresponding app-derived CSV. The output JSON files are retained locally but were **not committed** to GitHub.

Pending for V11: independent 2020 raster, VIIRS support/count products and spatial-app CSV exports for Shanghai (`CHN.24.1.10_1`), Bao'an (`CHN.6.15.1_1`) and Qimen (`CHN.1.11.1_1`); then rerun this method and independently validate their LISA outcomes. Also pending: real six-band A02 data-quality extraction, independent GHSL source checks, cloud memory/runtime benchmarks. None of those tasks can be marked PASS based on this Yanqing preflight.

**Review decision:** retain V11 as PENDING; no new PR or repo data fixtures are justified from this preflight alone.

<!-- END ORIGINAL SOURCE 008 -->


---

## Source 009: `06_LIBRARY_STAGING_EXACT_ORIGINALS/A02_DQ_UNKNOWN_FIELD_FINDING_2026-11-15.md`

**Original bytes:** 4,362 · **SHA-256:** `b4484af154e06a57d044c7e9ea69bfda29867de2968c625eb9eb04b0e022777b` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 009 -->
# A02 — real CSV `dq_status=unknown` field defect / root-cause investigation

Date: 15 November 2026. Repository: `hoanfg/spatial-app`. **Carry forward to the ONE consolidated Major Review PR; not a new PR.**

## Reproducible observed symptom

All 17,177 newly exported 2020 cell records across Shanghai (886), Bao'an (7,148) and Qimen (9,143) have `dq_status=unknown`. The five per-cell columns (`dq_observed_fraction`, `dq_negative_fraction`, `dq_zero_fraction`, `dq_mean_valid_months`, `dq_low_month_fraction`) are all empty. Separately, `dq_stat_missing=False`, and independent VIIRS pixel-overlap checks validate the main radiance values. No evidence suggests a forgotten UI action caused these particular empty columns.

## Exact code path / confirmed failure mode

1. `app.py:fetch_ntl_raster()` creates `annual_image_with_quality(col.map(_mask_cloud_free), roi)`, and downloads the GeoTIFF with `getDownloadUrl`. The ZIP branch selects its first `.tif` if a ZIP is returned.
2. `app.py:run_pipeline()` calls `cell_quality(tif_bytes, grid_wgs)` automatically as part of the core computation; that result is joined into `grid_utm`.
3. `ntl/semantics.py:cell_quality()` accepts the quality bands **only if** `src.count == 6` AND `tuple(src.descriptions[1:]) == QUALITY_BANDS` in exact order. When the condition is false, every `dq_*` numerical field becomes `NaN`, followed by `dq_status=unknown`, without a visible schema-error message.
4. `app.py:export_df` joins all `grid_utm` `dq_` columns; `ntl/lisa_ui.py` incorporates `export_df` into the downloadable `*_lisa_cells.csv`. The extra buttons in `ntl/quality_ui.py` (observation count, negative clipping sensitivity, GHSL validation) are optional **additional region-level diagnostics**. They do not populate these automatically generated per-cell fields.
5. `tests/test_data_semantics.py` writes a synthetic six-band GeoTIFF and explicitly assigns the expected band descriptions (`dst.set_band_description(i,name)`), so the test does NOT establish that live Earth Engine GeoTIFF delivery satisfies the description schema.

## Competing explanations to distinguish with one live capture

- The application may receive a six-band TIFF whose `src.descriptions[1:]` are absent or normalized differently.
- The application may receive fewer than six bands (e.g., download format / unexpected ZIP grouping) or an alternative schema.
- Stale deployed app version or an obsolete cached raster may also produce `unknown`; do not declare this hypothesis false without checking deployment commit and the `fetch_ntl_raster` cache/version.

**Current evidential status:** the deterministic code branch that generates `unknown` has been established, and all three field CSVs exhibit its output. The exact **live six-band `src.count` and `src.descriptions` remain unobserved** because the application-requested TIFF bytes were not captured. Therefore it is *not yet scientifically defensible* to state that Earth Engine definitely stripped the descriptions.

## Targeted corrective patch (one PR only, after confirming live raster schema)

1. Add a safe diagnostic at the network-to-raster interface: band count, descriptions, any ZIP members, and cache/deployment provenance (no credentials or raw raster upload required). Do not silently downgrade unrecognized schema to fully unknown without explaining the reason to the user.
2. Confirm band 1 exactly matches the pre-A02 legacy NTL contract at equal spatial settings.
3. Map valid six-band values to the known ordered semantic schema only if the producer provenance is established; refuse arbitrary six-band products instead of trusting band count alone. Explicitly distinguish absent label metadata from genuinely missing observation pixels.
4. Add one focused regression covering the **actual field condition** (e.g. nameless six-band geotiff) rather than increasing redundant synthetic test count, and confirm that known missing / zero / negative cases preserve intended semantics.
5. Perform field validation on an Earth Engine raster containing **genuine zero-support observations within the analysis polygon** before declaring A02 scientifically PASS.

**Decision:** retain the bug finding and scoped patch proposal in private staging for the user's single consolidated PR; do not open an isolated PR, alter NTL zero-fill policy, or claim A02 is fixed.

<!-- END ORIGINAL SOURCE 009 -->


---

## Source 010: `06_LIBRARY_STAGING_EXACT_ORIGINALS/BAOAN_A02_PERFORMANCE_POST_MERGE_AUDIT_2026-11-15.md`

**Original bytes:** 4,019 · **SHA-256:** `dd96ca1716064c6a4d558d707ae555e824571a75181de2369ca06863df4056f1` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 010 -->
# Bao'an A02 & runtime post-merge audit — 2026-11-15

## Scope and provenance
- Area: Shenzhen Bao'an, 2020, 500 m; 7,148 grid cells, grid IDs 0–7147.
- Inputs: an app-exported cell-level CSV and `spatial_app_performance.json`, both user-provided on 2026-11-15.
- Baseline: pre-A02-fix Bao'an app CSV, 2020/500 m, preserved privately from V11 validation.
- CSV SHA-256: `40b76f2f0f1fec0834be16f88e4b97084986886f5edc84d8718e28bf263eaece`.
- Profiler JSON SHA-256: `04e634f07ff2816641f1fba3faa948485adeec5a4fdb3901474c0422b3dba2cf`.
- Do not upload the underlying user CSV or Cloud process log to GitHub.

## A02 field results
- Cell IDs: unique, identical ordering to baseline, 7,148/7,148.
- `dq_status`: `observed` in 7,148/7,148, `unknown` in 0.
- All five per-cell quality metrics have 7,148/7,148 non-missing values:
  `dq_observed_fraction`, `dq_negative_fraction`, `dq_zero_fraction`,
  `dq_mean_valid_months`, `dq_low_month_fraction`.
- Pre-fix baseline: all five metrics missing in 7,148 rows; `dq_status=unknown` in all rows.
- Observed fraction: all rows 1.0. Negative/zero/low-month fractions: all rows 0.0.
- Mean valid months: minimum 10.000000, mean
  11.988060, maximum 12.000000;
  observed fraction 1 does **not** imply all 12 months were valid.
- `dq_stat_missing`: false for every grid cell.
- Crucial regression: **all 24 non-DQ CSV columns exactly match the
  pre-fix baseline** (numeric tolerance absolute 1e-10, no relative tolerance).
  `ntl_mean`, `ntl_sol`, spatial IDs/geometry-derived fields, scores, ranks,
  quantiles and groups unchanged.

Conclusion: **A02 field PASS at Bao'an 2020/500 m**. Does not prove the
same schema behavior across all locales or historical VIIRS years.

## Profiler results
- `pipeline_success = true`; all 13 profiled stages have `status=ok`,
  no recorded error type.
- Main analysis pipeline wall time: **46.6687 s**.
- Sum of the 6 instrumented initial stages: 46.0708 s, with
  0.5979 s not attributed to those stages.
- A02 cell quality: **25.0028 s**, or
  **53.6%** of primary pipeline.
  Current implementation calls per-band zonal extraction repeatedly;
  batching exactextract on aligned bands is a candidate optimization,
  subject to exact numeric regression tests.
- Grid build: 9.7399 s; NTL zonal mean: 9.6193 s;
  NTL EE download: 1.4220 s; boundary load: 0.1477 s;
  Global Moran: 0.1391 s.
- Subsequent optional LISA: 3.6794 s;
  GHSL built fetch + zonal + agreement: 7.8895 s;
  GHSL population fetch + zonal + agreement: 8.0610 s.
- Sum of all stage durations including these later optional user actions:
  65.7007 s.
  `time_since_recorder_created_s=369.7477`
  is **elapsed wall-clock since recorder creation** and includes user activity
  or idle intervals; it is **not** computation time.
- Peak sampled process RSS: **728.531 MiB**,
  observed during `ntl.zonal_mean` (grid build peaked at 711.379 MiB).
  Baseline process RSS at first recorded stage: 591.270 MiB.
- Process-wide RSS, sampled every 0.1 second; may miss
  brief peaks and cannot be compared to an unknown Streamlit Cloud memory limit.
  One successful run cannot prove capacity under concurrency or other localities.

Conclusion: **profiler functional PASS**, **observed single-run pipeline success**.
Performance optimization candidate A02 (25 s) is open, but not a correctness bug.
No OOM/timeout event appears in this profiler trace, which does not prove such
events are impossible.

## Audit disposition
- A02 quality metadata at Bao'an 2020/500 m: **PASS (field)**.
- NTL regression vs baseline: **PASS (all 24 non-DQ columns unchanged)**.
- Profiling function: **PASS (instrumentation works)**.
- Single-run Cloud runtime: **observed success**; not a load/stress benchmark.
- GHSL built/pop profiler stages: **both OK**. Correlation and external
  scientific validity are independent of profiler status; refer to prior
  Shanghai field validation and user-observed Bao'an/Qimen charts.

No production modification is proposed on the basis of these two inputs.

<!-- END ORIGINAL SOURCE 010 -->


---

## Source 011: `06_LIBRARY_STAGING_EXACT_ORIGINALS/CLOUD_RUNTIME_LOG_REVIEW_2026-11-14.md`

**Original bytes:** 3,570 · **SHA-256:** `8c07d580c1bfe8a39a3356267f7dc8aa3c567c7c6e34fe519a3c239c635db5e1` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 011 -->
# Streamlit Cloud runtime log review — 14 November 2026

**Source:** user-supplied Streamlit deployment log downloaded on 14 Nov 2026, containing entries from 11–14 Nov 2026 (UTC). File SHA-256: `92d1b8829288fbc50458989e4d0fcda1ec4b2486b10b77469352902d4799f873`. The full source log is retained privately, **not committed**. This report is an interpretation of the log, not an end-to-end Cloud benchmark.

## Observed facts

- Cloud startup used **Python 3.14.10** and **Streamlit 1.67.0**; package installation completed and the web server started (source lines 128–129, 245–246, 295–296).
- The dependency installation initially selected PyArrow 26.0.1, then the platform automatically replaced it with 24.0.0 because of a known segmentation-fault concern (lines 247–257). There is **no observed segmentation fault** in the log.
- Two import failures, `ModuleNotFoundError: No module named 'ntl.semantics'`, were logged on **12 November** during a GitHub code pull (lines 419–455). `Updated app!` followed at line 458, and the app was used on later dates. This historic failure is **not evidence of a current missing module**. The module is present on the reviewed `main` branch.
- 99 notices requested replacement of deprecated `st.components.v1.html` with `st.iframe`; 107 requested replacing `use_container_width` with `width`. These are deprecation notices, **not exceptions**; legacy iframe usage may originate in third-party code and needs call-site attribution before changing behavior.
- 34 warnings reported that the currently selected CartoDB tile source may require an API key. This presents a base-map availability risk, separate from numeric raster/NTL/LISA computations. An explicit tile-provider fallback should be verified visually rather than blindly swapping map style.
- 19 `Updated app!` messages appear across the captured period. Initial Git checkout processed roughly 20,023 files; that may contribute to cold startup, but this log alone does not separate Git checkout time from network and host variance.
- No explicit `MemoryError`, OOM-killer message, process termination, or execution timeout appears in this file. **Their absence does not establish an upper bound on memory or per-analysis latency.**

## Decisions and release gates

1. Carry **in-app session-accessible profiling** in the single consolidated draft PR: end-to-end and stage wall times, sampled process RSS, success/error type and JSON/CSV exports. The profiler does not claim per-user isolated memory or a physical maximum.
2. Carry A02 fail-closed six-band schema diagnostics and native-lattice GHSL quantity conservation fix in **the same PR**. They address issues found in CSV/raster comparisons; the deployment log does not directly diagnose either one.
3. Before merge, run CI and one authenticated Cloud field comparison. Confirm that VIIRS `getDownloadURL` quality-band metadata is populated or displays an explicit failure reason, and compare GHSL built/pop per-cell totals with the native-grid references. Inspect performance JSON under representative cells and cloud concurrency.
4. Treat compatibility notices as a tracked maintenance issue within review; update first-party width calls only with tested Streamlit version support, determine origin of iframe calls, and verify a no-key base-map option visually. Do not conflate cosmetic warnings with a scientific failure.

**Status:** log triage complete; production validation pending. No human user identifiers, credentials, raw log bodies, or Cloud secrets are included in this evidence report.

<!-- END ORIGINAL SOURCE 011 -->


---

## Source 012: `06_LIBRARY_STAGING_EXACT_ORIGINALS/CONSOLIDATED_FIELD_EVIDENCE_2026-11.md`

**Original bytes:** 4,820 · **SHA-256:** `b64865b6eb9a8532a88c4721f0b0cd9c30887e17af43bb918854e4d21d7afeab` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 012 -->
# Consolidated independent field evidence — November 2026

This report records bounded checks relevant to the A02/GHSL/runtime correction. Source GeoTIFFs, user cell CSVs and GeoJSONs remain outside the public repository; only aggregate results and SHA-256 values are published here. Results are **not** a claim of final live Cloud acceptance.

## V11 cross-location, 2020 VIIRS

Three GADM 4.1 localities: Shanghai Core (`CHN.24.1.10_1`), Shenzhen Bao'an (`CHN.6.15.1_1`), and Anhui Qimen (`CHN.1.11.1_1`). The 2020 reference median, valid-month raster and masked-median raster were exported independently from Google Earth Engine. Cell values were compared against actual 500 m application CSV/GeoJSON outputs.

| Area | All application cells | Full 500m cells | Boundary-clipped cells |
|---|---:|---:|---:|
| Shanghai | 886 | 706 | 180 |
| Bao'an | 7,148 | 6,131 | 1,017 |
| Qimen | 9,143 | 8,493 | 650 |
| **Total** | **17,177** | **15,330** | **1,847** |

All 15,330 full cells passed a four-decimal CSV rounding comparison with independently integrated reference radiance. Of 1,847 clipped cells, 1,846 met the literal absolute 5e-5 bound. Bao'an `grid_id=628`: CSV `18.8768`, independent `18.876850039`, exceeded by only 3.93e-8; all clipped cells pass 5.01e-5 including a 1e-7 numerical guard. The clipped polygons in this check are the application's exported GeoJSON geometry, not a fully independent polygon reconstruction from GADM source. Queen-neighbor and BH-FDR checks on the application CSV results found no mismatches, subject to Monte Carlo seed and value-rounding qualifications in the private evidence.

This is scientific reference evidence and should not be rerun as a substitute for testing changes to production A02 or GHSL code.

## GHSL quantity-conservation defect, Shanghai 2020

Product: `JRC/GHSL/P2023A` original 100 m Mollweide (`ESRI:54009`), native pixel quantities, compared to application-style EPSG:4326 at nominal 100 m. Shared interior bounding box (`121.35899,31.17207,121.57093,31.33289`) avoids edge-coverage artifacts. All native/app sample coordinates were independently transformed.

| Quantity | Native grid total | App-style uncorrected sum | Bias |
|---|---:|---:|---:|
| Built-up surface (m²) | 118,319,940 | 137,859,621 | +16.51428% |
| Population (persons) | 11,674,618.205 | 13,612,238.308 | +16.59686% |

The original reference core had 36,234 source pixels, versus 42,244 destination pixels. Independent nearest-neighbor warping reproduced **42,244/42,244** destination values exactly for both products. Thus the bias arises when reprojected *per-source-pixel amounts* are summed as if independent destination-pixel amounts. The remedy is a source-lattice-preserving coverage-weighted sum, **not** a universal scalar calibration. The empirical 16.5% error is bounded to this Shanghai case; other cities and Spearman/AUC effects require evaluation after deploying the correction.

Input file SHA-256 (native → application-style):

- Built surface: `cb72bc30727e89c43daecee6276b242ee141d8d1c971adde85f409020151cee6` → `93fbe303ed47c6276689409b53a05118e41f8a12a9f8aca3bf85223c84983244`.
- Population: `3f20333936035fefc208a42cfdf8ab63414afc8f1c4f2ccad6c6294497fbf0b6` → `31d75bb8be7a5641281ed6e516e1fbc9f7480f9cc25af30034127b5c5fca4b8f`.

## A02 quality bands, Bao'an 2020

Independent six-band `Export.image.toDrive` TIFF uses the expected names and `float32` values. Band one matched the independent VIIRS median exactly at 26,786 shared finite pixels. All 27,013 quality raster pixels were observed, with monthly support between nine and twelve. No genuine zero-support / low-support pixel is present in this field sample. The actual app's different `getDownloadURL` path remains unverified. All 17,177 previously exported app-cell CSV rows had `dq_status=unknown` and empty quality fields. The production patch should record the band count/descriptions and fail closed when the schema is not trustworthy; do not claim the root cause is proven until a Cloud download is observed.

Six-band input SHA-256: `5569fd153784dfee99d28d6a2413982f16fe9613691e9e62baeb937313b4f4c1`.

## Cloud/runtime acceptance gate

A Streamlit Cloud log (source retained outside this repository) shows a historical `ntl.semantics` import error on November 12 that was followed by app updates; runtime on November 14 generated UI deprecation notices and CartoDB tile warnings. It does not establish per-analysis wall time or RSS, nor OOM or timeout conditions. The PR adds user-visible performance JSON/CSV recording; measure one authenticated Cloud run before merge. The same gate must test native-GHSL sums and A02 quality metadata from actual `getDownloadURL` transfers, and capture regression/CI results. Do not publish any access credentials or original user geospatial data.

<!-- END ORIGINAL SOURCE 012 -->


---

## Source 013: `06_LIBRARY_STAGING_EXACT_ORIGINALS/GHSL_A02_REAL_FIELD_FINDINGS_2026-11-15.md`

**Original bytes:** 7,041 · **SHA-256:** `484478ad27db5b48bbce380fc8496649739326affc26d1dddf1a7f9939452562` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 013 -->
# Spatial App — field evidence: GHSL native vs app-style raster and A02 six-band intake

Date: 2026-11-15 (Asia/Ho_Chi_Minh). This document preserves **real exported data** from the user's connected Google Drive. No GitHub PR, production edit or renewed Yanqing/V11 test is included.

## Sources, spatial target and scope

GHSL 2020 JRC P2023A: `JRC/GHSL/P2023A/GHS_BUILT_S/2020` (`built_surface`, m² of built-up area per 100 m original grid cell), and `JRC/GHSL/P2023A/GHS_POP/2020` (`population_count`, persons per original grid cell). Native projection in the retrieved GeoTIFFs: `ESRI:54009` (World Mollweide), pixel spacing 100×100 projected meters. Application export: `EPSG:4326` at an Earth Engine scale of 100 nominal meters, actually ~8,515–8,530 geodesic m² per cell in this area. Google data catalogue: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S and https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP.

The five distinct raster types are present in Drive folder `1VJGX8ElFo2xavlRrD7Wcox__UwsjTOrs`; an A02 six-band copy is also in separate folder `1oEHzRYEVKNnrJv5M7PU4H8q2CrniK6fI`. The first folder's updated file listing, not a stale folder preview, supplied the two native GHSL outputs. Original source assets remain on Google Drive; not bundled in the repository.

The geographic export rectangle for GHSL is `[121.35299, 31.16607, 121.57693, 31.33889]`. To reduce nonuniform edge rasterization, a common interior rectangle `[121.35899, 31.17207, 121.57093, 31.33289]` (0.006° inset on all four sides) is used for the primary comparison. Both native/app pixels are selected by centre position, independently transformed to geographic coordinates. This is a bounded-field comparison, **not** an administrative census estimate or official total for Shanghai.

## GHSL measured impact — identical geographic core

| Quantity | Native GHSL grid total | App-style EPSG:4326 grid total | App-style overcount | Identical nearest-sampled pixel values |
|---|---:|---:|---:|---:|
| Built-up surface | 118,319,940.000 | 137,859,621.000 | +16.51428% | 42,244/42,244 |
| Residential population | 11,674,618.205 | 13,612,238.308 | +16.59686% | 42,244/42,244 |

Native core has **36,234** pixels; app-style core has **42,244** pixels. Independently warping the native raster to the destination grid with nearest-neighbour resampling reproduced **all 42,244/42,244 sampled destination pixel values exactly** for each of the two products. Therefore the error is not that a source pixel's stored value is changed: **a per-native-pixel quantity is repeated across a denser EPSG:4326 lattice, then summed as if each destination pixel were a separate 100×100 m source quantity**. This is a **confirmed quantity-conservation defect in the application GHSL validation/aggregation path** if totals are used without area conversion or native-grid integration.

Comparison over the full finite exported footprint (more sensitive to raster-edge footprint treatment): built-up surface **+17.08992%** (native 132,558,787 m²; app 155,212,982 m²), population **+17.02134%** (native 12,602,775.004 persons; app 14,747,936.687 persons). Independent repeated core insets give: built {'.003': 17.12041, '.006': 16.51428, '.010': 16.94212, '.015': 17.32608}; population {'.003': 17.1483, '.006': 16.59686, '.010': 16.9983, '.015': 17.31684}. This variation is expected from grid boundaries and source pixelization, not uncertainty about the fundamental failure mechanism.

The app-style cells cover **8514.7–8530.0 m²** physically, whereas source pixels represent quantities per 10,000 m² Mollweide cells. At least **62 of 48,500** app-style `built_surface` pixels exceed the physical area of the destination pixel, independently indicating that an intensive/area-preserving reinterpretation is required before physical interpretation.

**Production trace:** `ntl/ee_extra.py::fetch_ghsl_raster()` calls `getDownloadURL` with `scale=100, crs='EPSG:4326'`, then `ntl/quality_ui.py` calls `zonal_stat(raw, grid_wgs, 'sum', clip_negative=True, fill_missing=0.0)` with no compensation for changed destination cell size. `ntl/zonal.py` performs a pixel-footprint fraction-weighted `sum` on whatever grid is supplied. An appropriate production correction would download or otherwise aggregate in the source's native equal-area 100m lattice, transforming polygons into its CRS for coverage-weighted sums. **Do not** blindly scale EPSG:4326 pixel values by a single latitude factor: that is an approximate diagnostic, not a robust spatial integration method. Preserve the existing NTL and LISA estimators.

## A02 six-band export — verified, but no low/missing-support test case

The actual `baoan_2020_a02_six_band_reference.tif` has six `float32` bands with exact descriptions:

`avg_rad, dq_observed_fraction, dq_negative_fraction, dq_zero_fraction, dq_mean_valid_months, dq_low_month_fraction`.

Shape: 119×227 cells; CRS EPSG:4326. All 27,013 cells have observed fraction = 1, zero negative/zero median flags and zero low-month flags. Observed-month counts: {9.0: 1, 10.0: 26, 11.0: 802, 12.0: 26184}. Comparison with the previously independent 2020 Bao'an median export showed **26,786/26,786 exactly matching band-one values in their shared finite footprint**. The other 227 rows/pixels are outside the earlier export footprint, not proof of an observation gap inside the district.

These new data prove that Earth Engine `Export.image.toDrive` can preserve all six descriptions and that band one agrees with the independent NTL annual-median raster. However, **no pixels here have fewer than 9 months**, so this is not a real-field test of `no_observation` or `low_month_fraction`. Furthermore **the Streamlit app uses `getDownloadURL`, not Drive export**, and all 17,177 previous app CSV rows still showed `dq_status=unknown`. The specific live Cloud download band count/names remain unobserved, so A02's Cloud failure mechanism remains unresolved. Staged schema warnings and tests are not yet applied to production.

## Reproducibility and release gate

- The standalone comparator is `ghsl_field_compare_2020.py`; JSON with all stats and SHA-256: `GHSL_A02_SHANGHAI_BAOAN_FIELD_METRICS_2026-11-15.json`. Input file names are in that JSON.
- Native vs app two samples are on different pixel lattices; compare within the common geographic core before interpreting full-extent pixel sums.
- The field evidence **confirms GHSL overcount** in Shanghai 2020. It does not quantify the bias in other places/epochs or the impact on rank-based Spearman/AUC metrics. This is not a claim that the app's reported global NTL/LISA results are invalid.
- For the consolidated PR: correct native GHSL integration, add real-field conservation regression and fail-closed A02 schema diagnostics. Require one authenticated Cloud run with published raster schema and practical performance metrics before closure. **No extra copies of user rasters or proprietary data in GitHub.**

<!-- END ORIGINAL SOURCE 013 -->


---

## Source 014: `06_LIBRARY_STAGING_EXACT_ORIGINALS/PR_STAGING_NOTES.md`

**Original bytes:** 16,264 · **SHA-256:** `55006f34c322dbbe7e6e2a57f0cf4038f6fa8ec4038fd9cd1bf15a461d4cfadc` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 014 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 14 November 2026 (revised from 13 November). Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Eleven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

## Review update 14 November 2026 — no new PR

- Hardened the GHSL check against **partial-coverage false positives**: eligible cells must have nearly 100% finite, unmasked raster area in BOTH native and app exports. Ineligible per-cell differences are NaN, not numerically compared.
- Added guard for GHSL native 100 m product resolution; a wrongly supplied 1 km raster fails preflight.
- Hardened A02 source independence: selecting ROI from the application's own band-1 mask could silently drop an app-side masked pixel. Reference valid-month count now defines the footprint, so this case fails.
- Negative controls expanded; `python -m pytest -q test_validation_scripts.py` now reports **11 passed**.
- All field validation gates remain unfulfilled without matching real-data rasters and application exports. Preserve project policy: **one future consolidated PR**, no branch/PR in this stage.

## 15 November 2026 — v4 single-PR carry-forward

1. Require **actual per-ID spatial identity** using UTM and WGS84 centroids, not only grid ID/area. The current production app already exports all required fields. Checker code and comparator are staged, not pushed to GitHub.
2. Reject non-integral valid-month counts in A02 references.
3. **11/11 isolated checker tests passed.** Deliberate same-area grid swaps and missing centroid columns are rejected.
4. Historical Yanqing 2020 GADM, real VIIRS raster and application CSV were checked with the amended comparator. Exactly **8,333/8,333** per-cell NTL references and centroid identity comparisons passed at exported rounding tolerances; detailed metrics JSON and source hashes are included, but private input raster/GeoJSON/CSV and the 8,333-row diagnostic table are *not* bundled.
5. No new branch, PR, production algorithm changes or geospatial data bundles. One consolidated PR remains the only proposed repository update.

## Field update 15 November 2026 — V11 edge closure + A02 real-data `unknown`

- **V11 new evidence:** analyzed exactly 1,847 previously excluded boundary-clipped cells from 3 user GeoJSONs against 3 independent EE VIIRS TIFFs. All covered. 1,846/1,847 pass the literal 5e-5 half-bin; one Bao'an record (`grid_id=628`) exceeds by 3.93e-8 and is explicitly reported; 1,847/1,847 pass 5.01e-5 including a 1e-7 floating guard. Prior 15,330 core cell results were not repeated. Detailed private report: `V11_EDGE_COMPLETION_2026-11-15.md`.
- **A02 real-data finding:** `dq_status=unknown` for all 17,177 new cell CSV rows; strict exact 6-band-description condition in `cell_quality` is a verified route to this symptom. Optional Data Quality UI buttons do not populate those fields. Actual live band count/description still unobserved; do not claim a confirmed Cloud root cause. Proposed surgical diagnostics/fix, not yet applied: `A02_DQ_UNKNOWN_FIELD_FINDING_2026-11-15.md`.
- No production changes, no new PR, no revalidation of old Yanqing benchmarks, no large GeoJSON/raster inputs added to the public repo. Keep these artifacts in the existing private staging folder.

## Unresolved scientific gates — 15 November 2026, targeted remediation staged

- A02 silent unknown is confirmed in 17,177 new field CSV rows. Nine EE `Export.image.toDrive` single-band TIFFs show band descriptions, so absent names in the distinct application `getDownloadURL` output remain a **hypothesis**, not a proved root cause.
- Prepared but **did not deploy** a fail-closed A02 schema patch (only app-created raster may use verified, unlabeled six-band positional fallback). Explicit schema warnings and focused regression controls are included in `remaining_field_package.zip` (8/8 focused tests pass locally). No NTL/Moran/LISA estimator modifications.
- Prepared 5 real-data EE exports for one A02 six-band Bao'an raster and matched native/reprojected GHSL 2020 built/pop at Shanghai. No Earth Engine task has been submitted from this session. Run once and process Drive outputs when available; do not repeat Yanqing/V11.
- Cloud runtime remains unmeasured; owner Cloud logs available via Manage app; no claims of memory PASS.
- Remain on ONE future consolidated PR. Source rasters and large geospatial outputs remain outside public repo.

## Field update 15 November 2026 — GHSL measured real-world bias; A02 six-band EE export

- Five distinct TIFF export products were located in two same-named Google Drive folders. The folder preview briefly omitted the two new native GHSL files; direct `list_folder` found both. Source bytes were retrieved and analyzed; no re-export needed.
- **GHSL empirical defect confirmed:** Shanghai 2020 `JRC/GHSL/P2023A` `GHS_BUILT_S` and `GHS_POP` per-native-100m-cell amounts were exported at native Mollweide 100 m and application-style EPSG:4326 `scale=100`. In a common inset geographic core, naive appstyle sums exceed native by **16.51428% built area** and **16.59686% population**. Reprojection of the native raster to the app grid by nearest neighbor matched **42,244/42,244** app-grid samples for each product exactly: native per-pixel amounts were duplicated onto more/smaller cells before unadjusted zonal sums. Original `ntl/ee_extra.py` hardcodes EPSG:4326 and `ntl/quality_ui.py` sums destination-grid amounts. This is real-world, source-grid quantity-conservation evidence, not a synthetic demonstration. Impact at other sites remains unmeasured.
- **A02 field reference verified but Cloud unknown unresolved:** Export.image.toDrive Bao'an six-band VIIRS GeoTIFF contains exact six `avg_rad` and `dq_` band descriptions. Band one matched the independent 2020 VIIRS median on every **26,786/26,786** shared finite pixel. All 27,013 quality pixels are observed with **9–12** monthly supports; the export lacks genuine missing/low-support cells. Streamlit uses distinct getDownloadURL route and its 17,177 prior CSV rows have `dq_status=unknown`; cannot declare Cloud root cause solved from this export.
- New non-GitHub staged evidence: `GHSL_A02_REAL_FIELD_FINDINGS_2026-11-15.md`, `GHSL_A02_SHANGHAI_BAOAN_FIELD_METRICS_2026-11-15.json`, and `ghsl_field_compare_2020.py`. GeoTIFF input bytes stay on connected Google Drive; hashes are in JSON. Implement the GHSL native-grid conservation fix and fail-closed A02 Cloud schema diagnosis together only after review, **one consolidated PR**. No repetition of Yanqing/V11 and no production code edit in this field audit.

## 15 November 2026 — In-app performance instrumentation and native GHSL correction candidate

User has no Streamlit Cloud **Manage app** access and therefore cannot obtain owner logs. In the **same planned consolidated PR** (not a new PR), add owner-visible/self-service profiling:

- `ntl/performance.py` (new): `PerformanceRecorder` with `time.perf_counter`, 0.1s sampled process RSS from `/proc/self/status` (optional psutil fallback), end-to-end pipeline duration, per-stage elapsed time, short error type only, and in-app JSON/CSV download. No external reporting endpoint or user-data logging. Process RAM can include concurrent sessions; high-water mark is sampled, not guaranteed maximum.
- Strict integration into `app.py`, `ntl/lisa_ui.py`, `ntl/quality_ui.py`: time boundary loading, grid creation, Earth Engine download, exactextract mean, A02 per-cell quality, Global Moran, Local LISA, extra Space-Time year retrieval, native GHSL fetch, GHSL zonal sum and GHSL external-proxy agreement. A failing main pipeline still has a per-stage diagnostic in-app. The performance panel appears in LISA after a successful analysis.
- `ntl/ghsl_native.py` (new): source-grid affine and CRS windowing with 100m native Mollweide pixel alignment. Earth Engine getDownloadURL's `region` parameter is ignored when CRS+transform are specified, so pass bounded `dimensions` plus source CRS+transform and pre-clip image to ROI. Validate pixel count, CRS, transform and grid dimensions of downloaded TIFF before zonal sum. The exact window for the real Shanghai native GHSL raster is 331 x 202 pixels and affine `[100,0,11030200,0,-100,3800200]`, as measured previously.
- Carry forward the earlier fail-closed A02 six-band schema patch and focused tests, no change to zero-fill NTL/Moran/LISA models.
- Candidate file `Spatial_App_Consolidated_PR_Candidate_A02_GHSL_Performance_2026-11-15.zip` in this staging folder. Includes `apply_consolidated_review_patch.py` to generate **one unified diff** inside a clean repository checkout; default does not modify or commit anything. GitHub integration anchor counts verified against `main` (all expected counts), although the actual full Streamlit/EE deployment has **not** yet been exercised.
- **16/16 focused tests PASS** in isolated container Python (A02=8, GHSL source-grid=4, profiler=4). These are not equivalent to a Cloud/EE green light. `targeted_tests.xml` is bundled.
- Stop gate: compare the corrected native GHSL per-cell totals/Spearman/AUC against the already-saved real raster reference and capture one authenticated Cloud profiler JSON; verify A02 real `getDownloadURL` schema. Do not declare GHSL/A02/Cloud fully closed before this. No new PR opened and no old V11/Yanqing reruns.

## 15 November 2026 — User-supplied Cloud log and consolidated draft PR #24

- Reviewed complete 1,313-line Streamlit Cloud log covering 11–14 November (downloaded 14 November). Detected two historic `ntl.semantics` import tracebacks on 12 November followed by app updates, 99 `st.components.v1.html` notices, 107 `use_container_width` notices, 34 CartoDB API-key warnings, Python 3.14.10, and automatic downgrade from PyArrow 26 to 24. No logged OOM, forced kill, or timeout. The uploaded log cannot establish Cloud per-analysis timing or a process RAM bound.
- GitHub **draft PR #24** opened: https://github.com/hoanfg/spatial-app/pull/24 (branch `review/consolidated-a02-ghsl-runtime-2026-11`, head `0a1dec7c5a471e600d96f2347cae001ef3c74910`). It consolidates GHSL native-source-grid fixes, A02 schema diagnostics, visible runtime profiler, tests and compact field/log evidence in 12 files. **Main remains unchanged.** Raw field data and logs are not committed.
- Targeted GHSL-native and performance tests re-executed in the available environment: **8 passed**. Full GitHub Actions CI was still in progress when the PR was opened. The 8 A02 tests and full test matrix require CI / the geospatial test environment. Do not claim a merge-ready state until CI, Cloud A02 download schema, GHSL results and profiler JSON are checked.
- Preserve the original one-PR rule: do not open a secondary fix PR or re-run historical Yanqing/V11 evidence without a change that warrants it. Any necessary review changes should update the **same PR #24**.

### 15 November 2026 — Draft PR #24 CI regression fixes and gate

- Opened one draft PR #24 on the reviewed `main` snapshot; public PR: https://github.com/hoanfg/spatial-app/pull/24. No merge, no production deployment, no separate follow-up PR. Field data and full user Cloud log are not committed.
- Initial PR CI failed in the lightweight core job because the new `ntl/ghsl_native.py` imported Rasterio at module import time. This was corrected with a lazy `transform_bounds` import (commit `9218ec185d836b26913b9c6ded452517d92228e7`).
- Next core CI completed 30/32 tests, with two legacy GHSL tests failing because the revised fetch path imported `requests` in the lightweight test job and used a new native-grid transport. Introduced `_download_native()` with lazy `requests` import, restored the early large-bbox guard, and adjusted the existing GHSL mock test to validate the native-window interface rather than the removed reprojecting download (commit `b4f25b45bacc49c581fa1610afe110a78c747bea`).
- **Final CI on `b4f25b45`: both `push` and `pull_request` workflows completed SUCCESS**, each running core T01–T28 and UI AppTest jobs. PR body gate checkbox updated. No extra Yanqing/V11 analysis performed.
- **Remaining merge blockers:** authenticated Cloud A02 six-band schema and per-cell DQ, native GHSL cell sums/metric changes, in-app performance JSON/RSS on representative runs, map fallback/interface compatibility checks. The PR remains a draft; `main` remains unchanged.

<!-- END ORIGINAL SOURCE 014 -->


---

## Source 015: `06_LIBRARY_STAGING_EXACT_ORIGINALS/README.md`

**Original bytes:** 9,716 · **SHA-256:** `a0b82b9fd376b4e8c3f96adfb7e8f7f7497e761a9f6dee2cf070c56371c284e9` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 015 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **15 November 2026** (incremental v4 of 13–14 November staging). Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code and a small, reproducible Yanqing 2020 metrics JSON**, but no Earth Engine credentials, private input GeoTIFFs, original GADM boundaries, or large per-cell result tables. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** eleven synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV must be a current Spatial App cell export containing `grid_id`, `area_km2`, `ntl_mean` and four rounded **per-ID centroids** (`centroid_lon`, `centroid_lat`, `centroid_x_epsgNNNN`, `centroid_y_epsgNNNN`) for the same GADM boundary and grid. Area and IDs alone are insufficient to detect identical-size cells reordered geographically.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas and source 100 m resolution, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Each cell now reports native/app **valid-area fractions**, and a comparison is eligible only with at least 99.9999% valid area in both rasters. Merely intersecting a single valid pixel cannot justify full coverage. Missing or partial reference/application coverage is reported and causes a nonzero CLI exit code. Ineligible differences are blanked, while partial raw sums remain available only for diagnostics. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters. The **independent month-count** reference mask defines the comparison footprint; a missing/masked application pixel is flagged rather than excluded from validation. Extra app-only coverage outside the count reference also fails.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (11 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

## November 14 reviewer hardening

- GHSL now measures **fraction of each polygon covered by finite unmasked raster pixels**, not just the presence of any intersection. Only fully covered cells enter regional comparison totals and Spearman; partial diagnostics remain visible but never silently pass.
- Native GHSL must have projected 100 m resolution (within 1 m tolerance); the code still cannot independently prove the correct version/epoch/band without source metadata.
- A02 uses **independent reference count coverage** to choose pixels for validation. App-masked observations with valid reference count are checked as failures rather than skipped.
- Negative controls exercise one missing interior source pixel, invalid native product resolution, and an application-only missing A02 pixel. Eleven tests pass as of this staging version.

See `REVIEW_FINDINGS_2026-11-14.md` for the checker's identified failure modes and scientific boundaries.

## 15 November addendum — grid identity and negative controls

- **GHSL:** per-cell UTM centroids (application exports rounded to 0.1 m) and geographic centroids (six decimal places) must match the independently reconstructed grid at their respective rounding precision. Omitting these four columns is an error, not permission to skip the spatial-identity check.
- **Cross-location comparator:** the staged `compare_raster_cells.py` now applies the same per-ID geometry gate *before* calculating raster zonal statistics. It is intended to replace the existing script in the **single future consolidated PR**, not to create a micro-PR.
- **A02:** reject a valid-month raster with fractional counts, which can indicate an improperly resampled month-count reference. A count of months must be integral.
- **Real-data regression:** independent raster–polygon overlay was rerun on the historical Yanqing 2020 archive. **8,333/8,333** NTL cells met the CSV rounding tolerance (0.00005 nW/cm²/sr), and **8,333/8,333** UTM/WGS84 centroids met their recorded rounding tolerances. See `yanqing_2020_regression_metrics.json` and the recorded input SHA-256s. A controlled swap of the locations of two equal-area historical cells was rejected.
- **Limits:** this is a reproducibility check of the previously archived Yanqing data, **not** a newly acquired VIIRS/A02 six-band or JRC GHSL dataset. V11, GHSL live comparison and A02 real missingness remain PENDING.

<!-- END ORIGINAL SOURCE 015 -->


---

## Source 016: `06_LIBRARY_STAGING_EXACT_ORIGINALS/REVIEW_FINDINGS_2026-11-14.md`

**Original bytes:** 3,461 · **SHA-256:** `5ddace573c0c0c79920b1812a29b11205a3c2932bbfc57000558bf6d0975d95e` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 016 -->
# Spatial App — Staging review findings (14 November 2026)

## Executive finding

Three **potential false-assurance paths in the external validation checkers** were found and corrected in this staged package. These are **checker defects**, not demonstrated defects in the Spatial App production analysis. No changes were made to the GitHub repository.

| ID | Prior checker behavior | Risk | Hardening | Synthetic negative control |
|---|---|---|---|---|
| S01 | GHSL considered a cell covered if *any* finite pixel intersected it | An area with partly missing source data could be treated as fully comparable | Compute valid-area fraction per cell; require >= 0.999999 from both rasters; drop partial cells from quantitative differences; incomplete coverage forces non-zero CLI status | One interior source NoData pixel triggers incomplete coverage |
| S02 | GHSL accepted any projected native raster | A 1 km or unrelated grid could be mislabeled as the 100 m source | Native resolution within 1 m of 100 m required, still manually verify product/band/epoch | 1 km synthetic input rejected |
| S03 | A02 checked only the pixels where the application's first band had an unmasked value | A corrupted app-side mask could remove failing pixels from the test set | Use independent valid-month count raster to define reference footprint, flag extra app-only pixels | One app-only masked pixel is detected |

## Test execution

- Command: `python -m pytest -q test_validation_scripts.py`.
- Result: **9 passed** in the isolated synthetic checker suite.
- No field GHSL or new Earth Engine export was supplied or used in these tests.
- `pytest-results.xml` contains executable test evidence; `SHA256SUMS.txt` records staged file hashes.

## Scientific boundaries

- GHSL native data are per-pixel quantities (residential population count or built-up m²), not population or built-up density. Summation must account for pixel/polygon intersection fraction.
- Spatial App's GHSL `fetch_ghsl_raster` reprojects into EPSG:4326 at a requested 100 m scale and selects the first band; a potential bias due to reprojection remains **unquantified** without corresponding real source raster and app-exported GeoTIFF.
- A complete geometric coverage check cannot recover observational missingness that the application has previously converted to zero (`unmask(0)`). The detector reports this separately.
- Six-band A02 comparisons require three perfectly aligned real exports. Source-layer equivalence (same year, monthly filter and exact raster grid) remains a manual gate.
- CI PASS on 9 tests confirms only checker behavior under the included cases, not V11 completion, GHSL field accuracy or A02 field validity.

## Source method references

- GHSL POP product: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL BUILT-S product: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- GHSL JRC open downloads: https://human-settlement.emergency.copernicus.eu/download.php
- Earth Engine resampling: https://developers.google.com/earth-engine/guides/resample
- ExactExtract operations: https://isciences.github.io/exactextract/operations.html

## Staging policy

Do not open a new micro-PR for this report alone. The corrected tools and tests are held for the owner's **one consolidated future review PR**. The package contains no GHSL tiles or other large geospatial datasets and no credentials.

<!-- END ORIGINAL SOURCE 016 -->


---

## Source 017: `06_LIBRARY_STAGING_EXACT_ORIGINALS/REVIEW_FINDINGS_2026-11-15.md`

**Original bytes:** 4,122 · **SHA-256:** `0ce9c8d7b12bc8066a5b1899516f55587a7e0ec3c9772be84c2611f48b1e69dd` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 017 -->
# Spatial App — Independent checker follow-up (15 November 2026)

## Decision

Continue staging changes for one future major-review PR; no new PR and no changes to production formulas. An area-only comparator can fail to detect a spatial identity mismatch for equal-area cells. Fix the independent checking tools before interpreting later GHSL comparisons.

## Finding S04 — same-area ID swaps bypass the previous area gate

- Observed in: both the staged GHSL comparator and the existing `validation/cross_location/compare_raster_cells.py` checked grid IDs, polygon counts and areas, but not **per-ID geographic identity**.
- Why this matters: two full 500 m grid cells both have `area_km2 = 0.25`; their polygon-to-CSV pairing can be wrong while an area and ID validation still reports success.
- Remedy staged: check rounded UTM centroids (`centroid_x_epsgNNNN` and `centroid_y_epsgNNNN`, tolerance 0.051 m) and geographic centroids (`centroid_lon`, `centroid_lat`, tolerance 0.00000051°) against the independently recreated clipped GADM polygon for each `grid_id`.
- Negative control: interchange the exported centroid coordinates of two equal-area cells while leaving `grid_id` and `area_km2` untouched. Both staged comparators reject the mismatch. Missing centroid metadata also forces explicit failure.
- Production code and CSV schemas: **unchanged**; required centroid columns already exist in normal current application exports.

## Historical Yanqing field regression

A replay of the updated `compare_raster_cells.py` used:

- full-precision GADM 4.1 Yanqing GeoJSON from the historical private archive;
- the VIIRS 2020 annual reference GeoTIFF from the same archive;
- the **original** application 2020 500 m CSV with UTM/WGS84 centroids;
- 500 m clipped UTM grid, matching the existing baseline inference geometry.

Results: **8,333/8,333 cells** passed the raster–polygon NTL comparison within 0.00005 nW/cm²/sr (MAE 0.0000250230; maximum absolute error 0.0000499933). All **8,333/8,333 cells** also met the geographic centroid identity rounding tolerances. The maximum UTM-x and UTM-y rounding discrepancies were 0.049872 m and 0.049979 m; maximum longitude/latitude discrepancy was below 0.0000005°. The source and script checksums are retained in `yanqing_2020_regression_metrics.json` and `SHA256SUMS.txt`.

This is an **independent recomputation using archived field input** from Yanqing, not new field sampling. A controlled same-area swap of two historical full-size cells was correctly rejected by the new check. It does not establish V11 across contrasting locations or GHSL product equality.

## Finding S05 — fractional monthly observation counts

The staged A02 checker checked count in `[0,12]` but did not reject, for example, `2.5` months of annual valid observation support. Such a value can arise if a reference count raster is improperly interpolated. The checker now requires integral valid-month counts, and the corrupted synthetic example is rejected.

## Scope availability on archived VIIRS rasters

Historical annual medians and month-count reference rasters have 30,814 pixels per year (2014 and 2020). In both cases all count pixels recorded 12 valid months and no median pixels were masked. The 2014 raster contained one negative valid median; 2020 had none. Neither case contained measured-zero medians or fewer-than-three-month support. **These real images cannot test the A02 data-semantics edge cases involving genuine missing observations.**

## Acceptance log

- **11 passed** — `python -m pytest -q test_validation_scripts.py` (synthetic oracle and negative-control tests).
- **8,333 passed** — Yanqing 2020 archived field raster/polygon comparator and per-ID centroid verification.
- **Expected fail** — spatial-identity negative control on two same-area historical cell IDs.
- **Not run / PENDING** — GHSL native JRC 100 m versus real Earth Engine reprojected raster; A02 true six-band export; Shanghai/Bao'an/Qimen independent per-cell validation; Cloud benchmark.
- No new PR, no code modification in `ntl/`, and no large GeoJSON/GeoTIFF committed.

<!-- END ORIGINAL SOURCE 017 -->


---

## Source 018: `06_LIBRARY_STAGING_EXACT_ORIGINALS/SHANGHAI_GHSL_INDEPENDENT_FIELD_EVIDENCE_2026-11-15.zip::SHANGHAI_GHSL_POST_DEPLOY_EVIDENCE_2026-11-15.md`

**Original bytes:** 4,754 · **SHA-256:** `e46979acb604d88486d008e973c005eb5f89059f765e5b8cfeadfedee21b5cec` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 018 -->
# Shanghai GHSL 2020 — independent post-deployment validation

Date: 2026-11-15. Scope: Shanghai Core (`CHN.24.1.10_1`), year 2020, 500 m grid, GHSL built-surface and population. Evidence relates to the post-merge #26 application figures shown by the user; it does **not** re-run V11 or Yanqing.

## Direct observations from the deployed UI

- GHSL built surface: Spearman rho **-0.079**, 95% block-bootstrap CI **[-0.22, 0.09]**, top-quartile AUC **0.395**; scatter plot displayed.
- GHSL population: Spearman rho **0.136**, 95% block-bootstrap CI **[-0.03, 0.27]**, top-quartile AUC **0.576**; scatter plot displayed.
- The old 100%-zero proxy and `NaN` results no longer appear in this deployment output.

## Independent reference calculation

Inputs: original Earth Engine native-Mollweide 100 m GHSL TIFFs previously exported to Drive; the application's Shanghai 500 m grid GeoJSON and NTL CSV previously provided by the user (886 cells). No `ntl` app imports, no `exactextract` implementation dependency.

Algorithm:
1. Load GeoJSON and CSV, sort by `grid_id`, verify corresponding NTL values.
2. Project actual cell polygons from EPSG:4326 to the raster's ESRI:54009 using GeoPandas/PROJ. **Keep the GHSL raster on its original 100 m source grid.**
3. For each grid polygon, compute Shapely polygon overlap with each candidate GHSL pixel: `sum(pixel_amount * intersection_area / 10_000 m²)`.
4. Retain original 500 m cell area in km²; derive proxy density = GHSL sum / area.
5. Apply the same core-cell eligibility rule, `area_km2 >= 0.99 * (500 / 1000)^2`, giving **715 / 886** eligible cells.
6. Calculate Spearman ranks with average ties, Mann–Whitney top-quartile AUC, and 200 block-bootstrap Spearman draws with 5 x 5 cells, seed 42 and EPSG:32651 grid-centroid coordinates. 

## Independent results

| Metric | Built surface | Population |
|---|---:|---:|
| Eligible core cells | 715 | 715 |
| Core cells with positive GHSL proxy | 715 | 715 |
| GHSL core zero share | 0% | 0% |
| Spearman rho | -0.0794533 | 0.1358105 |
| Block-bootstrap 95% CI | [-0.220123, 0.086086] | [-0.029628, 0.271008] |
| Top-quartile AUC | 0.394636 | 0.576274 |
| Core median GHSL density | 353,036 m²/km² | 33,799 people/km² |
| Core median NTL | 41.2612 | 41.2612 |

All three key metrics (rho, CI endpoints, AUC) agree with both deployed UI screenshots to their displayed rounding precision. Thus the deployed application's metrics have been independently reproduced from the archived native-resolution GHSL field data. This is strong evidence that the previously broken raster/vector CRS alignment is now functioning correctly in Shanghai.

## Scientific interpretation and limitations

The Shanghai inner core has very weak monotonic association between VIIRS nighttime radiance and GHSL built surface (weak slightly negative rho) or GHSL population (weak slightly positive rho). Both displayed 95% Spearman confidence intervals contain zero; the observed evidence does not establish a reliably nonzero monotonic association. The AUC comparisons are descriptive, not separately tested here. GHSL counts and built surface are **not** direct nighttime light ground truth, and a dense urban core can have limited spatial differentiation in radiance, different daytime activity, commercial intensity or housing intensity. Avoid claiming that this disproves VIIRS or that the GHSL data are bad.

The independent calculation **does not** compare every post-deployment application's GHSL per-cell result one-to-one, since per-cell GHSL arrays were not exported from the live app. Metrics matching at screenshot precision do not prove pixel-for-pixel identity. It does independently reproduce the aggregate validation pipeline. The saved TIFFs were exported via Earth Engine `Export.image.toDrive`, while the deployed app now uses `ee.data.computePixels` to fetch a native grid: a matching statistical result offers corroboration but not an exhaustive byte-level equivalence proof.

No actual live Cloud RSS/runtime JSON and no post-merge A02 per-cell CSV have been assessed in this task. Separate post-deployment A02 and runtime acceptance gates remain open. Cross-location GHSL evaluation should be tested on regions with different urban/rural composition without altering the statistical estimators based solely on Shanghai's low rho.

## Included evidence

- `SHANGHAI_GHSL_INDEPENDENT_CELL_VALIDATION_2026-11-15.json`: exact summary metrics.
- `shanghai_ghsl_independent_validation_2026_11.py`: independent source-grid overlap and matching statistics, no Spatial App imports.
- `SHANGHAI_GHSL_POST_DEPLOY_EVIDENCE_2026-11-15.md`: this report.
- Source raster/CSV/GeoJSON are **not** redistributed in this ZIP; they remain user-supplied separate inputs.

<!-- END ORIGINAL SOURCE 018 -->


---

## Source 019: `06_LIBRARY_STAGING_EXACT_ORIGINALS/SHANGHAI_GHSL_POST_DEPLOY_EVIDENCE_2026-11-15.md`

**Original bytes:** 4,754 · **SHA-256:** `e46979acb604d88486d008e973c005eb5f89059f765e5b8cfeadfedee21b5cec` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 019 -->
# Shanghai GHSL 2020 — independent post-deployment validation

Date: 2026-11-15. Scope: Shanghai Core (`CHN.24.1.10_1`), year 2020, 500 m grid, GHSL built-surface and population. Evidence relates to the post-merge #26 application figures shown by the user; it does **not** re-run V11 or Yanqing.

## Direct observations from the deployed UI

- GHSL built surface: Spearman rho **-0.079**, 95% block-bootstrap CI **[-0.22, 0.09]**, top-quartile AUC **0.395**; scatter plot displayed.
- GHSL population: Spearman rho **0.136**, 95% block-bootstrap CI **[-0.03, 0.27]**, top-quartile AUC **0.576**; scatter plot displayed.
- The old 100%-zero proxy and `NaN` results no longer appear in this deployment output.

## Independent reference calculation

Inputs: original Earth Engine native-Mollweide 100 m GHSL TIFFs previously exported to Drive; the application's Shanghai 500 m grid GeoJSON and NTL CSV previously provided by the user (886 cells). No `ntl` app imports, no `exactextract` implementation dependency.

Algorithm:
1. Load GeoJSON and CSV, sort by `grid_id`, verify corresponding NTL values.
2. Project actual cell polygons from EPSG:4326 to the raster's ESRI:54009 using GeoPandas/PROJ. **Keep the GHSL raster on its original 100 m source grid.**
3. For each grid polygon, compute Shapely polygon overlap with each candidate GHSL pixel: `sum(pixel_amount * intersection_area / 10_000 m²)`.
4. Retain original 500 m cell area in km²; derive proxy density = GHSL sum / area.
5. Apply the same core-cell eligibility rule, `area_km2 >= 0.99 * (500 / 1000)^2`, giving **715 / 886** eligible cells.
6. Calculate Spearman ranks with average ties, Mann–Whitney top-quartile AUC, and 200 block-bootstrap Spearman draws with 5 x 5 cells, seed 42 and EPSG:32651 grid-centroid coordinates. 

## Independent results

| Metric | Built surface | Population |
|---|---:|---:|
| Eligible core cells | 715 | 715 |
| Core cells with positive GHSL proxy | 715 | 715 |
| GHSL core zero share | 0% | 0% |
| Spearman rho | -0.0794533 | 0.1358105 |
| Block-bootstrap 95% CI | [-0.220123, 0.086086] | [-0.029628, 0.271008] |
| Top-quartile AUC | 0.394636 | 0.576274 |
| Core median GHSL density | 353,036 m²/km² | 33,799 people/km² |
| Core median NTL | 41.2612 | 41.2612 |

All three key metrics (rho, CI endpoints, AUC) agree with both deployed UI screenshots to their displayed rounding precision. Thus the deployed application's metrics have been independently reproduced from the archived native-resolution GHSL field data. This is strong evidence that the previously broken raster/vector CRS alignment is now functioning correctly in Shanghai.

## Scientific interpretation and limitations

The Shanghai inner core has very weak monotonic association between VIIRS nighttime radiance and GHSL built surface (weak slightly negative rho) or GHSL population (weak slightly positive rho). Both displayed 95% Spearman confidence intervals contain zero; the observed evidence does not establish a reliably nonzero monotonic association. The AUC comparisons are descriptive, not separately tested here. GHSL counts and built surface are **not** direct nighttime light ground truth, and a dense urban core can have limited spatial differentiation in radiance, different daytime activity, commercial intensity or housing intensity. Avoid claiming that this disproves VIIRS or that the GHSL data are bad.

The independent calculation **does not** compare every post-deployment application's GHSL per-cell result one-to-one, since per-cell GHSL arrays were not exported from the live app. Metrics matching at screenshot precision do not prove pixel-for-pixel identity. It does independently reproduce the aggregate validation pipeline. The saved TIFFs were exported via Earth Engine `Export.image.toDrive`, while the deployed app now uses `ee.data.computePixels` to fetch a native grid: a matching statistical result offers corroboration but not an exhaustive byte-level equivalence proof.

No actual live Cloud RSS/runtime JSON and no post-merge A02 per-cell CSV have been assessed in this task. Separate post-deployment A02 and runtime acceptance gates remain open. Cross-location GHSL evaluation should be tested on regions with different urban/rural composition without altering the statistical estimators based solely on Shanghai's low rho.

## Included evidence

- `SHANGHAI_GHSL_INDEPENDENT_CELL_VALIDATION_2026-11-15.json`: exact summary metrics.
- `shanghai_ghsl_independent_validation_2026_11.py`: independent source-grid overlap and matching statistics, no Spatial App imports.
- `SHANGHAI_GHSL_POST_DEPLOY_EVIDENCE_2026-11-15.md`: this report.
- Source raster/CSV/GeoJSON are **not** redistributed in this ZIP; they remain user-supplied separate inputs.

<!-- END ORIGINAL SOURCE 019 -->


---

## Source 020: `06_LIBRARY_STAGING_EXACT_ORIGINALS/Spatial_App_A02_GHSL_Remaining_Field_Package.zip::README.md`

**Original bytes:** 5,568 · **SHA-256:** `c77f737d7a59562c5f476f3cc688dc62a1f87bcc3ba9f55ebd77c7afaa0a2140` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 020 -->
# Spatial App — Unresolved-field-evidence package (single future PR)

Date: 2026-11-15. Repository: `hoanfg/spatial-app` (main). **Private staging only**: no PR, no repository changes, no geospatial data copied into the repository. Historical Yanqing/V11/FDR/Moran findings are reused and were not recomputed.

## A02 `dq_status=unknown`: established facts vs open hypotheses

- All 17,177 app CSV cells for Shanghai, Bao'an and Qimen carry unknown A02 status, but independently checked NTL values remain valid. This is an **observed field failure**, not missing button presses.
- Production `cell_quality()` currently requires `src.count==6` and exact names `src.descriptions[1:] == QUALITY_BANDS`; failure silently gives NaN/unknown. This is an established failure mechanism.
- The 9 independent EE `Export.image.toDrive` TIFFs contain names (single-band `avg_rad` / `valid_month`). Therefore **do not claim** that the app's different `getDownloadURL(format='GEO_TIFF')` route necessarily strips names.
- The pending targeted patch adds a verified-producer **unlabeled six-band** fallback, validation of binary flags/month counts/mutual consistency, and explicit UI diagnostics if count/schema is truly wrong. Arbitrary user TIFFs, partly named/conflicting TIFFs, and 1-band TIFFs are never assumed to have quality bands. Preserve all existing NTL/LISA formulas.
- `ntl/semantics.py` is the proposed module replacement. `apply_a02_schema_patch.py` generates a **reviewable diff** from a real checkout, updating that module and the two downstream consumers in `app.py` plus `ntl/quality_ui.py`; the script does **not** modify a checkout without `--write`. This patch has **NOT been applied to the public GitHub repository**.
- New focused tests: `python -m pytest -q tests/test_a02_field_schema.py` → **8 passed** in the staging environment (Python 3.13, Rasterio 1.5.0). This is a focused regression, not full CI and not live EE proof.

## Exactly five new exports (GHSL and A02)

Open `validation/gee_a02_ghsl_field_exports_2020.js` in Google Earth Engine Code Editor. It creates **5 tasks** in Drive folder `spatial_app_field_validation_2020`:

1. `baoan_2020_a02_six_band_reference.tif` — production-equivalent six-band radiance/quality image, aligned to the *already exported* Bao'an 2020 reference TIFF.
2. `shanghai_2020_ghsl_built_native_100m.tif` — JRC GHSL built-surface 2020, **Earth Engine asset's native projection and affine transform**.
3. `shanghai_2020_ghsl_built_appstyle_4326_100m.tif` — same image reprojected with production `EPSG:4326`, scale 100m.
4. `shanghai_2020_ghsl_pop_native_100m.tif` — GHSL population count on source 100m projection.
5. `shanghai_2020_ghsl_pop_appstyle_4326_100m.tif` — matching production-style reprojection.

If EE splits files into same-named Drive folders, leave them intact: Drive search by folder and filename can locate them. No new CSV/GeoJSON is required; the existing Shanghai district 2020 CSV and GeoJSON are already available.

**Limits:** GHSL paired exports are *real EE GHSL field data* and permit measuring reprojection-related per-cell/region quantity shifts. They do not replace an independently downloaded JRC source tile for a full cross-provider replication. The A02 Drive export probes real six-band pixel semantics/labels, but does not observe the raw TIFF bytes returned to Streamlit Cloud by `getDownloadURL`; production schema status remains unknown until the targeted logging patch is deployed or a raw capture is obtained.

To audit GHSL, use the existing private staging tool `audit_ghsl_native_vs_reprojected.py` from the earlier v4 bundle (one run each `kind=built` and `kind=pop`). It compares exact fractional pixel-polygon sums, valid coverage and Spearman-rank movement. Do not compare global raster totals: use the clipped GADM cells and their complete-coverage flags.

## Streamlit Cloud — remaining operational gate

CI is not a memory benchmark. Real latency/peak RAM/HTTP failure analysis requires a run in Streamlit Community Cloud. The owner can open the app, select **Manage app** at bottom right, then download **Cloud logs**. Do not upload `.streamlit/secrets.toml`, credentials or personal-account tokens. Logs show errors but not necessarily peak RAM; a controlled, opt-in in-app profiler would be needed for exact RAM use. No RAM or latency PASS is claimed.

## Single-PR acceptance gate

- A02: Six-band GeoTIFF has correct schema, aligns with masked-median and months reference, no false distinction between missing / zero / negative; live application shows populated `dq_` fields after deploying fix. Any unknown schema is visible to the user.
- GHSL: Real **native vs appstyle** raster inputs have matching year/band/provenance and quantified per-cell disagreement. Decide whether the production GHSL `zonal_stat(sum)` needs a conservation-aware approach from *measured* results, not synthetic bias guesses.
- Cloud: Actual operational logs / measurements are reviewed with no unexplained failures.
- Only then prepare **one consolidated PR**, importing *selected* code and compact evidence summaries; keep large private data and source GeoTIFFs off GitHub.

## Public sources

- VIIRS: `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` (2020), `avg_rad` masked by `cf_cvg > 0`.
- JRC GHSL built-up `JRC/GHSL/P2023A/GHS_BUILT_S/2020` (`built_surface` m²/pixel).
- JRC GHSL population `JRC/GHSL/P2023A/GHS_POP/2020` (`population_count` persons/pixel).
- EE `Export.image.toDrive()` with `crsTransform` and `crs` explicitly documented for native-pixel alignment.

<!-- END ORIGINAL SOURCE 020 -->


---

## Source 021: `06_LIBRARY_STAGING_EXACT_ORIGINALS/Spatial_App_Consolidated_PR_Candidate_A02_GHSL_Performance_2026-11-15.zip::README.md`

**Original bytes:** 7,159 · **SHA-256:** `8610ab1372b8838eade489c22b7d676dc37e7824c6ce90c05ab46b230e8d6e5d` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 021 -->
# Spatial App — one-PR code candidate: A02, native GHSL, owner-visible performance

Date: 2026-11-15. Target: `hoanfg/spatial-app` `main` as observed on this date.
**Status: prepared and locally unit-tested, NOT pushed to GitHub, NOT Cloud-tested.**
This package is an addition to the **existing** `/Spatial-App/major-review-staging/` register. It is not another PR, branch or v5 validation exercise.

## Contents

- `ntl/semantics.py`: existing fail-closed A02 six-band schema fallback. Only a six-band download created through the application's own trusted producer can use unlabeled band order after logical and range checks. Other/mislabeled files fail closed.
- `ntl/ghsl_native.py`: GHSL native 100 m Mollweide source-grid window builder. Uses the true pixel CRS+affine, computes a bounded window and downloads with `crs_transform` + `dimensions`. Validates downloaded single-band GeoTIFF metadata before a zonal sum.
- `ntl/performance.py`: per-analysis self-service, low-overhead profiler. Measures full-pipeline wall time plus timed stages, sampled process RSS (Linux /proc; optional psutil fallback), and stage failures without exception text. Provides an expandable table and JSON/CSV downloads in Streamlit. Does **not** need Manage app or Cloud logs.
- `tests/test_a02_field_schema.py`, `tests/test_ghsl_native_grid.py`, `tests/test_runtime_performance.py`: focused unit tests; no Earth Engine account needed.
- `apply_consolidated_review_patch.py`: strict, fail-closed integration patch creator. Default creates a diff only. Targets current `app.py`, `ntl/quality_ui.py`, `ntl/lisa_ui.py`, `ntl/ee_extra.py`, `ntl/semantics.py` and adds new modules/tests. It does not commit, push or open PR.
- The original field-evidence files and user rasters stay in Drive / private Library, not in this ZIP.

## Local application (once the consolidated PR is ready for review)

From a **clean checkout** of this repository:

```bash
python /path/to/apply_consolidated_review_patch.py --repo /path/to/spatial-app
# Inspect generated single_review_candidate.diff.
python /path/to/apply_consolidated_review_patch.py --repo /path/to/spatial-app --write
python -m pytest -q tests/test_a02_field_schema.py tests/test_ghsl_native_grid.py tests/test_runtime_performance.py
python -m pytest -q tests
```

The apply script checks exact known source anchors and compiles changed Python files **before writing**. If it detects source drift, stop and reconcile; never bypass the guard by repeated broad string replacement. It is intended for a single consolidated PR with existing V11 verification and GHSL evidence, not a standalone commit.

## What the user will see after deployment

- After **Chạy phân tích** / **Run analysis**, the **LISA · Panel** view contains an expander **⏱️ Hiệu suất xử lý (không cần Cloud logs)**. It shows total pipeline wall time, time per stage and sampled process RAM and allows downloading a small JSON/CSV. When the full LISA or GHSL validation runs, the same recorder acquires further stage rows.
- Timed stages: boundary load, grid build, Earth Engine NTL fetch, NTL zonal mean, A02 quality extraction, Global Moran, Local Moran LISA, and GHSL native fetch / zonal sum / external proxy agreement. Optional Space-Time previous-year fetch is measured.
- If the main analysis fails, the failure-stage timings are still available in the screen's empty/result state, without exporting exception messages.
- The values are **process-wide Streamlit RSS**, not RAM isolated to one user, not a true instantaneous memory maximum, and not the platform's hidden RAM limit. Earth Engine timing is request/download wait observed by the app, not separate Earth Engine server compute CPU time. The sample interval is 0.1s and can miss sub-0.1s spikes.
- No background telemetry, network instrumentation endpoint, log secrets, raw query strings or user locations are collected or uploaded by the profiler. JSON/CSV are generated locally within the user's session on download.

## Source-grid GHSL correction and limits

`GHS_BUILT_S` and `GHS_POP` values are per-native-source-pixel amounts (m² and people), not densities. Current app uses nearest-neighbor EPSG:4326 100 m sampling then area-fraction-weighted `sum`, which duplicates quantities. The new fetch retains native equal-area 100 m pixel footprints and clips to the geographic ROI **before** requesting the bounded native lattice window. No arbitrary universal 16.5% scaling.

The downloaded TIFF must satisfy the expected native CRS, exact origin/transform, 100 m source pixel size, dimensions and single-band schema. Failure is surfaced rather than reverting to the biased EPSG:4326 sum. The original zonal `sum` computes fractional intersection of each native 100m pixel with 500m polygons.

**Important:** Earth Engine `Image.getDownloadURL` documents that `region` is ignored when both `crs` and `crs_transform` are provided. This module explicitly computes and supplies bounded `dimensions`; `image.clip(roi)` remains. Limit: 3,000,000 source pixels, and Earth Engine's 32 MB getDownloadURL cap still applies.

**Already measured real field data:** Shanghai 2020, common inset native vs app-style GHSL naive sum = +16.51428% built, +16.59686% population. `native_download_params()` was checked against the saved original source raster affine; the requested 331×202 window and 100m transform exactly match the independently exported native TIFF.

**Not yet proven:** a live Cloud `getDownloadURL()` response with the new parameters; real app cell-by-cell Spearman/AUC deltas after patch; memory/runtime under production concurrency. Keep scientific/operational PASS pending until these are measured on the deployed candidate.

## A02 qualification

The Bao'an six-band Earth Engine Drive export has correctly named six bands and 9–12 supported months, but the application uses a different `getDownloadURL` transport and 17,177 previous app rows still contain `dq_status=unknown`. The staged schema patch can expose the live cause and may recover fully unlabeled **trusted** six-band images when logical contracts pass. It is not proof that the Cloud's cause was definitively unlabeled bands. It does not change NTL zero-filling policy or Moran/LISA estimators.

## Suggested one-PR acceptance sequence

1. Integrate code in one clean branch, inspect diff, run the full test suite and record CI.
2. In an authenticated Streamlit Cloud instance, run **one** district (Shanghai or Bao'an), confirm A02 schema status and `dq_status` and export the new in-app performance JSON (no Manage app needed).
3. Run GHSL built and pop comparison there, inspect native grid CRS/affine, compare corrected per-grid sums and Spearman/AUC with independent source-GHSL calculations, use existing real files / hashes as baseline.
4. Check perf on a representative district and one larger region; report wall time and sampled process RSS with a note about shared sessions and short peaks. Decide RAM/time limits based on the actual Cloud tier, not made-up thresholds.
5. Only then merge one consolidated PR. Keep original TIFFs / user CSVs and GeoJSON files out of public GitHub.

<!-- END ORIGINAL SOURCE 021 -->


---

## Source 022: `06_LIBRARY_STAGING_EXACT_ORIGINALS/V11_2020_REFERENCE_RASTER_INTAKE_2026-11-14.md`

**Original bytes:** 3,993 · **SHA-256:** `e894614571169faf4ece973def016b0a4994ca0809a57b62f05bdc2dee429015` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 022 -->
# V11 — Independent reference GeoTIFF intake and consistency check

**Date:** 2026-11-14.  **Input:** Nine GeoTIFF exports discovered in two separate Google Drive folders, downloaded read-only.

**Scope:** Binary readability, source metadata, CRS/transform/pixel alignment, recorded SHA-256, and inter-product raster consistency. This is *not* independent zonal LISA/app CSV validation. No prior Yanqing test was rerun.

| Region | Raster shape | Valid reference pixels | Zero-month / invalid pixels | Monthly support counts | Georeference | Consistency |
|---|---:|---:|---:|---|---|---|
| Shanghai urban core | 49 × 62 | 3,038 | 0 | 12: 3,038 | aligned | consistent |
| Shenzhen Bao'an | 119 × 227 | 26,786 | 227 | 0: 227, 9: 1, 10: 26, 11: 780, 12: 25,979 | aligned | consistent |
| Anhui Qimen | 137 × 192 | 26,304 | 0 | 10: 127, 11: 17,136, 12: 9,041 | aligned | consistent |

## Critical interpretation

- Bao'an has 227 pixels in the raster bounding rectangle with 0 valid months, and these are **exactly** pixels whose annual radiance and masked median are NaN (the full southernmost raster row). This is consistent with a raster-export edge/footprint effect, **not proof of real no-observation inside the Bao'an GADM polygon**. Verify polygon intersection before asserting any missingness inside the district.
- Qimen has valid pixels with 10, 11, and 12 monthly composites; Bao'an has pixels with 9–12. This is genuine raster variation in per-pixel monthly-composite support across the bounding rectangle; monthly `cf_cvg>0` does not count cloud-free nights.
- All three exports use EPSG:4326; each group has the same pixel geometry, and the finite annual median values match the masked reference exactly.
- The nine raster files do **not** establish app CSV agreement, LISA, six-band A02 semantics, or a GHSL field benchmark. V11 remains **PARTIAL/PENDING** until app CSV and polygon-specific cross-check are available.

## File provenance (downloaded bytes)

| Region | Product | Bytes | SHA-256 |
|---|---|---:|---|
| shanghai_core | shanghai_core_viirs_2020_reference.tif | 11,031 | `74c825a461d73bf5c60eedb0c556ae704ed8e023307c07d320c48902ad755948` |
| shanghai_core | shanghai_core_valid_months_2020.tif | 1,273 | `8e0a207e5cd237c8ceaddb97c6b1c2a58764c207568a65fbc8c3dcca1e1cf7d3` |
| shanghai_core | shanghai_core_viirs_2020_masked_median.tif | 11,051 | `5572851b5ef9d97206539e212cdb7a3e4d7ace517dc78c1187934be6db9a455b` |
| shenzhen_baoan | shenzhen_baoan_viirs_2020_reference.tif | 78,976 | `04117f799a684d3fc5c6e7d9d3fc498cc1938e57fb3ff50b15699a7059a8f705` |
| shenzhen_baoan | shenzhen_baoan_valid_months_2020.tif | 1,960 | `4a720b105a0afda20d07710d1814cec863701eb349fbf012e586031dea70d999` |
| shenzhen_baoan | shenzhen_baoan_viirs_2020_masked_median.tif | 78,996 | `87d9f47830ab48ef12fba7957be4f2117c8752c7936f7eac410aa1751c201e8d` |
| anhui_qimen | anhui_qimen_viirs_2020_reference.tif | 33,350 | `dfac4c7e663cf42261458b8c1ffe88daea7ddae63e0ed7e46230fc75552070cb` |
| anhui_qimen | anhui_qimen_valid_months_2020.tif | 3,415 | `f89f9a446b04396ff9e10aa597b8f54ecbee5ed6d5593d0214c018d16d36e14a` |
| anhui_qimen | anhui_qimen_viirs_2020_masked_median.tif | 33,370 | `c8b34d2a3f174e4cf0efcb43123dc2089285389a16ce456fbe52f38e7ee41e85` |

Source Drive folders:

- https://drive.google.com/drive/folders/1ftAUuIXRoAD25_JsX-REbQ9CLQcp2c1w (8 files)
- https://drive.google.com/drive/folders/1WKfOszMt7nUJxEXfqmNCQ9MrXp-v1FAo (1 file)

## Next evidence needed

- Obtain and align 2020 / 500m app CSV exports for Shanghai core, Shenzhen Bao'an and Anhui Qimen, including `grid_id`, `area_km2`, `ntl_mean`, and full LISA columns.
- Independently intersect the existing GADM district boundaries and reference rasters to distinguish inside-polygon missingness from bounding-rectangle padding.
- Apply pre-specified 500m raster-cell comparison and then independent local-Moran/FDR comparison. Only those operations can move V11 from reference-intake to field-validated status.

<!-- END ORIGINAL SOURCE 022 -->


---

## Source 023: `06_LIBRARY_STAGING_EXACT_ORIGINALS/V11_CROSS_LOCATION_FIELD_VALIDATION_2026-11-15.md`

**Original bytes:** 6,952 · **SHA-256:** `465635eda5d2061ba1f63d86b5113419d0b3d324f24c46632d04f2ba2b89117f` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 023 -->
# V11 cross-location field validation: Shanghai, Bao'an, Qimen

Date: 15 November 2026
**Status: PARTIAL FIELD VERIFIED.** This is new evidence for the three V11 target locations, not a rerun of Yanqing.

## Scope and provenance

- Inputs: 6 CSVs exported from spatial-app (one NTL and one LISA CSV for each locality), 9 original 2020 VIIRS GeoTIFFs exported independently by the user from Google Earth Engine and retrieved from two Google Drive folders.
- Original boundaries: GADM v4.1 districts represented in the repository `hoanfg/spatial-app`; this run **did not** materialize the three boundary GeoJSON files into the analysis runtime. Consequently the exact geometry of cut/edge cells could not be reconstructed independently here.
- Validation program is separate from the production `ntl.zonal` and `ntl.lisa_core` imports. Input SHA-256 fingerprints are recorded in `V11_CROSS_LOCATION_INPUT_MANIFEST_2026-11-15.json`.
- VIIRS reference dataset: `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG`, year 2020; reference median with `cf_cvg > 0`, exported EPSG:4326 at scale 463.83 m. App CSV: year 2020, UTM 500 m cells, raw NTL.

## Independent numeric results

### NTL raster-to-cell comparison

For every **unclipped 500 m square**, the benchmark rebuilds the square in UTM from its gridded CSV centroid, transforms its polygon to EPSG:4326, intersects it with the independent reference raster pixel polygons, and recomputes an area-weighted radiance mean (clipping valid negative radiance at zero). This is not a copy of production `ntl_mean`.

| Location | App cells | Full-square cells independently compared | Pass at ±0.00005 | MAE | Max absolute error |
|---|---:|---:|---:|---:|---:|
| Shanghai | 886 | 706 | 706/706 | 0.000025472 | 0.000049957 |
| Bao'an | 7,148 | 6,131 | 6,131/6,131 | 0.000025034 | 0.000049998 |
| Qimen | 9,143 | 8,493 | 8,493/8,493 | 0.000024630 | 0.000049994 |

**Aggregate:** 15,330/15,330 full-square cells match to the four-decimal CSV rounding bound. **Not tested here:** 1,847 cut/partial polygon cells; these require the exact GADM boundary polygons. Do not report all 17,177 cells as independently raster-validated.

### LISA deterministic checks

The independent checker creates Queen adjacency with a dictionary of 500 m UTM grid indices, excludes cells below 99% of 0.25 km², recomputes z-scores from the rounded CSV NTL values, calculates local Moran observed I and spatial lag, checks raw quadrants, and applies a separately coded Benjamini–Hochberg step-up procedure to every exported p-value.

| Location | Local I checked | Queen neighbor differences | BH-FDR significant | FDR flag differences | I max abs difference | Raw quadrant differences |
|---|---:|---:|---:|---:|---:|---:|
| Shanghai | 715 | 0 | 159 | 0 | 0.0000519 | 0 |
| Bao'an | 6,185 | 0 | 2,848 | 0 | 0.0000573 | 0 |
| Qimen | 8,532 | 0 | 869 | 0 | 0.0030472 | 1 |

- All three NTL CSVs and respective LISA CSVs are identical across their common first 32 columns and match one-to-one on `grid_id`.
- All exported BH-FDR significant flags agree with the independently recomputed step-up threshold. **This is a consistency check of exported p-values; it does not itself validate Monte Carlo p-generation.**
- **One raw quadrant disagreement:** Qimen `grid_id=2070`, where NTL rounds to `0.2944` and the recomputed z-score is approximately `-0.0000828` (near zero). The export reports `High-High`, while recomputing with rounded CSV yields `Low-High`. Its `lisa_p_sim=0.182`, its final class is `Not Significant`, and **no final significance or HH/LL label is affected**. The difference is consistent with sensitivity to input rounding, not independently proof of a production error.

### Conditional Monte Carlo replication on genuinely new geographical cases

An independent NumPy RNG with 999 conditional draws per focal cell and distinct sampled nonfocal neighbors was run on a stratified sample of exported p-values in each region. Seeds intentionally differ from the app. A doubled smaller-tail inclusive p-value was compared with `lisa_p_sim` (the denominator of local I cancels in tail comparison).

| Location | Independently resimulated cells | Pearson correlation with exported p | MAE of p | Disagreement for raw p < 0.05 |
|---|---:|---:|---:|---:|
| Shanghai | 387 | 0.99624 | 0.0141 | 7 |
| Bao'an | 400 | 0.99599 | 0.0146 | 12 |
| Qimen | 400 | 0.99557 | 0.0145 | 10 |

- Total: **1,187** resimulated cells. The sample was intentionally stratified by reported p-value ranges and is not a probability sample of all cells.
- Small p-value and raw threshold differences are expected under distinct Monte Carlo draws; these are not exact fixed-seed equality tests. The BH-FDR comparisons in the previous table were performed separately on all stored p-values.

### A02 observational quality is not verified in the live exports

- **All 17,177 cells** have `dq_status=unknown`; none has finite `dq_observed_fraction`, `dq_mean_valid_months`, or the other per-cell observational quality indicators.
- This is observed in the actual spatial-app CSV exports, not inferred from synthetic tests. It demonstrates that the A02 observational metadata contract is **not usable in these six outputs**, although the primary band NTL values match.
- The cause cannot be established from the CSV alone; candidate explanations include the downloaded GeoTIFF missing expected band names or an unexpected single-band TIFF. Inspect an actual live app-downloaded TIFF with `rasterio` for band count and descriptions before changing production semantics.

## Decision and outstanding verification

- **V11: PARTIAL FIELD VERIFIED.** VIIRS NTL on 15,330 full 500 m cells and deterministic LISA (Queen/Local Moran/BH) across three new regions have strong independent support. Independent conditional Monte Carlo samples agree closely.
- **Open: 1,847 cut cells.** Their polygon geometry must be reconstructed from exact GADM source to independently verify the area-weighted means; matched full cells must not be conflated with border cells.
- **Open: A02 per-cell quality metrics.** All relevant columns are unknown in real exports; requires production output six-band TIFF metadata inspection, a minimal justified fix if necessary, and one real rerun.
- **Open: GHSL native-grid comparison and Cloud operational metrics.** No new GHSL/Cloud evidence was generated by this V11 audit; do not change their prior status.
- **No change to production code and no new PR.** Keep this evidence as a single set of inputs for the already planned consolidated Major Review.

## Reproducibility

Run `v11_field_validation_2026_11.py` and `v11_independent_permutation_sample.py` with the 6 CSVs and 9 reference TIFFs as named in the input manifest. The full-square check requires pandas, NumPy, rasterio, Shapely, and pyproj; it does not need `exactextract` or the app code. The Monte Carlo sample uses NumPy and pandas. Output JSONs record all summary metrics.


<!-- END ORIGINAL SOURCE 023 -->


---

## Source 024: `06_LIBRARY_STAGING_EXACT_ORIGINALS/V11_CROSS_LOCATION_VALIDATION_EVIDENCE_2026-11-15.zip::V11_CROSS_LOCATION_FIELD_VALIDATION_2026-11-15.md`

**Original bytes:** 6,952 · **SHA-256:** `465635eda5d2061ba1f63d86b5113419d0b3d324f24c46632d04f2ba2b89117f` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 024 -->
# V11 cross-location field validation: Shanghai, Bao'an, Qimen

Date: 15 November 2026
**Status: PARTIAL FIELD VERIFIED.** This is new evidence for the three V11 target locations, not a rerun of Yanqing.

## Scope and provenance

- Inputs: 6 CSVs exported from spatial-app (one NTL and one LISA CSV for each locality), 9 original 2020 VIIRS GeoTIFFs exported independently by the user from Google Earth Engine and retrieved from two Google Drive folders.
- Original boundaries: GADM v4.1 districts represented in the repository `hoanfg/spatial-app`; this run **did not** materialize the three boundary GeoJSON files into the analysis runtime. Consequently the exact geometry of cut/edge cells could not be reconstructed independently here.
- Validation program is separate from the production `ntl.zonal` and `ntl.lisa_core` imports. Input SHA-256 fingerprints are recorded in `V11_CROSS_LOCATION_INPUT_MANIFEST_2026-11-15.json`.
- VIIRS reference dataset: `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG`, year 2020; reference median with `cf_cvg > 0`, exported EPSG:4326 at scale 463.83 m. App CSV: year 2020, UTM 500 m cells, raw NTL.

## Independent numeric results

### NTL raster-to-cell comparison

For every **unclipped 500 m square**, the benchmark rebuilds the square in UTM from its gridded CSV centroid, transforms its polygon to EPSG:4326, intersects it with the independent reference raster pixel polygons, and recomputes an area-weighted radiance mean (clipping valid negative radiance at zero). This is not a copy of production `ntl_mean`.

| Location | App cells | Full-square cells independently compared | Pass at ±0.00005 | MAE | Max absolute error |
|---|---:|---:|---:|---:|---:|
| Shanghai | 886 | 706 | 706/706 | 0.000025472 | 0.000049957 |
| Bao'an | 7,148 | 6,131 | 6,131/6,131 | 0.000025034 | 0.000049998 |
| Qimen | 9,143 | 8,493 | 8,493/8,493 | 0.000024630 | 0.000049994 |

**Aggregate:** 15,330/15,330 full-square cells match to the four-decimal CSV rounding bound. **Not tested here:** 1,847 cut/partial polygon cells; these require the exact GADM boundary polygons. Do not report all 17,177 cells as independently raster-validated.

### LISA deterministic checks

The independent checker creates Queen adjacency with a dictionary of 500 m UTM grid indices, excludes cells below 99% of 0.25 km², recomputes z-scores from the rounded CSV NTL values, calculates local Moran observed I and spatial lag, checks raw quadrants, and applies a separately coded Benjamini–Hochberg step-up procedure to every exported p-value.

| Location | Local I checked | Queen neighbor differences | BH-FDR significant | FDR flag differences | I max abs difference | Raw quadrant differences |
|---|---:|---:|---:|---:|---:|---:|
| Shanghai | 715 | 0 | 159 | 0 | 0.0000519 | 0 |
| Bao'an | 6,185 | 0 | 2,848 | 0 | 0.0000573 | 0 |
| Qimen | 8,532 | 0 | 869 | 0 | 0.0030472 | 1 |

- All three NTL CSVs and respective LISA CSVs are identical across their common first 32 columns and match one-to-one on `grid_id`.
- All exported BH-FDR significant flags agree with the independently recomputed step-up threshold. **This is a consistency check of exported p-values; it does not itself validate Monte Carlo p-generation.**
- **One raw quadrant disagreement:** Qimen `grid_id=2070`, where NTL rounds to `0.2944` and the recomputed z-score is approximately `-0.0000828` (near zero). The export reports `High-High`, while recomputing with rounded CSV yields `Low-High`. Its `lisa_p_sim=0.182`, its final class is `Not Significant`, and **no final significance or HH/LL label is affected**. The difference is consistent with sensitivity to input rounding, not independently proof of a production error.

### Conditional Monte Carlo replication on genuinely new geographical cases

An independent NumPy RNG with 999 conditional draws per focal cell and distinct sampled nonfocal neighbors was run on a stratified sample of exported p-values in each region. Seeds intentionally differ from the app. A doubled smaller-tail inclusive p-value was compared with `lisa_p_sim` (the denominator of local I cancels in tail comparison).

| Location | Independently resimulated cells | Pearson correlation with exported p | MAE of p | Disagreement for raw p < 0.05 |
|---|---:|---:|---:|---:|
| Shanghai | 387 | 0.99624 | 0.0141 | 7 |
| Bao'an | 400 | 0.99599 | 0.0146 | 12 |
| Qimen | 400 | 0.99557 | 0.0145 | 10 |

- Total: **1,187** resimulated cells. The sample was intentionally stratified by reported p-value ranges and is not a probability sample of all cells.
- Small p-value and raw threshold differences are expected under distinct Monte Carlo draws; these are not exact fixed-seed equality tests. The BH-FDR comparisons in the previous table were performed separately on all stored p-values.

### A02 observational quality is not verified in the live exports

- **All 17,177 cells** have `dq_status=unknown`; none has finite `dq_observed_fraction`, `dq_mean_valid_months`, or the other per-cell observational quality indicators.
- This is observed in the actual spatial-app CSV exports, not inferred from synthetic tests. It demonstrates that the A02 observational metadata contract is **not usable in these six outputs**, although the primary band NTL values match.
- The cause cannot be established from the CSV alone; candidate explanations include the downloaded GeoTIFF missing expected band names or an unexpected single-band TIFF. Inspect an actual live app-downloaded TIFF with `rasterio` for band count and descriptions before changing production semantics.

## Decision and outstanding verification

- **V11: PARTIAL FIELD VERIFIED.** VIIRS NTL on 15,330 full 500 m cells and deterministic LISA (Queen/Local Moran/BH) across three new regions have strong independent support. Independent conditional Monte Carlo samples agree closely.
- **Open: 1,847 cut cells.** Their polygon geometry must be reconstructed from exact GADM source to independently verify the area-weighted means; matched full cells must not be conflated with border cells.
- **Open: A02 per-cell quality metrics.** All relevant columns are unknown in real exports; requires production output six-band TIFF metadata inspection, a minimal justified fix if necessary, and one real rerun.
- **Open: GHSL native-grid comparison and Cloud operational metrics.** No new GHSL/Cloud evidence was generated by this V11 audit; do not change their prior status.
- **No change to production code and no new PR.** Keep this evidence as a single set of inputs for the already planned consolidated Major Review.

## Reproducibility

Run `v11_field_validation_2026_11.py` and `v11_independent_permutation_sample.py` with the 6 CSVs and 9 reference TIFFs as named in the input manifest. The full-square check requires pandas, NumPy, rasterio, Shapely, and pyproj; it does not need `exactextract` or the app code. The Monte Carlo sample uses NumPy and pandas. Output JSONs record all summary metrics.


<!-- END ORIGINAL SOURCE 024 -->


---

## Source 025: `06_LIBRARY_STAGING_EXACT_ORIGINALS/V11_EDGE_COMPLETION_2026-11-15.md`

**Original bytes:** 4,368 · **SHA-256:** `4cdb1b84cf0ceb2cc970560c699967971d169da568840a1a67c3892221c66896` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 025 -->
# V11 — Cross-location 2020 edge-cell validation completion

Date: 15 November 2026. Repository: `hoanfg/spatial-app`. **Private staging evidence; not a new PR.**

## Scope and evidence boundary

- **New analysis only:** 1,847 clipped/partial 500 m polygons that were excluded from the earlier 15,330-cell independent raster check. No previously verified full-cell zonal computations were rerun.
- The new polygon inputs are the **three user-exported application GeoJSONs**. Their IDs, areas, centroids and `ntl_mean` exactly agree with the corresponding user CSVs (all 17,177 IDs), and their geometries are nonempty/valid. The independent VIIRS raster source is the 2020 Earth Engine reference export; the integration routine does not import any `spatial-app` zonal code.
- Pixel-by-polygon intersections are computed in the EPSG:4326 GeoTIFF plane (as in the raster zonal coverage definition); masked/nonfinite values are skipped and valid negative median radiances clipped at zero, matching the legacy NTL policy. All new edge polygons have valid reference raster coverage.

## New numerical results (edge cells only)

| Case | Clipped cells checked | Within strict 0.00005 | Strict exceedances | Maximum absolute error | Within 0.0000501 |
|---|---:|---:|---:|---:|---:|
| Shanghai / Nội đô Thượng Hải | 180 | 180 | 0 | 0.00004959946 | 180 |
| Shenzhen / Bao'an | 1,017 | 1,016 | 1 | 0.00005003932 | 1,017 |
| Huangshan / Qimen | 650 | 650 | 0 | 0.00004993913 | 650 |
| **Total** | **1,847** | **1,846** | **1** | **0.00005003932** | **1,847** |

The **one** strict exceedance is `Bao'an grid_id=628`, area 0.010610 km², CSV `ntl_mean=18.8768`, independent raster overlay `18.876850039319148`. Difference: `0.000050039319148`, exceeding the four-decimal half-bin (`0.00005`) by `0.000000039319148` (3.93 × 10⁻⁸).

This is a **borderline numerical/rounding discrepancy**, not evidence of materially incorrect radiance extraction. It is retained explicitly. With the stated additive 0.0000001 floating-point allowance, 1,847/1,847 edge cells pass. This does not override or re-label the strict comparison: **1 strict exception remains**.

## Combined interpretation of prior and newly completed V11 checks

| Evidence component | Current interpretation |
|---|---|
| Existing 15,330 whole-cell raster comparisons | Previously verified within strict four-decimal CSV rounding, reused unchanged |
| New 1,847 boundary-clipped raster comparisons | 1,846 strict pass + 1 tiny rounding-boundary exception; all 1,847 within 0.0000501 |
| All 17,177 app cells (NTL raster consistency) | No material discrepancy detected at output precision; nuanced one-cell strict exception above |
| Prior independent Queen adjacency / Local I / BH-FDR | Preserved, not recomputed |
| A02 per-cell observation support | **Not validated:** all 17,177 `dq_status=unknown`; tracked separately |
| GHSL native-grid conservation / Cloud benchmark | **Still pending; unrelated to V11 NTL validation** |

**Important independence limitation:** the reference radiance raster is external, but the boundary-clipped polygon geometries are application-exported GeoJSON. Their aggregate geographic area and bounding box were separately checked against GADM-curated source metadata on GitHub (GIDs: `CHN.24.1.10_1`, `CHN.6.15.1_1`, `CHN.1.11.1_1`). This is not a source-boundary, vertex-by-vertex reconstruction of every polygon. Prior GADM provenance audits remain in force and are not duplicated here.

## Input provenance and reproducibility

All raw GeoJSON files stay outside the public repository; do not commit multi-megabyte polygon datasets by default. Original user CSVs and external reference TIFFs likewise remain private. The edge metrics JSON records SHA-256 for each of the nine newly used inputs (3 GeoJSONs, 3 NTL CSVs, 3 reference TIFFs). Per-cell edge residual CSVs (1,847 records combined) are included only in the private staging evidence ZIP. Independently re-run `v11_edge_only_independent.py` on those exact files to reproduce the results.

**Disposition:** V11 2020 cross-location NTL/LISA scientific numerical field validation is complete in the stated scope, with one explicit near-rounding strict exception; this is **not** an A02 or GHSL field PASS. Hold compact evidence for the next single consolidated major-review PR, rather than opening a new PR now.

<!-- END ORIGINAL SOURCE 025 -->


---

## Source 026: `06_LIBRARY_STAGING_EXACT_ORIGINALS/V11_EDGE_ONLY_PRIVATE_EVIDENCE_2026-11-15.zip::A02_DQ_UNKNOWN_FIELD_FINDING_2026-11-15.md`

**Original bytes:** 4,362 · **SHA-256:** `b4484af154e06a57d044c7e9ea69bfda29867de2968c625eb9eb04b0e022777b` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 026 -->
# A02 — real CSV `dq_status=unknown` field defect / root-cause investigation

Date: 15 November 2026. Repository: `hoanfg/spatial-app`. **Carry forward to the ONE consolidated Major Review PR; not a new PR.**

## Reproducible observed symptom

All 17,177 newly exported 2020 cell records across Shanghai (886), Bao'an (7,148) and Qimen (9,143) have `dq_status=unknown`. The five per-cell columns (`dq_observed_fraction`, `dq_negative_fraction`, `dq_zero_fraction`, `dq_mean_valid_months`, `dq_low_month_fraction`) are all empty. Separately, `dq_stat_missing=False`, and independent VIIRS pixel-overlap checks validate the main radiance values. No evidence suggests a forgotten UI action caused these particular empty columns.

## Exact code path / confirmed failure mode

1. `app.py:fetch_ntl_raster()` creates `annual_image_with_quality(col.map(_mask_cloud_free), roi)`, and downloads the GeoTIFF with `getDownloadUrl`. The ZIP branch selects its first `.tif` if a ZIP is returned.
2. `app.py:run_pipeline()` calls `cell_quality(tif_bytes, grid_wgs)` automatically as part of the core computation; that result is joined into `grid_utm`.
3. `ntl/semantics.py:cell_quality()` accepts the quality bands **only if** `src.count == 6` AND `tuple(src.descriptions[1:]) == QUALITY_BANDS` in exact order. When the condition is false, every `dq_*` numerical field becomes `NaN`, followed by `dq_status=unknown`, without a visible schema-error message.
4. `app.py:export_df` joins all `grid_utm` `dq_` columns; `ntl/lisa_ui.py` incorporates `export_df` into the downloadable `*_lisa_cells.csv`. The extra buttons in `ntl/quality_ui.py` (observation count, negative clipping sensitivity, GHSL validation) are optional **additional region-level diagnostics**. They do not populate these automatically generated per-cell fields.
5. `tests/test_data_semantics.py` writes a synthetic six-band GeoTIFF and explicitly assigns the expected band descriptions (`dst.set_band_description(i,name)`), so the test does NOT establish that live Earth Engine GeoTIFF delivery satisfies the description schema.

## Competing explanations to distinguish with one live capture

- The application may receive a six-band TIFF whose `src.descriptions[1:]` are absent or normalized differently.
- The application may receive fewer than six bands (e.g., download format / unexpected ZIP grouping) or an alternative schema.
- Stale deployed app version or an obsolete cached raster may also produce `unknown`; do not declare this hypothesis false without checking deployment commit and the `fetch_ntl_raster` cache/version.

**Current evidential status:** the deterministic code branch that generates `unknown` has been established, and all three field CSVs exhibit its output. The exact **live six-band `src.count` and `src.descriptions` remain unobserved** because the application-requested TIFF bytes were not captured. Therefore it is *not yet scientifically defensible* to state that Earth Engine definitely stripped the descriptions.

## Targeted corrective patch (one PR only, after confirming live raster schema)

1. Add a safe diagnostic at the network-to-raster interface: band count, descriptions, any ZIP members, and cache/deployment provenance (no credentials or raw raster upload required). Do not silently downgrade unrecognized schema to fully unknown without explaining the reason to the user.
2. Confirm band 1 exactly matches the pre-A02 legacy NTL contract at equal spatial settings.
3. Map valid six-band values to the known ordered semantic schema only if the producer provenance is established; refuse arbitrary six-band products instead of trusting band count alone. Explicitly distinguish absent label metadata from genuinely missing observation pixels.
4. Add one focused regression covering the **actual field condition** (e.g. nameless six-band geotiff) rather than increasing redundant synthetic test count, and confirm that known missing / zero / negative cases preserve intended semantics.
5. Perform field validation on an Earth Engine raster containing **genuine zero-support observations within the analysis polygon** before declaring A02 scientifically PASS.

**Decision:** retain the bug finding and scoped patch proposal in private staging for the user's single consolidated PR; do not open an isolated PR, alter NTL zero-fill policy, or claim A02 is fixed.

<!-- END ORIGINAL SOURCE 026 -->


---

## Source 027: `06_LIBRARY_STAGING_EXACT_ORIGINALS/V11_EDGE_ONLY_PRIVATE_EVIDENCE_2026-11-15.zip::V11_EDGE_COMPLETION_2026-11-15.md`

**Original bytes:** 4,368 · **SHA-256:** `4cdb1b84cf0ceb2cc970560c699967971d169da568840a1a67c3892221c66896` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 027 -->
# V11 — Cross-location 2020 edge-cell validation completion

Date: 15 November 2026. Repository: `hoanfg/spatial-app`. **Private staging evidence; not a new PR.**

## Scope and evidence boundary

- **New analysis only:** 1,847 clipped/partial 500 m polygons that were excluded from the earlier 15,330-cell independent raster check. No previously verified full-cell zonal computations were rerun.
- The new polygon inputs are the **three user-exported application GeoJSONs**. Their IDs, areas, centroids and `ntl_mean` exactly agree with the corresponding user CSVs (all 17,177 IDs), and their geometries are nonempty/valid. The independent VIIRS raster source is the 2020 Earth Engine reference export; the integration routine does not import any `spatial-app` zonal code.
- Pixel-by-polygon intersections are computed in the EPSG:4326 GeoTIFF plane (as in the raster zonal coverage definition); masked/nonfinite values are skipped and valid negative median radiances clipped at zero, matching the legacy NTL policy. All new edge polygons have valid reference raster coverage.

## New numerical results (edge cells only)

| Case | Clipped cells checked | Within strict 0.00005 | Strict exceedances | Maximum absolute error | Within 0.0000501 |
|---|---:|---:|---:|---:|---:|
| Shanghai / Nội đô Thượng Hải | 180 | 180 | 0 | 0.00004959946 | 180 |
| Shenzhen / Bao'an | 1,017 | 1,016 | 1 | 0.00005003932 | 1,017 |
| Huangshan / Qimen | 650 | 650 | 0 | 0.00004993913 | 650 |
| **Total** | **1,847** | **1,846** | **1** | **0.00005003932** | **1,847** |

The **one** strict exceedance is `Bao'an grid_id=628`, area 0.010610 km², CSV `ntl_mean=18.8768`, independent raster overlay `18.876850039319148`. Difference: `0.000050039319148`, exceeding the four-decimal half-bin (`0.00005`) by `0.000000039319148` (3.93 × 10⁻⁸).

This is a **borderline numerical/rounding discrepancy**, not evidence of materially incorrect radiance extraction. It is retained explicitly. With the stated additive 0.0000001 floating-point allowance, 1,847/1,847 edge cells pass. This does not override or re-label the strict comparison: **1 strict exception remains**.

## Combined interpretation of prior and newly completed V11 checks

| Evidence component | Current interpretation |
|---|---|
| Existing 15,330 whole-cell raster comparisons | Previously verified within strict four-decimal CSV rounding, reused unchanged |
| New 1,847 boundary-clipped raster comparisons | 1,846 strict pass + 1 tiny rounding-boundary exception; all 1,847 within 0.0000501 |
| All 17,177 app cells (NTL raster consistency) | No material discrepancy detected at output precision; nuanced one-cell strict exception above |
| Prior independent Queen adjacency / Local I / BH-FDR | Preserved, not recomputed |
| A02 per-cell observation support | **Not validated:** all 17,177 `dq_status=unknown`; tracked separately |
| GHSL native-grid conservation / Cloud benchmark | **Still pending; unrelated to V11 NTL validation** |

**Important independence limitation:** the reference radiance raster is external, but the boundary-clipped polygon geometries are application-exported GeoJSON. Their aggregate geographic area and bounding box were separately checked against GADM-curated source metadata on GitHub (GIDs: `CHN.24.1.10_1`, `CHN.6.15.1_1`, `CHN.1.11.1_1`). This is not a source-boundary, vertex-by-vertex reconstruction of every polygon. Prior GADM provenance audits remain in force and are not duplicated here.

## Input provenance and reproducibility

All raw GeoJSON files stay outside the public repository; do not commit multi-megabyte polygon datasets by default. Original user CSVs and external reference TIFFs likewise remain private. The edge metrics JSON records SHA-256 for each of the nine newly used inputs (3 GeoJSONs, 3 NTL CSVs, 3 reference TIFFs). Per-cell edge residual CSVs (1,847 records combined) are included only in the private staging evidence ZIP. Independently re-run `v11_edge_only_independent.py` on those exact files to reproduce the results.

**Disposition:** V11 2020 cross-location NTL/LISA scientific numerical field validation is complete in the stated scope, with one explicit near-rounding strict exception; this is **not** an A02 or GHSL field PASS. Hold compact evidence for the next single consolidated major-review PR, rather than opening a new PR now.

<!-- END ORIGINAL SOURCE 027 -->


---

## Source 028: `06_LIBRARY_STAGING_EXACT_ORIGINALS/spatial_app_single_pr_staging_2026-11-13.zip::PR_STAGING_NOTES.md`

**Original bytes:** 4,067 · **SHA-256:** `26a3a56a1a57839e45bb4066d32b92675c143ccbb676782afe14d93ad1caa4ae` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 028 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 13 November 2026. Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Seven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

<!-- END ORIGINAL SOURCE 028 -->


---

## Source 029: `06_LIBRARY_STAGING_EXACT_ORIGINALS/spatial_app_single_pr_staging_2026-11-13.zip::README.md`

**Original bytes:** 6,389 · **SHA-256:** `88d35d669a6caecbbfa0c6976d5e5a7f248a8177ab2de79015d2da53165d82f6` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 029 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **13 November 2026**. Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code only, no Earth Engine credentials, private data or real-world result tables**. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** seven synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV is a spatial-app cell export containing `grid_id`, `area_km2`, `ntl_mean` for the same GADM boundary and 500 m cell configuration.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Missing reference or application coverage is reported and causes a nonzero CLI exit code. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (7 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

<!-- END ORIGINAL SOURCE 029 -->


---

## Source 030: `06_LIBRARY_STAGING_EXACT_ORIGINALS/spatial_app_single_pr_staging_2026-11-14_v3.zip::PR_STAGING_NOTES.md`

**Original bytes:** 4,992 · **SHA-256:** `972a638ebbac490dc990ca0d5602f04a500ffe03d3d4b8d99e0a6b6581599c9d` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 030 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 14 November 2026 (revised from 13 November). Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Nine tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

## Review update 14 November 2026 — no new PR

- Hardened the GHSL check against **partial-coverage false positives**: eligible cells must have nearly 100% finite, unmasked raster area in BOTH native and app exports. Ineligible per-cell differences are NaN, not numerically compared.
- Added guard for GHSL native 100 m product resolution; a wrongly supplied 1 km raster fails preflight.
- Hardened A02 source independence: selecting ROI from the application's own band-1 mask could silently drop an app-side masked pixel. Reference valid-month count now defines the footprint, so this case fails.
- Negative controls expanded; `python -m pytest -q test_validation_scripts.py` now reports **9 passed**.
- All field validation gates remain unfulfilled without matching real-data rasters and application exports. Preserve project policy: **one future consolidated PR**, no branch/PR in this stage.

<!-- END ORIGINAL SOURCE 030 -->


---

## Source 031: `06_LIBRARY_STAGING_EXACT_ORIGINALS/spatial_app_single_pr_staging_2026-11-14_v3.zip::README.md`

**Original bytes:** 7,942 · **SHA-256:** `b3a3b72db9e8ef51843c77824bebf500ef359bafd9596b6cf91c6ba6eaef7648` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 031 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **14 November 2026** (updated from 13 November). Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code only, no Earth Engine credentials, private data or real-world result tables**. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** nine synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV is a spatial-app cell export containing `grid_id`, `area_km2`, `ntl_mean` for the same GADM boundary and 500 m cell configuration.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas and source 100 m resolution, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Each cell now reports native/app **valid-area fractions**, and a comparison is eligible only with at least 99.9999% valid area in both rasters. Merely intersecting a single valid pixel cannot justify full coverage. Missing or partial reference/application coverage is reported and causes a nonzero CLI exit code. Ineligible differences are blanked, while partial raw sums remain available only for diagnostics. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters. The **independent month-count** reference mask defines the comparison footprint; a missing/masked application pixel is flagged rather than excluded from validation. Extra app-only coverage outside the count reference also fails.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (9 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

## November 14 reviewer hardening

- GHSL now measures **fraction of each polygon covered by finite unmasked raster pixels**, not just the presence of any intersection. Only fully covered cells enter regional comparison totals and Spearman; partial diagnostics remain visible but never silently pass.
- Native GHSL must have projected 100 m resolution (within 1 m tolerance); the code still cannot independently prove the correct version/epoch/band without source metadata.
- A02 uses **independent reference count coverage** to choose pixels for validation. App-masked observations with valid reference count are checked as failures rather than skipped.
- Negative controls exercise one missing interior source pixel, invalid native product resolution, and an application-only missing A02 pixel. Nine tests pass as of this staging version.

See `REVIEW_FINDINGS_2026-11-14.md` for the checker's identified failure modes and scientific boundaries.

<!-- END ORIGINAL SOURCE 031 -->


---

## Source 032: `06_LIBRARY_STAGING_EXACT_ORIGINALS/spatial_app_single_pr_staging_2026-11-14_v3.zip::REVIEW_FINDINGS_2026-11-14.md`

**Original bytes:** 3,461 · **SHA-256:** `5ddace573c0c0c79920b1812a29b11205a3c2932bbfc57000558bf6d0975d95e` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 032 -->
# Spatial App — Staging review findings (14 November 2026)

## Executive finding

Three **potential false-assurance paths in the external validation checkers** were found and corrected in this staged package. These are **checker defects**, not demonstrated defects in the Spatial App production analysis. No changes were made to the GitHub repository.

| ID | Prior checker behavior | Risk | Hardening | Synthetic negative control |
|---|---|---|---|---|
| S01 | GHSL considered a cell covered if *any* finite pixel intersected it | An area with partly missing source data could be treated as fully comparable | Compute valid-area fraction per cell; require >= 0.999999 from both rasters; drop partial cells from quantitative differences; incomplete coverage forces non-zero CLI status | One interior source NoData pixel triggers incomplete coverage |
| S02 | GHSL accepted any projected native raster | A 1 km or unrelated grid could be mislabeled as the 100 m source | Native resolution within 1 m of 100 m required, still manually verify product/band/epoch | 1 km synthetic input rejected |
| S03 | A02 checked only the pixels where the application's first band had an unmasked value | A corrupted app-side mask could remove failing pixels from the test set | Use independent valid-month count raster to define reference footprint, flag extra app-only pixels | One app-only masked pixel is detected |

## Test execution

- Command: `python -m pytest -q test_validation_scripts.py`.
- Result: **9 passed** in the isolated synthetic checker suite.
- No field GHSL or new Earth Engine export was supplied or used in these tests.
- `pytest-results.xml` contains executable test evidence; `SHA256SUMS.txt` records staged file hashes.

## Scientific boundaries

- GHSL native data are per-pixel quantities (residential population count or built-up m²), not population or built-up density. Summation must account for pixel/polygon intersection fraction.
- Spatial App's GHSL `fetch_ghsl_raster` reprojects into EPSG:4326 at a requested 100 m scale and selects the first band; a potential bias due to reprojection remains **unquantified** without corresponding real source raster and app-exported GeoTIFF.
- A complete geometric coverage check cannot recover observational missingness that the application has previously converted to zero (`unmask(0)`). The detector reports this separately.
- Six-band A02 comparisons require three perfectly aligned real exports. Source-layer equivalence (same year, monthly filter and exact raster grid) remains a manual gate.
- CI PASS on 9 tests confirms only checker behavior under the included cases, not V11 completion, GHSL field accuracy or A02 field validity.

## Source method references

- GHSL POP product: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL BUILT-S product: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- GHSL JRC open downloads: https://human-settlement.emergency.copernicus.eu/download.php
- Earth Engine resampling: https://developers.google.com/earth-engine/guides/resample
- ExactExtract operations: https://isciences.github.io/exactextract/operations.html

## Staging policy

Do not open a new micro-PR for this report alone. The corrected tools and tests are held for the owner's **one consolidated future review PR**. The package contains no GHSL tiles or other large geospatial datasets and no credentials.

<!-- END ORIGINAL SOURCE 032 -->


---

## Source 033: `06_LIBRARY_STAGING_EXACT_ORIGINALS/spatial_app_single_pr_staging_2026-11-15_v4.zip::PR_STAGING_NOTES.md`

**Original bytes:** 5,978 · **SHA-256:** `fce7228d802a6989deb7eb352423d91ce1f403dde844d8cb24f06d5b5459a89d` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 033 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 14 November 2026 (revised from 13 November). Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Eleven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

## Review update 14 November 2026 — no new PR

- Hardened the GHSL check against **partial-coverage false positives**: eligible cells must have nearly 100% finite, unmasked raster area in BOTH native and app exports. Ineligible per-cell differences are NaN, not numerically compared.
- Added guard for GHSL native 100 m product resolution; a wrongly supplied 1 km raster fails preflight.
- Hardened A02 source independence: selecting ROI from the application's own band-1 mask could silently drop an app-side masked pixel. Reference valid-month count now defines the footprint, so this case fails.
- Negative controls expanded; `python -m pytest -q test_validation_scripts.py` now reports **11 passed**.
- All field validation gates remain unfulfilled without matching real-data rasters and application exports. Preserve project policy: **one future consolidated PR**, no branch/PR in this stage.

## 15 November 2026 — v4 single-PR carry-forward

1. Require **actual per-ID spatial identity** using UTM and WGS84 centroids, not only grid ID/area. The current production app already exports all required fields. Checker code and comparator are staged, not pushed to GitHub.
2. Reject non-integral valid-month counts in A02 references.
3. **11/11 isolated checker tests passed.** Deliberate same-area grid swaps and missing centroid columns are rejected.
4. Historical Yanqing 2020 GADM, real VIIRS raster and application CSV were checked with the amended comparator. Exactly **8,333/8,333** per-cell NTL references and centroid identity comparisons passed at exported rounding tolerances; detailed metrics JSON and source hashes are included, but private input raster/GeoJSON/CSV and the 8,333-row diagnostic table are *not* bundled.
5. No new branch, PR, production algorithm changes or geospatial data bundles. One consolidated PR remains the only proposed repository update.

<!-- END ORIGINAL SOURCE 033 -->


---

## Source 034: `06_LIBRARY_STAGING_EXACT_ORIGINALS/spatial_app_single_pr_staging_2026-11-15_v4.zip::README.md`

**Original bytes:** 9,716 · **SHA-256:** `a0b82b9fd376b4e8c3f96adfb7e8f7f7497e761a9f6dee2cf070c56371c284e9` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 034 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **15 November 2026** (incremental v4 of 13–14 November staging). Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code and a small, reproducible Yanqing 2020 metrics JSON**, but no Earth Engine credentials, private input GeoTIFFs, original GADM boundaries, or large per-cell result tables. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** eleven synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV must be a current Spatial App cell export containing `grid_id`, `area_km2`, `ntl_mean` and four rounded **per-ID centroids** (`centroid_lon`, `centroid_lat`, `centroid_x_epsgNNNN`, `centroid_y_epsgNNNN`) for the same GADM boundary and grid. Area and IDs alone are insufficient to detect identical-size cells reordered geographically.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas and source 100 m resolution, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Each cell now reports native/app **valid-area fractions**, and a comparison is eligible only with at least 99.9999% valid area in both rasters. Merely intersecting a single valid pixel cannot justify full coverage. Missing or partial reference/application coverage is reported and causes a nonzero CLI exit code. Ineligible differences are blanked, while partial raw sums remain available only for diagnostics. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters. The **independent month-count** reference mask defines the comparison footprint; a missing/masked application pixel is flagged rather than excluded from validation. Extra app-only coverage outside the count reference also fails.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (11 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

## November 14 reviewer hardening

- GHSL now measures **fraction of each polygon covered by finite unmasked raster pixels**, not just the presence of any intersection. Only fully covered cells enter regional comparison totals and Spearman; partial diagnostics remain visible but never silently pass.
- Native GHSL must have projected 100 m resolution (within 1 m tolerance); the code still cannot independently prove the correct version/epoch/band without source metadata.
- A02 uses **independent reference count coverage** to choose pixels for validation. App-masked observations with valid reference count are checked as failures rather than skipped.
- Negative controls exercise one missing interior source pixel, invalid native product resolution, and an application-only missing A02 pixel. Eleven tests pass as of this staging version.

See `REVIEW_FINDINGS_2026-11-14.md` for the checker's identified failure modes and scientific boundaries.

## 15 November addendum — grid identity and negative controls

- **GHSL:** per-cell UTM centroids (application exports rounded to 0.1 m) and geographic centroids (six decimal places) must match the independently reconstructed grid at their respective rounding precision. Omitting these four columns is an error, not permission to skip the spatial-identity check.
- **Cross-location comparator:** the staged `compare_raster_cells.py` now applies the same per-ID geometry gate *before* calculating raster zonal statistics. It is intended to replace the existing script in the **single future consolidated PR**, not to create a micro-PR.
- **A02:** reject a valid-month raster with fractional counts, which can indicate an improperly resampled month-count reference. A count of months must be integral.
- **Real-data regression:** independent raster–polygon overlay was rerun on the historical Yanqing 2020 archive. **8,333/8,333** NTL cells met the CSV rounding tolerance (0.00005 nW/cm²/sr), and **8,333/8,333** UTM/WGS84 centroids met their recorded rounding tolerances. See `yanqing_2020_regression_metrics.json` and the recorded input SHA-256s. A controlled swap of the locations of two equal-area historical cells was rejected.
- **Limits:** this is a reproducibility check of the previously archived Yanqing data, **not** a newly acquired VIIRS/A02 six-band or JRC GHSL dataset. V11, GHSL live comparison and A02 real missingness remain PENDING.

<!-- END ORIGINAL SOURCE 034 -->


---

## Source 035: `06_LIBRARY_STAGING_EXACT_ORIGINALS/spatial_app_single_pr_staging_2026-11-15_v4.zip::REVIEW_FINDINGS_2026-11-15.md`

**Original bytes:** 4,122 · **SHA-256:** `0ce9c8d7b12bc8066a5b1899516f55587a7e0ec3c9772be84c2611f48b1e69dd` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 035 -->
# Spatial App — Independent checker follow-up (15 November 2026)

## Decision

Continue staging changes for one future major-review PR; no new PR and no changes to production formulas. An area-only comparator can fail to detect a spatial identity mismatch for equal-area cells. Fix the independent checking tools before interpreting later GHSL comparisons.

## Finding S04 — same-area ID swaps bypass the previous area gate

- Observed in: both the staged GHSL comparator and the existing `validation/cross_location/compare_raster_cells.py` checked grid IDs, polygon counts and areas, but not **per-ID geographic identity**.
- Why this matters: two full 500 m grid cells both have `area_km2 = 0.25`; their polygon-to-CSV pairing can be wrong while an area and ID validation still reports success.
- Remedy staged: check rounded UTM centroids (`centroid_x_epsgNNNN` and `centroid_y_epsgNNNN`, tolerance 0.051 m) and geographic centroids (`centroid_lon`, `centroid_lat`, tolerance 0.00000051°) against the independently recreated clipped GADM polygon for each `grid_id`.
- Negative control: interchange the exported centroid coordinates of two equal-area cells while leaving `grid_id` and `area_km2` untouched. Both staged comparators reject the mismatch. Missing centroid metadata also forces explicit failure.
- Production code and CSV schemas: **unchanged**; required centroid columns already exist in normal current application exports.

## Historical Yanqing field regression

A replay of the updated `compare_raster_cells.py` used:

- full-precision GADM 4.1 Yanqing GeoJSON from the historical private archive;
- the VIIRS 2020 annual reference GeoTIFF from the same archive;
- the **original** application 2020 500 m CSV with UTM/WGS84 centroids;
- 500 m clipped UTM grid, matching the existing baseline inference geometry.

Results: **8,333/8,333 cells** passed the raster–polygon NTL comparison within 0.00005 nW/cm²/sr (MAE 0.0000250230; maximum absolute error 0.0000499933). All **8,333/8,333 cells** also met the geographic centroid identity rounding tolerances. The maximum UTM-x and UTM-y rounding discrepancies were 0.049872 m and 0.049979 m; maximum longitude/latitude discrepancy was below 0.0000005°. The source and script checksums are retained in `yanqing_2020_regression_metrics.json` and `SHA256SUMS.txt`.

This is an **independent recomputation using archived field input** from Yanqing, not new field sampling. A controlled same-area swap of two historical full-size cells was correctly rejected by the new check. It does not establish V11 across contrasting locations or GHSL product equality.

## Finding S05 — fractional monthly observation counts

The staged A02 checker checked count in `[0,12]` but did not reject, for example, `2.5` months of annual valid observation support. Such a value can arise if a reference count raster is improperly interpolated. The checker now requires integral valid-month counts, and the corrupted synthetic example is rejected.

## Scope availability on archived VIIRS rasters

Historical annual medians and month-count reference rasters have 30,814 pixels per year (2014 and 2020). In both cases all count pixels recorded 12 valid months and no median pixels were masked. The 2014 raster contained one negative valid median; 2020 had none. Neither case contained measured-zero medians or fewer-than-three-month support. **These real images cannot test the A02 data-semantics edge cases involving genuine missing observations.**

## Acceptance log

- **11 passed** — `python -m pytest -q test_validation_scripts.py` (synthetic oracle and negative-control tests).
- **8,333 passed** — Yanqing 2020 archived field raster/polygon comparator and per-ID centroid verification.
- **Expected fail** — spatial-identity negative control on two same-area historical cell IDs.
- **Not run / PENDING** — GHSL native JRC 100 m versus real Earth Engine reprojected raster; A02 true six-band export; Shanghai/Bao'an/Qimen independent per-cell validation; Cloud benchmark.
- No new PR, no code modification in `ntl/`, and no large GeoJSON/GeoTIFF committed.

<!-- END ORIGINAL SOURCE 035 -->


---

## Source 036: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/SHANGHAI_GHSL_INDEPENDENT_FIELD_EVIDENCE_2026-11-15.zip::SHANGHAI_GHSL_POST_DEPLOY_EVIDENCE_2026-11-15.md`

**Original bytes:** 4,754 · **SHA-256:** `e46979acb604d88486d008e973c005eb5f89059f765e5b8cfeadfedee21b5cec` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 036 -->
# Shanghai GHSL 2020 — independent post-deployment validation

Date: 2026-11-15. Scope: Shanghai Core (`CHN.24.1.10_1`), year 2020, 500 m grid, GHSL built-surface and population. Evidence relates to the post-merge #26 application figures shown by the user; it does **not** re-run V11 or Yanqing.

## Direct observations from the deployed UI

- GHSL built surface: Spearman rho **-0.079**, 95% block-bootstrap CI **[-0.22, 0.09]**, top-quartile AUC **0.395**; scatter plot displayed.
- GHSL population: Spearman rho **0.136**, 95% block-bootstrap CI **[-0.03, 0.27]**, top-quartile AUC **0.576**; scatter plot displayed.
- The old 100%-zero proxy and `NaN` results no longer appear in this deployment output.

## Independent reference calculation

Inputs: original Earth Engine native-Mollweide 100 m GHSL TIFFs previously exported to Drive; the application's Shanghai 500 m grid GeoJSON and NTL CSV previously provided by the user (886 cells). No `ntl` app imports, no `exactextract` implementation dependency.

Algorithm:
1. Load GeoJSON and CSV, sort by `grid_id`, verify corresponding NTL values.
2. Project actual cell polygons from EPSG:4326 to the raster's ESRI:54009 using GeoPandas/PROJ. **Keep the GHSL raster on its original 100 m source grid.**
3. For each grid polygon, compute Shapely polygon overlap with each candidate GHSL pixel: `sum(pixel_amount * intersection_area / 10_000 m²)`.
4. Retain original 500 m cell area in km²; derive proxy density = GHSL sum / area.
5. Apply the same core-cell eligibility rule, `area_km2 >= 0.99 * (500 / 1000)^2`, giving **715 / 886** eligible cells.
6. Calculate Spearman ranks with average ties, Mann–Whitney top-quartile AUC, and 200 block-bootstrap Spearman draws with 5 x 5 cells, seed 42 and EPSG:32651 grid-centroid coordinates. 

## Independent results

| Metric | Built surface | Population |
|---|---:|---:|
| Eligible core cells | 715 | 715 |
| Core cells with positive GHSL proxy | 715 | 715 |
| GHSL core zero share | 0% | 0% |
| Spearman rho | -0.0794533 | 0.1358105 |
| Block-bootstrap 95% CI | [-0.220123, 0.086086] | [-0.029628, 0.271008] |
| Top-quartile AUC | 0.394636 | 0.576274 |
| Core median GHSL density | 353,036 m²/km² | 33,799 people/km² |
| Core median NTL | 41.2612 | 41.2612 |

All three key metrics (rho, CI endpoints, AUC) agree with both deployed UI screenshots to their displayed rounding precision. Thus the deployed application's metrics have been independently reproduced from the archived native-resolution GHSL field data. This is strong evidence that the previously broken raster/vector CRS alignment is now functioning correctly in Shanghai.

## Scientific interpretation and limitations

The Shanghai inner core has very weak monotonic association between VIIRS nighttime radiance and GHSL built surface (weak slightly negative rho) or GHSL population (weak slightly positive rho). Both displayed 95% Spearman confidence intervals contain zero; the observed evidence does not establish a reliably nonzero monotonic association. The AUC comparisons are descriptive, not separately tested here. GHSL counts and built surface are **not** direct nighttime light ground truth, and a dense urban core can have limited spatial differentiation in radiance, different daytime activity, commercial intensity or housing intensity. Avoid claiming that this disproves VIIRS or that the GHSL data are bad.

The independent calculation **does not** compare every post-deployment application's GHSL per-cell result one-to-one, since per-cell GHSL arrays were not exported from the live app. Metrics matching at screenshot precision do not prove pixel-for-pixel identity. It does independently reproduce the aggregate validation pipeline. The saved TIFFs were exported via Earth Engine `Export.image.toDrive`, while the deployed app now uses `ee.data.computePixels` to fetch a native grid: a matching statistical result offers corroboration but not an exhaustive byte-level equivalence proof.

No actual live Cloud RSS/runtime JSON and no post-merge A02 per-cell CSV have been assessed in this task. Separate post-deployment A02 and runtime acceptance gates remain open. Cross-location GHSL evaluation should be tested on regions with different urban/rural composition without altering the statistical estimators based solely on Shanghai's low rho.

## Included evidence

- `SHANGHAI_GHSL_INDEPENDENT_CELL_VALIDATION_2026-11-15.json`: exact summary metrics.
- `shanghai_ghsl_independent_validation_2026_11.py`: independent source-grid overlap and matching statistics, no Spatial App imports.
- `SHANGHAI_GHSL_POST_DEPLOY_EVIDENCE_2026-11-15.md`: this report.
- Source raster/CSV/GeoJSON are **not** redistributed in this ZIP; they remain user-supplied separate inputs.

<!-- END ORIGINAL SOURCE 036 -->


---

## Source 037: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/Spatial_App_A02_GHSL_Remaining_Field_Package.zip::README.md`

**Original bytes:** 5,568 · **SHA-256:** `c77f737d7a59562c5f476f3cc688dc62a1f87bcc3ba9f55ebd77c7afaa0a2140` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 037 -->
# Spatial App — Unresolved-field-evidence package (single future PR)

Date: 2026-11-15. Repository: `hoanfg/spatial-app` (main). **Private staging only**: no PR, no repository changes, no geospatial data copied into the repository. Historical Yanqing/V11/FDR/Moran findings are reused and were not recomputed.

## A02 `dq_status=unknown`: established facts vs open hypotheses

- All 17,177 app CSV cells for Shanghai, Bao'an and Qimen carry unknown A02 status, but independently checked NTL values remain valid. This is an **observed field failure**, not missing button presses.
- Production `cell_quality()` currently requires `src.count==6` and exact names `src.descriptions[1:] == QUALITY_BANDS`; failure silently gives NaN/unknown. This is an established failure mechanism.
- The 9 independent EE `Export.image.toDrive` TIFFs contain names (single-band `avg_rad` / `valid_month`). Therefore **do not claim** that the app's different `getDownloadURL(format='GEO_TIFF')` route necessarily strips names.
- The pending targeted patch adds a verified-producer **unlabeled six-band** fallback, validation of binary flags/month counts/mutual consistency, and explicit UI diagnostics if count/schema is truly wrong. Arbitrary user TIFFs, partly named/conflicting TIFFs, and 1-band TIFFs are never assumed to have quality bands. Preserve all existing NTL/LISA formulas.
- `ntl/semantics.py` is the proposed module replacement. `apply_a02_schema_patch.py` generates a **reviewable diff** from a real checkout, updating that module and the two downstream consumers in `app.py` plus `ntl/quality_ui.py`; the script does **not** modify a checkout without `--write`. This patch has **NOT been applied to the public GitHub repository**.
- New focused tests: `python -m pytest -q tests/test_a02_field_schema.py` → **8 passed** in the staging environment (Python 3.13, Rasterio 1.5.0). This is a focused regression, not full CI and not live EE proof.

## Exactly five new exports (GHSL and A02)

Open `validation/gee_a02_ghsl_field_exports_2020.js` in Google Earth Engine Code Editor. It creates **5 tasks** in Drive folder `spatial_app_field_validation_2020`:

1. `baoan_2020_a02_six_band_reference.tif` — production-equivalent six-band radiance/quality image, aligned to the *already exported* Bao'an 2020 reference TIFF.
2. `shanghai_2020_ghsl_built_native_100m.tif` — JRC GHSL built-surface 2020, **Earth Engine asset's native projection and affine transform**.
3. `shanghai_2020_ghsl_built_appstyle_4326_100m.tif` — same image reprojected with production `EPSG:4326`, scale 100m.
4. `shanghai_2020_ghsl_pop_native_100m.tif` — GHSL population count on source 100m projection.
5. `shanghai_2020_ghsl_pop_appstyle_4326_100m.tif` — matching production-style reprojection.

If EE splits files into same-named Drive folders, leave them intact: Drive search by folder and filename can locate them. No new CSV/GeoJSON is required; the existing Shanghai district 2020 CSV and GeoJSON are already available.

**Limits:** GHSL paired exports are *real EE GHSL field data* and permit measuring reprojection-related per-cell/region quantity shifts. They do not replace an independently downloaded JRC source tile for a full cross-provider replication. The A02 Drive export probes real six-band pixel semantics/labels, but does not observe the raw TIFF bytes returned to Streamlit Cloud by `getDownloadURL`; production schema status remains unknown until the targeted logging patch is deployed or a raw capture is obtained.

To audit GHSL, use the existing private staging tool `audit_ghsl_native_vs_reprojected.py` from the earlier v4 bundle (one run each `kind=built` and `kind=pop`). It compares exact fractional pixel-polygon sums, valid coverage and Spearman-rank movement. Do not compare global raster totals: use the clipped GADM cells and their complete-coverage flags.

## Streamlit Cloud — remaining operational gate

CI is not a memory benchmark. Real latency/peak RAM/HTTP failure analysis requires a run in Streamlit Community Cloud. The owner can open the app, select **Manage app** at bottom right, then download **Cloud logs**. Do not upload `.streamlit/secrets.toml`, credentials or personal-account tokens. Logs show errors but not necessarily peak RAM; a controlled, opt-in in-app profiler would be needed for exact RAM use. No RAM or latency PASS is claimed.

## Single-PR acceptance gate

- A02: Six-band GeoTIFF has correct schema, aligns with masked-median and months reference, no false distinction between missing / zero / negative; live application shows populated `dq_` fields after deploying fix. Any unknown schema is visible to the user.
- GHSL: Real **native vs appstyle** raster inputs have matching year/band/provenance and quantified per-cell disagreement. Decide whether the production GHSL `zonal_stat(sum)` needs a conservation-aware approach from *measured* results, not synthetic bias guesses.
- Cloud: Actual operational logs / measurements are reviewed with no unexplained failures.
- Only then prepare **one consolidated PR**, importing *selected* code and compact evidence summaries; keep large private data and source GeoTIFFs off GitHub.

## Public sources

- VIIRS: `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` (2020), `avg_rad` masked by `cf_cvg > 0`.
- JRC GHSL built-up `JRC/GHSL/P2023A/GHS_BUILT_S/2020` (`built_surface` m²/pixel).
- JRC GHSL population `JRC/GHSL/P2023A/GHS_POP/2020` (`population_count` persons/pixel).
- EE `Export.image.toDrive()` with `crsTransform` and `crs` explicitly documented for native-pixel alignment.

<!-- END ORIGINAL SOURCE 037 -->


---

## Source 038: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/Spatial_App_Consolidated_PR_Candidate_A02_GHSL_Performance_2026-11-15.zip::README.md`

**Original bytes:** 7,159 · **SHA-256:** `8610ab1372b8838eade489c22b7d676dc37e7824c6ce90c05ab46b230e8d6e5d` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 038 -->
# Spatial App — one-PR code candidate: A02, native GHSL, owner-visible performance

Date: 2026-11-15. Target: `hoanfg/spatial-app` `main` as observed on this date.
**Status: prepared and locally unit-tested, NOT pushed to GitHub, NOT Cloud-tested.**
This package is an addition to the **existing** `/Spatial-App/major-review-staging/` register. It is not another PR, branch or v5 validation exercise.

## Contents

- `ntl/semantics.py`: existing fail-closed A02 six-band schema fallback. Only a six-band download created through the application's own trusted producer can use unlabeled band order after logical and range checks. Other/mislabeled files fail closed.
- `ntl/ghsl_native.py`: GHSL native 100 m Mollweide source-grid window builder. Uses the true pixel CRS+affine, computes a bounded window and downloads with `crs_transform` + `dimensions`. Validates downloaded single-band GeoTIFF metadata before a zonal sum.
- `ntl/performance.py`: per-analysis self-service, low-overhead profiler. Measures full-pipeline wall time plus timed stages, sampled process RSS (Linux /proc; optional psutil fallback), and stage failures without exception text. Provides an expandable table and JSON/CSV downloads in Streamlit. Does **not** need Manage app or Cloud logs.
- `tests/test_a02_field_schema.py`, `tests/test_ghsl_native_grid.py`, `tests/test_runtime_performance.py`: focused unit tests; no Earth Engine account needed.
- `apply_consolidated_review_patch.py`: strict, fail-closed integration patch creator. Default creates a diff only. Targets current `app.py`, `ntl/quality_ui.py`, `ntl/lisa_ui.py`, `ntl/ee_extra.py`, `ntl/semantics.py` and adds new modules/tests. It does not commit, push or open PR.
- The original field-evidence files and user rasters stay in Drive / private Library, not in this ZIP.

## Local application (once the consolidated PR is ready for review)

From a **clean checkout** of this repository:

```bash
python /path/to/apply_consolidated_review_patch.py --repo /path/to/spatial-app
# Inspect generated single_review_candidate.diff.
python /path/to/apply_consolidated_review_patch.py --repo /path/to/spatial-app --write
python -m pytest -q tests/test_a02_field_schema.py tests/test_ghsl_native_grid.py tests/test_runtime_performance.py
python -m pytest -q tests
```

The apply script checks exact known source anchors and compiles changed Python files **before writing**. If it detects source drift, stop and reconcile; never bypass the guard by repeated broad string replacement. It is intended for a single consolidated PR with existing V11 verification and GHSL evidence, not a standalone commit.

## What the user will see after deployment

- After **Chạy phân tích** / **Run analysis**, the **LISA · Panel** view contains an expander **⏱️ Hiệu suất xử lý (không cần Cloud logs)**. It shows total pipeline wall time, time per stage and sampled process RAM and allows downloading a small JSON/CSV. When the full LISA or GHSL validation runs, the same recorder acquires further stage rows.
- Timed stages: boundary load, grid build, Earth Engine NTL fetch, NTL zonal mean, A02 quality extraction, Global Moran, Local Moran LISA, and GHSL native fetch / zonal sum / external proxy agreement. Optional Space-Time previous-year fetch is measured.
- If the main analysis fails, the failure-stage timings are still available in the screen's empty/result state, without exporting exception messages.
- The values are **process-wide Streamlit RSS**, not RAM isolated to one user, not a true instantaneous memory maximum, and not the platform's hidden RAM limit. Earth Engine timing is request/download wait observed by the app, not separate Earth Engine server compute CPU time. The sample interval is 0.1s and can miss sub-0.1s spikes.
- No background telemetry, network instrumentation endpoint, log secrets, raw query strings or user locations are collected or uploaded by the profiler. JSON/CSV are generated locally within the user's session on download.

## Source-grid GHSL correction and limits

`GHS_BUILT_S` and `GHS_POP` values are per-native-source-pixel amounts (m² and people), not densities. Current app uses nearest-neighbor EPSG:4326 100 m sampling then area-fraction-weighted `sum`, which duplicates quantities. The new fetch retains native equal-area 100 m pixel footprints and clips to the geographic ROI **before** requesting the bounded native lattice window. No arbitrary universal 16.5% scaling.

The downloaded TIFF must satisfy the expected native CRS, exact origin/transform, 100 m source pixel size, dimensions and single-band schema. Failure is surfaced rather than reverting to the biased EPSG:4326 sum. The original zonal `sum` computes fractional intersection of each native 100m pixel with 500m polygons.

**Important:** Earth Engine `Image.getDownloadURL` documents that `region` is ignored when both `crs` and `crs_transform` are provided. This module explicitly computes and supplies bounded `dimensions`; `image.clip(roi)` remains. Limit: 3,000,000 source pixels, and Earth Engine's 32 MB getDownloadURL cap still applies.

**Already measured real field data:** Shanghai 2020, common inset native vs app-style GHSL naive sum = +16.51428% built, +16.59686% population. `native_download_params()` was checked against the saved original source raster affine; the requested 331×202 window and 100m transform exactly match the independently exported native TIFF.

**Not yet proven:** a live Cloud `getDownloadURL()` response with the new parameters; real app cell-by-cell Spearman/AUC deltas after patch; memory/runtime under production concurrency. Keep scientific/operational PASS pending until these are measured on the deployed candidate.

## A02 qualification

The Bao'an six-band Earth Engine Drive export has correctly named six bands and 9–12 supported months, but the application uses a different `getDownloadURL` transport and 17,177 previous app rows still contain `dq_status=unknown`. The staged schema patch can expose the live cause and may recover fully unlabeled **trusted** six-band images when logical contracts pass. It is not proof that the Cloud's cause was definitively unlabeled bands. It does not change NTL zero-filling policy or Moran/LISA estimators.

## Suggested one-PR acceptance sequence

1. Integrate code in one clean branch, inspect diff, run the full test suite and record CI.
2. In an authenticated Streamlit Cloud instance, run **one** district (Shanghai or Bao'an), confirm A02 schema status and `dq_status` and export the new in-app performance JSON (no Manage app needed).
3. Run GHSL built and pop comparison there, inspect native grid CRS/affine, compare corrected per-grid sums and Spearman/AUC with independent source-GHSL calculations, use existing real files / hashes as baseline.
4. Check perf on a representative district and one larger region; report wall time and sampled process RSS with a note about shared sessions and short peaks. Decide RAM/time limits based on the actual Cloud tier, not made-up thresholds.
5. Only then merge one consolidated PR. Keep original TIFFs / user CSVs and GeoJSON files out of public GitHub.

<!-- END ORIGINAL SOURCE 038 -->


---

## Source 039: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/V11_CROSS_LOCATION_VALIDATION_EVIDENCE_2026-11-15.zip::V11_CROSS_LOCATION_FIELD_VALIDATION_2026-11-15.md`

**Original bytes:** 6,952 · **SHA-256:** `465635eda5d2061ba1f63d86b5113419d0b3d324f24c46632d04f2ba2b89117f` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 039 -->
# V11 cross-location field validation: Shanghai, Bao'an, Qimen

Date: 15 November 2026
**Status: PARTIAL FIELD VERIFIED.** This is new evidence for the three V11 target locations, not a rerun of Yanqing.

## Scope and provenance

- Inputs: 6 CSVs exported from spatial-app (one NTL and one LISA CSV for each locality), 9 original 2020 VIIRS GeoTIFFs exported independently by the user from Google Earth Engine and retrieved from two Google Drive folders.
- Original boundaries: GADM v4.1 districts represented in the repository `hoanfg/spatial-app`; this run **did not** materialize the three boundary GeoJSON files into the analysis runtime. Consequently the exact geometry of cut/edge cells could not be reconstructed independently here.
- Validation program is separate from the production `ntl.zonal` and `ntl.lisa_core` imports. Input SHA-256 fingerprints are recorded in `V11_CROSS_LOCATION_INPUT_MANIFEST_2026-11-15.json`.
- VIIRS reference dataset: `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG`, year 2020; reference median with `cf_cvg > 0`, exported EPSG:4326 at scale 463.83 m. App CSV: year 2020, UTM 500 m cells, raw NTL.

## Independent numeric results

### NTL raster-to-cell comparison

For every **unclipped 500 m square**, the benchmark rebuilds the square in UTM from its gridded CSV centroid, transforms its polygon to EPSG:4326, intersects it with the independent reference raster pixel polygons, and recomputes an area-weighted radiance mean (clipping valid negative radiance at zero). This is not a copy of production `ntl_mean`.

| Location | App cells | Full-square cells independently compared | Pass at ±0.00005 | MAE | Max absolute error |
|---|---:|---:|---:|---:|---:|
| Shanghai | 886 | 706 | 706/706 | 0.000025472 | 0.000049957 |
| Bao'an | 7,148 | 6,131 | 6,131/6,131 | 0.000025034 | 0.000049998 |
| Qimen | 9,143 | 8,493 | 8,493/8,493 | 0.000024630 | 0.000049994 |

**Aggregate:** 15,330/15,330 full-square cells match to the four-decimal CSV rounding bound. **Not tested here:** 1,847 cut/partial polygon cells; these require the exact GADM boundary polygons. Do not report all 17,177 cells as independently raster-validated.

### LISA deterministic checks

The independent checker creates Queen adjacency with a dictionary of 500 m UTM grid indices, excludes cells below 99% of 0.25 km², recomputes z-scores from the rounded CSV NTL values, calculates local Moran observed I and spatial lag, checks raw quadrants, and applies a separately coded Benjamini–Hochberg step-up procedure to every exported p-value.

| Location | Local I checked | Queen neighbor differences | BH-FDR significant | FDR flag differences | I max abs difference | Raw quadrant differences |
|---|---:|---:|---:|---:|---:|---:|
| Shanghai | 715 | 0 | 159 | 0 | 0.0000519 | 0 |
| Bao'an | 6,185 | 0 | 2,848 | 0 | 0.0000573 | 0 |
| Qimen | 8,532 | 0 | 869 | 0 | 0.0030472 | 1 |

- All three NTL CSVs and respective LISA CSVs are identical across their common first 32 columns and match one-to-one on `grid_id`.
- All exported BH-FDR significant flags agree with the independently recomputed step-up threshold. **This is a consistency check of exported p-values; it does not itself validate Monte Carlo p-generation.**
- **One raw quadrant disagreement:** Qimen `grid_id=2070`, where NTL rounds to `0.2944` and the recomputed z-score is approximately `-0.0000828` (near zero). The export reports `High-High`, while recomputing with rounded CSV yields `Low-High`. Its `lisa_p_sim=0.182`, its final class is `Not Significant`, and **no final significance or HH/LL label is affected**. The difference is consistent with sensitivity to input rounding, not independently proof of a production error.

### Conditional Monte Carlo replication on genuinely new geographical cases

An independent NumPy RNG with 999 conditional draws per focal cell and distinct sampled nonfocal neighbors was run on a stratified sample of exported p-values in each region. Seeds intentionally differ from the app. A doubled smaller-tail inclusive p-value was compared with `lisa_p_sim` (the denominator of local I cancels in tail comparison).

| Location | Independently resimulated cells | Pearson correlation with exported p | MAE of p | Disagreement for raw p < 0.05 |
|---|---:|---:|---:|---:|
| Shanghai | 387 | 0.99624 | 0.0141 | 7 |
| Bao'an | 400 | 0.99599 | 0.0146 | 12 |
| Qimen | 400 | 0.99557 | 0.0145 | 10 |

- Total: **1,187** resimulated cells. The sample was intentionally stratified by reported p-value ranges and is not a probability sample of all cells.
- Small p-value and raw threshold differences are expected under distinct Monte Carlo draws; these are not exact fixed-seed equality tests. The BH-FDR comparisons in the previous table were performed separately on all stored p-values.

### A02 observational quality is not verified in the live exports

- **All 17,177 cells** have `dq_status=unknown`; none has finite `dq_observed_fraction`, `dq_mean_valid_months`, or the other per-cell observational quality indicators.
- This is observed in the actual spatial-app CSV exports, not inferred from synthetic tests. It demonstrates that the A02 observational metadata contract is **not usable in these six outputs**, although the primary band NTL values match.
- The cause cannot be established from the CSV alone; candidate explanations include the downloaded GeoTIFF missing expected band names or an unexpected single-band TIFF. Inspect an actual live app-downloaded TIFF with `rasterio` for band count and descriptions before changing production semantics.

## Decision and outstanding verification

- **V11: PARTIAL FIELD VERIFIED.** VIIRS NTL on 15,330 full 500 m cells and deterministic LISA (Queen/Local Moran/BH) across three new regions have strong independent support. Independent conditional Monte Carlo samples agree closely.
- **Open: 1,847 cut cells.** Their polygon geometry must be reconstructed from exact GADM source to independently verify the area-weighted means; matched full cells must not be conflated with border cells.
- **Open: A02 per-cell quality metrics.** All relevant columns are unknown in real exports; requires production output six-band TIFF metadata inspection, a minimal justified fix if necessary, and one real rerun.
- **Open: GHSL native-grid comparison and Cloud operational metrics.** No new GHSL/Cloud evidence was generated by this V11 audit; do not change their prior status.
- **No change to production code and no new PR.** Keep this evidence as a single set of inputs for the already planned consolidated Major Review.

## Reproducibility

Run `v11_field_validation_2026_11.py` and `v11_independent_permutation_sample.py` with the 6 CSVs and 9 reference TIFFs as named in the input manifest. The full-square check requires pandas, NumPy, rasterio, Shapely, and pyproj; it does not need `exactextract` or the app code. The Monte Carlo sample uses NumPy and pandas. Output JSONs record all summary metrics.


<!-- END ORIGINAL SOURCE 039 -->


---

## Source 040: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/V11_EDGE_ONLY_PRIVATE_EVIDENCE_2026-11-15.zip::A02_DQ_UNKNOWN_FIELD_FINDING_2026-11-15.md`

**Original bytes:** 4,362 · **SHA-256:** `b4484af154e06a57d044c7e9ea69bfda29867de2968c625eb9eb04b0e022777b` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 040 -->
# A02 — real CSV `dq_status=unknown` field defect / root-cause investigation

Date: 15 November 2026. Repository: `hoanfg/spatial-app`. **Carry forward to the ONE consolidated Major Review PR; not a new PR.**

## Reproducible observed symptom

All 17,177 newly exported 2020 cell records across Shanghai (886), Bao'an (7,148) and Qimen (9,143) have `dq_status=unknown`. The five per-cell columns (`dq_observed_fraction`, `dq_negative_fraction`, `dq_zero_fraction`, `dq_mean_valid_months`, `dq_low_month_fraction`) are all empty. Separately, `dq_stat_missing=False`, and independent VIIRS pixel-overlap checks validate the main radiance values. No evidence suggests a forgotten UI action caused these particular empty columns.

## Exact code path / confirmed failure mode

1. `app.py:fetch_ntl_raster()` creates `annual_image_with_quality(col.map(_mask_cloud_free), roi)`, and downloads the GeoTIFF with `getDownloadUrl`. The ZIP branch selects its first `.tif` if a ZIP is returned.
2. `app.py:run_pipeline()` calls `cell_quality(tif_bytes, grid_wgs)` automatically as part of the core computation; that result is joined into `grid_utm`.
3. `ntl/semantics.py:cell_quality()` accepts the quality bands **only if** `src.count == 6` AND `tuple(src.descriptions[1:]) == QUALITY_BANDS` in exact order. When the condition is false, every `dq_*` numerical field becomes `NaN`, followed by `dq_status=unknown`, without a visible schema-error message.
4. `app.py:export_df` joins all `grid_utm` `dq_` columns; `ntl/lisa_ui.py` incorporates `export_df` into the downloadable `*_lisa_cells.csv`. The extra buttons in `ntl/quality_ui.py` (observation count, negative clipping sensitivity, GHSL validation) are optional **additional region-level diagnostics**. They do not populate these automatically generated per-cell fields.
5. `tests/test_data_semantics.py` writes a synthetic six-band GeoTIFF and explicitly assigns the expected band descriptions (`dst.set_band_description(i,name)`), so the test does NOT establish that live Earth Engine GeoTIFF delivery satisfies the description schema.

## Competing explanations to distinguish with one live capture

- The application may receive a six-band TIFF whose `src.descriptions[1:]` are absent or normalized differently.
- The application may receive fewer than six bands (e.g., download format / unexpected ZIP grouping) or an alternative schema.
- Stale deployed app version or an obsolete cached raster may also produce `unknown`; do not declare this hypothesis false without checking deployment commit and the `fetch_ntl_raster` cache/version.

**Current evidential status:** the deterministic code branch that generates `unknown` has been established, and all three field CSVs exhibit its output. The exact **live six-band `src.count` and `src.descriptions` remain unobserved** because the application-requested TIFF bytes were not captured. Therefore it is *not yet scientifically defensible* to state that Earth Engine definitely stripped the descriptions.

## Targeted corrective patch (one PR only, after confirming live raster schema)

1. Add a safe diagnostic at the network-to-raster interface: band count, descriptions, any ZIP members, and cache/deployment provenance (no credentials or raw raster upload required). Do not silently downgrade unrecognized schema to fully unknown without explaining the reason to the user.
2. Confirm band 1 exactly matches the pre-A02 legacy NTL contract at equal spatial settings.
3. Map valid six-band values to the known ordered semantic schema only if the producer provenance is established; refuse arbitrary six-band products instead of trusting band count alone. Explicitly distinguish absent label metadata from genuinely missing observation pixels.
4. Add one focused regression covering the **actual field condition** (e.g. nameless six-band geotiff) rather than increasing redundant synthetic test count, and confirm that known missing / zero / negative cases preserve intended semantics.
5. Perform field validation on an Earth Engine raster containing **genuine zero-support observations within the analysis polygon** before declaring A02 scientifically PASS.

**Decision:** retain the bug finding and scoped patch proposal in private staging for the user's single consolidated PR; do not open an isolated PR, alter NTL zero-fill policy, or claim A02 is fixed.

<!-- END ORIGINAL SOURCE 040 -->


---

## Source 041: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/V11_EDGE_ONLY_PRIVATE_EVIDENCE_2026-11-15.zip::V11_EDGE_COMPLETION_2026-11-15.md`

**Original bytes:** 4,368 · **SHA-256:** `4cdb1b84cf0ceb2cc970560c699967971d169da568840a1a67c3892221c66896` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 041 -->
# V11 — Cross-location 2020 edge-cell validation completion

Date: 15 November 2026. Repository: `hoanfg/spatial-app`. **Private staging evidence; not a new PR.**

## Scope and evidence boundary

- **New analysis only:** 1,847 clipped/partial 500 m polygons that were excluded from the earlier 15,330-cell independent raster check. No previously verified full-cell zonal computations were rerun.
- The new polygon inputs are the **three user-exported application GeoJSONs**. Their IDs, areas, centroids and `ntl_mean` exactly agree with the corresponding user CSVs (all 17,177 IDs), and their geometries are nonempty/valid. The independent VIIRS raster source is the 2020 Earth Engine reference export; the integration routine does not import any `spatial-app` zonal code.
- Pixel-by-polygon intersections are computed in the EPSG:4326 GeoTIFF plane (as in the raster zonal coverage definition); masked/nonfinite values are skipped and valid negative median radiances clipped at zero, matching the legacy NTL policy. All new edge polygons have valid reference raster coverage.

## New numerical results (edge cells only)

| Case | Clipped cells checked | Within strict 0.00005 | Strict exceedances | Maximum absolute error | Within 0.0000501 |
|---|---:|---:|---:|---:|---:|
| Shanghai / Nội đô Thượng Hải | 180 | 180 | 0 | 0.00004959946 | 180 |
| Shenzhen / Bao'an | 1,017 | 1,016 | 1 | 0.00005003932 | 1,017 |
| Huangshan / Qimen | 650 | 650 | 0 | 0.00004993913 | 650 |
| **Total** | **1,847** | **1,846** | **1** | **0.00005003932** | **1,847** |

The **one** strict exceedance is `Bao'an grid_id=628`, area 0.010610 km², CSV `ntl_mean=18.8768`, independent raster overlay `18.876850039319148`. Difference: `0.000050039319148`, exceeding the four-decimal half-bin (`0.00005`) by `0.000000039319148` (3.93 × 10⁻⁸).

This is a **borderline numerical/rounding discrepancy**, not evidence of materially incorrect radiance extraction. It is retained explicitly. With the stated additive 0.0000001 floating-point allowance, 1,847/1,847 edge cells pass. This does not override or re-label the strict comparison: **1 strict exception remains**.

## Combined interpretation of prior and newly completed V11 checks

| Evidence component | Current interpretation |
|---|---|
| Existing 15,330 whole-cell raster comparisons | Previously verified within strict four-decimal CSV rounding, reused unchanged |
| New 1,847 boundary-clipped raster comparisons | 1,846 strict pass + 1 tiny rounding-boundary exception; all 1,847 within 0.0000501 |
| All 17,177 app cells (NTL raster consistency) | No material discrepancy detected at output precision; nuanced one-cell strict exception above |
| Prior independent Queen adjacency / Local I / BH-FDR | Preserved, not recomputed |
| A02 per-cell observation support | **Not validated:** all 17,177 `dq_status=unknown`; tracked separately |
| GHSL native-grid conservation / Cloud benchmark | **Still pending; unrelated to V11 NTL validation** |

**Important independence limitation:** the reference radiance raster is external, but the boundary-clipped polygon geometries are application-exported GeoJSON. Their aggregate geographic area and bounding box were separately checked against GADM-curated source metadata on GitHub (GIDs: `CHN.24.1.10_1`, `CHN.6.15.1_1`, `CHN.1.11.1_1`). This is not a source-boundary, vertex-by-vertex reconstruction of every polygon. Prior GADM provenance audits remain in force and are not duplicated here.

## Input provenance and reproducibility

All raw GeoJSON files stay outside the public repository; do not commit multi-megabyte polygon datasets by default. Original user CSVs and external reference TIFFs likewise remain private. The edge metrics JSON records SHA-256 for each of the nine newly used inputs (3 GeoJSONs, 3 NTL CSVs, 3 reference TIFFs). Per-cell edge residual CSVs (1,847 records combined) are included only in the private staging evidence ZIP. Independently re-run `v11_edge_only_independent.py` on those exact files to reproduce the results.

**Disposition:** V11 2020 cross-location NTL/LISA scientific numerical field validation is complete in the stated scope, with one explicit near-rounding strict exception; this is **not** an A02 or GHSL field PASS. Hold compact evidence for the next single consolidated major-review PR, rather than opening a new PR now.

<!-- END ORIGINAL SOURCE 041 -->


---

## Source 042: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_app_single_pr_staging_2026-11-13.zip::PR_STAGING_NOTES.md`

**Original bytes:** 4,067 · **SHA-256:** `26a3a56a1a57839e45bb4066d32b92675c143ccbb676782afe14d93ad1caa4ae` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 042 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 13 November 2026. Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Seven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

<!-- END ORIGINAL SOURCE 042 -->


---

## Source 043: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_app_single_pr_staging_2026-11-13.zip::README.md`

**Original bytes:** 6,073 · **SHA-256:** `4fdb38e3ba95397c30d8679d12794f5623bd5dbe8d595d4488876671c923f2b5` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 043 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **13 November 2026**. Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code only, no Earth Engine credentials, private data or real-world result tables**. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** two synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A synthetic GHSL command-line smoke test also executed, with a 9-cell fabricated grid; that is **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV is a spatial-app cell export containing `grid_id`, `area_km2`, `ntl_mean` for the same GADM boundary and 500 m cell configuration.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (2 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

<!-- END ORIGINAL SOURCE 043 -->


---

## Source 044: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_app_single_pr_staging_2026-11-13_v2.zip::PR_STAGING_NOTES.md`

**Original bytes:** 4,067 · **SHA-256:** `26a3a56a1a57839e45bb4066d32b92675c143ccbb676782afe14d93ad1caa4ae` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 044 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 13 November 2026. Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Seven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

<!-- END ORIGINAL SOURCE 044 -->


---

## Source 045: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_app_single_pr_staging_2026-11-13_v2.zip::README.md`

**Original bytes:** 6,389 · **SHA-256:** `88d35d669a6caecbbfa0c6976d5e5a7f248a8177ab2de79015d2da53165d82f6` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 045 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **13 November 2026**. Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code only, no Earth Engine credentials, private data or real-world result tables**. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** seven synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV is a spatial-app cell export containing `grid_id`, `area_km2`, `ntl_mean` for the same GADM boundary and 500 m cell configuration.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Missing reference or application coverage is reported and causes a nonzero CLI exit code. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (7 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

<!-- END ORIGINAL SOURCE 045 -->


---

## Source 046: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_app_single_pr_staging_2026-11-14_v3.zip::PR_STAGING_NOTES.md`

**Original bytes:** 4,992 · **SHA-256:** `972a638ebbac490dc990ca0d5602f04a500ffe03d3d4b8d99e0a6b6581599c9d` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 046 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 14 November 2026 (revised from 13 November). Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Nine tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

## Review update 14 November 2026 — no new PR

- Hardened the GHSL check against **partial-coverage false positives**: eligible cells must have nearly 100% finite, unmasked raster area in BOTH native and app exports. Ineligible per-cell differences are NaN, not numerically compared.
- Added guard for GHSL native 100 m product resolution; a wrongly supplied 1 km raster fails preflight.
- Hardened A02 source independence: selecting ROI from the application's own band-1 mask could silently drop an app-side masked pixel. Reference valid-month count now defines the footprint, so this case fails.
- Negative controls expanded; `python -m pytest -q test_validation_scripts.py` now reports **9 passed**.
- All field validation gates remain unfulfilled without matching real-data rasters and application exports. Preserve project policy: **one future consolidated PR**, no branch/PR in this stage.

<!-- END ORIGINAL SOURCE 046 -->


---

## Source 047: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_app_single_pr_staging_2026-11-14_v3.zip::README.md`

**Original bytes:** 7,942 · **SHA-256:** `b3a3b72db9e8ef51843c77824bebf500ef359bafd9596b6cf91c6ba6eaef7648` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 047 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **14 November 2026** (updated from 13 November). Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code only, no Earth Engine credentials, private data or real-world result tables**. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** nine synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV is a spatial-app cell export containing `grid_id`, `area_km2`, `ntl_mean` for the same GADM boundary and 500 m cell configuration.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas and source 100 m resolution, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Each cell now reports native/app **valid-area fractions**, and a comparison is eligible only with at least 99.9999% valid area in both rasters. Merely intersecting a single valid pixel cannot justify full coverage. Missing or partial reference/application coverage is reported and causes a nonzero CLI exit code. Ineligible differences are blanked, while partial raw sums remain available only for diagnostics. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters. The **independent month-count** reference mask defines the comparison footprint; a missing/masked application pixel is flagged rather than excluded from validation. Extra app-only coverage outside the count reference also fails.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (9 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

## November 14 reviewer hardening

- GHSL now measures **fraction of each polygon covered by finite unmasked raster pixels**, not just the presence of any intersection. Only fully covered cells enter regional comparison totals and Spearman; partial diagnostics remain visible but never silently pass.
- Native GHSL must have projected 100 m resolution (within 1 m tolerance); the code still cannot independently prove the correct version/epoch/band without source metadata.
- A02 uses **independent reference count coverage** to choose pixels for validation. App-masked observations with valid reference count are checked as failures rather than skipped.
- Negative controls exercise one missing interior source pixel, invalid native product resolution, and an application-only missing A02 pixel. Nine tests pass as of this staging version.

See `REVIEW_FINDINGS_2026-11-14.md` for the checker's identified failure modes and scientific boundaries.

<!-- END ORIGINAL SOURCE 047 -->


---

## Source 048: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_app_single_pr_staging_2026-11-14_v3.zip::REVIEW_FINDINGS_2026-11-14.md`

**Original bytes:** 3,461 · **SHA-256:** `5ddace573c0c0c79920b1812a29b11205a3c2932bbfc57000558bf6d0975d95e` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 048 -->
# Spatial App — Staging review findings (14 November 2026)

## Executive finding

Three **potential false-assurance paths in the external validation checkers** were found and corrected in this staged package. These are **checker defects**, not demonstrated defects in the Spatial App production analysis. No changes were made to the GitHub repository.

| ID | Prior checker behavior | Risk | Hardening | Synthetic negative control |
|---|---|---|---|---|
| S01 | GHSL considered a cell covered if *any* finite pixel intersected it | An area with partly missing source data could be treated as fully comparable | Compute valid-area fraction per cell; require >= 0.999999 from both rasters; drop partial cells from quantitative differences; incomplete coverage forces non-zero CLI status | One interior source NoData pixel triggers incomplete coverage |
| S02 | GHSL accepted any projected native raster | A 1 km or unrelated grid could be mislabeled as the 100 m source | Native resolution within 1 m of 100 m required, still manually verify product/band/epoch | 1 km synthetic input rejected |
| S03 | A02 checked only the pixels where the application's first band had an unmasked value | A corrupted app-side mask could remove failing pixels from the test set | Use independent valid-month count raster to define reference footprint, flag extra app-only pixels | One app-only masked pixel is detected |

## Test execution

- Command: `python -m pytest -q test_validation_scripts.py`.
- Result: **9 passed** in the isolated synthetic checker suite.
- No field GHSL or new Earth Engine export was supplied or used in these tests.
- `pytest-results.xml` contains executable test evidence; `SHA256SUMS.txt` records staged file hashes.

## Scientific boundaries

- GHSL native data are per-pixel quantities (residential population count or built-up m²), not population or built-up density. Summation must account for pixel/polygon intersection fraction.
- Spatial App's GHSL `fetch_ghsl_raster` reprojects into EPSG:4326 at a requested 100 m scale and selects the first band; a potential bias due to reprojection remains **unquantified** without corresponding real source raster and app-exported GeoTIFF.
- A complete geometric coverage check cannot recover observational missingness that the application has previously converted to zero (`unmask(0)`). The detector reports this separately.
- Six-band A02 comparisons require three perfectly aligned real exports. Source-layer equivalence (same year, monthly filter and exact raster grid) remains a manual gate.
- CI PASS on 9 tests confirms only checker behavior under the included cases, not V11 completion, GHSL field accuracy or A02 field validity.

## Source method references

- GHSL POP product: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL BUILT-S product: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- GHSL JRC open downloads: https://human-settlement.emergency.copernicus.eu/download.php
- Earth Engine resampling: https://developers.google.com/earth-engine/guides/resample
- ExactExtract operations: https://isciences.github.io/exactextract/operations.html

## Staging policy

Do not open a new micro-PR for this report alone. The corrected tools and tests are held for the owner's **one consolidated future review PR**. The package contains no GHSL tiles or other large geospatial datasets and no credentials.

<!-- END ORIGINAL SOURCE 048 -->


---

## Source 049: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_app_single_pr_staging_2026-11-15_v4.zip::PR_STAGING_NOTES.md`

**Original bytes:** 5,978 · **SHA-256:** `fce7228d802a6989deb7eb352423d91ce1f403dde844d8cb24f06d5b5459a89d` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 049 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 14 November 2026 (revised from 13 November). Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Eleven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

## Review update 14 November 2026 — no new PR

- Hardened the GHSL check against **partial-coverage false positives**: eligible cells must have nearly 100% finite, unmasked raster area in BOTH native and app exports. Ineligible per-cell differences are NaN, not numerically compared.
- Added guard for GHSL native 100 m product resolution; a wrongly supplied 1 km raster fails preflight.
- Hardened A02 source independence: selecting ROI from the application's own band-1 mask could silently drop an app-side masked pixel. Reference valid-month count now defines the footprint, so this case fails.
- Negative controls expanded; `python -m pytest -q test_validation_scripts.py` now reports **11 passed**.
- All field validation gates remain unfulfilled without matching real-data rasters and application exports. Preserve project policy: **one future consolidated PR**, no branch/PR in this stage.

## 15 November 2026 — v4 single-PR carry-forward

1. Require **actual per-ID spatial identity** using UTM and WGS84 centroids, not only grid ID/area. The current production app already exports all required fields. Checker code and comparator are staged, not pushed to GitHub.
2. Reject non-integral valid-month counts in A02 references.
3. **11/11 isolated checker tests passed.** Deliberate same-area grid swaps and missing centroid columns are rejected.
4. Historical Yanqing 2020 GADM, real VIIRS raster and application CSV were checked with the amended comparator. Exactly **8,333/8,333** per-cell NTL references and centroid identity comparisons passed at exported rounding tolerances; detailed metrics JSON and source hashes are included, but private input raster/GeoJSON/CSV and the 8,333-row diagnostic table are *not* bundled.
5. No new branch, PR, production algorithm changes or geospatial data bundles. One consolidated PR remains the only proposed repository update.

<!-- END ORIGINAL SOURCE 049 -->


---

## Source 050: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_app_single_pr_staging_2026-11-15_v4.zip::README.md`

**Original bytes:** 9,716 · **SHA-256:** `a0b82b9fd376b4e8c3f96adfb7e8f7f7497e761a9f6dee2cf070c56371c284e9` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 050 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **15 November 2026** (incremental v4 of 13–14 November staging). Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code and a small, reproducible Yanqing 2020 metrics JSON**, but no Earth Engine credentials, private input GeoTIFFs, original GADM boundaries, or large per-cell result tables. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** eleven synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV must be a current Spatial App cell export containing `grid_id`, `area_km2`, `ntl_mean` and four rounded **per-ID centroids** (`centroid_lon`, `centroid_lat`, `centroid_x_epsgNNNN`, `centroid_y_epsgNNNN`) for the same GADM boundary and grid. Area and IDs alone are insufficient to detect identical-size cells reordered geographically.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas and source 100 m resolution, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Each cell now reports native/app **valid-area fractions**, and a comparison is eligible only with at least 99.9999% valid area in both rasters. Merely intersecting a single valid pixel cannot justify full coverage. Missing or partial reference/application coverage is reported and causes a nonzero CLI exit code. Ineligible differences are blanked, while partial raw sums remain available only for diagnostics. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters. The **independent month-count** reference mask defines the comparison footprint; a missing/masked application pixel is flagged rather than excluded from validation. Extra app-only coverage outside the count reference also fails.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (11 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

## November 14 reviewer hardening

- GHSL now measures **fraction of each polygon covered by finite unmasked raster pixels**, not just the presence of any intersection. Only fully covered cells enter regional comparison totals and Spearman; partial diagnostics remain visible but never silently pass.
- Native GHSL must have projected 100 m resolution (within 1 m tolerance); the code still cannot independently prove the correct version/epoch/band without source metadata.
- A02 uses **independent reference count coverage** to choose pixels for validation. App-masked observations with valid reference count are checked as failures rather than skipped.
- Negative controls exercise one missing interior source pixel, invalid native product resolution, and an application-only missing A02 pixel. Eleven tests pass as of this staging version.

See `REVIEW_FINDINGS_2026-11-14.md` for the checker's identified failure modes and scientific boundaries.

## 15 November addendum — grid identity and negative controls

- **GHSL:** per-cell UTM centroids (application exports rounded to 0.1 m) and geographic centroids (six decimal places) must match the independently reconstructed grid at their respective rounding precision. Omitting these four columns is an error, not permission to skip the spatial-identity check.
- **Cross-location comparator:** the staged `compare_raster_cells.py` now applies the same per-ID geometry gate *before* calculating raster zonal statistics. It is intended to replace the existing script in the **single future consolidated PR**, not to create a micro-PR.
- **A02:** reject a valid-month raster with fractional counts, which can indicate an improperly resampled month-count reference. A count of months must be integral.
- **Real-data regression:** independent raster–polygon overlay was rerun on the historical Yanqing 2020 archive. **8,333/8,333** NTL cells met the CSV rounding tolerance (0.00005 nW/cm²/sr), and **8,333/8,333** UTM/WGS84 centroids met their recorded rounding tolerances. See `yanqing_2020_regression_metrics.json` and the recorded input SHA-256s. A controlled swap of the locations of two equal-area historical cells was rejected.
- **Limits:** this is a reproducibility check of the previously archived Yanqing data, **not** a newly acquired VIIRS/A02 six-band or JRC GHSL dataset. V11, GHSL live comparison and A02 real missingness remain PENDING.

<!-- END ORIGINAL SOURCE 050 -->


---

## Source 051: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_app_single_pr_staging_2026-11-15_v4.zip::REVIEW_FINDINGS_2026-11-15.md`

**Original bytes:** 4,122 · **SHA-256:** `0ce9c8d7b12bc8066a5b1899516f55587a7e0ec3c9772be84c2611f48b1e69dd` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 051 -->
# Spatial App — Independent checker follow-up (15 November 2026)

## Decision

Continue staging changes for one future major-review PR; no new PR and no changes to production formulas. An area-only comparator can fail to detect a spatial identity mismatch for equal-area cells. Fix the independent checking tools before interpreting later GHSL comparisons.

## Finding S04 — same-area ID swaps bypass the previous area gate

- Observed in: both the staged GHSL comparator and the existing `validation/cross_location/compare_raster_cells.py` checked grid IDs, polygon counts and areas, but not **per-ID geographic identity**.
- Why this matters: two full 500 m grid cells both have `area_km2 = 0.25`; their polygon-to-CSV pairing can be wrong while an area and ID validation still reports success.
- Remedy staged: check rounded UTM centroids (`centroid_x_epsgNNNN` and `centroid_y_epsgNNNN`, tolerance 0.051 m) and geographic centroids (`centroid_lon`, `centroid_lat`, tolerance 0.00000051°) against the independently recreated clipped GADM polygon for each `grid_id`.
- Negative control: interchange the exported centroid coordinates of two equal-area cells while leaving `grid_id` and `area_km2` untouched. Both staged comparators reject the mismatch. Missing centroid metadata also forces explicit failure.
- Production code and CSV schemas: **unchanged**; required centroid columns already exist in normal current application exports.

## Historical Yanqing field regression

A replay of the updated `compare_raster_cells.py` used:

- full-precision GADM 4.1 Yanqing GeoJSON from the historical private archive;
- the VIIRS 2020 annual reference GeoTIFF from the same archive;
- the **original** application 2020 500 m CSV with UTM/WGS84 centroids;
- 500 m clipped UTM grid, matching the existing baseline inference geometry.

Results: **8,333/8,333 cells** passed the raster–polygon NTL comparison within 0.00005 nW/cm²/sr (MAE 0.0000250230; maximum absolute error 0.0000499933). All **8,333/8,333 cells** also met the geographic centroid identity rounding tolerances. The maximum UTM-x and UTM-y rounding discrepancies were 0.049872 m and 0.049979 m; maximum longitude/latitude discrepancy was below 0.0000005°. The source and script checksums are retained in `yanqing_2020_regression_metrics.json` and `SHA256SUMS.txt`.

This is an **independent recomputation using archived field input** from Yanqing, not new field sampling. A controlled same-area swap of two historical full-size cells was correctly rejected by the new check. It does not establish V11 across contrasting locations or GHSL product equality.

## Finding S05 — fractional monthly observation counts

The staged A02 checker checked count in `[0,12]` but did not reject, for example, `2.5` months of annual valid observation support. Such a value can arise if a reference count raster is improperly interpolated. The checker now requires integral valid-month counts, and the corrupted synthetic example is rejected.

## Scope availability on archived VIIRS rasters

Historical annual medians and month-count reference rasters have 30,814 pixels per year (2014 and 2020). In both cases all count pixels recorded 12 valid months and no median pixels were masked. The 2014 raster contained one negative valid median; 2020 had none. Neither case contained measured-zero medians or fewer-than-three-month support. **These real images cannot test the A02 data-semantics edge cases involving genuine missing observations.**

## Acceptance log

- **11 passed** — `python -m pytest -q test_validation_scripts.py` (synthetic oracle and negative-control tests).
- **8,333 passed** — Yanqing 2020 archived field raster/polygon comparator and per-ID centroid verification.
- **Expected fail** — spatial-identity negative control on two same-area historical cell IDs.
- **Not run / PENDING** — GHSL native JRC 100 m versus real Earth Engine reprojected raster; A02 true six-band export; Shanghai/Bao'an/Qimen independent per-cell validation; Cloud benchmark.
- No new PR, no code modification in `ntl/`, and no large GeoJSON/GeoTIFF committed.

<!-- END ORIGINAL SOURCE 051 -->


---

## Source 052: `07_ARCHIVES_AND_PRIOR_SNAPSHOTS/spatial_validation_followup_tools_2026-11-13.zip::README.md`

**Original bytes:** 6,073 · **SHA-256:** `4fdb38e3ba95397c30d8679d12794f5623bd5dbe8d595d4488876671c923f2b5` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 052 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **13 November 2026**. Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code only, no Earth Engine credentials, private data or real-world result tables**. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** two synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A synthetic GHSL command-line smoke test also executed, with a 9-cell fabricated grid; that is **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV is a spatial-app cell export containing `grid_id`, `area_km2`, `ntl_mean` for the same GADM boundary and 500 m cell configuration.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (2 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

<!-- END ORIGINAL SOURCE 052 -->


---

## Source 053: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial-app-audit-evidence.zip::claude-checklist.md`

**Original bytes:** 8,579 · **SHA-256:** `c30cd548bf98ceb052cca7e308655b10735c6d24fe6e93cbe3420b2f82633654` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 053 -->
# Báo cáo kiểm chứng: NTL spatial econometrics

Nov 11, 2026 · @hoang le

## Kết luận

**Logic tính toán đã được kiểm tra trên dữ liệu giả lập; chưa có bất kỳ phép thử nào trên dữ liệu vệ tinh thật.** 32 test qua, 2 test bị bỏ qua ở máy mình vì thiếu thư viện, và CI trên GitHub báo xanh cho bản `main` hiện tại. Không có benchmark đối chiếu với phần mềm khác hoặc kết quả đã công bố.

- **Đã kiểm chứng:** cú pháp, 32 test logic trên dữ liệu tổng hợp, CI xanh, và mã trong `main` trùng với mã đã kiểm (trừ một dòng tiêu đề giao diện).
- **Chưa kiểm chứng:** mã tải dữ liệu từ Earth Engine (đếm tháng, GHSL), các bảng điều khiển mới khi bấm nút, hiệu năng và bộ nhớ 1GB như README nêu, và các ngưỡng kết luận.
- **Hệ quả cho nghiên cứu:** chưa nên trích số liệu từ công cụ như bằng chứng thực nghiệm cho đến khi chạy một vùng thật và đối chiếu được (mục 4 và 5).

## Lệnh đã chạy và kết quả thực tế

Chạy ngày 11/11/2026 trên `main` tại commit `81a53c96`, Python 3.13.18, numpy 2.5.3, pandas 3.0.5, scipy 1.18.1, pytest 9.1.1. Máy này **không có** streamlit, altair, geopandas, rasterio, exactextract, earthengine-api và folium, và không cài thêm được vì mạng bị chặn.

| Lệnh | Kết quả thực tế | Ý nghĩa |
| --- | --- | --- |
| `python3 -m py_compile app.py ntl/*.py tests/*.py` | OK, không lỗi | Chỉ chứng minh cú pháp hợp lệ, không chứng minh đúng |
| `python3 -m pytest -q -rs` | 32 passed, 2 skipped trong 4,55 s | Skip: `test_ui_smoke.py` (thiếu streamlit), `test_zonal.py` (thiếu rasterio) |
| `pytest --collect-only` | 22 test ở `test_lisa_reliability.py`, 10 test ở `test_robustness.py` | T01–T20 lõi LISA, T21–T28 phần mới |
| `same_logic.py origin/robustness-suite` (so cây cú pháp AST) | Tất cả file `OK`, trừ `ntl/quality_ui.py` khác | Khác chỉ ở một chuỗi tiêu đề ("Kiểm tra sâu (chạy khi bấm nút)" thành "Kiểm tra sâu") và docstring. Logic trong `main` trùng mã đã kiểm |
| GitHub Actions, workflow `tests`, `main` @ `81a53c96` | `success` | CI có cài đủ thư viện, nên `test_zonal` và `test_ui_smoke` chạy ở đó. Mình thấy kết luận từng lần chạy, chưa đọc lại log chi tiết hôm nay |
| GitHub Actions, nhánh `robustness-suite` | Lần 1 `failure` (01:18 UTC), lần sau sửa test `success` (01:22 UTC) | Lỗi lần 1 là kỳ vọng sai trong `test_zonal` do mình tính nhầm, không phải lỗi mã |

## Benchmark và ngưỡng đã dùng

**Không có benchmark bên ngoài.** Trong các lệnh mình tra lại được, không có phép so sánh với PySAL/esda hay GeoDa (hai gói `esda` và `libpysal` không có trên máy này), không so với kết quả đã công bố, và không đo thời gian hay bộ nhớ. Các test kiểm tính đúng đắn nội bộ: bất biến toán học (ví dụ T07 kiểm định lý hoán vị của trung bình đệ tâm), trường hợp suy biến (toàn tối, hằng số, đảo biệt lập) và ổn định theo seed.

Các ngưỡng sau là **quy ước thực hành được đặt cứng trong mã, chưa hiệu chỉnh bằng dữ liệu hay tài liệu**:

| Ngưỡng | Giá trị | Dùng để |
| --- | --- | --- |
| Jaccard trung vị của các biến thể | ≥ 0,70 "vững"; ≥ 0,50 "trung bình"; dưới đó "yếu" | Kết luận độ vững của cụm High-High |
| "Lõi vững" | Là HH ở bản gốc và trong ít nhất 80% số lần chạy | Diện tích ổn định |
| Spearman ρ với GHSL | ≥ 0,60 "mạnh"; dưới 0,40 "yếu"; cần ít nhất 30 ô lõi | Mức đồng thuận ngoài |
| Bootstrap theo khối | 200 lần, khối 5×5 ô | Khoảng tin cậy của ρ |
| Cảnh báo chất lượng dữ liệu | pixel âm > 10%; có pixel NaN; ô bằng 0 > 50% (chỉ lưu ý); pixel không có tháng quan sát > 1%; pixel dưới 3 tháng > 20% | Khung "Chất lượng dữ liệu" |
| So sánh cắt âm / giữ âm | Cảnh báo nếu ρ dưới 0,98 hoặc tỷ lệ ô thay đổi vượt 10% | Kết luận về xử lý giá trị âm |
| Sàn p-value | 2 / (số hoán vị + 1) | Với ít hoán vị và FDR, cụm có thể không bao giờ bị bác bỏ (đã gặp với 199 hoán vị) |

Khi viết bài, nên gọi đây là ngưỡng mô tả tham khảo và báo cáo từng Jaccard thay vì chỉ nhãn "vững".

## Phép thử có dữ liệu thật

**Không có.** Trong các lệnh mình tra lại được, không có lần nào chạy trên ảnh VIIRS, dữ liệu GHSL hay ranh giới GADM thật.

- **Dữ liệu của các test** đều do mã tự sinh bằng `numpy.random.default_rng` với seed cố định (trừ `test_zonal`, dùng GeoTIFF nhỏ tự dựng trong bộ nhớ).
- **`test_zonal`** dùng thư viện thật (rasterio, exactextract) nhưng trên ảnh 2×4 pixel dựng sẵn. Nó chỉ chạy trên CI.
- **`test_ui_smoke`** chạy giao diện bằng `AppTest` với dữ liệu tổng hợp, không gọi Earth Engine. Nó kiểm tra tab LISA hiển thị không lỗi và có khung chẩn đoán; không bấm nút nào.
- **Thư mục `data/`** có ranh giới GADM của 35 nước nhưng không test nào đọc chúng.
- **Mạng:** môi trường chạy của mình không ra được Earth Engine và không có thông tin đăng nhập.

Bạn đã chạy ứng dụng thật ở spatial-app.streamlit.app và gửi ảnh chụp giao diện. Đây là bằng chứng rằng ứng dụng chạy được, nhưng mình chưa đối chiếu số liệu nhìn thấy trong ảnh với một nguồn độc lập.

## Những điểm chưa thể kiểm chứng

Bảng dưới đây nêu từng điểm, vì sao chưa kiểm được và cách kiểm.

| Điểm chưa kiểm chứng | Vì sao | Cách kiểm |
| --- | --- | --- |
| Mã tải từ Earth Engine: đếm tháng quan sát (`cf_cvg`), GHSL (`JRC/GHSL/P2023A/GHS_BUILT_S`, `GHS_POP`), tên band, epoch, giới hạn 3 triệu pixel | Không có mạng tới Earth Engine và không có thông tin đăng nhập; test chỉ dùng đối tượng giả (`MagicMock`) | Chạy từng nút trong ứng dụng thật với một vùng nhỏ; đối chiếu tên band và đơn vị với tài liệu dataset |
| Các khung mới khi bấm nút ("Chất lượng dữ liệu" ở tab Dữ liệu, "Kiểm định độ vững" ở tab LISA) | Smoke test chỉ hiển thị tab LISA, không bấm nút; khung "Chất lượng dữ liệu" nằm trong `app.py` nên không được test nào chạm tới | Mở ứng dụng, bấm từng nút, theo dõi lỗi; thêm test `AppTest` có bấm nút |
| Đúng đắn của LISA so với phần mềm chuẩn | Chưa cài `esda`, `libpysal` và không có mạng | Chạy cùng một lưới với esda (hoặc GeoDa), so Moran's I, quadrant, p-value với cùng seed và số hoán vị |
| Hiệu năng và giới hạn \~1GB RAM mà README nêu | Chưa đo thời gian hay bộ nhớ trên vùng lớn | Đo trên Streamlit Cloud với vùng lớn nhất bạn dự định; ghi đỉnh RAM và thời gian |
| Ngưỡng kết luận (Jaccard, ρ, các cảnh báo chất lượng) | Là quy ước, chưa hiệu chỉnh | Mô phỏng trên dữ liệu có đáp án biết trước; hoặc nêu rõ là tham khảo khi viết bài |
| Chuỗi VIIRS có bị đổi mã hóa hay hiệu chỉnh theo năm không (bộ `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG`) | Chưa tra tài liệu dataset; một bài 2026 nêu thay đổi mã hóa năm 2022 ở một sản phẩm VIIRS khác | Đọc mô tả dataset trên Earth Engine; vẽ ánh sáng trung bình cả nước theo năm để tìm bước nhảy |
| Khung "khoảng tối" có thực sự phát hiện nhà bỏ trống/bong bóng không | Không có dữ liệu giá nhà hay nhà trống để đối chiếu, và công cụ chưa tính "khoảng tối" như một đại lượng | Đây là việc của nghiên cứu, không phải của phần mềm: cần dữ liệu giá nhà/nhà trống của ít nhất một nước |
| Danh sách Contributors trên GitHub | API và lịch sử đã sạch; thanh bên vẫn hiện "claude" do bộ nhớ đệm | Kiểm tra lại sau vài ngày; nếu còn, liên hệ GitHub Support |

<!-- END ORIGINAL SOURCE 053 -->


---

## Source 054: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial-app-audit-evidence.zip::commands-and-evidence.md`

**Original bytes:** 4,191 · **SHA-256:** `f52b3288839c315b729e9de2adcabf1a98d07baf896cfd94d2805d259bffda21` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 054 -->
# Commands and evidence guide

Run PowerShell from the audit workspace (the parent of this outputs directory). Commands below are the successful final workflow, consolidated for reproduction. Earlier failed installation attempts remain in the install logs. This does not change the pinned repository source.

```powershell
$base = (Get-Location).Path
New-Item -ItemType Directory -Force work,outputs | Out-Null
git clone --filter=blob:none --no-checkout --depth 1 --single-branch --branch main https://github.com/hoanfg/spatial-app.git work/audit-repo
git -C work/audit-repo sparse-checkout init --cone
git -C work/audit-repo sparse-checkout set ntl tests docs .github .streamlit data/gadm41_CHN_gpkg
git -C work/audit-repo checkout main
git -C work/audit-repo rev-parse HEAD
# Audited SHA must be 81a53c96eb1405c56665146325383c6e02350dc9.
# If main has changed, explicitly fetch and checkout that SHA before comparing results.
py -3.13 -m venv work/venv
$python = Join-Path $base 'work/venv/Scripts/python.exe'
& $python -m pip install -r work/audit-repo/requirements.txt scipy pytest esda libpysal psutil numba
& $python -m pip check
& $python -m pip freeze
Push-Location work/audit-repo
& $python -m compileall -q app.py ntl tests
& $python -m pytest -vv -ra
Pop-Location
Invoke-WebRequest 'https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_CHN.gpkg' -OutFile work/gadm41_CHN.gpkg
Invoke-WebRequest 'https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_CHN_3.json.zip' -OutFile work/gadm41_CHN_3.json.zip
& $python outputs/audit_harness.py gadm raster numeric
& $python outputs/gadm_source.py
& $python outputs/schema_check.py
& $python outputs/moran_n30.py
& $python outputs/ui_clicks.py
& $python outputs/quality_ui_click.py
& $python outputs/ee_probe.py
& $python outputs/benchmark.py
& $python outputs/municipality_benchmark.py
git -C work/audit-repo diff --exit-code
git -C work/audit-repo diff --cached --exit-code
git -C work/audit-repo status --porcelain=v1
git -C work/audit-repo ls-remote origin refs/heads/main
```

The harnesses in outputs can be run directly in this workspace. They resolve the workspace as their parent directory and expect the clone and virtual environment under work. They write result files to outputs; rerunning can replace prior result files. The report describes the original dated run and is not automatically refreshed by rerunning individual harnesses. For exact package reproduction use environment-freeze.txt, rather than resolving the latest dependencies again.

Logs from the actual run:

- pytest-full.log: all 36 tests, including real raster and Streamlit imports, no skips.
- dependency-install.log, requirements-install.log, requirements-retry.log: package install attempts and successful retry. The first requirements attempt overlapped pip operations and hit a Windows file lock; the sequential retry succeeded.
- gadm-raster.log: preliminary GADM pass plus independent raster tests. Preliminary comparison to simplified GeoJSON is superseded by china-gpkg-validation.json and china-schema-validation.json. Its raw NAME_1 mismatch count reflects schema remapping, not lost districts.
- china-gpkg.log: authoritative full-resolution GADM comparison.
- moran-comparison.log and moran-n30-exact.log: numeric comparisons, exact null distributions.
- ui-clicks.log and quality-ui-click.log: additional AppTest runs. Expected Streamlit deprecation/bare-mode warnings may appear; results are in corresponding JSON files.
- earth-engine-probe.log/json: network success and explicit authentication block.
- ram-benchmark.log/json: corrected process-tree memory monitor; synthetic raster workload.
- municipality-grid-benchmark.log/json: real geometry grid workloads and Chongqing guard.
- final-checks.log: dependency consistency, compilation, commit and main verification. Python generated untracked __pycache__ directories during testing; no tracked source files were modified.

Source and result hashes are provided. The source GADM and clone are retained in work, outside the evidence ZIP. The ZIP contains the report, commands, harnesses, raw result tables, logs and environment information, not the large repository/virtual environment.

<!-- END ORIGINAL SOURCE 054 -->


---

## Source 055: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial-app-audit-evidence.zip::verification-report.md`

**Original bytes:** 19,853 · **SHA-256:** `c940de78b45f6db6d6f8f66841d82f6036240f134a2c6e58aa87a8ad227d3931` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 055 -->
# Independent audit of hoanfg/spatial-app

Audit date: 11 November 2026 (Asia/Saigon). Commit: **81a53c96eb1405c56665146325383c6e02350dc9**. Branch main was checked against origin before and after testing. The repository's tracked files were not edited. All additional harnesses live outside the clone.

## Assessment

The existing software suite is reproducibly healthy with full GIS dependencies: **36 passed, 0 skipped, 27.02 seconds**. This strengthens the evidence beyond the Claude report's 32 local passes and dependency skips. It does **not** justify an unconditional statement that the application or its scientific inferences are validated.

The independent checks found a consequential difference in LISA inference: the app samples neighbors **with replacement**, whereas the conventional conditional permutation benchmark samples without replacement. Local statistics also use a different normalization from ESDA. A source-metadata check found one district-name mismatch. Fractional raster extraction works on the tested cases, but finite NoData sentinels lose their masks.

Real VIIRS, observation-count and GHSL downloads remain **blocked by absent Earth Engine authorization**. The network itself worked. No real satellite measurements or empirical proxy correlations were produced.

## Reproducibility and scope

A Git partial clone with a sparse checkout was used: complete application source, tests, docs, workflow/config files, and all China data. Other countries' data and full historical blobs were intentionally not downloaded. This is a clone of the actual pinned commit, not code reconstructed from a chat preview. The two earlier unfiltered clone attempts were stopped in favor of this smaller clone.

The original uploaded Claude report is preserved as `claude-checklist.md`. Python **3.13.7**, Windows 11, 4 physical/8 logical CPUs and **7.86 GiB physical RAM** were used. Full dependency versions are in `environment-freeze.txt`; installation logs include the initial overlapping-pip file-lock failure and the successful sequential retry. `pip check` reports no broken requirements. Important libraries: geopandas 1.2.0, rasterio 1.5.2, exactextract 0.3.0, ESDA 2.10.0, libpysal 4.15.1, NumPy 2.5.4, SciPy 1.18.1, Streamlit 1.67.0. See the freeze for the complete environment.

Selected pure functions in `app.py` were extracted using Python's AST, with their original function bodies unchanged and caching decorators removed, to avoid launching the application or initializing Earth Engine. The required globals were supplied by the harness. This tests those functions directly; it is not an end-to-end authenticated app run.

| Claude checklist item | Independent result | Evidence |
| --- | --- | --- |
| Syntax | Passed compilation of app, ntl and tests | final-checks.log |
| Complete existing suite | 36 passed, no skipped tests | pytest-full.log |
| GIS/exactextract dependencies | Installed and exercised | dependency-install.log; requirements-retry.log |
| Local/Global Moran against PySAL | Global matches; Local scaling and null-model differences identified | moran-comparison.json; moran-n30-exact.json |
| Real China GADM geometry and metadata | All 2,420 geometries checked; one source-name mismatch | china-topology-validation.json; china-gpkg-validation.json; china-schema-validation.json |
| Four municipalities | Separate units preserved; source units selected by their IDs cover GADM level 1 | china-gpkg-validation.json |
| Synthetic zonal extraction | Existing tests and independent fractional-coverage tests passed; finite NoData limitation reproduced | raster-comparison.json |
| Additional UI buttons | Five LISA/panel buttons and offline negative-clipping button ran without exceptions/errors | ui-clicks.json; quality-ui-click.json |
| Real VIIRS / cloud-free month count / GHSL | Blocked: Earth Engine account not authorized | earth-engine-probe.json |
| 500 m RAM | Measured synthetic grid/extraction/LISA plus real municipality grid construction | ram-benchmark.json; municipality-grid-benchmark.json |
| Threshold calibration / housing-vacancy interpretation | Not empirically validated; no ground-truth dataset supplied | Scope limitation |
| VIIRS temporal continuity across 2022 | No real time-series test possible without authorized data access | Scope limitation |
| GitHub CI history | Workflow configuration reviewed; historical CI logs were not independently re-audited | Local full-suite run supplies direct evidence instead |
| Contributor sidebar cache | Outside the computational audit; not tested | No claim made |

## Findings requiring attention

### 1. Local Moran inference uses a different conditional null model (high priority)

`ntl/lisa_core.py:local_moran` draws neighbor indices using `rng.integers` for each neighbor slot. The focal observation is excluded, but other observations can repeat within the same simulated neighborhood. This is conditional resampling **with replacement**, not the usual conditional randomization without replacement. It changes the null distribution, particularly for small active samples or high neighbor counts. Matching a seed alone cannot make two different algorithms equivalent.

For a 3×3 synthetic grid corner, exhaustive enumeration gives a two-sided smaller-tail probability of **0.142857** without replacement (56 combinations), versus **0.218750** with replacement (512 ordered samples). The app gives **0.221020** using 99,999 simulations, consistent with its with-replacement implementation.

This also occurs at the app's stated minimum sample size, not only on a nine-cell illustration. On a 30-cell 6×5 grid, exact corner probabilities are **0.564860** without replacement and **0.583624** with replacement; the app gives **0.579220**, and ESDA gives **0.562700** after explicitly converting its one-tail pseudo p to the two-tail convention. In this particular 30-cell fixture, the app identifies **0** cells at unadjusted 5%, versus **1** for ESDA. This is one reproducible fixture, not an estimate of the error rate across real datasets.

The application counts both tails inclusively with a 1e-12 tie tolerance. ESDA's smaller-tail handling also differs at ties. Consequently raw `p_sim` values must not be compared as if all conventions were identical. The exact enumerations isolate the with/without-replacement difference independently of those tie and seed details.

Recommendation: choose and document the intended conditional null; use sampling without replacement if conventional ESDA/GeoDa comparability is intended, then rerun significance, FDR and downstream hotspot checks. **No fix was applied.** Until resolved, report LISA significance as this implementation's custom resampling result, not as independently ESDA-validated inference.

### 2. Local I normalization differs from ESDA (explicit convention required)

For all six Queen/Rook cases (n=9, 100, 400), all raw quadrants agree. The app's unrounded Local I equals ESDA Local I multiplied by **n/(n−1)**. Multiplying the app values by (n−1)/n leaves a maximum discrepancy of about **1.8e-15**. This is a normalization difference rather than evidence of wrong neighbor signs or quadrants. It should be documented or aligned before exchanging Local I values with ESDA.

This scaling is separate from the p-value problem above. Changing only the scaling will not correct the null model.

### 3. One China district name differs from the GADM source (medium priority)

The file `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Hunan_Yiyang/CHN_Hunan_Yiyang_Yiyang_District.geojson` has `GID_2 = CHN.14.10.2_1` and `NAME_2 = Yiyang`. The matching GADM 4.1 level-3 source record has `GID_3 = CHN.14.10.2_1` and **NAME_3 = Nan**. Its geometry is preserved; its display/file label does not preserve the source name. This can misidentify selected or exported observations even when the geometry is correct. No rationale for the alias was established in this audit.

All other **2,419** source level-3 names match exactly. All **2,420** types match source `ENGTYPE_3`.

### 4. Finite raster NoData masks are dropped (limited current-path exposure)

`ntl/zonal.py:zonal_stat` reads an unmasked array and rewrites it without copying the source NoData metadata. On a one-row raster `[10, -9999]`, where -9999 is explicitly marked NoData, the clipped mean is **5**, whereas a mask-preserving mean of valid pixels is **10**. Keeping negatives would also admit the sentinel into calculations.

The main `app.py` path uses the same read/rewrite pattern. The current Earth Engine path explicitly unmask-fills missing values with zero upstream, so this fixture is a robustness limitation for finite-sentinel rasters, not proof that an actual Earth Engine result was corrupted. Zero-filling absent observations is itself an intentional measurement convention and must remain visible in provenance.

## Numerical and raster checks

Global Moran in `app.py:morans_i` uses **binary Queen weights**. With that same weight definition, ESDA and the app agree to numerical precision: for n=100, app I = **0.2774650541675269**, ESDA I = **0.27746505416752687**. The second n=400 case also matches to numerical precision. This validates the observed I on the tested grids; no claim of identical p-values is made where permutation generators or tail definitions differ.

Local Moran uses **row-standardized** weights on the active/lit, non-edge sample. Comparisons used the same active sample and remapped ESDA's quadrant codes. Main-app binary Global Moran and the LISA region summary are not interchangeable statistics: their weights and potentially their samples differ.

The independent 2×2 raster test used fractional polygon coverage and deliberately nonsequential IDs. A polygon spanning half of all four pixels yields mean **4**, weighted sum **8**; the single top-left pixel yields **1** for both. Ordering is retained. Outside-raster mean stays NaN when `fill_missing=None`; an outside sum is zero. The existing negative-clipping and NaN-to-zero tests also passed. These cases establish tested fractional-coverage behavior, not the accuracy of every projection/resampling configuration or real satellite product.

## China GADM validation

All **2,420** curated GeoJSON files were decoded and checked: no invalid/empty geometry, no duplicate district GID, and no pairwise polygon overlap exceeding **1 m²**, measured after projection to EPSG:6933. Sub-m² slivers and exact zero-tolerance topology were not asserted away.

The full-resolution official GADM GeoPackage has **2,421** level-3 records. Every curated ID matches a source level-3 ID. The sole omitted source record has every administrative attribute set to the literal `NA`; it is not silently counted as a named district. No unmatched curated ID was found.

All **2,420** curated geometries match the source coordinate structure after Polygon/MultiPolygon normalization and coordinate tolerance **1e-8 degree**; maximum relative planar area discrepancy is **5.09e-13**. This demonstrates preservation of the downloaded GADM source within serialization precision, not present-day legal boundary accuracy. The source GeoPackage SHA-256 is recorded in `source-hashes.json`.

The curated schema is deliberately remapped: source `GID_3` becomes curated `GID_2`; `NAME_3` becomes `NAME_2`; `ENGTYPE_3` becomes `TYPE_2`; and curated `NAME_1` is the processing folder/group, often province plus prefecture, rather than always the original province. All folder grouping rules match after normalization of accents, whitespace and punctuation. External joins must use the preserved ID, not assume original GADM column semantics.

| Municipality | Curated units | Folder | Source units selected by curated IDs vs ADM1 symmetric-difference fraction |
| --- | ---: | --- | ---: |
| Beijing | 11 | Beijing | 0 |
| Shanghai | 12 | Shanghai | 0 |
| Tianjin | 12 | Tianjin | 0 |
| Chongqing | 32 | Chongqing | 0 |

The zero fractions are computed from source subdivisions selected by the curated ID set; preservation of the actual curated coordinates is established separately at the 1e-8-degree tolerance above. Thus these municipalities were not accidentally replaced with one whole-city analysis file. Their subdivision count and any aggregated central-city unit reflect this GADM source; this does not establish that they are a complete set of today's official districts.

An initial comparison used GADM's much smaller downloadable GeoJSON, whose geometry differs from the full-resolution GeoPackage. Exact geometry equality and raw NAME_1 comparisons from that preliminary pass are superseded by the GeoPackage and explicit schema-mapping checks. Do not interpret the preliminary differences as missing or corrupted geometry.

## Earth Engine and dataset checks

The Earth Engine discovery endpoint returned HTTP **200**, as did the GHSL catalog. `ee.Initialize()` failed with `EEException: Please authorize access to your Earth Engine account ...`. No authentication ceremony was started and no private keys were requested or copied.

Planned live ROI: **116.38–116.40° E, 39.89–39.91° N**, year **2020**. Annual VIIRS median, cloud-free observation-month raster, GHSL built-up and GHSL population were all gated on successful initialization and therefore **not executed**. There is no live-data agreement statistic in this report.

The public catalog confirms the app's VIIRS dataset identifier and bands `avg_rad`/`cf_cvg`, and GHSL dataset identifiers and semantic bands `built_surface`/`population_count`. GHSL epochs are spaced five years apart, with interpolation/extrapolation in the products. The code's `nearest_epoch` caps selection at 2020; that cap should not be read as proof every 2020 pixel is a direct observation. Selecting GHSL band index 0 is position-dependent and was not exercised against the live collection here.

The `MAX_PIXELS=3,000,000` preflight is a code safeguard, not an empirical proof all download shapes satisfy Earth Engine limits. Official getDownloadURL limits also include **32 MB** and **10,000 pixels per dimension**. Long thin regions and reprojection details remain untested against the service.

VIIRS nominal pixel size **463.83 m** is a length, approximately **0.215 km²** per square pixel; a 500 m analytical cell is **0.25 km²**. Neither should be described as 463 or 500 square metres. The monthly product is not filtered for all temporary lights/background. No empirical calibration, temporal discontinuity test, vacancy/price validation, or causal interpretation was established.

## 500 m memory benchmarks

Each case ran in a fresh subprocess. The monitor sampled at 50 ms and included the Python launcher **and all child processes**, recording peak summed resident RAM and peak private committed bytes. The first launcher-only monitor was recognized as invalid and discarded; only corrected runs below are used. There was no enforced 1 GiB container limit. Peak RSS sampling can miss short spikes, and summed RSS may double-count shared pages. Windows private commitment is not Linux container RSS.

Synthetic cases use square UTM boundaries, one float32 raster pixel per 500 m cell, the actual `build_grid`, actual `zonal_stat`, and actual `run_lisa` with **499 permutations**. The raster values are synthetic. Global Moran, Folium rendering, Streamlit/cache state, real EE response buffers, and concurrent sessions are excluded. Pure-function harness overhead is included. Runs were single measurements; timings are indicative and affected by other audit work on the same machine.

| Cells | Grid seconds | Zonal seconds | LISA seconds | Peak RSS MiB | Peak private MiB |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 0.47 | 3.85 | 0.80 | 162.6 | 609.9 |
| 50,176 | 2.56 | 20.33 | 9.33 | 215.5 | 665.3 |
| 149,769 | 9.24 | 65.97 | 29.54 | 343.4 | 798.1 |

Real municipality geometries were unioned and reprojected with the app's dynamic UTM rule, then passed to its unmodified grid constructor. These cases measure **grid construction only**, not real VIIRS extraction or whole-city LISA:

| Municipality | Result / cells | Grid seconds | Peak RSS MiB | Peak private MiB |
| --- | ---: | ---: | ---: | ---: |
| Beijing | 66607 | 26.234 | 209.9 | 423.8 |
| Shanghai | 29021 | 136.381 | 191.9 | 400.3 |
| Tianjin | 47677 | 33.932 | 183.2 | 394.0 |
| Chongqing | Guard rejected | 0.000 | 109.9 | 301.8 |

Chongqing's bounding-box estimate is **844,161**, exceeding the preclip guard **600,000**; it rejects before allocating the grid. Its estimated clipped count is **333,830**, also beyond the 150,000 cap. Beijing, Shanghai and Tianjin do build at 500 m in this environment. Therefore the blanket claim that every whole-city 500 m grid is impossible is unsupported, while partitioning large or complex areas remains useful and Chongqing's rejection is verified.

These results do **not** verify the README's universal “within 1GB without crashing” claim on Streamlit Community Cloud. A full authenticated app/container workload, real geometry/raster complexity, caching, and concurrent user activity could increase memory. No cloud OOM experiment was performed.

## UI coverage and remaining limits

The existing two Streamlit AppTests passed. An additional harness clicked seed stability, raw/P99/log comparison, tail-fraction sensitivity, robustness checks, and add-to-panel using the suite's 400-cell synthetic fixture. All five had zero app exceptions and zero `st.error` elements. A separate raster-backed quality-panel test clicked “compare without clipping negatives” and populated the expected cache (4 cells, 25% changed, maximum difference 2).

These are AppTest checks, not manual browser/rendering QA. Earth Engine-backed quality buttons and the real acquisition-to-export workflow remain blocked by authentication. No claims are made for external housing/vacancy validity, calibrated “strong/weak” thresholds, multi-year continuity or production cloud behavior.

## Next actions supported by evidence

1. Resolve/document the conditional permutation model and Local I normalization before relying on LISA significance as ESDA-compatible.
2. Review the Nan/Yiyang source-name discrepancy using `CHN.14.10.2_1` as the identity.
3. Preserve finite NoData masks if accepting rasters beyond the current zero-unmasked EE path.
4. Run the supplied Earth Engine probe in an authorized project, then compare real annual values, observation counts, GHSL aggregation and temporal continuity.
5. Measure the complete deployed application under its actual memory limit before retaining an unconditional 1 GB reliability claim.

No repository fixes or external publications were made.

## Primary references

- [Audited commit](https://github.com/hoanfg/spatial-app/tree/81a53c96eb1405c56665146325383c6e02350dc9)
- [GADM 4.1 download page](https://gadm.org/download_country.html) and [China full-resolution GeoPackage](https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_CHN.gpkg)
- [VIIRS monthly VCMSLCFG catalog](https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_MONTHLY_V1_VCMSLCFG)
- [GHSL built surface catalog](https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S)
- [GHSL population catalog](https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP)
- [Earth Engine getDownloadURL limits](https://developers.google.com/earth-engine/apidocs/ee-image-getdownloadurl)
- ESDA implementation actually installed: see `esda-reference-excerpts.txt` and package version in `environment-freeze.txt`; comparison formulas were inspected locally rather than relying on recalled documentation.

<!-- END ORIGINAL SOURCE 055 -->


---

## Source 056: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial_app_2026_11_11_validation_evidence_complete.zip::yanqing_2014_temporal_raster_validation_report.md`

**Original bytes:** 5,654 · **SHA-256:** `41d2a8ea43a81d53c560c1f35644ec92705843baa9660432e67eb578aab3086c` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 056 -->
# Independent VIIRS 2014 & Temporal Input Validation — Yanqing, Beijing

**Date:** 2026-11-11  
**Reference app commit:** `9574cf872c52d266aa15c363df7965cce31601f0`  
**Region:** GADM v4.1 `CHN.2.1.11_1` (Yanqing), 500 m analysis grid, EPSG:32650.

## Result: PASS for 2014 VIIRS extraction

An independent Google Earth Engine 2014 annual-median GeoTIFF was combined with the **8,333 original clipped polygons**, recovered from the independently audited 2020 validation evidence. Area-weighted pixel–polygon overlap was calculated without importing spatial-app's `exactextract` implementation. To match the app, each finite negative radiance pixel was clipped to zero **before** zonal averaging.

| Measurement | Result |
|---|---:|
| Number of cells | 8,333 |
| Matches within CSV's 4-decimal precision (absolute difference ≤ 0.00005) | **8,333 / 8,333** |
| Mean absolute difference | **0.0000250540** nW/cm²/sr |
| 95th-percentile absolute difference | **0.0000476443** nW/cm²/sr |
| Largest absolute difference | **0.0000499896** nW/cm²/sr |
| Pearson correlation | **0.999999999785** |
| Full 500 m squares | 7,703 / 7,703 passed |
| Slightly clipped cells | 30 / 30 passed |
| Edge-masked cells | 600 / 600 passed |

### Raster / coverage audit

The 2014 annual-median zero-filled reference, NoData-preserving median and month-coverage GeoTIFF all have **217 × 142 = 30,814 pixels**, CRS **EPSG:4326**, and the same affine transform as the independently exported 2020 reference raster. Their spatial extent and pixel grid match exactly.

- `yanqing_valid_months_2014.tif`: **all 30,814 pixels have value 12** (the count of monthly images with `cf_cvg > 0`), with no masked pixels. This is not equivalent to 12 individual clear-sky satellite observations.
- `yanqing_viirs_2014_masked_median.tif`: **no masked/NoData pixels**, `nodata=-9999` recorded in metadata. Every pixel value equals the zero-filled median file, so `unmask(0)` does not influence this particular output.
- The reference median has **one pixel of negative radiance**, minimum **−0.010230635 nW/cm²/sr**. As spatial-app clips finite negatives to zero before computing grid means, independent reproduction must do likewise. That single pixel affects two grid cells, `grid_id=7442` and `7443`. Raw un-clipped zonal means are **0.016861** and **0.038360**; clipped means **0.022089** and **0.039794**, matching webapp exports `0.0221` and `0.0398` to four decimals. This confirms the clipping rule has a measurable, localized effect in 2014, though not large at district scale.

### Temporal comparison (2014 → 2020)

For the same 8,333 grid cells, comparing independently extracted **2014 annual-median means** with the app's validated **2020 grid means**:

| Metric | 2014 | 2020 |
|---|---:|---:|
| Unweighted mean cell NTL (nW/cm²/sr) | **0.445159** | **1.413719** |

- Mean change: **+0.968560** nW/cm²/sr; 2020 mean was roughly **3.176 times** 2014 (about **+217.6%**).
- **8,221 cells increased** in absolute NTL, **112 cells decreased**; none are tied using extracted 2014 values and four-decimal 2020 values.
- The app assigns **4,711** cells to `4_Synchronized_Decline`, but among these **4,624 increased** in absolute NTL and **87 decreased**.

**Interpretation:** `Synchronized_Decline` in `run_spacetime_lisa` is defined when the year-standardized `log1p(NTL)` z-score **and** neighboring z-score both fall (`delta_z < 0`, `delta_lag_z < 0`), conditional on movement magnitude ≥0.05. It measures **declining relative standing**, not a drop in absolute radiance or evidence of economic contraction. The four regimes are directional classifications, **not independently statistically significant Local Moran tests**. A clearer display label is `Synchronized Relative Decline` with an explicit explanatory note.

### Scope and limitations

This test establishes **computational reproduction** of 2014 VIIRS extraction and, together with prior 2020 audit, validates both temporal endpoint inputs at exported CSV precision. It does **not** establish sensor calibration accuracy, causal economic interpretation, a continuous 2014–2020 annual trend, or the appropriateness of using nighttime lights as a GDP proxy.

- GeoTIFFs were exported through Google Earth Engine's `Export.image.toDrive`, whereas the app uses `getDownloadURL`. The two outputs here share the same spatial grid and reproduce output means, but this does not prove all raster exports always align identically.
- The 2020 data in the basic temporal counts come from the app's 2020 column, previously verified against the separate 2020 reference raster (8,333/8,333).
- Source-cell CSV stores four decimal places. Equality can only be established **within its rounding precision**, not to full unrounded pixel or geometry precision.
- Because all 2014/2020 pixel locations are covered by twelve monthly composites in this export, missing-data robustness here is uninformative for less-observed locations/years.
- The year-by-year magnitude of NTL increase should not automatically be attributed to economic growth: satellite calibration, processing, background removal, measurement choices and local circumstances can contribute.

## Artifacts

- `yanqing_2014_viirs_cell_validation.csv`: original and independently calculated 2014 NTL cell means and absolute errors for all cells.
- `validate_viirs_2014.py`: polygon–pixel overlap code, from source GeoTIFF to per-cell output.
- `yanqing_2014_validation_execution.log`: execution output and detailed comparisons.
- The 2014 source rasters, temporal input CSV and 8,333-cell reconstructed GeoJSON are included in the evidence archive.

<!-- END ORIGINAL SOURCE 056 -->


---

## Source 057: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial_app_2026_11_11_validation_evidence_complete.zip::yanqing_2020_measurement_sensitivity_report.md`

**Original bytes:** 5,885 · **SHA-256:** `d587529713166268fcbab5f2f0f807399777540fb41dcd3d198abbd31cbb6b3a` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 057 -->
# Measurement sensitivity validation — Yanqing, Beijing (2020, 500 m)

**Ngày:** 11/11/2026. **Đối tượng:** 8.333 ô lưới của Diên Khánh (Yanqing), `CHN.2.1.11_1`, 2020. **Mã ứng dụng được đối chiếu:** commit `9574cf872c52d266aa15c363df7965cce31601f0` sau PR #10.

## Kết luận chính

**Đạt kiểm chứng tính nhất quán về dữ liệu và độ nhạy đo lường trong pilot này:**
- `masked median` và `zero-filled median` giống nhau **tuyệt đối** tại cả 30.814 pixel của raster đã tải; masked median có **0 pixel NoData**. Do đó, không có thay đổi NTL/Gini/Moran/LISA khi giữ mask cho mẫu này.
- Đổi `annual median` thành `annual mean` làm tăng NTL trung bình không trọng số **4.366%**, từ **1.4137188** lên **1.4754449 nW/cm²/sr**. Gini NTL tăng từ **0.6809244** lên **0.6861015**.
- Binary-Queen Global Moran's I trên toàn bộ ô từ **0.914128499** lên **0.914558970**. Đây là Moran tính độc lập trong script trên toàn bộ mẫu, không nhất thiết bằng một chỉ số khác của LISA panel.
- Giữ nguyên quy trình LISA (999 conditional permutations **không hoàn lại**, seed 42, hai đuôi, tie tol 1e−12, BH-FDR alpha 0.05): HH từ **370** lên **385**, LL từ **2510** xuống **2499**. Jaccard HH **0.96104**, LL **0.96201**.
- Baseline median tái lập **100% nhãn LISA** từ CSV ứng dụng, cùng số HH và LL, giúp phân biệt ảnh hưởng tổng hợp ảnh tháng khỏi khác biệt giả lập.

## Input và kiểm tra GeoTIFF

| Raster | Kích thước | Pixel NoData | Min–max trong ROI | Bản chất |
|---|---:|---:|---:|---|
| Baseline median+zero | 217×142 | 0 | 0.225–59.445 | `yanqing_viirs_2020_reference.tif` |
| Annual mean+zero | 217×142 | 0 | 0.236–57.370 | `yanqing_viirs_2020_annual_mean.tif` |
| Median giữ NoData | 217×142 | 0 | 0.225–59.445 | `yanqing_viirs_2020_masked_median.tif` |

- Ba ảnh có cùng hệ tọa độ EPSG:4326, affine transform và kích thước. `masked median` có metadata `nodata=-9999`, nhưng không chứa pixel mask thực tế trong phạm vi xuất.
- File đếm tháng quan sát `yanqing_valid_months_2020.tif` đã được kiểm tra trước đây: các pixel xuất ra đều có 12 tháng hợp lệ; điều này nhất quán với kết quả không có pixel missing trong median của mẫu này.
- Ranh giới GADM và lưới 500 m đã được dựng lại từ dữ liệu kiểm định trước; **trung bình mỗi ô được tính bằng diện tích giao nhau của polygon và pixel**, không dùng lấy mẫu tại tâm ô, không import `ntl.zonal` hoặc `exactextract`.

## Các chỉ tiêu so sánh

| Chỉ tiêu | Median baseline | Annual mean | Masked median |
|---|---:|---:|---:|
| NTL trung bình không trọng số | 1.4137188 | 1.4754449 | 1.4137188 |
| NTL trung bình có trọng số diện tích | 1.4454962 | 1.5091569 | 1.4454962 |
| Gini toàn bộ 8.333 ô | 0.6809244 | 0.6861015 | 0.6809244 |
| Gini 7.733 ô không biên | 0.6861742 | 0.6910807 | 0.6861742 |
| Global Moran binary Queen, toàn vùng | 0.914128499 | 0.914558970 | 0.914128499 |
| Global Moran binary Queen, không biên | 0.914175690 | 0.914704806 | 0.914175690 |
| Dark share (đúng 0 trong polygon mean) | 0% | 0% | 0% |
| HH cells | 370 | 385 | 370 |
| LL cells | 2510 | 2499 | 2510 |
| HH area share | 4.61690% | 4.80407% | 4.61690% |

**Annual mean – median (mỗi ô):** MAE 0.0771845, median AE 0.0103399, P95 AE 0.3205303, max AE 6.0436231 nW/cm²/sr, Pearson r 0.9972279, Spearman rho 0.9941553.

**Kiểm định LISA:** Queen neighbors trên tập ô không biên (area>=0.99×0.25 km²), standardized z trên cùng active set, 999 permutations conditional without replacement, 2-sided +1 Monte Carlo p với ties, Benjamini–Hochberg alpha 0.05. Mô phỏng **paired** dùng chính xác cùng các bộ chỉ số láng giềng rút ngẫu nhiên cho median và mean. Baseline mô phỏng khớp 100% nhãn của file xuất ứng dụng.

## Giới hạn cần nêu khi viết bài

1. Không có pixel thiếu trong Yanqing 2020, do đó **không thể đánh giá mức độ sai lệch do `unmask(0)` trong một trường hợp thực sự có missing**. Muốn kiểm định giả định này cần địa bàn/năm có missing hoặc một thí nghiệm mask có kiểm soát (khi đó chỉ đo độ nhạy trên dữ liệu giả lập).
2. Annual mean là **trung bình không trọng số của 12 ảnh tổng hợp tháng**, không phải annual mean theo số quan sát `cf_cvg`. Không thể gọi đây là lựa chọn đo lường luôn tốt hơn/trung vị luôn tốt hơn.
3. Các kết quả LISA có p-value phụ thuộc phương pháp permutation, seed, và BH. Ở đây cùng seed/draws giúp cô lập thay đổi phương pháp tổng hợp ảnh, không phải chứng minh ý nghĩa kinh tế của hotspot.
4. Bằng chứng chỉ bao phủ **một vùng, một năm, cùng sản phẩm VIIRS**; chưa xác thực tính ổn định theo thời gian hoặc tính khái quát sang vùng khác.
5. Phân tích này không kiểm tra lại tương quan GHSL vì chưa có file dữ liệu GHSL cấp ô; không suy diễn về GDP, giá nhà hay nhà trống.
6. Kết quả không đòi hỏi tăng RAM của Streamlit và **không sửa repository**.

## Tái lập

- `run_yanqing_measurement_sensitivity.py`: mã phân tích độc lập.
- `yanqing_2020_measurement_sensitivity_cells.csv`: dữ liệu từng ô, gồm NTL ba cách tính, Local I, p-value, nhãn cụm, sai khác mean−median.
- `yanqing_2020_measurement_sensitivity_metrics.json`: metric/mask info và SHA-256 đầu vào.
- Ranh giới GADM, polygon ô lưới, CSV gốc và cả ba GeoTIFF trong ZIP bằng chứng.

<!-- END ORIGINAL SOURCE 057 -->


---

## Source 058: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial_app_2026_11_11_validation_evidence_complete.zip::yanqing_2020_transformation_sensitivity_report.md`

**Original bytes:** 6,598 · **SHA-256:** `5a29e6bc2f5c96b160fd3447f4076e4cb4034272c2c260afa6afa48a15e3b6b1` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 058 -->
# Independent Transformation Sensitivity Validation — Yanqing, Beijing (2020)

**Date:** 11 November 2026  
**Baseline:** `hoanfg/spatial-app`, post-PR #10 method (`conditional-wor-esda-v2`).  
**Input:** 8,333 Yanqing 500 m cells. Full-precision `ntl_baseline_ref` comes from independently re-extracted VIIRS raster in the previous validation; `ntl_mean` in original app CSV is rounded to four decimals.

## Purpose and methods

This test isolates *how NTL transformation changes LISA inference*, not whether a satellite measurement is correct. The same 8,333 cells, 7,733 non-edge cells, snapped UTM Queen-neighborhood indices, 999 conditional permutations **without replacement** (seed 42), inclusive two-sided pseudo-p with `(min(ge,le)+1)*2/1000`, and BH-FDR at alpha=0.05 were used for all three versions. The transformations mirror `ntl/lisa_diagnostics.py` and `ntl/lisa_core.py`:

- **Raw:** positive annual-median radiance as measured.
- **P99:** `min(NTL, quantile(NTL[NTL>0], .99))`; positive-N​TL cap **21.996610** nW/cm²/sr (84 cells capped). The resulting radiance is re-standardized.
- **Log:** `ln(NTL)`, *not* `log1p(NTL)`, and then re-standardized over the same active sample. All 8,333 Yanqing NTL values are strictly positive in this dataset.

The independent implementation reconstructs Queen neighbors from snapped exported UTM centroids, uses ESDA-scaled Local I, and the same replacement-free conditional null with synchronized random permutation draws for all methods. **Raw reproduces all 8,333 app LISA class labels and every exported p-value exactly.** Its computed Local I differs from the rounded exported version by no more than 0.000050.

## Results

| Metric | Raw | P99 winsorization | Log NTL |
|---|---:|---:|---:|
| High–High cells | 370 | 457 | 1,050 |
| Low–Low cells | 2,510 | 2,510 | 2,441 |
| All significant cells after FDR | 2,880 | 2,967 | 3,491 |
| HH area share | 4.617% | 5.702% | 13.102% |
| HH raw quadrants before significance | 1,072 | 1,135 | 2,517 |
| NTL mean (raw units where applicable) | 1.413719 | 1.331317 | — |
| Standardized input skewness | 6.312 | 4.905 | 1.928 |
| Excess kurtosis | 48.127 | 25.754 | 3.659 |

### High–High overlap

| Comparison | Intersection | Union | Jaccard | First-only | Second-only |
|---|---:|---:|---:|---:|---:|
| Raw vs P99 | 370 | 457 | 0.809628 | 0 | 87 |
| Raw vs log | 370 | 1,050 | 0.352381 | 0 | 680 |
| P99 vs log | 457 | 1,050 | 0.435238 | 0 | 593 |

**Crucial interpretation:** All 370 raw HH cells persist under P99 and log. A low raw-log Jaccard is due to the **expansion** of log-HH (+680), not displacement of the 370 brightest-core hotspots. The new 680 log HH cells were all `Not Significant` under raw; the additional P99 HH cells were similarly all raw `Not Significant`.

Among the 680 newly identified log-HH cells, raw radiance has median **2.731** nW/cm²/sr (range 1.096–10.894), versus median **13.259** for the original 370 raw HH cells. These newly identified cells are therefore typically moderately bright, not the brightest radiance outliers.

### Why log makes the difference

Raw NTL is strongly right-skewed (**skewness 6.31**, excess kurtosis 48.13). Extremely bright cells strongly influence the *raw-scale* mean and standard deviation. Under log transformation, the relative influence of extremes falls. In this dataset, the mean raw radiance on the active analysis sample is **1.474**, whereas exponentiating the mean logged radiance gives a geometric center of **0.624**. Both the standardized signs (quadrants) and the Monte Carlo significance pattern can change after that transformation. The proportion of focal-cell quadrant assignments that differs between raw and log is **20.38%**. Raw has 1,072 candidate HH quadrants; log has 2,517. Because a transformation changes the reference distribution and autocorrelation scores, a lower threshold alone is **not** a complete explanation.

Raw-to-P99 changes far less: candidate HH quadrants rise from 1,072 to 1,135, while P99-capping reduces skewness from 6.31 to 4.90. P99 caps 84 exceptionally bright cells at 21.9966, reducing their leverage. Under the tested settings, the LL significance count is unaffected by P99 but changes under log.

A few statistical decisions also move outside HH: 83 raw-LL cells become nonsignificant under log, and 14 previously nonsignificant cells become LL. These are legitimate sensitivity findings rather than, by themselves, code failures.

## Validation status and limits

- **Passed:** raw reproduction of app classes and p-values; identical Queen-neighbor degrees; reproducible, paired raw/P99/log Monte Carlo comparison under documented rules.
- **Sensitivity confirmed:** log is a materially different *estimand/analysis scale*: HH footprint rises from 4.617% to 13.102%; neither is automatically the scientifically correct representation.
- **Not concluded:** which scale best predicts economic activity, building occupancy, GDP or growth; whether hotspot thresholds are optimal; generalization to other cities or years; sensitivity to alternate weight specifications and grid scales. GHSL concordance shown in prior app screenshots applies to the original configuration; recalculation for transformed NTL requires matching GHSL cell-level data.

## Research recommendation

Pre-specify **raw annual-median VIIRS radiance as the primary physical-light measurement**, with P99 and log as explicit robustness alternatives. If the substantive question concerns **relative differences across dim and moderately lit places**, log can be justified as its own primary specification, but it must not be presented as numerically interchangeable with raw. Report all three HH footprints and their Jaccard overlap, not only labels such as “robust” or “weak.” Do not pool transformed NTL levels or their hotspot flags in one regression without defining the measurement scale.

The VIIRS input is nonnegative in this sample and `ln(NTL)` was feasible; across other cities/years where `NTL=0`, the app's log rule excludes zeros when `include_zeros=False`, requiring consistent treatment and disclosure.

## Reproducibility

Run `python validate_yanqing_transformations.py` with NumPy, pandas and SciPy from the ZIP evidence package and the three CSV files named in the script (or adjust `P`). Files `yanqing_2020_transformation_sensitivity_metrics.json` and `yanqing_2020_transformation_sensitivity_cells.csv` record the numerical output. SHA-256 source file hashes are included in JSON. No repository changes or Earth Engine downloads were needed in this stage.

<!-- END ORIGINAL SOURCE 058 -->


---

## Source 059: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial_app_2026_11_11_validation_evidence_complete.zip::yanqing_spatial_robustness_validation_report.md`

**Original bytes:** 6,987 · **SHA-256:** `9efd7fe7a01ea2b4b3904117e909bb369451b65ef5968dae28d30ccc452533f9` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 059 -->
# Independent Spatial Robustness Validation — Yanqing, Beijing, 2020

**Status:** Completed (four LISA specifications). **Scope:** VIIRS annual median, GADM v4.1 Yanqing, EPSG:32650, 500 m and 1,000 m, Queen vs Rook. **Date:** 2026-11-11.

## Executive summary

The independent code exactly replicates **8,333/8,333 cell classifications** and the exported simulation p-values for the original **Queen / 500 m** webapp result. Recomputing spatial weights with Rook materially reduces significant High–High (HH) and Low–Low (LL) cells. Doubling the grid size yields a similar fraction of regional land in HH, but only partial geographical agreement between the two spatial resolutions (area-weighted intersection-over-union for Queen HH = 0.6547). There is **no evidence of a software calculation error** from these tests. There is meaningful **model specification sensitivity**.

## Reproducible data and method

- Source: user-provided `yanqing_viirs_2020_reference.tif`, independently validated against the app's 500 m NTL extraction in the previous stage; same GADM boundary file and CSV as the previous stages.
- 500 m: original 8,333 GADM-clipped grid polygons, NTL values computed from the reference GeoTIFF, without CSV rounding.
- 1,000 m: **new grid snapped to 1,000 m UTM coordinates** following the app's `build_grid` logic; clip to the same GADM geometry; area-weighted polygon/raster intersection to extract NTL independently. There are 2,162 grid polygons and the region areas agree within 0.00002 km².
- LISA: NTL raw, reference standardization on non-edge cells (sample SD, ddof=1); exclude polygons with area < 99% of nominal cell area. Queen has up to 8 adjacent cells (including corners); Rook up to 4 edge-sharing cells. Excluded cells cannot be neighbors. Conditional permutation *without replacement* (999 permutations, seed 42); two-sided p = min(1, 2(min(ge,le)+1)/1000), with inclusive ties, BH FDR at α=0.05 over tested cells. This matches the app's post-PR#10 implementation.
- Difference between resolutions assessed with polygon-set geometry: spatial Jaccard = intersection area / union area; it is not meaningful to compare raw cell counts across different grid sizes.
- No Streamlit execution or app modification required.

## LISA results

| Specification | Grid polygons | Tested cells | Edge-masked | HH count | LL count | HH area (km²) | HH share (%) | LL area (km²) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Queen 500 m | 8,333 | 7,733 | 600 | 370 | 2,510 | 92.50 | 4.6169 | 627.50 |
| Rook 500 m | 8,333 | 7,733 | 600 | 187 | 906 | 46.75 | 2.3334 | 226.50 |
| Queen 1,000 m | 2,162 | 1,865 | 297 | 92 | 562 | 92.00 | 4.5919 | 561.98 |
| Rook 1,000 m | 2,162 | 1,865 | 297 | 46 | 210 | 46.00 | 2.2960 | 209.99 |

All four analyses found zero FDR-significant High–Low and Low–High cells. The denominator of HH area share is total clipped Yanqing area (~2,003.51 km²), including edge cells. Edge masking changes the eligible analysis area and needs to be kept explicit in any paper.

## Queen versus Rook, at fixed resolution

| Comparison | HH cell intersection | HH cell Jaccard | LL cell intersection | LL cell Jaccard |
|---|---:|---:|---:|---:|
| 500 m Queen versus Rook | 187 | 0.5054 | 906 | 0.3610 |
| 1,000 m Queen versus Rook | 46 | 0.5000 | 210 | 0.3737 |

The Rook significant HH and LL sets are subsets of the corresponding Queen sets in both tested scales. Their smaller size may reflect fewer neighbors, different spatial lag, permutation null distribution and changes in FDR significance; the tests do not identify a single causal reason without further decomposition. Rook is not automatically more correct or more conservative in all geographies.

## Changing resolution at fixed weights — geographical footprint overlap

| Comparison | 500 m HH area (km²) | 1,000 m HH area (km²) | Intersection (km²) | Spatial Jaccard | Share of 500 m HH retained |
|---|---:|---:|---:|---:|---:|
| Queen HH | 92.50 | 92.00 | 73.00 | 0.6547 | 78.92% |
| Rook HH | 46.75 | 46.00 | 37.75 | 0.6864 | 80.75% |

Additional spatial Jaccard: Queen LL 0.8371; Rook LL 0.5479.

The broadly consistent aggregate HH area is **not** proof of complete location stability. New 1,000 m grid alignment, changing support, edge-mask share, and scale dependence (modifiable areal unit problem / MAUP) can change both neighbor structure and statistics.

## Quality checks

- Exact replication of **all 8,333** published labels for Queen 500 m. Maximum absolute difference between recalculated and exported 500 m Queen `p_sim` = **0.00000**.
- Full-source region boundary yields 2,162 1,000 m cells and approximately the same regional area as the existing 500 m grid.
- No missing or nonpositive annual-median NTL values in the extracted 1,000 m polygon means.
- All calculations performed using the same reference GeoTIFF that had previously passed independent 500 m extraction validation.

## Assessment and research recommendations

1. **Software reproducibility (Queen 500 m): PASS**. Method comparison is not a code defect test; no new defect established.
2. **Weight specification robustness: SENSITIVE**. HH area roughly halves and LL classifications drop sharply with Rook, although Rook-significant areas remain nested within Queen-significant areas.
3. **Spatial resolution robustness: MODERATE**. HH area proportion is stable, but about 21% of the original Queen HH footprint does not overlap the 1,000 m HH footprint, yielding spatial Jaccard 0.655.
4. For research, prespecify one primary weights model (Queen 500 m is the app baseline), disclose Rook and 1,000 m as robustness checks, and avoid presenting the exact hotspot boundaries as scale-invariant.
5. Future checks: consistency across an independent urban geography/year, month-level NTL observation quality in imperfect-data contexts, and the interpretation of space-time LISA regime labels. Bootstrapping the geographical stability, or cross-scale agreement across seed choices, would further separate permutation variability from scale effects.

### Reproducibility bundle

- `validate_yanqing_spatial_robustness.py`: full independent code, no imports from `spatial-app`.
- `yanqing_spatial_robustness_metrics.json`: all numerical metrics and SHA-256 hashes of key input files.
- `yanqing_spatial_robustness_500m_cells.csv`, `yanqing_spatial_robustness_1000m_cells.csv`: each specification's neighborhood count, p-value and final LISA class.
- `yanqing_spatial_robustness_1000m.geojson`: 1,000 m polygons with NTL and both LISA classes.
- `yanqing_spatial_robustness_execution.log`: execution output.
- Source GADM geometry, baseline VIIRS GeoTIFF, original app-export CSVs and full-precision reference mean CSV are included in the ZIP.

**Limitation:** This is an internal-method benchmark with independent implementation and original VIIRS values, not an external ground-truth validation of NTL as a measure of economic activity; results pertain to Yanqing 2020 only.

<!-- END ORIGINAL SOURCE 059 -->


---

## Source 060: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial_app_2026_11_11_validation_evidence_complete.zip::yanqing_temporal_validation_report.md`

**Original bytes:** 8,054 · **SHA-256:** `3f104e22e1bb248eabbc548f62eaf83281c0937880b09ae73d4ecd7d02956ff5` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 060 -->
# Temporal Validation — Yanqing (Diên Khánh), Bắc Kinh, 2014 → 2020

**Trạng thái:** PASS về tái lập phép tính Space-Time từ dữ liệu CSV đã xuất, với một sai khác tại ngưỡng do làm tròn; **chưa PASS** về kiểm chứng độc lập raster VIIRS năm 2014, vốn chưa được cung cấp.

**Nguồn:** `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv` (8.333 ô); đối chiếu công thức trong `ntl/lisa_core.py`, repository `hoanfg/spatial-app`, phiên bản sau PR #10 (merge SHA `9574cf872c52d266aa15c363df7965cce31601f0`). Các công thức được lập trình lại bằng Python riêng (`validate_temporal.py`) thay vì gọi trực tiếp hàm ứng dụng. Việc kiểm chứng tính toán trên CSV không đồng nghĩa xác nhận dữ liệu ảnh vệ tinh đầu vào năm 2014.

## 1. Các phép tính đã tái lập

- **8.333 ô**, trong đó **7.733 ô nội vùng** và **600 ô loại tại biên**.
- `ntl_2020` bằng `ntl_mean` ở cả 8.333 ô.
- `delta_ntl`, `delta_ln_ntl`, `z_2014`, `z_2020`, `delta_z`, `delta_lag_z`, `movement_magnitude` tái lập từ `ntl_2014`, `ntl_2020`, tọa độ và Queen neighbors trong sai số được kỳ vọng từ làm tròn bốn chữ số NTL đầu vào.
- Queen neighbor counts khớp **8.333/8.333** với cột đã xuất.
- Nhãn Space-Time từ **giá trị dịch chuyển và hướng đã làm tròn do app xuất** khớp **8.333/8.333**. Khi tính lại trực tiếp từ NTL có bốn chữ số thập phân, **8.332/8.333** nhãn khớp. Ô `grid_id=3922` có `movement_magnitude` tính lại ≈ **0,049964**, trong khi CSV xuất **0,0500** (ngưỡng 0,05), tạo sai khác một nhãn. Điều này không đủ để kết luận lỗi tính toán trong ứng dụng: đầu vào CSV là giá trị đã làm tròn, còn app sử dụng giá trị chưa làm tròn trước khi xuất.

## 2. Định nghĩa *Synchronized Decline* thực tế

Ứng dụng sử dụng:

`v_t = ln(1 + max(NTL_t, 0))`; `z_t = (v_t - mean(v_t on core))/(sd(v_t on core, ddof=1))`.

`delta_z = z_2020 - z_2014`; `delta_lag_z = QueenLag(z_2020) - QueenLag(z_2014)`.

Độ lớn thay đổi `m = sqrt(delta_z² + delta_lag_z²)`. Chỉ những ô nội vùng có `m >= 0.05` mới thuộc một trong bốn chế độ định hướng:

- **Synergistic Growth:** `delta_z >= 0`, `delta_lag_z >= 0`.
- **Agglomeration Shadow:** `delta_z < 0`, `delta_lag_z >= 0`.
- **Emergent Pioneer:** `delta_z >= 0`, `delta_lag_z < 0`.
- **Synchronized Decline:** `delta_z < 0`, `delta_lag_z < 0`.

**Quan trọng:** Tên `Synchronized Decline` chỉ **suy giảm vị thế tương đối** (Z-score log NTL của ô và láng giềng giảm sau khi chuẩn hóa riêng tại mỗi năm), **không có nghĩa giá trị NTL tuyệt đối giảm**. Các nhãn cũng không phải kết quả của permutation test hay FDR: đây là phân loại mô tả dựa trên hướng và ngưỡng thay đổi.

## 3. Kết quả theo nhãn gốc từ webapp

| Chế độ | Số ô | Ô NTL tăng tuyệt đối | Ô NTL giảm tuyệt đối | NTL 2014 TB | NTL 2020 TB |
|---|---:|---:|---:|---:|---:|
| Synergistic Growth | 1.456 | 1.456 | 0 | 0,481 | 3,859 |
| Agglomeration Shadow | 75 | 75 | 0 | 0,819 | 2,148 |
| Emergent Pioneer | 194 | 194 | 0 | 0,324 | 1,075 |
| **Synchronized Decline** | **4.711** | **4.624** | **87** | **0,532** | **1,029** |
| Excluded or Static | 1.897 | 1.872 | 25 | 0,201 | 0,498 |

- **98,15%** ô của chế độ `Synchronized Decline` thực chất **tăng NTL tuyệt đối**. Trung bình nhóm này tăng gần gấp đôi.
- `Synchronized Decline` chiếm **60,92% của 7.733 ô nội vùng** (và 56,53% tổng 8.333 ô). Phần lớn sự thay đổi là giảm tương đối so với phân phối đã chuẩn hóa, không phải suy giảm đô thị/economic activity.
- Toàn vùng: NTL trung bình không trọng số **0,4452 → 1,4137**; **8.221 ô tăng**, **112 ô giảm** tuyệt đối, tính cả ô biên.
- Vì chỉ có hai mốc 2014/2020, đây là **so sánh hai thời điểm**, không chứng minh khuynh hướng tăng liên tục ở các năm giữa.

## 4. Spatial Markov từ CSV

Bảng chuyển trạng thái các phân vị NTL (Q1–Q4), đơn vị **số ô** (mẫu 7.733 ô nội vùng):

| 2014 → 2020 | Q1 | Q2 | Q3 | Q4 |
|---|---:|---:|---:|---:|
| Q1 | 1.482 | 422 | 23 | 6 |
| Q2 | 446 | 1.190 | 245 | 53 |
| Q3 | 4 | 321 | 1.426 | 181 |
| Q4 | 0 | 1 | 239 | 1.694 |

- **74,90%** ô vẫn thuộc cùng quartile giữa hai mốc, mặc dù NTL tuyệt đối toàn vùng tăng mạnh.
- Chỉ số Shorrocks theo phép tính của source ứng dụng: khoảng **0,3347** (dựa trên bảng xác suất chuyển tiếp đã làm tròn một chữ số phần trăm). Chỉ tiêu này mô tả sự dịch chuyển thứ hạng, không phải tăng trưởng ánh sáng tuyệt đối.

## 5. Sensitivity theo ngưỡng movement magnitude

Thay ngưỡng của quy tắc phân loại, giữ nguyên các delta do app xuất và không đổi dữ liệu:

| Ngưỡng | Synergistic Growth | Agglomeration Shadow | Emergent Pioneer | Synchronized Decline | Excluded/Static |
|---|---:|---:|---:|---:|---:|
| 0,025 | 1.555 | 137 | 438 | 5.242 | 961 |
| **0,050 (baseline)** | **1.456** | **75** | **194** | **4.711** | **1.897** |
| 0,100 | 1.254 | 42 | 62 | 2.949 | 4.026 |
| 0,200 | 998 | 23 | 20 | 1.111 | 6.181 |

Như vậy, **số ô được gắn nhãn theo chuyển động khá nhạy với ngưỡng**. Điều này không chứng tỏ thuật toán sai, nhưng người dùng nên đọc đây là một phân tích mô tả có giả định cần công bố. Ở biên ngưỡng, việc xuất số làm tròn có thể làm một số ô chuyển nhóm khi người khác tính lại từ CSV.

## 6. Kết luận và khuyến nghị cho ứng dụng

1. **PASS — công thức và phân loại trong CSV:** kiểm tra độc lập cho kết quả nhất quán; ngoại lệ `grid_id=3922` là tình huống nhạy với việc CSV làm tròn gần 0,05.
2. **Cần chỉnh diễn giải/nhãn UI:** thay vì hiểu `Synchronized Decline` là "suy giảm ánh sáng/kinh tế", nên mô tả rõ "Relative Z-score decline of cell and spatial neighborhood" (suy giảm vị thế tương đối của ô và láng giềng). Tương tự, `Synergistic Growth` không tự bảo đảm tốc độ tăng kinh tế cao.
3. **Nhãn Space-Time không phải nhãn có ý nghĩa thống kê:** kết quả không thực hiện permutations hay FDR; không gọi các nhóm này là statistically significant mà không có kiểm định riêng.
4. **Ngưỡng `movement_magnitude=0,05` cần được công bố** và trình bày kết quả robustness theo nhiều ngưỡng.
5. **Chưa kiểm chứng đầu vào 2014:** cần raster VIIRS 2014 do một pipeline Earth Engine độc lập tạo ra để đối chiếu lại tất cả 8.333 ô như đã làm năm 2020. Nếu muốn kiểm chứng tính nhất quán liên thời gian, nên xem thêm các năm trung gian 2015–2019, không chỉ hai mốc.
6. Các phát biểu liên quan đến **GDP, đô thị hóa hay tác động kinh tế** vẫn cần kiểm chứng bên ngoài; thay đổi NTL không tự động chứng minh thay đổi GDP.

## 7. Artefacts

- `yanqing_temporal_validation_by_cell.csv`: biến tái tính, nhãn app và nhãn độc lập từng `grid_id`.
- `yanqing_temporal_regime_summary.csv`: thống kê theo nhóm (nhãn tái tính từ CSV, có một ngoại lệ do làm tròn; bảng nhãn gốc phía trên là số chính thức từ app).
- `yanqing_temporal_markov_counts.csv`: bảng chuyển quartile dạng số ô.
- `yanqing_temporal_validation_results.json`: kiểm định, sai số và sensitivity chi tiết.
- `validate_temporal.py`: mã tái lập độc lập từ CSV nguồn.

Không chỉnh sửa repository trong bước này.

<!-- END ORIGINAL SOURCE 060 -->


---

## Source 061: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial_app_2026_11_11_validation_evidence_complete.zip::yanqing_validation_report.md`

**Original bytes:** 4,027 · **SHA-256:** `8f949647d87a3d71f49446cca393b9b9bb404e70f59e941e75022709e2fa8851` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 061 -->
# Kiểm chứng độc lập Local Moran / LISA — Diên Khánh, Bắc Kinh (2020, 500 m)

**Ngày:** 11/11/2026. **Nguồn:** `CHN_beijing_yanqing_2020_500m_lisa_cells.csv` do người dùng xuất từ spatial-app. **Công thức đối chiếu:** repository `hoanfg/spatial-app`, `main` sau PR #10, commit `9574cf872c52d266aa15c363df7965cce31601f0`. Đây là phân tích độc lập trên bản CSV đã xuất, **không phải** một phép đo lặp lại từ raster VIIRS gốc hay một phiên chạy ESDA.

## Kiểm chứng xác định (deterministic)

| Phép kiểm | Kết quả |
|---|---|
| Số dòng / ô | 8.333 |
| Ô biên theo ngưỡng diện tích < 0,99 × 0,25 km² | 600; khớp hoàn toàn |
| Ô tham gia LISA | 7.733 |
| Ma trận láng giềng Queen, so số láng giềng từng ô | 8.333/8.333 khớp |
| Quadrant thô HH, LL, HL, LH | 7.733/7.733 khớp |
| Local Moran I tái tính từ NTL đã xuất | Sai khác tuyệt đối tối đa 0,00016805 |
| Benjamini–Hochberg ở α = 0,05, tính lại từ `lisa_p_sim` xuất | Khớp tuyệt đối, 2.880 ô |
| HH / LL từ BH trên p-value xuất | 370 / 2.510 ô |

Sai khác Local I không được diễn giải như sai số thuật toán: cột `ntl_mean` và `lisa_I` trong CSV đã được làm tròn, còn thuật toán gốc có dữ liệu trước khi làm tròn.

## Conditional permutation độc lập

- Mô hình: giữ focal cố định, lấy các phần tử khác **không hoàn lại** trong mỗi lần hoán vị, độ trễ không gian chuẩn hóa theo số láng giềng, Local Moran theo chuẩn ESDA. **999 permutations**, seed độc lập **20261111**.
- Quy tắc pseudo p-value: hai phía, lấy hai lần đuôi nhỏ hơn, cộng một, tie tolerance 1e-12; sau đó BH ở α = 0,05.
- Tương quan giữa p-value tái mô phỏng và CSV của app: **0,996736**.
- Mean absolute difference của p: **0,015636**; P95 absolute difference: **0,058**.
- Số ô BH significant: **2.879** (độc lập) so với **2.880** (app); **179 ô** khác quyết định BH theo seed này.

| Cụm | App | Độc lập | Giao | Hợp | Jaccard |
|---|---:|---:|---:|---:|---:|
| High–High | 370 | 375 | 360 | 385 | 0,9351 |
| Low–Low | 2.510 | 2.504 | 2.430 | 2.584 | 0,9404 |

Không nên coi 179 ô đổi quyết định là 179 lỗi: pseudop có sai số Monte Carlo, đặc biệt quanh ngưỡng FDR; dữ liệu NTL xuất ra cũng đã bị làm tròn. Để quy kết sai lệch, cần thêm các thử nghiệm thay seed và tăng số hoán vị. Những test deterministic đã tái lập đúng cấu trúc quan sát được.

## Giới hạn còn lại

1. Không có raster VIIRS gốc, vì thế **chưa** kiểm tra độc lập giá trị zonal/`exactextract` ở từng ô hoặc số tháng quan sát `cf_cvg`.
2. Không có bảng GHSL per-cell, vì thế **chưa** tính lại Spearman/AUC/bootstrap từ đầu; hình chụp màn hình là kết quả **trong app**.
3. Đây là phép triển khai lại phép tính từ CSV; **không phải** benchmark phần mềm ESDA trên toàn 8.333 ô trong phiên hiện tại.
4. Bản export không mang theo đầy đủ hyperparameters hay `lisa_method_version`; cấu hình được suy ra từ source code, p-value và kết quả xuất. Nên xuất thêm metadata vùng/cấu hình để audit được toàn bộ.

## File tái lập

- `validate_yanqing_lisa.py`: code độc lập, cần NumPy/Pandas, chạy cùng thư mục với CSV nguồn.
- `yanqing_lisa_independent_cell_comparison.csv`: so sánh từng `grid_id`.
- `yanqing_lisa_independent_summary.json`: thống kê máy đọc được.
- `validation_run_log.txt`: log chạy.

**Đánh giá:** Tầng statistical validation vượt qua các kiểm tra định lượng đầu tiên, với giới hạn Monte Carlo được nhận diện rõ. Tầng raster-extraction và external proxy vẫn cần dữ liệu cấp pixel hoặc GHSL per-cell độc lập.

<!-- END ORIGINAL SOURCE 061 -->


---

## Source 062: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial_app_2026_11_11_validation_evidence_complete.zip::yanqing_viirs_all_cells_validation_report.md`

**Original bytes:** 6,561 · **SHA-256:** `092904cafcfa05dd6ef11ee4e5dad5f8c0fc5dd376668249ff9e166bf9dc0522` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 062 -->
# Xác thực độc lập VIIRS — Diên Khánh (Yanqing), Bắc Kinh, năm 2020

**Ngày:** 11/11/2026  
**Commit spatial-app:** [`9574cf872c52d266aa15c363df7965cce31601f0`](https://github.com/hoanfg/spatial-app/commit/9574cf872c52d266aa15c363df7965cce31601f0)  
**Địa bàn GADM 4.1:** `CHN.2.1.11_1`, EPSG:32650, lưới phân tích 500 m  
**Nguồn ảnh:** người dùng xuất hai GeoTIFF từ Google Earth Engine bằng một script độc lập khỏi ứng dụng.

## Kết luận

**PASS cho toàn bộ 8.333/8.333 ô**: trung bình ảnh VIIRS tính độc lập theo tỷ lệ diện tích giao polygon–pixel trùng với `ntl_mean` của webapp khi làm tròn đến bốn chữ số thập phân. Tất cả sai khác tuyệt đối đều ≤ 0,00005 nW/cm²/sr; **không còn ô biên ngoại lệ**. Kết quả khẳng định việc tổng hợp raster thành các ô lưới 500 m của mẫu Yanqing 2020 được tái lập độc lập trong phạm vi độ chính xác của file CSV xuất ra.

| Đại lượng | Kết quả |
|---|---:|
| Tổng ô | **8.333** |
| Ô nguyên 0,25 km² | **7.703** |
| Ô cắt nhẹ nhưng không đánh dấu biên | **30** |
| Ô được gắn nhãn biên | **600** |
| Khớp 4 chữ số thập phân | **8,333/8.333** |
| MAE | **0.0000250230** nW/cm²/sr |
| Median absolute error | **0.0000253275** nW/cm²/sr |
| 95th percentile absolute error | **0.0000473949** nW/cm²/sr |
| Max absolute error | **0.0000499933** nW/cm²/sr |
| Pearson r | **0.999999999971** |
| Tổng diện tích CSV | **2003.508895** km² |
| Tổng diện tích polygon tái dựng | **2003.508912** km² |

## Phương pháp

1. Sử dụng GeoJSON Yanqing tại commit đã kiểm định và khôi phục đầy đủ tọa độ nguồn. GeoJSON, giá trị nguồn và SHA-256 của các input có trong bộ bằng chứng. Mã GID `CHN.2.1.11_1` được giữ nguyên.
2. Chiếu ranh giới sang UTM EPSG:32650; tạo các ô vuông 500 × 500 m bắt đầu tại tọa độ bội số của 500, nới một ô; cắt từng ô bằng ranh giới. Kiểm tra được **đúng 8.333 đa giác** theo cùng thứ tự `grid_id` và diện tích/tâm tọa độ trùng với các giá trị được làm tròn trong CSV.
3. Chiếu mỗi **đa giác đã cắt** về CRS raster EPSG:4326. Với mỗi pixel, tính diện tích giao nhau giữa polygon và pixel theo hệ tọa độ raster, nhân với `avg_rad` rồi chia tổng diện tích giao nhau. Script tính độc lập không import `ntl.zonal` hoặc `exactextract`.
4. So sánh kết quả reference với `ntl_mean` của CSV theo từng `grid_id` — cả 630 ô bị cắt (600 biên + 30 cắt nhẹ), không chỉ ô nguyên vẹn. File `yanqing_viirs_all_8333_polygon_comparison.csv` chứa các phép đối chiếu và sai số.

## Kiểm tra theo nhóm

| Nhóm ô | Số ô | MAE | Sai số lớn nhất | Khớp 4 chữ số |
|---|---:|---:|---:|---:|
| `full` | 7,703 | 0.000025250 | 0.000049993 | 7,703/7,703 |
| `minor_clipped` | 30 | 0.000027901 | 0.000046435 | 30/30 |
| `edge_masked` | 600 | 0.000021962 | 0.000049888 | 600/600 |

### Giá trị tổng hợp vùng

- Trung bình có trọng số diện tích từ app: **1.445496506 nW/cm²/sr**.
- Trung bình có trọng số diện tích từ reference: **1.445496216 nW/cm²/sr**.
- Tổng `NTL × km²` từ app: **2896.065108050**; từ reference: **2896.064526359**. Đây chỉ là tổng quy ước trên lưới, không phải GDP.

### Số tháng quan sát

Earth Engine Console báo 12 ảnh tháng. Raster `yanqing_valid_months_2020.tif` chứa **30.814/30.814 pixel bằng 12** trong bounding rectangle được xuất. Đây là số tháng có chỉ thị `cf_cvg > 0` theo script cung cấp, không phải số quan sát vệ tinh riêng lẻ hoặc bằng chứng rằng không có sai số cảm biến.

## Vì sao phép đối chiếu lần trước còn một ô khác biệt?

Khi dùng ranh giới được lượng tử hóa còn 7 chữ số thập phân, `grid_id 349` có sai số ~0,0000643. Sau khi tái dựng với phần thập phân nguồn đầy đủ, sai số ô này giảm xuống mức làm tròn CSV. Điều này chỉ ra độ nhạy của **ô bị cắt** với độ chính xác hình học; không phải bằng chứng có lỗi trong phép trích xuất NTL của ứng dụng.

## Giới hạn khoa học còn lại

- **Đây là validation việc tái lập giá trị NTL theo cùng nguồn và cùng quy tắc**, không phải validation rằng NTL luôn đo đúng GDP, hoạt động kinh tế hoặc nhà bỏ trống.
- Raster tham chiếu được xuất bằng `Export.image.toDrive`, không phải chính byte raster của `getDownloadURL` trong app. Hai phương thức có thể có khác biệt về căn chỉnh lưới; với bộ dữ liệu này kết quả zonal mean khớp đến mức làm tròn.
- `annual median`, `cf_cvg > 0`, `unmask(0)` và clipping âm là những lựa chọn xử lý cần đánh giá thêm nếu muốn kết luận về bias đo lường. Ảnh tháng hợp lệ 12/12 tại ROI này không chứng minh điều tương tự ở khu vực/năm khác.
- Chưa benchmark RAM toàn diện của Streamlit Cloud; chưa kiểm tra vùng khác, năm khác, hoặc đối chiếu độ chính xác sản phẩm VIIRS với quan sát mặt đất.
- Từ số CSV chỉ lưu bốn chữ số thập phân, phép kiểm tra không thể chứng minh khớp chính xác ở độ chính xác toàn phần của số thực chưa làm tròn.

## Bằng chứng và tái lập

- `yanqing_viirs_all_8333_polygon_comparison.csv`: đối chiếu từng ô và sai số.
- `yanqing_viirs_all_cells_metrics.json`: số liệu + SHA-256 dữ liệu đầu vào.
- `validate_yanqing_all_cells.py`: mã Python tính độc lập theo polygon overlap.
- `yanqing_gadm41_source.geojson`: ranh giới nguồn lưu lại với tọa độ chính xác.
- `yanqing_grid_reconstructed.geojson`: toàn bộ 8.333 polygon đã cắt trong hệ tọa độ địa lý.
- Hai raster VIIRS/month count và CSV gốc (nếu cần tái lập) được lưu trong ZIP bằng chứng.

**Kết luận cuối:** Đạt kiểm chứng cấp ô và vùng cho **toàn bộ 8.333 ô** thuộc Diên Khánh 2020. Phần kiểm chứng tiếp theo nên chuyển sang đánh giá **measurement sensitivity** và **external validity** thay vì mở thêm một vòng kiểm thử cùng công thức.

<!-- END ORIGINAL SOURCE 062 -->


---

## Source 063: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/files/spatial_app_2026_11_11_validation_evidence_complete.zip::yanqing_viirs_validation_report.md`

**Original bytes:** 5,858 · **SHA-256:** `c72f33666f491988af3964dbe63b6179af80301dc78e6db6f6ffc341acb3c724` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 063 -->
# Independent VIIRS extraction validation — Yanqing, Beijing (2020)

**Date:** 2026-11-11  
**Target application:** `hoanfg/spatial-app`, post-merge commit `9574cf872c52d266aa15c363df7965cce31601f0`  
**Input files:** `dien_khanh_NTL_2020_500m.csv`, `yanqing_viirs_2020_reference.tif`, `yanqing_valid_months_2020.tif`.

## Verdict

**PASS for the 7,703 fully uncut 500-m UTM cells**, when compared with an independently exported Earth Engine VIIRS annual raster and an independent, fractional-coverage polygon-weighted raster calculation. All 7,703 agree with the four-decimal application CSV within its 0.00005 rounding bound. This verifies the output's cell-level extraction/aggregation for these cases, not the entire scientific validity of the satellite product.

**PARTIAL for all 8,333 cells.** The remaining 630 cells have some boundary clipping (600 are flagged `is_border_cell=1`; 30 more are flagged 0 but are slightly smaller than 0.25 km²). Boundary-clipped polygons cannot be reconstructed exactly from CSV centroid and area alone; no exact independent test was performed for these 630 cells. The 30 nearly uncut cells were approximated as uncut UTM squares for a diagnostic only.

## Earth Engine outputs

- `yanqing_viirs_2020_reference.tif`: EPSG:4326, float32, 217 columns × 142 rows (30,814 pixels); 0.00416665578233° pixel step; 115.69969776–116.60386207° longitude, 40.22906158–40.82072670° latitude.
- Valid annual raster values: minimum 0.225, maximum 59.445, mean 1.0597132 nW/cm²/sr over the **exported bounding rectangle**, not the district polygon. All 30,814 exported pixels are unmasked and positive.
- `yanqing_valid_months_2020.tif`: same grid, uint8, **all 30,814 values equal 12**. The Earth Engine Console reported 12 monthly images. This validates the month-count *indicator* generated by the supplied script for the exported rectangle; it is not a count of individual cloud-free satellite observations. Upstream `.unmask(0)` can obscure earlier missing-data distinctions.

## Reference computation

- Original `spatial-app` run used GADM Yanqing and UTM EPSG:32650, analytic cells of 500 × 500 meters, VIIRS monthly `VCMSLCFG`, `avg_rad` masked by monthly `cf_cvg > 0`, annual median then zero unmask. This is the reference **method** for building the Earth Engine export, but the exported GeoTIFF was generated by a separate Earth Engine Code Editor script.
- A separate Python script (`validate_viirs_yanqing.py`) recreated each **full, uncut** 500 m UTM polygon from its exported UTM centroid, projected the polygon into raster CRS, intersected it with the GeoTIFF pixel footprints, and calculated a polygon-overlap-area-weighted average. The independent implementation does not import `ntl.zonal` or `exactextract`.
- The CSV stores `ntl_mean` with four decimal places; a true match to full precision should therefore be within approximately 0.00005 per cell, not precisely 0.

### Fully uncut cells (area = 0.25 km² at exported precision)

| Metric | Result |
|---|---:|
| Exact 0.25 km² square cells compared | **7,703** |
| Pearson correlation (all 7,733 diagnostic non-border cells) | **0.9999999992** |
| Mean absolute error, 7,703 full cells | **0.0000252502** nW/cm²/sr |
| Maximum absolute error, 7,703 full cells | **0.0000499933** nW/cm²/sr |
| Cells exceeding 0.00005 absolute difference | **0 / 7,703** |

### Diagnostic including 30 almost-full clipped cells

The `is_border_cell=0` group contains 7,733 cells, **30** of which have area slightly below 0.25 km². Their reference was approximated as a full 500 m square for the diagnostic only.

| Metric | Result |
|---|---:|
| Cells in diagnostic | 7,733 |
| Mean absolute error | 0.0000271554 |
| Median absolute error | 0.0000255623 |
| 95th percentile absolute error | 0.0000475461 |
| Maximum absolute error | 0.0133583 |
| Largest discrepancy grid_id | **1682** (area **0.247942 km²**, not a full square) |

For comparison, a **center-pixel sample** instead of a fractional-coverage mean produced Pearson r ≈ 0.98789 and mean absolute error ≈ 0.15008. This illustrates why the correct pixel-overlap calculation matters.

## Limitations and next action

1. **630 partly clipped boundary cells** remain unverified to rounding precision. For an all-cell benchmark, obtain the exact Yanqing source polygon used by the app and repeat this independent calculation on the clipped polygons, using matching geometry-cleaning and grid-building conventions. The 600 `is_border_cell=1` cells are excluded from current polygon-mean reconstruction; 30 slightly clipped but unflagged cells were evaluated approximately.
2. Although the independent export agrees numerically on complete cells, this does **not** independently adjudicate whether annual median and upstream `unmask(0)` are appropriate scientific measurement choices; those are sensitivity analyses.
3. All 12 months are valid in the provided *exported monthly indicator*. This is not proof that there are no missing individual satellite observations, and not a test for other years.
4. `Export.image.toDrive` may have different raster alignment from app's `getDownloadURL`; near-perfect agreement here suggests matching effective pixel footprint values over this region. A pixel-by-pixel comparison would require the original app GeoTIFF.
5. No live authenticated application session, GEE API call, or Streamlit Cloud RAM measurement was performed in this local comparison. The Earth Engine exports were supplied by the user.

**Conclusion:** The **VIIRS annual zonal extraction pipeline is independently corroborated with extremely high precision on the 7,703 fully uncut cells** in the Yanqing 2020 dataset. The next optional step is clipping the remaining 630 cells against the exact curated GADM polygon, rather than repeating broad benchmarks or raising Streamlit RAM caps.

<!-- END ORIGINAL SOURCE 063 -->


---

## Source 064: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/pr24_notes/PR_STAGING_NOTES.md`

**Original bytes:** 16,264 · **SHA-256:** `55006f34c322dbbe7e6e2a57f0cf4038f6fa8ec4038fd9cd1bf15a461d4cfadc` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 064 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 14 November 2026 (revised from 13 November). Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Eleven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

## Review update 14 November 2026 — no new PR

- Hardened the GHSL check against **partial-coverage false positives**: eligible cells must have nearly 100% finite, unmasked raster area in BOTH native and app exports. Ineligible per-cell differences are NaN, not numerically compared.
- Added guard for GHSL native 100 m product resolution; a wrongly supplied 1 km raster fails preflight.
- Hardened A02 source independence: selecting ROI from the application's own band-1 mask could silently drop an app-side masked pixel. Reference valid-month count now defines the footprint, so this case fails.
- Negative controls expanded; `python -m pytest -q test_validation_scripts.py` now reports **11 passed**.
- All field validation gates remain unfulfilled without matching real-data rasters and application exports. Preserve project policy: **one future consolidated PR**, no branch/PR in this stage.

## 15 November 2026 — v4 single-PR carry-forward

1. Require **actual per-ID spatial identity** using UTM and WGS84 centroids, not only grid ID/area. The current production app already exports all required fields. Checker code and comparator are staged, not pushed to GitHub.
2. Reject non-integral valid-month counts in A02 references.
3. **11/11 isolated checker tests passed.** Deliberate same-area grid swaps and missing centroid columns are rejected.
4. Historical Yanqing 2020 GADM, real VIIRS raster and application CSV were checked with the amended comparator. Exactly **8,333/8,333** per-cell NTL references and centroid identity comparisons passed at exported rounding tolerances; detailed metrics JSON and source hashes are included, but private input raster/GeoJSON/CSV and the 8,333-row diagnostic table are *not* bundled.
5. No new branch, PR, production algorithm changes or geospatial data bundles. One consolidated PR remains the only proposed repository update.

## Field update 15 November 2026 — V11 edge closure + A02 real-data `unknown`

- **V11 new evidence:** analyzed exactly 1,847 previously excluded boundary-clipped cells from 3 user GeoJSONs against 3 independent EE VIIRS TIFFs. All covered. 1,846/1,847 pass the literal 5e-5 half-bin; one Bao'an record (`grid_id=628`) exceeds by 3.93e-8 and is explicitly reported; 1,847/1,847 pass 5.01e-5 including a 1e-7 floating guard. Prior 15,330 core cell results were not repeated. Detailed private report: `V11_EDGE_COMPLETION_2026-11-15.md`.
- **A02 real-data finding:** `dq_status=unknown` for all 17,177 new cell CSV rows; strict exact 6-band-description condition in `cell_quality` is a verified route to this symptom. Optional Data Quality UI buttons do not populate those fields. Actual live band count/description still unobserved; do not claim a confirmed Cloud root cause. Proposed surgical diagnostics/fix, not yet applied: `A02_DQ_UNKNOWN_FIELD_FINDING_2026-11-15.md`.
- No production changes, no new PR, no revalidation of old Yanqing benchmarks, no large GeoJSON/raster inputs added to the public repo. Keep these artifacts in the existing private staging folder.

## Unresolved scientific gates — 15 November 2026, targeted remediation staged

- A02 silent unknown is confirmed in 17,177 new field CSV rows. Nine EE `Export.image.toDrive` single-band TIFFs show band descriptions, so absent names in the distinct application `getDownloadURL` output remain a **hypothesis**, not a proved root cause.
- Prepared but **did not deploy** a fail-closed A02 schema patch (only app-created raster may use verified, unlabeled six-band positional fallback). Explicit schema warnings and focused regression controls are included in `remaining_field_package.zip` (8/8 focused tests pass locally). No NTL/Moran/LISA estimator modifications.
- Prepared 5 real-data EE exports for one A02 six-band Bao'an raster and matched native/reprojected GHSL 2020 built/pop at Shanghai. No Earth Engine task has been submitted from this session. Run once and process Drive outputs when available; do not repeat Yanqing/V11.
- Cloud runtime remains unmeasured; owner Cloud logs available via Manage app; no claims of memory PASS.
- Remain on ONE future consolidated PR. Source rasters and large geospatial outputs remain outside public repo.

## Field update 15 November 2026 — GHSL measured real-world bias; A02 six-band EE export

- Five distinct TIFF export products were located in two same-named Google Drive folders. The folder preview briefly omitted the two new native GHSL files; direct `list_folder` found both. Source bytes were retrieved and analyzed; no re-export needed.
- **GHSL empirical defect confirmed:** Shanghai 2020 `JRC/GHSL/P2023A` `GHS_BUILT_S` and `GHS_POP` per-native-100m-cell amounts were exported at native Mollweide 100 m and application-style EPSG:4326 `scale=100`. In a common inset geographic core, naive appstyle sums exceed native by **16.51428% built area** and **16.59686% population**. Reprojection of the native raster to the app grid by nearest neighbor matched **42,244/42,244** app-grid samples for each product exactly: native per-pixel amounts were duplicated onto more/smaller cells before unadjusted zonal sums. Original `ntl/ee_extra.py` hardcodes EPSG:4326 and `ntl/quality_ui.py` sums destination-grid amounts. This is real-world, source-grid quantity-conservation evidence, not a synthetic demonstration. Impact at other sites remains unmeasured.
- **A02 field reference verified but Cloud unknown unresolved:** Export.image.toDrive Bao'an six-band VIIRS GeoTIFF contains exact six `avg_rad` and `dq_` band descriptions. Band one matched the independent 2020 VIIRS median on every **26,786/26,786** shared finite pixel. All 27,013 quality pixels are observed with **9–12** monthly supports; the export lacks genuine missing/low-support cells. Streamlit uses distinct getDownloadURL route and its 17,177 prior CSV rows have `dq_status=unknown`; cannot declare Cloud root cause solved from this export.
- New non-GitHub staged evidence: `GHSL_A02_REAL_FIELD_FINDINGS_2026-11-15.md`, `GHSL_A02_SHANGHAI_BAOAN_FIELD_METRICS_2026-11-15.json`, and `ghsl_field_compare_2020.py`. GeoTIFF input bytes stay on connected Google Drive; hashes are in JSON. Implement the GHSL native-grid conservation fix and fail-closed A02 Cloud schema diagnosis together only after review, **one consolidated PR**. No repetition of Yanqing/V11 and no production code edit in this field audit.

## 15 November 2026 — In-app performance instrumentation and native GHSL correction candidate

User has no Streamlit Cloud **Manage app** access and therefore cannot obtain owner logs. In the **same planned consolidated PR** (not a new PR), add owner-visible/self-service profiling:

- `ntl/performance.py` (new): `PerformanceRecorder` with `time.perf_counter`, 0.1s sampled process RSS from `/proc/self/status` (optional psutil fallback), end-to-end pipeline duration, per-stage elapsed time, short error type only, and in-app JSON/CSV download. No external reporting endpoint or user-data logging. Process RAM can include concurrent sessions; high-water mark is sampled, not guaranteed maximum.
- Strict integration into `app.py`, `ntl/lisa_ui.py`, `ntl/quality_ui.py`: time boundary loading, grid creation, Earth Engine download, exactextract mean, A02 per-cell quality, Global Moran, Local LISA, extra Space-Time year retrieval, native GHSL fetch, GHSL zonal sum and GHSL external-proxy agreement. A failing main pipeline still has a per-stage diagnostic in-app. The performance panel appears in LISA after a successful analysis.
- `ntl/ghsl_native.py` (new): source-grid affine and CRS windowing with 100m native Mollweide pixel alignment. Earth Engine getDownloadURL's `region` parameter is ignored when CRS+transform are specified, so pass bounded `dimensions` plus source CRS+transform and pre-clip image to ROI. Validate pixel count, CRS, transform and grid dimensions of downloaded TIFF before zonal sum. The exact window for the real Shanghai native GHSL raster is 331 x 202 pixels and affine `[100,0,11030200,0,-100,3800200]`, as measured previously.
- Carry forward the earlier fail-closed A02 six-band schema patch and focused tests, no change to zero-fill NTL/Moran/LISA models.
- Candidate file `Spatial_App_Consolidated_PR_Candidate_A02_GHSL_Performance_2026-11-15.zip` in this staging folder. Includes `apply_consolidated_review_patch.py` to generate **one unified diff** inside a clean repository checkout; default does not modify or commit anything. GitHub integration anchor counts verified against `main` (all expected counts), although the actual full Streamlit/EE deployment has **not** yet been exercised.
- **16/16 focused tests PASS** in isolated container Python (A02=8, GHSL source-grid=4, profiler=4). These are not equivalent to a Cloud/EE green light. `targeted_tests.xml` is bundled.
- Stop gate: compare the corrected native GHSL per-cell totals/Spearman/AUC against the already-saved real raster reference and capture one authenticated Cloud profiler JSON; verify A02 real `getDownloadURL` schema. Do not declare GHSL/A02/Cloud fully closed before this. No new PR opened and no old V11/Yanqing reruns.

## 15 November 2026 — User-supplied Cloud log and consolidated draft PR #24

- Reviewed complete 1,313-line Streamlit Cloud log covering 11–14 November (downloaded 14 November). Detected two historic `ntl.semantics` import tracebacks on 12 November followed by app updates, 99 `st.components.v1.html` notices, 107 `use_container_width` notices, 34 CartoDB API-key warnings, Python 3.14.10, and automatic downgrade from PyArrow 26 to 24. No logged OOM, forced kill, or timeout. The uploaded log cannot establish Cloud per-analysis timing or a process RAM bound.
- GitHub **draft PR #24** opened: https://github.com/hoanfg/spatial-app/pull/24 (branch `review/consolidated-a02-ghsl-runtime-2026-11`, head `0a1dec7c5a471e600d96f2347cae001ef3c74910`). It consolidates GHSL native-source-grid fixes, A02 schema diagnostics, visible runtime profiler, tests and compact field/log evidence in 12 files. **Main remains unchanged.** Raw field data and logs are not committed.
- Targeted GHSL-native and performance tests re-executed in the available environment: **8 passed**. Full GitHub Actions CI was still in progress when the PR was opened. The 8 A02 tests and full test matrix require CI / the geospatial test environment. Do not claim a merge-ready state until CI, Cloud A02 download schema, GHSL results and profiler JSON are checked.
- Preserve the original one-PR rule: do not open a secondary fix PR or re-run historical Yanqing/V11 evidence without a change that warrants it. Any necessary review changes should update the **same PR #24**.

### 15 November 2026 — Draft PR #24 CI regression fixes and gate

- Opened one draft PR #24 on the reviewed `main` snapshot; public PR: https://github.com/hoanfg/spatial-app/pull/24. No merge, no production deployment, no separate follow-up PR. Field data and full user Cloud log are not committed.
- Initial PR CI failed in the lightweight core job because the new `ntl/ghsl_native.py` imported Rasterio at module import time. This was corrected with a lazy `transform_bounds` import (commit `9218ec185d836b26913b9c6ded452517d92228e7`).
- Next core CI completed 30/32 tests, with two legacy GHSL tests failing because the revised fetch path imported `requests` in the lightweight test job and used a new native-grid transport. Introduced `_download_native()` with lazy `requests` import, restored the early large-bbox guard, and adjusted the existing GHSL mock test to validate the native-window interface rather than the removed reprojecting download (commit `b4f25b45bacc49c581fa1610afe110a78c747bea`).
- **Final CI on `b4f25b45`: both `push` and `pull_request` workflows completed SUCCESS**, each running core T01–T28 and UI AppTest jobs. PR body gate checkbox updated. No extra Yanqing/V11 analysis performed.
- **Remaining merge blockers:** authenticated Cloud A02 six-band schema and per-cell DQ, native GHSL cell sums/metric changes, in-app performance JSON/RSS on representative runs, map fallback/interface compatibility checks. The PR remains a draft; `main` remains unchanged.

<!-- END ORIGINAL SOURCE 064 -->


---

## Source 065: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/remaining_validation_20261115/README.md`

**Original bytes:** 5,568 · **SHA-256:** `c77f737d7a59562c5f476f3cc688dc62a1f87bcc3ba9f55ebd77c7afaa0a2140` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 065 -->
# Spatial App — Unresolved-field-evidence package (single future PR)

Date: 2026-11-15. Repository: `hoanfg/spatial-app` (main). **Private staging only**: no PR, no repository changes, no geospatial data copied into the repository. Historical Yanqing/V11/FDR/Moran findings are reused and were not recomputed.

## A02 `dq_status=unknown`: established facts vs open hypotheses

- All 17,177 app CSV cells for Shanghai, Bao'an and Qimen carry unknown A02 status, but independently checked NTL values remain valid. This is an **observed field failure**, not missing button presses.
- Production `cell_quality()` currently requires `src.count==6` and exact names `src.descriptions[1:] == QUALITY_BANDS`; failure silently gives NaN/unknown. This is an established failure mechanism.
- The 9 independent EE `Export.image.toDrive` TIFFs contain names (single-band `avg_rad` / `valid_month`). Therefore **do not claim** that the app's different `getDownloadURL(format='GEO_TIFF')` route necessarily strips names.
- The pending targeted patch adds a verified-producer **unlabeled six-band** fallback, validation of binary flags/month counts/mutual consistency, and explicit UI diagnostics if count/schema is truly wrong. Arbitrary user TIFFs, partly named/conflicting TIFFs, and 1-band TIFFs are never assumed to have quality bands. Preserve all existing NTL/LISA formulas.
- `ntl/semantics.py` is the proposed module replacement. `apply_a02_schema_patch.py` generates a **reviewable diff** from a real checkout, updating that module and the two downstream consumers in `app.py` plus `ntl/quality_ui.py`; the script does **not** modify a checkout without `--write`. This patch has **NOT been applied to the public GitHub repository**.
- New focused tests: `python -m pytest -q tests/test_a02_field_schema.py` → **8 passed** in the staging environment (Python 3.13, Rasterio 1.5.0). This is a focused regression, not full CI and not live EE proof.

## Exactly five new exports (GHSL and A02)

Open `validation/gee_a02_ghsl_field_exports_2020.js` in Google Earth Engine Code Editor. It creates **5 tasks** in Drive folder `spatial_app_field_validation_2020`:

1. `baoan_2020_a02_six_band_reference.tif` — production-equivalent six-band radiance/quality image, aligned to the *already exported* Bao'an 2020 reference TIFF.
2. `shanghai_2020_ghsl_built_native_100m.tif` — JRC GHSL built-surface 2020, **Earth Engine asset's native projection and affine transform**.
3. `shanghai_2020_ghsl_built_appstyle_4326_100m.tif` — same image reprojected with production `EPSG:4326`, scale 100m.
4. `shanghai_2020_ghsl_pop_native_100m.tif` — GHSL population count on source 100m projection.
5. `shanghai_2020_ghsl_pop_appstyle_4326_100m.tif` — matching production-style reprojection.

If EE splits files into same-named Drive folders, leave them intact: Drive search by folder and filename can locate them. No new CSV/GeoJSON is required; the existing Shanghai district 2020 CSV and GeoJSON are already available.

**Limits:** GHSL paired exports are *real EE GHSL field data* and permit measuring reprojection-related per-cell/region quantity shifts. They do not replace an independently downloaded JRC source tile for a full cross-provider replication. The A02 Drive export probes real six-band pixel semantics/labels, but does not observe the raw TIFF bytes returned to Streamlit Cloud by `getDownloadURL`; production schema status remains unknown until the targeted logging patch is deployed or a raw capture is obtained.

To audit GHSL, use the existing private staging tool `audit_ghsl_native_vs_reprojected.py` from the earlier v4 bundle (one run each `kind=built` and `kind=pop`). It compares exact fractional pixel-polygon sums, valid coverage and Spearman-rank movement. Do not compare global raster totals: use the clipped GADM cells and their complete-coverage flags.

## Streamlit Cloud — remaining operational gate

CI is not a memory benchmark. Real latency/peak RAM/HTTP failure analysis requires a run in Streamlit Community Cloud. The owner can open the app, select **Manage app** at bottom right, then download **Cloud logs**. Do not upload `.streamlit/secrets.toml`, credentials or personal-account tokens. Logs show errors but not necessarily peak RAM; a controlled, opt-in in-app profiler would be needed for exact RAM use. No RAM or latency PASS is claimed.

## Single-PR acceptance gate

- A02: Six-band GeoTIFF has correct schema, aligns with masked-median and months reference, no false distinction between missing / zero / negative; live application shows populated `dq_` fields after deploying fix. Any unknown schema is visible to the user.
- GHSL: Real **native vs appstyle** raster inputs have matching year/band/provenance and quantified per-cell disagreement. Decide whether the production GHSL `zonal_stat(sum)` needs a conservation-aware approach from *measured* results, not synthetic bias guesses.
- Cloud: Actual operational logs / measurements are reviewed with no unexplained failures.
- Only then prepare **one consolidated PR**, importing *selected* code and compact evidence summaries; keep large private data and source GeoTIFFs off GitHub.

## Public sources

- VIIRS: `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` (2020), `avg_rad` masked by `cf_cvg > 0`.
- JRC GHSL built-up `JRC/GHSL/P2023A/GHS_BUILT_S/2020` (`built_surface` m²/pixel).
- JRC GHSL population `JRC/GHSL/P2023A/GHS_POP/2020` (`population_count` persons/pixel).
- EE `Export.image.toDrive()` with `crsTransform` and `crs` explicitly documented for native-pixel alignment.

<!-- END ORIGINAL SOURCE 065 -->


---

## Source 066: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/review_work_20261114/PR_STAGING_NOTES.md`

**Original bytes:** 4,992 · **SHA-256:** `972a638ebbac490dc990ca0d5602f04a500ffe03d3d4b8d99e0a6b6581599c9d` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 066 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 14 November 2026 (revised from 13 November). Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Nine tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

## Review update 14 November 2026 — no new PR

- Hardened the GHSL check against **partial-coverage false positives**: eligible cells must have nearly 100% finite, unmasked raster area in BOTH native and app exports. Ineligible per-cell differences are NaN, not numerically compared.
- Added guard for GHSL native 100 m product resolution; a wrongly supplied 1 km raster fails preflight.
- Hardened A02 source independence: selecting ROI from the application's own band-1 mask could silently drop an app-side masked pixel. Reference valid-month count now defines the footprint, so this case fails.
- Negative controls expanded; `python -m pytest -q test_validation_scripts.py` now reports **9 passed**.
- All field validation gates remain unfulfilled without matching real-data rasters and application exports. Preserve project policy: **one future consolidated PR**, no branch/PR in this stage.

<!-- END ORIGINAL SOURCE 066 -->


---

## Source 067: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/review_work_20261114/README.md`

**Original bytes:** 7,942 · **SHA-256:** `b3a3b72db9e8ef51843c77824bebf500ef359bafd9596b6cf91c6ba6eaef7648` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 067 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **14 November 2026** (updated from 13 November). Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code only, no Earth Engine credentials, private data or real-world result tables**. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** nine synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV is a spatial-app cell export containing `grid_id`, `area_km2`, `ntl_mean` for the same GADM boundary and 500 m cell configuration.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas and source 100 m resolution, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Each cell now reports native/app **valid-area fractions**, and a comparison is eligible only with at least 99.9999% valid area in both rasters. Merely intersecting a single valid pixel cannot justify full coverage. Missing or partial reference/application coverage is reported and causes a nonzero CLI exit code. Ineligible differences are blanked, while partial raw sums remain available only for diagnostics. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters. The **independent month-count** reference mask defines the comparison footprint; a missing/masked application pixel is flagged rather than excluded from validation. Extra app-only coverage outside the count reference also fails.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (9 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

## November 14 reviewer hardening

- GHSL now measures **fraction of each polygon covered by finite unmasked raster pixels**, not just the presence of any intersection. Only fully covered cells enter regional comparison totals and Spearman; partial diagnostics remain visible but never silently pass.
- Native GHSL must have projected 100 m resolution (within 1 m tolerance); the code still cannot independently prove the correct version/epoch/band without source metadata.
- A02 uses **independent reference count coverage** to choose pixels for validation. App-masked observations with valid reference count are checked as failures rather than skipped.
- Negative controls exercise one missing interior source pixel, invalid native product resolution, and an application-only missing A02 pixel. Nine tests pass as of this staging version.

See `REVIEW_FINDINGS_2026-11-14.md` for the checker's identified failure modes and scientific boundaries.

<!-- END ORIGINAL SOURCE 067 -->


---

## Source 068: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/review_work_20261114/REVIEW_FINDINGS_2026-11-14.md`

**Original bytes:** 3,461 · **SHA-256:** `5ddace573c0c0c79920b1812a29b11205a3c2932bbfc57000558bf6d0975d95e` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 068 -->
# Spatial App — Staging review findings (14 November 2026)

## Executive finding

Three **potential false-assurance paths in the external validation checkers** were found and corrected in this staged package. These are **checker defects**, not demonstrated defects in the Spatial App production analysis. No changes were made to the GitHub repository.

| ID | Prior checker behavior | Risk | Hardening | Synthetic negative control |
|---|---|---|---|---|
| S01 | GHSL considered a cell covered if *any* finite pixel intersected it | An area with partly missing source data could be treated as fully comparable | Compute valid-area fraction per cell; require >= 0.999999 from both rasters; drop partial cells from quantitative differences; incomplete coverage forces non-zero CLI status | One interior source NoData pixel triggers incomplete coverage |
| S02 | GHSL accepted any projected native raster | A 1 km or unrelated grid could be mislabeled as the 100 m source | Native resolution within 1 m of 100 m required, still manually verify product/band/epoch | 1 km synthetic input rejected |
| S03 | A02 checked only the pixels where the application's first band had an unmasked value | A corrupted app-side mask could remove failing pixels from the test set | Use independent valid-month count raster to define reference footprint, flag extra app-only pixels | One app-only masked pixel is detected |

## Test execution

- Command: `python -m pytest -q test_validation_scripts.py`.
- Result: **9 passed** in the isolated synthetic checker suite.
- No field GHSL or new Earth Engine export was supplied or used in these tests.
- `pytest-results.xml` contains executable test evidence; `SHA256SUMS.txt` records staged file hashes.

## Scientific boundaries

- GHSL native data are per-pixel quantities (residential population count or built-up m²), not population or built-up density. Summation must account for pixel/polygon intersection fraction.
- Spatial App's GHSL `fetch_ghsl_raster` reprojects into EPSG:4326 at a requested 100 m scale and selects the first band; a potential bias due to reprojection remains **unquantified** without corresponding real source raster and app-exported GeoTIFF.
- A complete geometric coverage check cannot recover observational missingness that the application has previously converted to zero (`unmask(0)`). The detector reports this separately.
- Six-band A02 comparisons require three perfectly aligned real exports. Source-layer equivalence (same year, monthly filter and exact raster grid) remains a manual gate.
- CI PASS on 9 tests confirms only checker behavior under the included cases, not V11 completion, GHSL field accuracy or A02 field validity.

## Source method references

- GHSL POP product: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL BUILT-S product: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- GHSL JRC open downloads: https://human-settlement.emergency.copernicus.eu/download.php
- Earth Engine resampling: https://developers.google.com/earth-engine/guides/resample
- ExactExtract operations: https://isciences.github.io/exactextract/operations.html

## Staging policy

Do not open a new micro-PR for this report alone. The corrected tools and tests are held for the owner's **one consolidated future review PR**. The package contains no GHSL tiles or other large geospatial datasets and no credentials.

<!-- END ORIGINAL SOURCE 068 -->


---

## Source 069: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/review_work_20261115/PR_STAGING_NOTES.md`

**Original bytes:** 10,484 · **SHA-256:** `fd601f45ab4e5a626d45d10ac8c16341b7bbea1edf62e87c1705939c30f804aa` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 069 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 14 November 2026 (revised from 13 November). Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Eleven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

## Review update 14 November 2026 — no new PR

- Hardened the GHSL check against **partial-coverage false positives**: eligible cells must have nearly 100% finite, unmasked raster area in BOTH native and app exports. Ineligible per-cell differences are NaN, not numerically compared.
- Added guard for GHSL native 100 m product resolution; a wrongly supplied 1 km raster fails preflight.
- Hardened A02 source independence: selecting ROI from the application's own band-1 mask could silently drop an app-side masked pixel. Reference valid-month count now defines the footprint, so this case fails.
- Negative controls expanded; `python -m pytest -q test_validation_scripts.py` now reports **11 passed**.
- All field validation gates remain unfulfilled without matching real-data rasters and application exports. Preserve project policy: **one future consolidated PR**, no branch/PR in this stage.

## 15 November 2026 — v4 single-PR carry-forward

1. Require **actual per-ID spatial identity** using UTM and WGS84 centroids, not only grid ID/area. The current production app already exports all required fields. Checker code and comparator are staged, not pushed to GitHub.
2. Reject non-integral valid-month counts in A02 references.
3. **11/11 isolated checker tests passed.** Deliberate same-area grid swaps and missing centroid columns are rejected.
4. Historical Yanqing 2020 GADM, real VIIRS raster and application CSV were checked with the amended comparator. Exactly **8,333/8,333** per-cell NTL references and centroid identity comparisons passed at exported rounding tolerances; detailed metrics JSON and source hashes are included, but private input raster/GeoJSON/CSV and the 8,333-row diagnostic table are *not* bundled.
5. No new branch, PR, production algorithm changes or geospatial data bundles. One consolidated PR remains the only proposed repository update.

## Field update 15 November 2026 — V11 edge closure + A02 real-data `unknown`

- **V11 new evidence:** analyzed exactly 1,847 previously excluded boundary-clipped cells from 3 user GeoJSONs against 3 independent EE VIIRS TIFFs. All covered. 1,846/1,847 pass the literal 5e-5 half-bin; one Bao'an record (`grid_id=628`) exceeds by 3.93e-8 and is explicitly reported; 1,847/1,847 pass 5.01e-5 including a 1e-7 floating guard. Prior 15,330 core cell results were not repeated. Detailed private report: `V11_EDGE_COMPLETION_2026-11-15.md`.
- **A02 real-data finding:** `dq_status=unknown` for all 17,177 new cell CSV rows; strict exact 6-band-description condition in `cell_quality` is a verified route to this symptom. Optional Data Quality UI buttons do not populate those fields. Actual live band count/description still unobserved; do not claim a confirmed Cloud root cause. Proposed surgical diagnostics/fix, not yet applied: `A02_DQ_UNKNOWN_FIELD_FINDING_2026-11-15.md`.
- No production changes, no new PR, no revalidation of old Yanqing benchmarks, no large GeoJSON/raster inputs added to the public repo. Keep these artifacts in the existing private staging folder.

## Unresolved scientific gates — 15 November 2026, targeted remediation staged

- A02 silent unknown is confirmed in 17,177 new field CSV rows. Nine EE `Export.image.toDrive` single-band TIFFs show band descriptions, so absent names in the distinct application `getDownloadURL` output remain a **hypothesis**, not a proved root cause.
- Prepared but **did not deploy** a fail-closed A02 schema patch (only app-created raster may use verified, unlabeled six-band positional fallback). Explicit schema warnings and focused regression controls are included in `remaining_field_package.zip` (8/8 focused tests pass locally). No NTL/Moran/LISA estimator modifications.
- Prepared 5 real-data EE exports for one A02 six-band Bao'an raster and matched native/reprojected GHSL 2020 built/pop at Shanghai. No Earth Engine task has been submitted from this session. Run once and process Drive outputs when available; do not repeat Yanqing/V11.
- Cloud runtime remains unmeasured; owner Cloud logs available via Manage app; no claims of memory PASS.
- Remain on ONE future consolidated PR. Source rasters and large geospatial outputs remain outside public repo.

## Field update 15 November 2026 — GHSL measured real-world bias; A02 six-band EE export

- Five distinct TIFF export products were located in two same-named Google Drive folders. The folder preview briefly omitted the two new native GHSL files; direct `list_folder` found both. Source bytes were retrieved and analyzed; no re-export needed.
- **GHSL empirical defect confirmed:** Shanghai 2020 `JRC/GHSL/P2023A` `GHS_BUILT_S` and `GHS_POP` per-native-100m-cell amounts were exported at native Mollweide 100 m and application-style EPSG:4326 `scale=100`. In a common inset geographic core, naive appstyle sums exceed native by **16.51428% built area** and **16.59686% population**. Reprojection of the native raster to the app grid by nearest neighbor matched **42,244/42,244** app-grid samples for each product exactly: native per-pixel amounts were duplicated onto more/smaller cells before unadjusted zonal sums. Original `ntl/ee_extra.py` hardcodes EPSG:4326 and `ntl/quality_ui.py` sums destination-grid amounts. This is real-world, source-grid quantity-conservation evidence, not a synthetic demonstration. Impact at other sites remains unmeasured.
- **A02 field reference verified but Cloud unknown unresolved:** Export.image.toDrive Bao'an six-band VIIRS GeoTIFF contains exact six `avg_rad` and `dq_` band descriptions. Band one matched the independent 2020 VIIRS median on every **26,786/26,786** shared finite pixel. All 27,013 quality pixels are observed with **9–12** monthly supports; the export lacks genuine missing/low-support cells. Streamlit uses distinct getDownloadURL route and its 17,177 prior CSV rows have `dq_status=unknown`; cannot declare Cloud root cause solved from this export.
- New non-GitHub staged evidence: `GHSL_A02_REAL_FIELD_FINDINGS_2026-11-15.md`, `GHSL_A02_SHANGHAI_BAOAN_FIELD_METRICS_2026-11-15.json`, and `ghsl_field_compare_2020.py`. GeoTIFF input bytes stay on connected Google Drive; hashes are in JSON. Implement the GHSL native-grid conservation fix and fail-closed A02 Cloud schema diagnosis together only after review, **one consolidated PR**. No repetition of Yanqing/V11 and no production code edit in this field audit.

<!-- END ORIGINAL SOURCE 069 -->


---

## Source 070: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/review_work_20261115/README.md`

**Original bytes:** 9,716 · **SHA-256:** `a0b82b9fd376b4e8c3f96adfb7e8f7f7497e761a9f6dee2cf070c56371c284e9` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 070 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **15 November 2026** (incremental v4 of 13–14 November staging). Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code and a small, reproducible Yanqing 2020 metrics JSON**, but no Earth Engine credentials, private input GeoTIFFs, original GADM boundaries, or large per-cell result tables. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** eleven synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV must be a current Spatial App cell export containing `grid_id`, `area_km2`, `ntl_mean` and four rounded **per-ID centroids** (`centroid_lon`, `centroid_lat`, `centroid_x_epsgNNNN`, `centroid_y_epsgNNNN`) for the same GADM boundary and grid. Area and IDs alone are insufficient to detect identical-size cells reordered geographically.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas and source 100 m resolution, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Each cell now reports native/app **valid-area fractions**, and a comparison is eligible only with at least 99.9999% valid area in both rasters. Merely intersecting a single valid pixel cannot justify full coverage. Missing or partial reference/application coverage is reported and causes a nonzero CLI exit code. Ineligible differences are blanked, while partial raw sums remain available only for diagnostics. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters. The **independent month-count** reference mask defines the comparison footprint; a missing/masked application pixel is flagged rather than excluded from validation. Extra app-only coverage outside the count reference also fails.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (11 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

## November 14 reviewer hardening

- GHSL now measures **fraction of each polygon covered by finite unmasked raster pixels**, not just the presence of any intersection. Only fully covered cells enter regional comparison totals and Spearman; partial diagnostics remain visible but never silently pass.
- Native GHSL must have projected 100 m resolution (within 1 m tolerance); the code still cannot independently prove the correct version/epoch/band without source metadata.
- A02 uses **independent reference count coverage** to choose pixels for validation. App-masked observations with valid reference count are checked as failures rather than skipped.
- Negative controls exercise one missing interior source pixel, invalid native product resolution, and an application-only missing A02 pixel. Eleven tests pass as of this staging version.

See `REVIEW_FINDINGS_2026-11-14.md` for the checker's identified failure modes and scientific boundaries.

## 15 November addendum — grid identity and negative controls

- **GHSL:** per-cell UTM centroids (application exports rounded to 0.1 m) and geographic centroids (six decimal places) must match the independently reconstructed grid at their respective rounding precision. Omitting these four columns is an error, not permission to skip the spatial-identity check.
- **Cross-location comparator:** the staged `compare_raster_cells.py` now applies the same per-ID geometry gate *before* calculating raster zonal statistics. It is intended to replace the existing script in the **single future consolidated PR**, not to create a micro-PR.
- **A02:** reject a valid-month raster with fractional counts, which can indicate an improperly resampled month-count reference. A count of months must be integral.
- **Real-data regression:** independent raster–polygon overlay was rerun on the historical Yanqing 2020 archive. **8,333/8,333** NTL cells met the CSV rounding tolerance (0.00005 nW/cm²/sr), and **8,333/8,333** UTM/WGS84 centroids met their recorded rounding tolerances. See `yanqing_2020_regression_metrics.json` and the recorded input SHA-256s. A controlled swap of the locations of two equal-area historical cells was rejected.
- **Limits:** this is a reproducibility check of the previously archived Yanqing data, **not** a newly acquired VIIRS/A02 six-band or JRC GHSL dataset. V11, GHSL live comparison and A02 real missingness remain PENDING.

<!-- END ORIGINAL SOURCE 070 -->


---

## Source 071: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/review_work_20261115/REVIEW_FINDINGS_2026-11-15.md`

**Original bytes:** 4,122 · **SHA-256:** `0ce9c8d7b12bc8066a5b1899516f55587a7e0ec3c9772be84c2611f48b1e69dd` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 071 -->
# Spatial App — Independent checker follow-up (15 November 2026)

## Decision

Continue staging changes for one future major-review PR; no new PR and no changes to production formulas. An area-only comparator can fail to detect a spatial identity mismatch for equal-area cells. Fix the independent checking tools before interpreting later GHSL comparisons.

## Finding S04 — same-area ID swaps bypass the previous area gate

- Observed in: both the staged GHSL comparator and the existing `validation/cross_location/compare_raster_cells.py` checked grid IDs, polygon counts and areas, but not **per-ID geographic identity**.
- Why this matters: two full 500 m grid cells both have `area_km2 = 0.25`; their polygon-to-CSV pairing can be wrong while an area and ID validation still reports success.
- Remedy staged: check rounded UTM centroids (`centroid_x_epsgNNNN` and `centroid_y_epsgNNNN`, tolerance 0.051 m) and geographic centroids (`centroid_lon`, `centroid_lat`, tolerance 0.00000051°) against the independently recreated clipped GADM polygon for each `grid_id`.
- Negative control: interchange the exported centroid coordinates of two equal-area cells while leaving `grid_id` and `area_km2` untouched. Both staged comparators reject the mismatch. Missing centroid metadata also forces explicit failure.
- Production code and CSV schemas: **unchanged**; required centroid columns already exist in normal current application exports.

## Historical Yanqing field regression

A replay of the updated `compare_raster_cells.py` used:

- full-precision GADM 4.1 Yanqing GeoJSON from the historical private archive;
- the VIIRS 2020 annual reference GeoTIFF from the same archive;
- the **original** application 2020 500 m CSV with UTM/WGS84 centroids;
- 500 m clipped UTM grid, matching the existing baseline inference geometry.

Results: **8,333/8,333 cells** passed the raster–polygon NTL comparison within 0.00005 nW/cm²/sr (MAE 0.0000250230; maximum absolute error 0.0000499933). All **8,333/8,333 cells** also met the geographic centroid identity rounding tolerances. The maximum UTM-x and UTM-y rounding discrepancies were 0.049872 m and 0.049979 m; maximum longitude/latitude discrepancy was below 0.0000005°. The source and script checksums are retained in `yanqing_2020_regression_metrics.json` and `SHA256SUMS.txt`.

This is an **independent recomputation using archived field input** from Yanqing, not new field sampling. A controlled same-area swap of two historical full-size cells was correctly rejected by the new check. It does not establish V11 across contrasting locations or GHSL product equality.

## Finding S05 — fractional monthly observation counts

The staged A02 checker checked count in `[0,12]` but did not reject, for example, `2.5` months of annual valid observation support. Such a value can arise if a reference count raster is improperly interpolated. The checker now requires integral valid-month counts, and the corrupted synthetic example is rejected.

## Scope availability on archived VIIRS rasters

Historical annual medians and month-count reference rasters have 30,814 pixels per year (2014 and 2020). In both cases all count pixels recorded 12 valid months and no median pixels were masked. The 2014 raster contained one negative valid median; 2020 had none. Neither case contained measured-zero medians or fewer-than-three-month support. **These real images cannot test the A02 data-semantics edge cases involving genuine missing observations.**

## Acceptance log

- **11 passed** — `python -m pytest -q test_validation_scripts.py` (synthetic oracle and negative-control tests).
- **8,333 passed** — Yanqing 2020 archived field raster/polygon comparator and per-ID centroid verification.
- **Expected fail** — spatial-identity negative control on two same-area historical cell IDs.
- **Not run / PENDING** — GHSL native JRC 100 m versus real Earth Engine reprojected raster; A02 true six-band export; Shanghai/Bao'an/Qimen independent per-cell validation; Cloud benchmark.
- No new PR, no code modification in `ntl/`, and no large GeoJSON/GeoTIFF committed.

<!-- END ORIGINAL SOURCE 071 -->


---

## Source 072: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/spatial_validation_followup/PR_STAGING_NOTES.md`

**Original bytes:** 4,067 · **SHA-256:** `26a3a56a1a57839e45bb4066d32b92675c143ccbb676782afe14d93ad1caa4ae` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 072 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 13 November 2026. Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Seven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

<!-- END ORIGINAL SOURCE 072 -->


---

## Source 073: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/spatial_validation_followup/README.md`

**Original bytes:** 6,389 · **SHA-256:** `88d35d669a6caecbbfa0c6976d5e5a7f248a8177ab2de79015d2da53165d82f6` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 073 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **13 November 2026**. Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code only, no Earth Engine credentials, private data or real-world result tables**. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** seven synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV is a spatial-app cell export containing `grid_id`, `area_km2`, `ntl_mean` for the same GADM boundary and 500 m cell configuration.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Missing reference or application coverage is reported and causes a nonzero CLI exit code. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (7 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

<!-- END ORIGINAL SOURCE 073 -->


---

## Source 074: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/spatial_work/PR_STAGING_NOTES.md`

**Original bytes:** 13,224 · **SHA-256:** `92e2c9dd00b4627d9e23cf843574f982e66d2025414a76e4c2a1e0699c0e1e30` · **Origin:** direct_file

<!-- BEGIN ORIGINAL SOURCE 074 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 14 November 2026 (revised from 13 November). Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Eleven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

## Review update 14 November 2026 — no new PR

- Hardened the GHSL check against **partial-coverage false positives**: eligible cells must have nearly 100% finite, unmasked raster area in BOTH native and app exports. Ineligible per-cell differences are NaN, not numerically compared.
- Added guard for GHSL native 100 m product resolution; a wrongly supplied 1 km raster fails preflight.
- Hardened A02 source independence: selecting ROI from the application's own band-1 mask could silently drop an app-side masked pixel. Reference valid-month count now defines the footprint, so this case fails.
- Negative controls expanded; `python -m pytest -q test_validation_scripts.py` now reports **11 passed**.
- All field validation gates remain unfulfilled without matching real-data rasters and application exports. Preserve project policy: **one future consolidated PR**, no branch/PR in this stage.

## 15 November 2026 — v4 single-PR carry-forward

1. Require **actual per-ID spatial identity** using UTM and WGS84 centroids, not only grid ID/area. The current production app already exports all required fields. Checker code and comparator are staged, not pushed to GitHub.
2. Reject non-integral valid-month counts in A02 references.
3. **11/11 isolated checker tests passed.** Deliberate same-area grid swaps and missing centroid columns are rejected.
4. Historical Yanqing 2020 GADM, real VIIRS raster and application CSV were checked with the amended comparator. Exactly **8,333/8,333** per-cell NTL references and centroid identity comparisons passed at exported rounding tolerances; detailed metrics JSON and source hashes are included, but private input raster/GeoJSON/CSV and the 8,333-row diagnostic table are *not* bundled.
5. No new branch, PR, production algorithm changes or geospatial data bundles. One consolidated PR remains the only proposed repository update.

## Field update 15 November 2026 — V11 edge closure + A02 real-data `unknown`

- **V11 new evidence:** analyzed exactly 1,847 previously excluded boundary-clipped cells from 3 user GeoJSONs against 3 independent EE VIIRS TIFFs. All covered. 1,846/1,847 pass the literal 5e-5 half-bin; one Bao'an record (`grid_id=628`) exceeds by 3.93e-8 and is explicitly reported; 1,847/1,847 pass 5.01e-5 including a 1e-7 floating guard. Prior 15,330 core cell results were not repeated. Detailed private report: `V11_EDGE_COMPLETION_2026-11-15.md`.
- **A02 real-data finding:** `dq_status=unknown` for all 17,177 new cell CSV rows; strict exact 6-band-description condition in `cell_quality` is a verified route to this symptom. Optional Data Quality UI buttons do not populate those fields. Actual live band count/description still unobserved; do not claim a confirmed Cloud root cause. Proposed surgical diagnostics/fix, not yet applied: `A02_DQ_UNKNOWN_FIELD_FINDING_2026-11-15.md`.
- No production changes, no new PR, no revalidation of old Yanqing benchmarks, no large GeoJSON/raster inputs added to the public repo. Keep these artifacts in the existing private staging folder.

## Unresolved scientific gates — 15 November 2026, targeted remediation staged

- A02 silent unknown is confirmed in 17,177 new field CSV rows. Nine EE `Export.image.toDrive` single-band TIFFs show band descriptions, so absent names in the distinct application `getDownloadURL` output remain a **hypothesis**, not a proved root cause.
- Prepared but **did not deploy** a fail-closed A02 schema patch (only app-created raster may use verified, unlabeled six-band positional fallback). Explicit schema warnings and focused regression controls are included in `remaining_field_package.zip` (8/8 focused tests pass locally). No NTL/Moran/LISA estimator modifications.
- Prepared 5 real-data EE exports for one A02 six-band Bao'an raster and matched native/reprojected GHSL 2020 built/pop at Shanghai. No Earth Engine task has been submitted from this session. Run once and process Drive outputs when available; do not repeat Yanqing/V11.
- Cloud runtime remains unmeasured; owner Cloud logs available via Manage app; no claims of memory PASS.
- Remain on ONE future consolidated PR. Source rasters and large geospatial outputs remain outside public repo.

## Field update 15 November 2026 — GHSL measured real-world bias; A02 six-band EE export

- Five distinct TIFF export products were located in two same-named Google Drive folders. The folder preview briefly omitted the two new native GHSL files; direct `list_folder` found both. Source bytes were retrieved and analyzed; no re-export needed.
- **GHSL empirical defect confirmed:** Shanghai 2020 `JRC/GHSL/P2023A` `GHS_BUILT_S` and `GHS_POP` per-native-100m-cell amounts were exported at native Mollweide 100 m and application-style EPSG:4326 `scale=100`. In a common inset geographic core, naive appstyle sums exceed native by **16.51428% built area** and **16.59686% population**. Reprojection of the native raster to the app grid by nearest neighbor matched **42,244/42,244** app-grid samples for each product exactly: native per-pixel amounts were duplicated onto more/smaller cells before unadjusted zonal sums. Original `ntl/ee_extra.py` hardcodes EPSG:4326 and `ntl/quality_ui.py` sums destination-grid amounts. This is real-world, source-grid quantity-conservation evidence, not a synthetic demonstration. Impact at other sites remains unmeasured.
- **A02 field reference verified but Cloud unknown unresolved:** Export.image.toDrive Bao'an six-band VIIRS GeoTIFF contains exact six `avg_rad` and `dq_` band descriptions. Band one matched the independent 2020 VIIRS median on every **26,786/26,786** shared finite pixel. All 27,013 quality pixels are observed with **9–12** monthly supports; the export lacks genuine missing/low-support cells. Streamlit uses distinct getDownloadURL route and its 17,177 prior CSV rows have `dq_status=unknown`; cannot declare Cloud root cause solved from this export.
- New non-GitHub staged evidence: `GHSL_A02_REAL_FIELD_FINDINGS_2026-11-15.md`, `GHSL_A02_SHANGHAI_BAOAN_FIELD_METRICS_2026-11-15.json`, and `ghsl_field_compare_2020.py`. GeoTIFF input bytes stay on connected Google Drive; hashes are in JSON. Implement the GHSL native-grid conservation fix and fail-closed A02 Cloud schema diagnosis together only after review, **one consolidated PR**. No repetition of Yanqing/V11 and no production code edit in this field audit.

## 15 November 2026 — In-app performance instrumentation and native GHSL correction candidate

User has no Streamlit Cloud **Manage app** access and therefore cannot obtain owner logs. In the **same planned consolidated PR** (not a new PR), add owner-visible/self-service profiling:

- `ntl/performance.py` (new): `PerformanceRecorder` with `time.perf_counter`, 0.1s sampled process RSS from `/proc/self/status` (optional psutil fallback), end-to-end pipeline duration, per-stage elapsed time, short error type only, and in-app JSON/CSV download. No external reporting endpoint or user-data logging. Process RAM can include concurrent sessions; high-water mark is sampled, not guaranteed maximum.
- Strict integration into `app.py`, `ntl/lisa_ui.py`, `ntl/quality_ui.py`: time boundary loading, grid creation, Earth Engine download, exactextract mean, A02 per-cell quality, Global Moran, Local LISA, extra Space-Time year retrieval, native GHSL fetch, GHSL zonal sum and GHSL external-proxy agreement. A failing main pipeline still has a per-stage diagnostic in-app. The performance panel appears in LISA after a successful analysis.
- `ntl/ghsl_native.py` (new): source-grid affine and CRS windowing with 100m native Mollweide pixel alignment. Earth Engine getDownloadURL's `region` parameter is ignored when CRS+transform are specified, so pass bounded `dimensions` plus source CRS+transform and pre-clip image to ROI. Validate pixel count, CRS, transform and grid dimensions of downloaded TIFF before zonal sum. The exact window for the real Shanghai native GHSL raster is 331 x 202 pixels and affine `[100,0,11030200,0,-100,3800200]`, as measured previously.
- Carry forward the earlier fail-closed A02 six-band schema patch and focused tests, no change to zero-fill NTL/Moran/LISA models.
- Candidate file `Spatial_App_Consolidated_PR_Candidate_A02_GHSL_Performance_2026-11-15.zip` in this staging folder. Includes `apply_consolidated_review_patch.py` to generate **one unified diff** inside a clean repository checkout; default does not modify or commit anything. GitHub integration anchor counts verified against `main` (all expected counts), although the actual full Streamlit/EE deployment has **not** yet been exercised.
- **16/16 focused tests PASS** in isolated container Python (A02=8, GHSL source-grid=4, profiler=4). These are not equivalent to a Cloud/EE green light. `targeted_tests.xml` is bundled.
- Stop gate: compare the corrected native GHSL per-cell totals/Spearman/AUC against the already-saved real raster reference and capture one authenticated Cloud profiler JSON; verify A02 real `getDownloadURL` schema. Do not declare GHSL/A02/Cloud fully closed before this. No new PR opened and no old V11/Yanqing reruns.

<!-- END ORIGINAL SOURCE 074 -->


---

## Source 075: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/spatial_work/Spatial_App_A02_GHSL_Remaining_Field_Package.zip::README.md`

**Original bytes:** 5,568 · **SHA-256:** `c77f737d7a59562c5f476f3cc688dc62a1f87bcc3ba9f55ebd77c7afaa0a2140` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 075 -->
# Spatial App — Unresolved-field-evidence package (single future PR)

Date: 2026-11-15. Repository: `hoanfg/spatial-app` (main). **Private staging only**: no PR, no repository changes, no geospatial data copied into the repository. Historical Yanqing/V11/FDR/Moran findings are reused and were not recomputed.

## A02 `dq_status=unknown`: established facts vs open hypotheses

- All 17,177 app CSV cells for Shanghai, Bao'an and Qimen carry unknown A02 status, but independently checked NTL values remain valid. This is an **observed field failure**, not missing button presses.
- Production `cell_quality()` currently requires `src.count==6` and exact names `src.descriptions[1:] == QUALITY_BANDS`; failure silently gives NaN/unknown. This is an established failure mechanism.
- The 9 independent EE `Export.image.toDrive` TIFFs contain names (single-band `avg_rad` / `valid_month`). Therefore **do not claim** that the app's different `getDownloadURL(format='GEO_TIFF')` route necessarily strips names.
- The pending targeted patch adds a verified-producer **unlabeled six-band** fallback, validation of binary flags/month counts/mutual consistency, and explicit UI diagnostics if count/schema is truly wrong. Arbitrary user TIFFs, partly named/conflicting TIFFs, and 1-band TIFFs are never assumed to have quality bands. Preserve all existing NTL/LISA formulas.
- `ntl/semantics.py` is the proposed module replacement. `apply_a02_schema_patch.py` generates a **reviewable diff** from a real checkout, updating that module and the two downstream consumers in `app.py` plus `ntl/quality_ui.py`; the script does **not** modify a checkout without `--write`. This patch has **NOT been applied to the public GitHub repository**.
- New focused tests: `python -m pytest -q tests/test_a02_field_schema.py` → **8 passed** in the staging environment (Python 3.13, Rasterio 1.5.0). This is a focused regression, not full CI and not live EE proof.

## Exactly five new exports (GHSL and A02)

Open `validation/gee_a02_ghsl_field_exports_2020.js` in Google Earth Engine Code Editor. It creates **5 tasks** in Drive folder `spatial_app_field_validation_2020`:

1. `baoan_2020_a02_six_band_reference.tif` — production-equivalent six-band radiance/quality image, aligned to the *already exported* Bao'an 2020 reference TIFF.
2. `shanghai_2020_ghsl_built_native_100m.tif` — JRC GHSL built-surface 2020, **Earth Engine asset's native projection and affine transform**.
3. `shanghai_2020_ghsl_built_appstyle_4326_100m.tif` — same image reprojected with production `EPSG:4326`, scale 100m.
4. `shanghai_2020_ghsl_pop_native_100m.tif` — GHSL population count on source 100m projection.
5. `shanghai_2020_ghsl_pop_appstyle_4326_100m.tif` — matching production-style reprojection.

If EE splits files into same-named Drive folders, leave them intact: Drive search by folder and filename can locate them. No new CSV/GeoJSON is required; the existing Shanghai district 2020 CSV and GeoJSON are already available.

**Limits:** GHSL paired exports are *real EE GHSL field data* and permit measuring reprojection-related per-cell/region quantity shifts. They do not replace an independently downloaded JRC source tile for a full cross-provider replication. The A02 Drive export probes real six-band pixel semantics/labels, but does not observe the raw TIFF bytes returned to Streamlit Cloud by `getDownloadURL`; production schema status remains unknown until the targeted logging patch is deployed or a raw capture is obtained.

To audit GHSL, use the existing private staging tool `audit_ghsl_native_vs_reprojected.py` from the earlier v4 bundle (one run each `kind=built` and `kind=pop`). It compares exact fractional pixel-polygon sums, valid coverage and Spearman-rank movement. Do not compare global raster totals: use the clipped GADM cells and their complete-coverage flags.

## Streamlit Cloud — remaining operational gate

CI is not a memory benchmark. Real latency/peak RAM/HTTP failure analysis requires a run in Streamlit Community Cloud. The owner can open the app, select **Manage app** at bottom right, then download **Cloud logs**. Do not upload `.streamlit/secrets.toml`, credentials or personal-account tokens. Logs show errors but not necessarily peak RAM; a controlled, opt-in in-app profiler would be needed for exact RAM use. No RAM or latency PASS is claimed.

## Single-PR acceptance gate

- A02: Six-band GeoTIFF has correct schema, aligns with masked-median and months reference, no false distinction between missing / zero / negative; live application shows populated `dq_` fields after deploying fix. Any unknown schema is visible to the user.
- GHSL: Real **native vs appstyle** raster inputs have matching year/band/provenance and quantified per-cell disagreement. Decide whether the production GHSL `zonal_stat(sum)` needs a conservation-aware approach from *measured* results, not synthetic bias guesses.
- Cloud: Actual operational logs / measurements are reviewed with no unexplained failures.
- Only then prepare **one consolidated PR**, importing *selected* code and compact evidence summaries; keep large private data and source GeoTIFFs off GitHub.

## Public sources

- VIIRS: `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` (2020), `avg_rad` masked by `cf_cvg > 0`.
- JRC GHSL built-up `JRC/GHSL/P2023A/GHS_BUILT_S/2020` (`built_surface` m²/pixel).
- JRC GHSL population `JRC/GHSL/P2023A/GHS_POP/2020` (`population_count` persons/pixel).
- EE `Export.image.toDrive()` with `crsTransform` and `crs` explicitly documented for native-pixel alignment.

<!-- END ORIGINAL SOURCE 075 -->


---

## Source 076: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/spatial_work/spatial_app_single_pr_staging_2026-11-15_v4.zip::PR_STAGING_NOTES.md`

**Original bytes:** 5,978 · **SHA-256:** `fce7228d802a6989deb7eb352423d91ce1f403dde844d8cb24f06d5b5459a89d` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 076 -->
# Single-PR staging register — VIIRS A02 and GHSL field audit

Date: 14 November 2026 (revised from 13 November). Target repository: `hoanfg/spatial-app`.

**Stage:** code review / preflight tooling only. **No pull request has been opened for this package.** Combine with other verified changes in one subsequent major-review PR. Do not merge or declare external validation complete on the strength of these synthetic tests alone.

## Deliverables (source only, no credentials or field data)

| File | Intended role |
|---|---|
| `audit_a02_six_bands.py` | Cross-check the six-band application VIIRS raster against independently exported masked annual median and count of valid monthly composites on exactly the same grid |
| `audit_ghsl_native_vs_reprojected.py` | Independently integrate GHSL per-pixel quantity by pixel-polygon area fraction, on native JRC projected grid and application EPSG:4326 GeoTIFF; quantify discrepancies |
| `test_validation_scripts.py` | Eleven tests of checkers, including synthetic positive/negative conditions and full-run comparison |
| `README.md` | Sources, command lines, scientific scope and known data dependencies |
| `pytest-results.xml` | Executed synthetic checker tests on this draft package |
| `SHA256SUMS.txt` | Byte-level integrity of deliverables (generated with the ZIP) |

## Changes since the initial two-test package

1. A02 now has explicit tests rejecting spatial grid mismatch and observed-vs-valid-month-count inconsistencies, as well as a deliberately corrupt observed flag.
2. GHSL now reports geometric coverage separately for native and app rasters, warns if one raster is incomplete, and returns non-zero from the CLI when any cell lacks comparable coverage. A missing-coverage synthetic test exercises the refusal.
3. GHSL per-cell sum is tested for partially clipped pixels (coverage-weighted quantity), not only whole pixels.
4. GHSL Spearman statistics now follow the **application's** analytical sample: core cells (area >= 99% of nominal cell) with finite raster values, and at least 30 qualifying cells; region-level quantity totals remain available for all comparable cells. The tool does not conflate a successful computation with scientific proof.
5. The full GHSL runner is exercised on a synthetic UTM/EPSG:4326 raster pair; it measures a known difference rather than marking it acceptable.

## Hard gates before a field-data PASS

- **A02:** supply a *true application-produced* six-band 2020 export, an independent masked-median GeoTIFF and valid-month count with exactly matching spatial grid, and compare each field. Require a region with *genuine* missing pixel observations before claiming a successful missingness stress test. A script that merely duplicates the production band formulas is not an independent end-to-end app validation.
- **GHSL:** supply one native JRC source tile and the *matching* application-exported GHSL GeoTIFF of the same kind, version, epoch and geographic extent, plus app cell CSV and GADM boundary. Check that the native source is really 100 m and the app image matches the product. Run both `kind=pop` and `kind=built` separately.
- **V11:** repeat real raster/CSV per-cell checks for Shanghai, Bao'an and Qimen; synthetic validation cannot close V11.
- **Cloud:** production performance requires an actual Cloud runtime measurement, not the green unit test suite.

## Decision and change policy

No modifications to app `ntl/`, APIs, missing-data policy, model formulas, source boundary files or GitHub workflows are proposed in this stage. If actual GHSL field comparisons establish a reproducible bias, capture exact input SHA-256, product epoch, resampling arguments and measured impact **before** opening a code-changing PR. Any scientific correction should be reviewed against historical Yanqing exports and existing regression tests.

The field data and user evidence archives should not be published or copied into the repository without separate approval. Store source GeoTIFFs externally and keep only compact execution summaries and hashes in the eventual major review.

## Review update 14 November 2026 — no new PR

- Hardened the GHSL check against **partial-coverage false positives**: eligible cells must have nearly 100% finite, unmasked raster area in BOTH native and app exports. Ineligible per-cell differences are NaN, not numerically compared.
- Added guard for GHSL native 100 m product resolution; a wrongly supplied 1 km raster fails preflight.
- Hardened A02 source independence: selecting ROI from the application's own band-1 mask could silently drop an app-side masked pixel. Reference valid-month count now defines the footprint, so this case fails.
- Negative controls expanded; `python -m pytest -q test_validation_scripts.py` now reports **11 passed**.
- All field validation gates remain unfulfilled without matching real-data rasters and application exports. Preserve project policy: **one future consolidated PR**, no branch/PR in this stage.

## 15 November 2026 — v4 single-PR carry-forward

1. Require **actual per-ID spatial identity** using UTM and WGS84 centroids, not only grid ID/area. The current production app already exports all required fields. Checker code and comparator are staged, not pushed to GitHub.
2. Reject non-integral valid-month counts in A02 references.
3. **11/11 isolated checker tests passed.** Deliberate same-area grid swaps and missing centroid columns are rejected.
4. Historical Yanqing 2020 GADM, real VIIRS raster and application CSV were checked with the amended comparator. Exactly **8,333/8,333** per-cell NTL references and centroid identity comparisons passed at exported rounding tolerances; detailed metrics JSON and source hashes are included, but private input raster/GeoJSON/CSV and the 8,333-row diagnostic table are *not* bundled.
5. No new branch, PR, production algorithm changes or geospatial data bundles. One consolidated PR remains the only proposed repository update.

<!-- END ORIGINAL SOURCE 076 -->


---

## Source 077: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/spatial_work/spatial_app_single_pr_staging_2026-11-15_v4.zip::README.md`

**Original bytes:** 9,716 · **SHA-256:** `a0b82b9fd376b4e8c3f96adfb7e8f7f7497e761a9f6dee2cf070c56371c284e9` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 077 -->
# Spatial App — External field validation tools (no repository changes)

Review date: **15 November 2026** (incremental v4 of 13–14 November staging). Scope: GHSL native-grid quantity conservation and VIIRS A02 six-band export consistency. This package contains **validation code and a small, reproducible Yanqing 2020 metrics JSON**, but no Earth Engine credentials, private input GeoTIFFs, original GADM boundaries, or large per-cell result tables. The scripts do not import the Spatial App production modules, call live APIs or alter scientific settings.

## Evidence distinction

- **Implemented, syntactically checked:** two independent command-line checkers.
- **Executed:** eleven synthetic automated tests passed (`python -m pytest -q test_validation_scripts.py`). A full synthetic GHSL runner and a negative-control reference-coverage check also executed; these are **not** field-validation evidence.
- **Not executed on real inputs:** GHSL original JRC GeoTIFF vs Earth Engine-downloaded GeoTIFF; A02 six-band real export vs independently exported masked median/month-count references. Those input combinations are not available in the current accessible files.
- **Not proven:** GHSL production bias magnitude, A02 performance on genuine missing observations, Shanghai/Bao'an/Qimen V11 completion, economic validity or Streamlit Cloud capacity.

## Tool A — GHSL native-grid versus application export

Use **the exact same GHSL product, release, epoch and band** in both rasters. For GHSL R2023A at 100 m, the official native equal-area product is World Mollweide (the raster's CRS metadata is authoritative). Verify that the app raster is an Earth Engine export using the application's existing `fetch_ghsl_raster()` path (EPSG:4326, requested scale 100 m, the first band). The app CSV must be a current Spatial App cell export containing `grid_id`, `area_km2`, `ntl_mean` and four rounded **per-ID centroids** (`centroid_lon`, `centroid_lat`, `centroid_x_epsgNNNN`, `centroid_y_epsgNNNN`) for the same GADM boundary and grid. Area and IDs alone are insufficient to detect identical-size cells reordered geographically.

```sh
python audit_ghsl_native_vs_reprojected.py \
  --boundary /path/to/CHN_Shanghai_Shanghai_District.geojson \
  --app-csv /path/to/shanghai_app_500m.csv \
  --native-ghsl /path/to/GHS_POP_E2020_original_Mollweide_100m.tif \
  --app-ghsl /path/to/shanghai_earth_engine_GHS_POP_E2020_epsg4326.tif \
  --kind pop \
  --out-csv /path/to/shanghai_ghsl_by_cell.csv \
  --out-json /path/to/shanghai_ghsl_audit.json
```

For built-up surface, use `--kind built` and the matching **total built-up surface** layer, not its non-residential band. The checker reconstructs clipped cells, verifies grid IDs/areas and source 100 m resolution, independently weights raster pixel *quantities* by native polygon overlap fractions and repeats this operation on the app raster, then reports regional totals, non-zero cell deviations, SHA-256 and Spearman (NTL versus proxy/area). Spearman uses only core cells (at least 99% of nominal cell area) with at least 30 comparable cells, matching the application; region totals use all comparable polygons. Each cell now reports native/app **valid-area fractions**, and a comparison is eligible only with at least 99.9999% valid area in both rasters. Merely intersecting a single valid pixel cannot justify full coverage. Missing or partial reference/application coverage is reported and causes a nonzero CLI exit code. Ineligible differences are blanked, while partial raw sums remain available only for diagnostics. A large difference may arise from reprojection, pixel alignment, masks, scale, product-version mismatch or coverage; investigate all of these before attributing the gap to an application bug.

**Do not** sum quantities directly using area-weighted `mean`; `exactextract` `sum` already uses pixel coverage fractions, while the preceding reprojection remains a different operation.

## Tool B — A02 six-band annual VIIRS consistency

Require **three GeoTIFFs on exactly the same raster grid**: (1) six-band Spatial App annual raster, (2) independent monthly-median reference exported *with NoData retained* (nodata must be correctly tagged, e.g. -9999), and (3) independent count of monthly valid observations (`cf_cvg > 0`), with the same year, region, imagery collection and pixel alignment. The existing `validation/cross_location/gee_viirs_2020.js` generates reference median and count rasters, but **does not itself generate the application's six-band product**.

```sh
python audit_a02_six_bands.py \
  --six-band /path/to/a02_app_six_band_2020.tif \
  --masked-median /path/to/shanghai_core_viirs_2020_masked_median.tif \
  --month-count /path/to/shanghai_core_valid_months_2020.tif \
  --out-json /path/to/shanghai_a02_field_audit.json
```

The checker strictly requires matching raster geometry and verifies six band descriptions, matching CRS/transform/dimensions and these pixel-level equations: radiance = masked median or 0; observation flag = valid median mask; negative flag = valid median < 0; observed-zero flag = valid median == 0; count = independently exported valid-month count; low-month flag = count < 3. It also records the number of observed zeros, truly missing pixels, negative medians and pixels with fewer than three valid months, so the reviewer can distinguish a meaningful missingness stress case from an all-observed Yanqing-style pilot. **It refuses to silently resample misaligned reference rasters. The **independent month-count** reference mask defines the comparison footprint; a missing/masked application pixel is flagged rather than excluded from validation. Extra app-only coverage outside the count reference also fails.**

A zero discrepancy in a region with no missing pixels checks the numerical identities but cannot validate behavior under genuine missingness.

## Source repositories / authoritative methods

- JRC GHSL downloadable datasets: https://human-settlement.emergency.copernicus.eu/download.php
- GHSL GHS-POP 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP
- GHSL GHS-BUILT-S 2023R: https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_BUILT_S
- Google Earth Engine resampling and aggregation: https://developers.google.com/earth-engine/guides/resample
- ExactExtract sum operation: https://isciences.github.io/exactextract/operations.html

## Validation gates

| Requirement | Field result in this package |
|---|---|
| Checker syntax and small fixed-oracle tests | **PASS** (11 tests) |
| A02 pixel-field comparison on a live six-band export | **NOT RUN — source unavailable** |
| A02 behavior in an actual missing-observation area | **NOT RUN — source unavailable** |
| GHSL native versus app reprojection for actual 2020 tiles | **NOT RUN — source unavailable** |
| GHSL population/built-up correlations after corrected aggregation | **NOT RUN — source unavailable** |
| V11 Shanghai/Bao'an/Qimen | **PENDING** |

**Data stewardship:** Store larger source GeoTIFFs and derived per-cell CSVs outside the source repository unless the owner explicitly approves publication; preserve original licenses and SHA-256 values. No new PR is needed for the current exploratory validation step.

## November 14 reviewer hardening

- GHSL now measures **fraction of each polygon covered by finite unmasked raster pixels**, not just the presence of any intersection. Only fully covered cells enter regional comparison totals and Spearman; partial diagnostics remain visible but never silently pass.
- Native GHSL must have projected 100 m resolution (within 1 m tolerance); the code still cannot independently prove the correct version/epoch/band without source metadata.
- A02 uses **independent reference count coverage** to choose pixels for validation. App-masked observations with valid reference count are checked as failures rather than skipped.
- Negative controls exercise one missing interior source pixel, invalid native product resolution, and an application-only missing A02 pixel. Eleven tests pass as of this staging version.

See `REVIEW_FINDINGS_2026-11-14.md` for the checker's identified failure modes and scientific boundaries.

## 15 November addendum — grid identity and negative controls

- **GHSL:** per-cell UTM centroids (application exports rounded to 0.1 m) and geographic centroids (six decimal places) must match the independently reconstructed grid at their respective rounding precision. Omitting these four columns is an error, not permission to skip the spatial-identity check.
- **Cross-location comparator:** the staged `compare_raster_cells.py` now applies the same per-ID geometry gate *before* calculating raster zonal statistics. It is intended to replace the existing script in the **single future consolidated PR**, not to create a micro-PR.
- **A02:** reject a valid-month raster with fractional counts, which can indicate an improperly resampled month-count reference. A count of months must be integral.
- **Real-data regression:** independent raster–polygon overlay was rerun on the historical Yanqing 2020 archive. **8,333/8,333** NTL cells met the CSV rounding tolerance (0.00005 nW/cm²/sr), and **8,333/8,333** UTM/WGS84 centroids met their recorded rounding tolerances. See `yanqing_2020_regression_metrics.json` and the recorded input SHA-256s. A controlled swap of the locations of two equal-area historical cells was rejected.
- **Limits:** this is a reproducibility check of the previously archived Yanqing data, **not** a newly acquired VIIRS/A02 six-band or JRC GHSL dataset. V11, GHSL live comparison and A02 real missingness remain PENDING.

<!-- END ORIGINAL SOURCE 077 -->


---

## Source 078: `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS/spatial_work/spatial_app_single_pr_staging_2026-11-15_v4.zip::REVIEW_FINDINGS_2026-11-15.md`

**Original bytes:** 4,122 · **SHA-256:** `0ce9c8d7b12bc8066a5b1899516f55587a7e0ec3c9772be84c2611f48b1e69dd` · **Origin:** embedded_in_original_zip

<!-- BEGIN ORIGINAL SOURCE 078 -->
# Spatial App — Independent checker follow-up (15 November 2026)

## Decision

Continue staging changes for one future major-review PR; no new PR and no changes to production formulas. An area-only comparator can fail to detect a spatial identity mismatch for equal-area cells. Fix the independent checking tools before interpreting later GHSL comparisons.

## Finding S04 — same-area ID swaps bypass the previous area gate

- Observed in: both the staged GHSL comparator and the existing `validation/cross_location/compare_raster_cells.py` checked grid IDs, polygon counts and areas, but not **per-ID geographic identity**.
- Why this matters: two full 500 m grid cells both have `area_km2 = 0.25`; their polygon-to-CSV pairing can be wrong while an area and ID validation still reports success.
- Remedy staged: check rounded UTM centroids (`centroid_x_epsgNNNN` and `centroid_y_epsgNNNN`, tolerance 0.051 m) and geographic centroids (`centroid_lon`, `centroid_lat`, tolerance 0.00000051°) against the independently recreated clipped GADM polygon for each `grid_id`.
- Negative control: interchange the exported centroid coordinates of two equal-area cells while leaving `grid_id` and `area_km2` untouched. Both staged comparators reject the mismatch. Missing centroid metadata also forces explicit failure.
- Production code and CSV schemas: **unchanged**; required centroid columns already exist in normal current application exports.

## Historical Yanqing field regression

A replay of the updated `compare_raster_cells.py` used:

- full-precision GADM 4.1 Yanqing GeoJSON from the historical private archive;
- the VIIRS 2020 annual reference GeoTIFF from the same archive;
- the **original** application 2020 500 m CSV with UTM/WGS84 centroids;
- 500 m clipped UTM grid, matching the existing baseline inference geometry.

Results: **8,333/8,333 cells** passed the raster–polygon NTL comparison within 0.00005 nW/cm²/sr (MAE 0.0000250230; maximum absolute error 0.0000499933). All **8,333/8,333 cells** also met the geographic centroid identity rounding tolerances. The maximum UTM-x and UTM-y rounding discrepancies were 0.049872 m and 0.049979 m; maximum longitude/latitude discrepancy was below 0.0000005°. The source and script checksums are retained in `yanqing_2020_regression_metrics.json` and `SHA256SUMS.txt`.

This is an **independent recomputation using archived field input** from Yanqing, not new field sampling. A controlled same-area swap of two historical full-size cells was correctly rejected by the new check. It does not establish V11 across contrasting locations or GHSL product equality.

## Finding S05 — fractional monthly observation counts

The staged A02 checker checked count in `[0,12]` but did not reject, for example, `2.5` months of annual valid observation support. Such a value can arise if a reference count raster is improperly interpolated. The checker now requires integral valid-month counts, and the corrupted synthetic example is rejected.

## Scope availability on archived VIIRS rasters

Historical annual medians and month-count reference rasters have 30,814 pixels per year (2014 and 2020). In both cases all count pixels recorded 12 valid months and no median pixels were masked. The 2014 raster contained one negative valid median; 2020 had none. Neither case contained measured-zero medians or fewer-than-three-month support. **These real images cannot test the A02 data-semantics edge cases involving genuine missing observations.**

## Acceptance log

- **11 passed** — `python -m pytest -q test_validation_scripts.py` (synthetic oracle and negative-control tests).
- **8,333 passed** — Yanqing 2020 archived field raster/polygon comparator and per-ID centroid verification.
- **Expected fail** — spatial-identity negative control on two same-area historical cell IDs.
- **Not run / PENDING** — GHSL native JRC 100 m versus real Earth Engine reprojected raster; A02 true six-band export; Shanghai/Bao'an/Qimen independent per-cell validation; Cloud benchmark.
- No new PR, no code modification in `ntl/`, and no large GeoJSON/GeoTIFF committed.

<!-- END ORIGINAL SOURCE 078 -->
