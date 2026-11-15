# A02 multi-band zonal performance optimization — review record

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
