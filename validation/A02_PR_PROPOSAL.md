# Preserve observational semantics alongside legacy NTL results (A02)

Missing observations, observed zero radiance and clipped negative annual medians can share `ntl_mean=0` under the current pipeline. Add per-cell observational fractions and monthly support metadata without changing legacy analysis values or statistical algorithms.

The change adds quality bands to annual raster downloads, retains their metadata in main/LISA exports, and includes both years in Space-Time CSVs. Regression tests cover mixed raster semantics and Space-Time UI/cache exports. CI discovers new test files automatically, preserving the A01 coverage fix from merged PR #19.

Validation: **66 local tests passed, no failures or skips** on Python 3.11 / Windows. JUnit results and reproducible synthetic sensitivity are recorded in `validation/evidence/a02/` and explained in `validation/DATA_SEMANTICS_A02.md`. Remote CI has not been run for this proposal. Synthetic missingness changes the measured indicators and classifications; it does not demonstrate an error in Yanqing's historical results.

Review as a draft until live Earth Engine multiband export, a real missingness case, and large-region resource checks are recorded. Additional CSV columns require review by consumers with strict schemas. Existing zero-fill policy remains in effect and is explicitly labeled in metadata.

Prepared with Codex assistance. Existing field rasters, independent comparison archives and historical validation results are attributed to their prior evidence records; this proposal does not claim their creation or independent authorship.

Review status: draft. Live Earth Engine and real-missingness acceptance remain pending; no automatic merge is authorized.
