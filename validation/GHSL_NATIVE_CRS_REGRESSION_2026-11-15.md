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
