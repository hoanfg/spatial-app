# 🌐 Spatial econometrics Project - Phase 1

## 📌 Project overview
This project focuses on building spatial grid infrastructure, a core data preprocessing technique in spatial econometrics analysis.

Phase 1 plays the role of creating a geographically accurate skeletal framework, allowing irregular administrative regions to be converted into a regular square grid matrix. This sets the premise for integrating and analyzing economic data in Raster format (such as nighttime light intensity data) or Point format (such as FDI enterprise density, bank branches).

---

## 🛠 Technical specification
- **Programming language:** Python 3.x
- **UI Framework:** Streamlit, integrated with Session State to prevent the re-run phenomenon of static systems.
- **GIS Core:** 
  `GeoPandas` & `Shapely`: Vector geometry processing, spatial algebraic operations.
  `NumPy`: Coordinate matrix generation optimized for performance.
- **Visualisation:** `Folium`, `streamlit-folium` Multi-layer interactive map.
- **Boundary data source:** Using **static GADM v4.1 (Shapefiles)** data instead of real-time APIs (GADM, 2022).
  *Reason:* Thoroughly resolve the "array data conflict" problem in econometrics when administrative boundaries merge or split across years. Static data ensures the spatial timeline is fixed according to the study year.
  
---

## ⚙️ Algorithmic mechanism
The grid clipping algorithm is designed in a 5-step process to optimize memory:

1. **Coordinate reference system (CRS) standardisation:** Convert original boundaries from the spherical coordinate system `WGS84` (longitude/latitude) to the projected coordinate system `UTM EPSG:32648` (measured in meters) to ensure geometric calculations are not distorted by the Earth's curvature
2. **Bounding box initialisation:** Calculate extreme coordinates (`minx, miny, maxx, maxy`) encompassing the entire province/city
3. **Rough grid matrix generation:** Use `NumPy` to iterate through X and Y axes with the step size `cell_size` (1000m, 2000m...), creating polygons covering the bounding box
4. **Spatial clipping:** Use the `gpd.clip()` algorithm to trim the excess rough grid outside using the complex administrative boundary polygon
5. **Visual synchronisation:** Reset the coordinate system back to `WGS84` to render on the Leaflet/Folium web map platform

---

## ⚠️ The "border cell" problem
When forcing a square grid matrix (e.g., 1x1 km = 1 km²) onto a winding administrative boundary, the clipping algorithm will generate a series of **border cells** with distorted shapes and reduced areas (e.g., only $0.15 km^2$ or $0.8 km^2$) (Openshaw, 1983)

In econometrics, if we perform a total count of nighttime light data or population for all these grid cells, the border cells will have very low NTL values because they are too small (Henderson et al., 2012). The regression model will mistakenly understand that this border area is an "underdeveloped economic region", causing **heteroskedasticity** and severely distorting the bias of the entire model (Openshaw, 1983)

### 💡 Self-proposed econometric standardization solution
To solve the above problem, Phase 1 has proactively calculated and stored the actual area variable `(area_km2)` for each clipped grid cell. In Phase 2, the system will apply 2 strategies:
1. **Density-based standardization**: Instead of using $Total NTL$ as the dependent variable, the model will use $\frac{Total NTL}{area\_km2}$ (Economic intensity per actual 1 km²)
2. **Border noise filtering**: Completely remove border grid cells with an area ratio $< 10\%$ of the standard grid area (e.g., $< 0.1 km^2$ for a 1x1km grid) to eliminate outliers from the dataset

---

## 🚀 What is this spatial grid used for?
Although the current UI is merely "visualization", the **hidden data table** beneath the map serves as the infrastructure to perform **spatial join** operations. Specifically:

1. **Micro GDP interpolation**: Attach night-time light pixel data (SNPP-VIIRS) to the grid. Brighter grid cells reflect a higher concentration of economic activity, allowing GDP estimation down to the ward/commune level or individual neighborhoods (100 hectares) instead of being limited to crude provincial-level GDP figures (Elvidge et al., 2017)
2. **Spatial inequality assessment**: Count the number of Points of Interest (POIs) such as Bank branches, ATMs, or Schools falling into each grid cell. From there, run spatial weight regression models (GWR) to examine the level of financial/educational access
3. **Climate/Real estate risk analysis**: Attach elevation data (DEM) or flood risk maps to the grid to value the decline in real estate value in high-risk grid cells

---

## References
Elvidge, C. D., Baugh, K., Zhizhin, M., Hsu, F. C., & Ghosh, T. (2017). VIIRS night-time lights. International Journal of Remote Sensing, 38(21), 5860-5879.

GADM. (2022). GADM database of Global Administrative Areas, version 4.1. Truy cập tại: https://gadm.org/

Henderson, J. V., Storeygard, A., & Weil, D. N. (2012). Measuring Economic Growth from Outer Space. American Economic Review, 102(2), 994-1028.

Openshaw, S. (1983). The Modifiable Areal Unit Problem. Concepts and Techniques in Modern Geography, 38.
