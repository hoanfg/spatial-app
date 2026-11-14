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
