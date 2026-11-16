# Editorial English reading edition

[English](CONSOLIDATED_FIELD_EVIDENCE_2026-11-en.md) | [Tiếng Việt](CONSOLIDATED_FIELD_EVIDENCE_2026-11-vi.md) | [Immutable historical evidence](CONSOLIDATED_FIELD_EVIDENCE_2026-11.md)

This edition normalizes punctuation and preserves the original report claims, data values, provenance, and time-specific qualifications. It is not a byte-identical forensic source; refer to the immutable original for SHA-256 and byte-offset verification.

---

# Recovery update: original inventory and 78 report bodies now supplied

This update supersedes the earlier missing-document inventory below. The user supplied the historical [JSON manifest](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_EVIDENCE_MANIFEST_2026-11-15.json), [archive verifier](audit-2026-11-15/recovered-originals/verify_spatial_app_audit_archive.py), [118-record CSV inventory](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_FILE_MANIFEST_2026-11-15.csv) and [all 78 complete Markdown reports](audit-2026-11-15/recovered-originals/SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md). All are preserved byte-for-byte; the previously generated reconstruction is not substituted for them.

The recovered JSON's whole-Markdown SHA-256 matches exactly. All 118 CSV records agree with JSON; every report body matches its recorded length/hash and corresponding direct-file or nested-member entry. The already published Bao'an CSV/profiler also match historical hashes. The archive verifier is syntax-checked only: its full run requires the original full ZIP and byte-range JSON, still unavailable. The recovered manifest indexes 271 nested files, but their bytes have not been recovered or checked here. No independent scientific computations were rerun.

The 78 reports now provide historical V11 edge-validation, Shanghai post-deployment GHSL and Bao'an A02 evidence, including qualifications. These are recovered original report statements, not fresh numerical recomputations or substitutes for missing per-cell results, rasters, plots and scripts. Full raw data publication and post-PR-27 Cloud benchmarking remain open.

The evidence README and next-performance baseline supplied by the user are embedded in full at the end of this document. Earlier contents and time-specific statements below are retained as history. Reproduce local checks using `node validation/audit_public_evidence.mjs --check-result`; see [recovery receipt](audit-2026-11-15/recovered-originals/recovery_receipt.json).

---

# Consolidated audit evidence: 15 November 2026

## Current evidence and limits

