# 2020 NTL cross-source comparison on exported 500 m app grids

**Status:** `descriptive_app_grid_evidence` : a deposited, bounded comparison, **not** a validation of economic activity, spatial FDR, missing-data zero handling, or all G01–G18 claims.

**Analysis date:** 2026-11-22. **Study areas:** Bao'an (Shenzhen), Qimen (Anhui), and the selected inner-Shanghai polygon. The inputs are three *same-run* pairs of Spatial App CSV and GeoJSON for year 2020 at 500 m. Exact exported GeoJSON polygons and their `grid_id` values are used; source-raster pixels and app cells are **not interchangeable**.

## Primary, same-app-grid findings

| Statistic | Bao'an | Qimen | Inner Shanghai |
|---|---:|---:|---:|
| Distinct app `grid_id` / valid polygons | 7,148 | 9,143 | 886 |
| App grid area, km² | 1,651.536 | 2,201.386 | 197.410 |
| Spearman(app NTL, reference monthly VIIRS) | 0.99999995 | 0.99999620 | 0.99999941 |
| Spearman(app NTL, EOG Annual V2.1 2020) | 0.9863 | 0.4532 | 0.9461 |
| Spearman(app NTL, OSM road length per km²) | 0.6963 | 0.2478 | 0.4208 |
| Spearman(app NTL, **summed** OSM building-footprint area / cell area) | 0.6166 | 0.0526 | 0.2687 |
| Spearman(app NTL, OSM point POI count) | 0.5150 | 0.0466 | 0.3253 |
| Spearman(app NTL, WSF 2019 native class `255` share) | 0.8345 | 0.2939 | -0.0009 |

Bao'an additional proxies: WorldCover 2020 native class `50` share, Spearman 0.8592; GHSL 2020 built_surface native-band mean, 0.8486. These are **different** urban proxies, not independent ground-truth economic outcomes. Neither the EOG product nor the monthly VIIRS product is fully independent of the other.

The main data table is [summary.csv](summary.csv). Earlier exploratory rounds first analyzed source raster pixels, then pixel-level OSM geometry; these are methodological baselines, **not separate independent field replications**. This folder records the third round on the application's actual exported `grid_id`.

## Why each proxy and statistic was chosen

This is a **measurement-convergence and spatial-sensitivity study** on the app's exported polygons, not a search for an economic ground truth. Every reported coefficient is tied to the same `grid_id` and **does not become an independent replication just because multiple products appear in a table**.

| Comparison | Operational calculation | Scientific rationale and interpretation ceiling |
| --- | --- | --- |
| App NTL versus independently processed monthly VIIRS | Recompute polygon-overlap radiance mean from the same monthly VCMSLCFG source and compare both **absolute per-cell error** and Spearman rho. | Primarily tests **processing and geospatial consistency**. Near-one rho is expected for shared source data and does **not** imply equal cell values or independent physical validation. |
| App NTL versus EOG Annual VIIRS | Area-overlap annual radiance from another annual product/workflow, then Spearman. | Tests **product/processing sensitivity**, not a totally independent sensor or automatic equivalence of zero/missingness rules. Qimen's much lower rho must be described, not averaged away. |
| OSM roads | Sum road **segment length inside each polygon** in a projected CRS; divide by cell area in km². | Road presence is an urbanization proxy; it does not measure travel time, network accessibility, road capacity or causal market access. |
| OSM buildings | Sum intersected footprint areas and divide by cell area, **without union/deduplication**. | Tests association with mapped structural footprints; overlapping features can overcount and the resulting fraction is not guaranteed to be at most one. |
| OSM POIs | Count mapped POI points intersecting each polygon. | Provides a separate mapped-activity proxy, strongly limited by completeness of OSM contributions; missing POIs do not prove missing activity. |
| WSF, WorldCover | Assign categorical **native-pixel center** values to app cells and count selected class shares. | Tests built-settlement/land-cover association without treating classes as jobs or causal outcomes. Edge fractions are approximate at pixel size. |
| GHSL built surface | Aggregate the specified **native-band** source values on app cells. | Compares another built-environment signal; its unit and aggregation must remain explicit and should not be mislabeled an economic outcome. |
| Spearman rho | Rank both cell series with tie handling and calculate Pearson correlation of ranks. | More robust to nonlinear monotone scales than raw-value Pearson; only states **rank association**, not calibration or independence. |
| 2 km spatial-block resampling | Group cells by `floor(UTM centroid coordinate / 2000)`, draw entire blocks with replacement **500 times** using seed `20261122`, recompute cellwise rho and report empirical 2.5/97.5 percentiles. | Samples geographic groups rather than pretending nearby cells are iid. Block size, origin, number of unique blocks and cross-block dependence remain unvalidated, so these are **sensitivity ranges, not calibrated 95% confidence intervals**. |

**What a result may say:** report sign/magnitude of a proxy association for the selected site-year, whether the ordering differs across products, source temporal mismatch (OSM 2026 versus NTL 2020, WSF 2019), and the observed sensitivity to block sampling. **What it may not say:** that NTL explains economic activity, that proxy disagreement establishes a data bug, or that these resampling ranges supply field-calibrated inference.

## Method and checking boundary

