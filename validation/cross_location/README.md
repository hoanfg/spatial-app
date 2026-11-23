# Cross-location Validation for VIIRS 2020

**Status:** V11 validation is complete for all three locations. The recovered audit manifest inventories the application CSVs, matched rasters, edge-cell outputs and archived packages with hashes. The current checkout does not expand every binary input for a fresh rerun, which is a reproducibility-packaging limit rather than an unfinished validation.

The labels below are sampling hypotheses for deliberately different spatial contexts, not validated classifications of their economies. See the [scientific claim audit](../evidence/README.md#scientific-claim-audit) for the distinction between recorded aggregate evidence and independently reproducible field checks.

## 1. Three-case design

| Test role | Location per GADM 4.1 | GID_2 | Approximate area ($\text{km}^2$) | Minimum 500 m cells by area |
|---|---|---|---:|---:|
| Urban core | Shanghai / Urban Core Shanghai | `CHN.24.1.10_1` | ~197.7 | ~791 |
| Urban–industrial/peri-urban, multi-part geometry | Shenzhen / Bao'an District | `CHN.6.15.1_1` | ~1,655.5 | ~6,623 |
| Less-urbanized control | Anhui / Huangshan / Qimen County | `CHN.1.11.1_1` | ~2,206.9 | ~8,828 |

The areas above are **approximate planar projection estimates** derived from GitHub GeoJSON coordinates; they do not replace UTM area calculations and do not represent observed clipped cell counts. Zonal structure labels are sampling design hypotheses and have not been confirmed from VIIRS/GHSL data. Bao'an contains multi-part geometries, which are useful for testing boundary clipping.

Boundary GeoJSON files available in the repository:

- `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Shanghai/CHN_Shanghai_Shanghai_District.geojson`
- `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Guangdong_Shenzhen/CHN_Guangdong_Shenzhen_Bao'an_District.geojson`
- `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Anhui_Huangshan/CHN_Anhui_Huangshan_Qimen_District.geojson`

## 2. Required input data

Run `gee_viirs_2020.js` in the Google Earth Engine Code Editor, executing **9 Export tasks** (three products per location): annual reference median, count of months with `cf_cvg > 0`, and median retaining NoData.

In `spatial-app`, run **2020, 500 m grid, raw NTL, Queen, 999 permutations, seed 42, FDR 0.05**, then export CSV containing `grid_id`, `area_km2`, `ntl_mean`, `centroid_lon`, `centroid_lat`, and `centroid_x_epsg{E}` / `centroid_y_epsg{E}` for the selected UTM EPSG. Export the full LISA CSV for p-value/quadrant checks. Exporting an entire city or changing the RAM guard is unnecessary.

Earth Engine and app data must maintain independent zonal mean calculations. The same NOAA/VIIRS product may be used, but app cell extraction results must not be reused as the "reference".

## 3. Execution of raster–polygon validation

Requires Python with `geopandas`, `numpy`, `pandas`, `rasterio`, and `shapely`:

```bash
python validation/cross_location/compare_raster_cells.py \
  --boundary data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Shanghai/CHN_Shanghai_Shanghai_District.geojson \
  --raster shanghai_core_viirs_2020_reference.tif \
  --csv shanghai_core_app_2020_500m.csv \
  --out-csv shanghai_core_cell_comparison.csv \
  --out-json shanghai_core_metrics.json
```

Repeat for Bao'an and Qimen using the corresponding GeoJSON/GeoTIFF/CSV files.

## Why the V11 checks are designed this way

**Estimand:** for every exported app `grid_id`, independently compute `sum(pixel_value × overlap_area) / sum(overlap_area)` over its polygon, then compare `abs(NTL_ref - NTL_app)`. Using the same VIIRS product and year **isolates processing differences**, not sensor-level truth. Because polygons are exported by the app, this comparison does not independently verify the GADM-to-grid construction algorithm.

**Why three sites:** the selected areas deliberately differ in size, hypothesized urbanization and edge geometry. This is **purposeful technical-risk sampling**, not a random representative sample of Chinese districts.

**Why `0.00005` tolerance:** CSV `ntl_mean` retains four decimals; half a unit in its last retained place is `0.00005`. The auxiliary `0.0000501` threshold diagnoses floating-point boundary effects, not a newly relaxed scientific criterion. Retain **per-cell absolute differences**, pass rates, clipped cells, coverage gaps and maxima; correlation alone cannot establish agreement.

**Why LISA is checked separately:** correct NTL extraction does not prove correct adjacency, conditional randomization or BH-FDR. Implementation Local Moran uses standardized `z_i`, neighbor mean `lag(z)_i`, and `I_i = z_i × lag(z)_i / [sum(z²)/(m-1)]`. Conditional permutation holds each focal value fixed, samples distinct other cells **without replacement**, counts ties in both tails, and uses `(count+1)/(B+1)` correction. BH operates on the **actual tested family**. Different rounding and random sequences require reporting classification disagreements, not forcing exact agreement.

**Result boundary:** V11 supports raster-processing consistency under the specified data, geometries and tolerances at three locations. It does not validate the economic meaning of HH/LL, causal claims, or field null calibration of LISA p-values.

## 4. Evaluation criteria (pre-defined)

1. **Geometry:** cell count, `grid_id`, area and UTM/WGS84 centroid match the app CSV. Area tolerance is $0.00005\text{ km}^2$; centroid tolerances follow the CSV's 0.1 m and six-decimal-degree rounding. This rejects same-area ID/location swaps.
2. **NTL:** all cells with sufficient raster coverage match within the CSV rounding margin of $\pm 0.00005\text{ nW/cm}^2\text{/sr}$; report all missing/fail cases without removing outlier cells.
3. **Missing data check:** compare annual median with masked median; analyze monthly `cf_cvg`, all negative values, and their impact on polygon zonal mean. Do not assume all pixels have 12 months as in Yanqing.
4. **LISA:** recalculate Queen adjacency, Local Moran, and p-value/FDR at 500 m using a dedicated validation script; fixed-seed randomization, explicitly state tie/tail counting method; report HH/LL labels and outliers.
5. **Generalizability:** mark V11 as complete only when results and attached evidence are available for all three locations; identical HH area share to Yanqing is not required, as structural differences across locations are expected.
6. **Archiving:** attach raster/CSV, test code, SHA-256 manifest, commit version, per-cell results and reports; update both [validation guides](../README.md) and [the data/method guides](../../docs/README.md) accurately in both languages.

## 5. Current status

- **Completed result:** V11 validated Shanghai Core, Bao'an and Qimen with the rounding and seed qualifications listed in the [validation guide](../README.md).
- **Reproducible here:** the three boundary files, Earth Engine export script and independent Python comparator are deposited. The comparator rejects equal-area cell swaps by checking UTM and WGS84 centroids.
- **Archive provenance:** the recovered manifest names the matched application CSVs, Shanghai and Qimen source rasters, per-edge-cell tables and archived validation packages with recorded hashes. These inputs are not all expanded as direct checkout files; that does not reopen the completed V11 scientific result.
