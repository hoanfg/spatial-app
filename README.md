# 🌐 Spatial econometrics Project

[ 🇬🇧 English ](README.md) | [ 🇻🇳 Tiếng Việt ](README-vi.md)

## 📌 Project overview
This project is an end-to-end **Spatial grid infrastructure and nighttime lights (NTL) extraction pipeline**, serving as a core data engineering tool for spatial econometrics.

The application resolves the complex task of standardizing irregular administrative boundaries into uniform spatial matrices, directly interfaces with Google Earth Engine (GEE) to extract real-world raster data (SNPP-VIIRS), and computes rigorous micro-level spatial statistics (LISA) for macro-economic panel regressions.

---

## 🛠 Technical specification
- **Language:** Python 3.x
  
- **UI & Deployment:** Streamlit (with Session State management to prevent static system reruns)
  
- **Geospatial engine:** 
  - `GeoPandas` & `Shapely`: Vector geometry processing, spatial algebraic operations
  - `NumPy`: Coordinate matrix generation optimized for performance
  - `rasterio`, `exactextract`: Raster sub-pixel processing (for local GeoTIFF fallback)
  
- **Cloud computing:** `earthengine-api` (Google Earth Engine) authenticated via GCP service accounts and Streamlit secrets
  
- **Visualization:** `Folium`, `Altair` (Dynamic multi-layer interactive maps)
  
- **Boundary data source:** Utilizing static GADM v4.1 (Shapefiles) instead of real-time APIs (GADM, 2022)
  
  - *Reason: Thoroughly resolve the "array data conflict" problem in econometrics when administrative boundaries merge or split across years. Static data ensures the spatial timeline is fixed according to the study year*

---

## ⚙️ Core pipeline capabilities

The system operates on a optimized, memory-safe 4-step pipeline:

1. Converts original boundaries from the spherical coordinate system `WGS84` (longitude/latitude) to the projected coordinate system `UTM EPSG:32648` (measured in meters) to ensure geometric calculations are not distorted by the Earth's curvature. Generates a strict square grid (e.g., 500m, 1000m) and uses gpd.clip() to trim excesses.
  
2. Bypasses GEE's extraction limits by downloading the raw VIIRS GeoTIFF composite directly to the local server, ensuring maximum native resolution (~463m)

3. Utilizes the C++ `exactextract` engine to calculate area-weighted NTL means based on fractional pixel coverage, reduce to minimum the inaccuracies of traditional centroid-based methods

4. Runs the local indicators of spatial association (Local Moran's I) algorithm to detect economic hotspots (High-High clusters), exporting macro-variables like spatial lag, distance to CBD, and light Gini coefficients directly to a panel CSV

---

## ⚠️ Methodological rigor & solved problems

**1. The "border cell" & MAUP problem:**
When forcing a square grid matrix (e.g., 1x1 km = 1 km²) onto a winding administrative boundary, the clipping algorithm will generate a series of **border cells** with distorted shapes and reduced areas (e.g., only $0.15 km^2$ or $0.8 km^2$) (Openshaw, 1983)

In econometrics, if we perform a total count of nighttime light data or population for all these grid cells, the border cells will have very low NTL values because they are too small (Henderson et al., 2012). The regression model will mistakenly understand that this border area is an "underdeveloped economic region", causing **heteroskedasticity** and severely distorting the bias of the entire model (Openshaw, 1983)

The pipeline strictly uses Listwise Deletion in its spatial graph generation. Edge-masked cells and unlit cells (zero-inflated noise) are completely removed from the spatial weights matrix (W) to prevent biased Local Moran's I calculations

**2. The Multiple Testing Problem in Spatial Clusters:**

Testing thousands of grid cells simultaneously for spatial clustering inevitably generates false positives (random chance clusters).

The LISA engine enforces the Benjamini-Hochberg False Discovery Rate (FDR) correction on conditional permutation p-values (Caldas de Castro & Singer, 2006). This guarantees that identified High-High bubbles are statistically robust.

**3. Panel regression bridge (macro from micro):**

Instead of raw grids, the tool outputs robust control variables for econometric models:

`hh_area_share`: Replaces crude national housing prices by measuring the physical spatial expansion of economic bubbles.

`ntl_raw_lag`: Captures spatial spillover effects without needing complex post-regression spatial matrices.

`dist_to_core_km`: Controls for distance decay to validate whether credit growth in peripheries is speculative.

---

## 🚀 What is this spatial grid used for?

Although the UI provides visualization, the **hidden data table** beneath the map serves as the infrastructure to perform **spatial join** operations. Specifically:

1. Attach night-time light pixel data (SNPP-VIIRS) to the grid. Brighter grid cells reflect a higher concentration of economic activity, allowing GDP estimation down to the ward/commune level or individual neighborhoods (100 hectares) instead of being limited to crude provincial-level GDP figures (Elvidge et al., 2017)
 
2. Count the number of Points of Interest (POIs) such as Bank branches, ATMs, or Schools falling into each grid cell. From there, run spatial weight regression models (GWR) to examine the level of financial/educational access

3. Attach elevation data (DEM) or flood risk maps to the grid to value the decline in real estate value in high-risk grid cells

---

## 📚 References

Anselin, L. (1995). Local Indicators of Spatial Association—LISA. Geographical Analysis, 27(2), 93-115. DOI: 10.1111/j.1538-4632.1995.tb00338.x

Caldas de Castro, M., & Singer, B. H. (2006). Controlling the false discovery rate: A new application to account for multiple and dependent tests in local statistics of spatial association. Geographical Analysis, 38(2), 180-208. DOI: 10.1111/j.0016-7363.2006.00682.x

Elvidge, C. D., Baugh, K., Zhizhin, M., Hsu, F. C., & Ghosh, T. (2017). VIIRS night-time lights. International Journal of Remote Sensing, 38(21), 5860-5879. DOI: 10.1080/01431161.2017.1342050

GADM. (2022). GADM database of Global Administrative Areas, version 4.1. Truy cập tại: https://gadm.org/

Henderson, J. V., Storeygard, A., & Weil, D. N. (2012). Measuring Economic Growth from Outer Space. American Economic Review, 102(2), 994-1028. DOI: 10.1257/aer.102.2.994

Openshaw, S. (1984). The Modifiable Areal Unit Problem. Concepts and Techniques in Modern Geography (CATMOG), 38. https://www.spatial-literacy.org/qmrg/catmog/catmog_38.pdf