1. Three app CSV/GeoJSON pairs agree on `grid_id`, `ntl_mean`, and cell area to exported rounding precision; all **17,177** polygons are nonempty and valid.
2. OSM 2026 GeoPackages were clipped by QGIS before use. For roads, calculate the length of each way **intersected with the app polygon**, in projected metres (EPSG:32650 for Bao'an/Qimen; 32651 for Shanghai), divide by cell km². For buildings, sum intersected footprint area, divide by cell area. No automatic de-duplication or polygon union is implied.
3. POI points are assigned by intersection. Categorical WSF/WorldCover shares assign each *native source pixel center* to one app cell; edge fractions are approximate at source-pixel resolution. VIIRS and EOG source pixels are area-overlap averaged on the WGS84 raster lattice; weights in degree² are not geodesic surface areas. Avoid interpreting tiny border discrepancies as definitive pipeline errors.
4. The **union of app-grid polygons**, not an independently fetched GADM polygon, was used for the exact-geometry boundary QA. Small outside-grid residues remain: roads **30.084 m**, **0.0396 m**, **12.972 m**, respectively; buildings **108.398 m²**, **0 m²**, **92.059 m²**. Do not state outside-GADM error is zero. Some landuse polygons overlap, and summed landuse footprint area can exceed cell area.
5. Reference VIIRS vs app NTL is nearly rank-identical, **not numerically identical in every cell**. Across cells with reference data, the count within absolute difference <=0.00005 is 7,089/7,147 in Bao'an, 9,121/9,143 in Qimen, and 876/886 in Shanghai. Maximum absolute differences are 0.38175, 0.00287, and 0.37639. Border/mask, pixel weighting, and export-projection differences remain possible explanations, not verified causes.

## Spatial-block sensitivity (not formal inference)

Non-overlapping 2-km projected blocks were sampled with replacement 500 times, fixed seed 20261122; the statistic is the cell-level Spearman correlation of app NTL with each proxy. The numbers below are empirical 2.5%–97.5% *block-resampling ranges*, **not** calibrated confidence intervals, null p-values, causal effects, or G17 FDR guarantees.

| Site | Number of 2-km blocks | Road-density rho | Road range | Building-area rho | Building range |
|---|---:|---:|---:|---:|---:|
| Bao'an | 539 | 0.6963 | 0.6724–0.7151 | 0.6166 | 0.5834–0.6438 |
| Qimen | 630 | 0.2478 | 0.2054–0.2859 | 0.0526 | 0.0156–0.0783 |
| Shanghai | 74 | 0.4208 | 0.3114–0.5238 | 0.2687 | 0.1141–0.4035 |

One Qimen building bootstrap draw was undefined because the sampled blocks had constant building-area values; **499** of 500 replicates were finite. The 2-km fixed block origin and resampling choice are themselves sensitivities. Run [spatial_block_resampling.py](spatial_block_resampling.py) with the owner-held per-cell CSV and exact app GeoJSON to reproduce these resampling ranges.

## G10/G18 and claim boundaries

- In these app exports all 17,177 `dq_status` values are `observed` and `dq_observed_fraction=1`; **this does not mean 12 valid months**. Qimen has many cells with fewer valid months. G10's distinction between observation counts and monthly completeness remains essential.
- The absence of a demonstrated **fully unobserved** real cell prevents field closure of G18 missing-versus-zero behavior. EOG Annual filtered zero is **not** equivalent to VIIRS `cf_cvg=0` or a missing source pixel.
- OSM is a **2026** extract; NTL/GHSL/WorldCover/EOG are for **2020**, WSF for **2019**. OSM absence cannot mean activity absence, especially in sparsely mapped Qimen (7 OSM point POIs).
- No matched employment, market-access, causal intervention, independently surveyed CBD, or field-calibrated spatial null has been supplied. **G04, G05, G17, and G18 remain open**; G10 is supplemented descriptively, not independently field-closed. Existing validation register state remains authoritative.
- Three selected regions cannot establish generalizability to China as a whole. Spearman statistics have no iid p-values here because cell outcomes are spatially dependent.

## Evidence, provenance and reproduction

The full underlying source files and per-cell round-3 outputs remain owner-held; bulky OSM GeoPackages and GeoTIFFs are **not** duplicated in this evidence directory. [source_sha256.csv](source_sha256.csv) records exact SHA-256 fingerprints of the source snapshots, and [summary.csv](summary.csv) records the deposited compact statistics. Per-cell round-3 output filenames are `BAOAN_same_grid_cells_with_proxies.csv`, `QIMEN_same_grid_cells_with_proxies.csv`, and `SHANGHAI_same_grid_cells_with_proxies.csv` (17,177 rows in aggregate). The associated owner-held analysis bundle also contains `validate_app_grid.py`, `extra_proxies.py`, `check_boundary.py`, raw QA JSON, and its own output checksums. Since those source inputs and full computation scripts are not all checked into this repository, this folder is **provenance-traceable and partially independently reproducible**, rather than a self-contained end-to-end rerun.

To reproduce the resampling from the owner-held bundle, place its `spatial_app_grid_validation` directory under a data root with the three exported GeoJSON files in that root, and run:

```bash
python validation/evidence/ntl_appgrid_multisource_2020/spatial_block_resampling.py --root /path/to/data-root --reps 500 --seed 20261122 --block-m 2000
```

Required packages: geopandas, pandas, numpy, scipy, shapely and a GeoJSON-capable vector driver. No app implementation is imported by the resampling script. Do not update `validation/scientific_closure_register.json` statuses to `closed` on the strength of these associations alone.

