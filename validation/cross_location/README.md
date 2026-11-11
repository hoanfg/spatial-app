# Cross-location Validation for VIIRS 2020

**Status:** Sample selected and tooling verified; NTL/LISA data for the three new locations is **not yet** available. Do not mark V11 as PASS prior to raster–CSV cross-checking.

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

In `spatial-app`, run **2020, 500 m grid, raw NTL, Queen, 999 permutations, seed 42, FDR 0.05**, then export CSV containing at least `grid_id, area_km2, ntl_mean`; export the full LISA CSV as well to enable p-value/quadrant cross-checking. Exporting the entire city or modifying the application's RAM protection mechanism is not required.

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

## 4. Evaluation criteria (pre-defined)

1. **Geometry:** cell count, `grid_id`, per-cell area match the app CSV within an area tolerance of $0.00005\text{ km}^2$.
2. **NTL:** all cells with sufficient raster coverage match within the CSV rounding margin of $\pm 0.00005\text{ nW/cm}^2\text{/sr}$; report all missing/fail cases without removing outlier cells.
3. **Missing data check:** compare annual median with masked median; analyze monthly `cf_cvg`, all negative values, and their impact on polygon zonal mean. Do not assume all pixels have 12 months as in Yanqing.
4. **LISA:** recalculate Queen adjacency, Local Moran, and p-value/FDR at 500 m using a dedicated validation script; fixed-seed randomization, explicitly state tie/tail counting method; report HH/LL labels and outliers.
5. **Generalizability:** mark V11 as complete only when results and attached evidence are available for all three locations; identical HH area share to Yanqing is not required, as structural differences across locations are expected.
6. **Archiving:** attach raster/CSV, test code, SHA-256 manifest, commit version, per-cell results, and reports; synchronously update both `docs/VALIDATION MASTER.md` and `docs/VALIDATION MASTER-vi.md` to reflect the new content accurately.

## 5. Execution status

- **Completed:** verified existence of three boundaries in GitHub, GID codes, bbox, approximate area; prepared Earth Engine script and Python comparator; comparator was run on Yanqing 2020, achieving **8,333/8,333** cells (max error ~0.00004999).
- **Pending:** export 2020 GeoTIFF for three regions, app CSV for three regions, per-cell raster validation and per-region LISA validation, independent GHSL comparison.
- **Decision:** keep V11 as `PENDING` until evidence is provided for all three locations.