Repository baseline: `349612530fe118820831af610f67015636981bde` (main after merged PR #27). This revision publishes the two retrievable user attachments and reconciles historical reports. It does not certify the entire audit campaign.

- [Bao'an original cell CSV](audit-2026-11-15/baoan_ntl_2020_500m.csv): 7,148 rows, 2020, 500 m. [Original profiler JSON](audit-2026-11-15/spatial_app_performance.json). Byte counts and SHA-256: [manifest](audit-2026-11-15/manifest.json).
- [Recomputed public summary](audit-2026-11-15/verified_summary.json). Reproduce with `node validation/audit_public_evidence.mjs --check-result`. This checks all rows, schema, finite quality values, ranges, unique IDs and hashes. It does not recompute raster extraction or scientific indicators.
- Historical V11 aggregate evidence below reports 17,177 cells across Shanghai Core, Bao'an and Qimen. Per-cell comparator outputs, source raster pairs, LISA results and external-validation plots for these three locations are not present in the reviewed repository. V11 is therefore **aggregate evidence recorded / public reproduction incomplete**, not a fresh PASS.
- Bao'an metadata is directly inspectable in the attached CSV. The previous CSV is unavailable here: the chat's claim of unchanged NTL before/after cannot be reverified. This sample does not validate genuine missing-support cases.
- Profiler: 46.6687 s pipeline, 25.0028 s A02, 728.531 MiB sampled server-process RSS. Created 2026-11-15 12:48:20 UTC, before PR #27; no source commit is embedded. No post-optimization speedup is established. Stage sums include later LISA/GHSL operations and must not be equated with pipeline time.
- Chat reports GHSL working again at three locations, but the retrieved attachments contain no GHSL per-cell outputs, rho/AUC values or plots. Profiler stage success is operational evidence only, not independent GHSL numerical agreement.

## Missing owner-held package

The retrieved chat describes `SPATIAL_APP_FULL_AUDIT_EVIDENCE_2026-11-15.zip` (118 source files, 271 extracted historical members, 78 Markdown reports), `SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md`, CSV/JSON manifests, a byte-range index, `verify_spatial_app_audit_archive.py`, and `SPATIAL_APP_NEXT_PERFORMANCE_BASELINE_2026-11-15.md` under Library path `/Spatial-App/audit-evidence-2026-11-15/`. These are **chat-reported inventory, not files recovered or verified in this revision**. The local project sources directory is empty. The retrieved chat pages return no older cursor. No package checksum is invented and no unavailable file is linked as a repository artifact.

The current entry point is the [validation guide](../README.md). Original A02, A03, A03-B and coverage reports are preserved in the [indexed document archive](historical_document_sources_2026-11-15.md); the [Yanqing evidence](yanqing/README.md) and [cross-location tooling](../cross_location/README.md) remain available at their own paths. This recovered subset is distinct from the unavailable full package.

## Preserved historical reports

The four reports below are embedded as original bytes, without removing historical caveats or replacing their time-specific statuses. The original consolidated report is followed by three short reports now merged here. Their old paths and hashes at the baseline commit are recorded in [the byte-range index](audit-2026-11-15/consolidation_index.json). Read current evidence above before historical pending/merge instructions.


---

## Source: validation/CONSOLIDATED_FIELD_EVIDENCE_2026-11.md

# Consolidated independent field evidence: November 2026

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


---

## Source: validation/CLOUD_RUNTIME_LOG_REVIEW_2026-11-14.md

# Streamlit Cloud runtime log review: 14 November 2026

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


---

## Source: validation/GHSL_NATIVE_CRS_REGRESSION_2026-11-15.md

# GHSL external validation: native raster/vector CRS regression

Date: 2026-11-15. Scope: Shanghai 2020 GHSL built-up and population, not NTL/Moran/LISA.

## Observed in the deployed application
After native-grid conservation fixes, the External validation view reported
`Spearman rho = nan`, `AUC = nan`, 100% zero proxy cells, and no plot.
This is not a scientifically interpretable validation result.

## Root cause
The GHSL raster is correctly retained in the source ESRI:54009 Mollweide grid.
But `ntl/quality_ui.py` still passed a vector GeoDataFrame in EPSG:4326 to
`zonal_stat(..., "sum", fill_missing=0.0)`. `exactextract` does not reproject
geometries for mismatched CRS; it warns and extracts empty intersections.
Filling these empty results with zero fabricates a zero-variance proxy.

The independent Shanghai reference TIFF has raster bounds
`[11030200, 3780000, 11063300, 3800200]` in ESRI:54009; selected
WGS84 grid polygons occupy approximately longitude 121.x and latitude 31.x.
In their raw units they cannot intersect. Reprojection of the polygons to
ESRI:54009 puts them in the GHSL footprint.

## Fix and controls
- Reproject **vector polygons only** into the source raster CRS before calling
  `exact_extract`, retaining 100 m raster pixel values and alignment.
- Reject a missing CRS, entirely disjoint geometry, or an extraction with no
  observed pixel intersections rather than reporting fabricated zeros.
- Distinguish genuinely observed zero GHSL values from missing intersections.
- Do not cache a comparison with an all-zero core proxy as a successful
  `nan` Spearman/AUC result. Display explicit feedback.
- Add geospatial integration tests with a synthetic Mollweide raster and
  WGS84 polygon geometry, including true-zero and no-overlap cases.

## Limits
This repair has synthetic regression coverage. It does not yet prove
that Streamlit Cloud's current Earth Engine `computePixels` response is
nonzero, or that updated Spearman/AUC match a reference distribution.
A single post-deployment run must close that gate.

Source: https://isciences.github.io/exactextract/_modules/exactextract/exact_extract.html
Private user-provided GHSL reference rasters remain outside GitHub.


---

## Source: validation/A02_MULTIBAND_OPTIMIZATION_2026-11-15.md

# A02 multi-band zonal performance optimization: review record

Date: 2026-11-15. Scope: A02 observational quality extraction only.
No NTL, Global Moran, LISA, FDR, GHSL, or legacy-zero-fill estimator changes.

## Baseline (real Streamlit Cloud, Bao'an 2020, 500 m, 7,148 cells)
- Analysis pipeline wall time: **46.6687 seconds**.
- A02 five-band extraction: **25.0028 seconds** (53.6% of pipeline).
- Grid build: **9.7399 seconds**; NTL zonal mean: **9.6193 seconds**.
- Sampled process RSS peak: **728.531 MiB**.
- Source: private `BAOAN_A02_PERFORMANCE_POST_MERGE_AUDIT_2026-11-15.md`
  and `spatial_app_performance.json` archived in the owner's Library
  under `/Spatial-App/audit-evidence-2026-11-15/`.
- These are single-run measurements, not latency or memory guarantees.

## Previous bottleneck
`ntl/semantics.py::cell_quality` independently called
`ntl/zonal.py::zonal_stat` for each of quality bands 2–6.
Each call created a temporary one-band GeoTIFF and traversed the same
cell polygons with `exact_extract`.

## Proposed optimized path
- Read five quality bands once with Rasterio, preserving source masks and
  replacing nonfinite values with NaN exactly as in the old path.
- Write one five-band **in-memory** float32/nodata=NaN GeoTIFF.
- Invoke `exact_extract` once over five explicitly named RasterioRasterSource
  bands, with the **same area-fraction-weighted mean** statistic.
- Join all results to the original `grid_id` order; missing stays NaN.
- Preserve strict A02 schema validation and unknown fallback.
- Add automated old-vs-new numerical regression including partial polygons,
  masked/nonfinite pixels, out-of-raster polygons and reordered IDs.

## Acceptance gates
1. All existing repository tests and new equivalence tests PASS.
2. Benchmark synthetic data without speed assertions; retain timing as
   evidence, not a guarantee about the Cloud environment.
3. After deployment, compare every A02 quality value for the Bao'an
   2020/500m field case to the previous 7,148-cell CSV, within 1e-7 in
   raw computation (or CSV precision where that is all that is available).
4. Verify unchanged `ntl_mean`, counts, Moran/LISA, and that no unknown
   statuses appear spuriously.
5. Record end-to-end elapsed time and sampled process RSS from the same
   location and settings. Do not merge this PR as a proven speedup
   before a live benchmark.

## Provenance
Full owner-held audit pack: `/Spatial-App/audit-evidence-2026-11-15/`.
This PR deliberately excludes raw private imagery, large shapefiles, raw
Cloud logs and proprietary account information.


---

## Recovered source: SPATIAL_APP_AUDIT_EVIDENCE_README_2026-11-15.md

# Spatial App: full original audit evidence, 2026-11-15

This is a **private evidence archive**, assembled *before* any performance optimization PR.
No production files or GitHub branches were changed by assembling it.

## Coverage (physically preserved)

- **118 original physical files**, including all **30 files** currently present in the Library `/Spatial-App/major-review-staging/` snapshot.
- **23 original ZIPs** left intact, with **271 indexed AND separately expanded files** to make CSV/JSON/scripts accessible without double-unzipping.
- **16 direct CSVs** plus **28 CSVs referenced inside original ZIPs**.
- **5 direct JSONs** plus **49 JSONs referenced inside original ZIPs**.
- **3 direct GeoJSONs**, **14 direct GeoTIFFs**, and **10 screenshots**.
- **78 complete Markdown source documents/versions**, merged into `SPATIAL_APP_AUDIT_ALL_MARKDOWN_VERBATIM_2026-11-15.md` without shortening or dropping text. Every original remains in the archive.

## Where to find evidence

- `01_ORIGINAL_FIELD_INPUTS`: the original app CSV/GeoJSON (including Bao'an, Shanghai and Qimen) and older audit CSV inputs.
- `02_EARTH_ENGINE_AND_GHSL_RASTERS`: original NOAA VIIRS, A02 six-band and GHSL native/app-style GeoTIFF evidence.
- `03_CELL_AND_METRIC_RESULTS`: cellwise V11 edge comparisons, quantitative JSON, and performance measurement.
- `04_SCRIPTS_FOR_REPRODUCIBILITY`: independent verification scripts and Earth Engine export source.
- `05_NOTES_REPORTS_AND_HISTORY`: original standalone audit notes and text.
- `06_LIBRARY_STAGING_EXACT_ORIGINALS`: **exact copy of all Library staging files at packaging time**, including every original report, script and archive.
- `07_ARCHIVES_AND_PRIOR_SNAPSHOTS`: other original ZIP snapshots of Yanqing / China GADM / historical review evidence.
- `08_PRIVATE_RAW_LOGS_AND_SCREENSHOTS`: original Streamlit log and user screenshots; **do not publish indiscriminately**.
- `10_WORKING_HISTORY_AND_ADDITIONAL_INPUTS`: older audit workspaces and older dataset excerpts, preserved for traceability.
- `11_EXPANDED_ORIGINAL_ARCHIVE_CONTENTS`: unchanged byte-for-byte copies of ALL files inside the historical ZIPs; the original ZIPs are kept too.
- `00_INDEX`: self-contained audit file manifest, SHA-256 list, Markdown byte offsets, and immutable GitHub provenance.

## Markdown consolidation and 100% preservation

The consolidated Markdown is a **view** of the original texts, not a replacement for raw files.
Each original document is inserted with **all bytes unchanged**. Its start byte, length and SHA-256 are recorded in `00_INDEX/MARKDOWN_BYTE_RANGES.json`.
The assembly script verified each segment against its raw source; `verify_spatial_app_audit_archive.py` can verify all SHA-256 hashes and byte offsets again.
Distinct historical versions and duplicate reports were intentionally kept, not silently reconciled.

## Audit interpretation and remaining limits

- **V11**: 17,177 cells at the three new locations were compared against reference VIIRS; the single Bao'an cut-cell rounding boundary is recorded in its original evidence report. Detailed CSV and metrics are included.
- **A02**: the post-deployment Bao'an CSV reports valid observation metadata for 7,148 cells with NTL values retained; the original before/after files and report are included.
- **GHSL**: original Shanghai source-grid/app-grid raster exports and independent post-deployment Spearman/AUC metrics are included; screenshots for Shanghai, Qimen, and Bao'an are preserved. The later four screenshots are observed UI results, not independent per-cell reconstructions for Qimen/Bao'an.
- **Performance**: the actual Streamlit Cloud recorder JSON is included, including stage times and sampled process RAM. It is not a Cloud capacity stress test.
- **Incomplete external scope**: not every file in the production repo is duplicated here. `GITHUB_CANONICAL_PROVENANCE.json` links immutable validation docs from the exact latest audited commit.

## Important scientific and publishing safeguards

Do not upload this **full private ZIP** as a GitHub commit. Large GeoJSON, raster TIFFs, raw Cloud log and screenshots should remain out of a public source repository unless deliberately reviewed.
For a future PR, use the consolidated report, small metric JSONs, selected cellwise CSV evidence and reproducibility scripts as appropriate. The PR should reference checksums for any large private raw inputs.
No files have been deleted or abbreviated in this archive; historical contradictions, when present, remain visible as originally written.


---

## Recovered source: SPATIAL_APP_NEXT_PERFORMANCE_BASELINE_2026-11-15.md

# Spatial App: next performance baseline after A02 PR #27

Date: 2026-11-15. Review-only record. No second PR, production change, or merge.

## PR #27 status

- URL: https://github.com/hoanfg/spatial-app/pull/27
- Head commit at review: `58f38fd381ffa005a31832e0d3fdd5841d5882c0`
- State: draft, unmerged at time checked.
- Both `push` and `pull_request` CI workflows passed (core + full AppTest including five-band A02 regression).
- New A02 extracts five quality bands in one `exact_extract` call. Legacy field CSV preservation and live Streamlit Cloud performance remain **unconfirmed** until deployed/benchmarked. Private audit archive: `/Spatial-App/audit-evidence-2026-11-15/`.

## Existing real Cloud baseline (Bao'an, 2020, 500 m, 7,148 cells)

From owner-provided profiler JSON before this optimization:

- `pipeline_wall_time_s`: 46.6687 s
- `a02.cell_quality`: 25.0028 s
- `grid.build`: 9.7399 s
- `ntl.zonal_mean`: 9.6193 s
- Peak sampled process RSS: 728.531 MiB

No post-optimization Cloud benchmark yet.

## Next priority: grid build, investigation only

Source: current repository `app.py::build_grid`. Workflow:
1. Make regular 500 m candidate polygons over enlarged bounding box.
2. Use `gpd.clip(..., keep_geom_type=True)` against the district boundary.
3. Drop empties/nonpositive area, assign `grid_id` in resulting output order.

Local exploratory measurement on **reconstructed** Bao'an geometry (union of 7,148 user-provided output GeoJSON cells, reprojected to EPSG:32650; not original GADM boundary):

- `gpd.read_file` 7,148 rows: 0.586 s.
- Conversion to UTM: 0.028 s.
- Shapely union to approximate district geometry: 0.272 s.
- Regular rectangular candidates: 20,116 cells.
- `gpd.clip` stage: 3.491 s; resulting 7,148 cells.

**Limitations:** Local runtime differs from Streamlit Cloud hardware and versions. The boundary is reconstructed from output cells, not the original source GADM polygon. This is a preliminary bottleneck localization, not a valid old-vs-new speedup benchmark and cannot be compared directly to the 9.7399 s Cloud `grid.build` wall time.

## Safety and correctness gate for grid performance work

- Preserve grid geometry, `grid_id`, ordering, `area_km2` and is-border-cell status exactly, including clipped and multipart boundary cases.
- Compare candidate algorithms on an identical original district GADM boundary and 500 m cell size; evaluate geometry equality/area tolerance and permutation-invariant properties.
- Compare memory use and full-grid correctness, not just wall-clock time.
- Do not optimize `ntl.zonal_mean` in the same PR as grid. The owner prefers small bounded scopes and one reviewable PR at a time.

## Next steps

1. Review/merge PR #27 only after the approval gates are met; CI is currently green but actual Cloud speed gain is not yet evidenced.
2. One post-deploy Bao'an 2020/500m performance JSON and field CSV will measure A02 runtime and establish numerical consistency against the existing baseline.
3. Investigate grid build as a *subsequent, separate* optimization only if the A02 improvement is verified.
