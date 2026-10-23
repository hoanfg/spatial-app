# TECHNICAL MANUAL AND METHODOLOGICAL FRAMEWORK

**Nighttime lights (NTL) data extractor & Spatial econometrics engine**

[ 🇬🇧 English ](README.md) | [ 🇻🇳 Tiếng Việt ](README-vi.md)

--------------------------------------------------

> **TL;DR (THE 30-SECOND SUMMARY)**
> 
> Don't have the bandwidth to read a 10-page academic manual? Here is the absolute core of what this engine does:
> 
> * Using satellite Nighttime Lights (NTL) as a proxy for GDP is a standard trick in economics. **BUT** the data is massive. Processing it usually crashes standard computers (RAM Out-Of-Memory) and takes weeks to do manually.
> * **What this app does:** Pick a region $\rightarrow$ The app auto-fetches *Google Earth Engine* data $\rightarrow$ Uses a C/C++ backend to crush millions of pixels into grids $\rightarrow$ **Bypasses the strict 1GB RAM cloud server limit without crashing.**
> * 1-click generates a perfectly clean CSV with ready-to-use economic indicators: Where is the true urban core? Where are the economic hotspots (LISA)? What is the inequality Gini? Just download it and plug it straight into your regression models.

--------------------------------------------------

This project is a system designed for **spatial econometrics**, combining a spatial grid infrastructure with a nighttime lights (NTL) data extraction pipeline.

The application addresses the workflow from standardizing irregular administrative boundaries into uniform square grids, connecting directly to Google Earth Engine (GEE) to retrieve raster data (SNPP-VIIRS), to automatically computing micro-level spatial statistics (LISA) and exporting panel datasets for macroeconomic modeling.

---

## CHAPTER 1: SYSTEM ARCHITECTURE OVERVIEW AND RESOURCE MANAGEMENT

The system is designed not merely as a remote sensing data extractor, but as a web-based spatial processing engine that directly connects geographic preprocessing (GIS) workflows with spatial econometric models.

### 1.1. Four-tier architecture

To handle the complexity of combining vector data (administrative boundaries), raster data (VIIRS satellite imagery), and spatial inferential statistics, the system decomposes the workflow into 4 independent tiers:

* **Tier 1:** 
  This tier is responsible for recursively scanning the local GADM directory structure. Using pattern recognition, Unicode normalization (NFC/NFD), and the `pycountry` library, the system automatically infers ISO3 identifiers, standardizes administrative names, and loads them into the user interface (UI) without relying on a static database.

* **Tier 2:** 
  Responsible for polygon geometry processing. This tier projects all vector data into a dynamic flat UTM (Universal Transverse Mercator) coordinate system based on the centroid longitude and latitude of the bounding box, and then constructs a regular spatial grid via vectorization using `numpy.meshgrid` and `shapely.box`.
  
* **Tier 3:** 
  The server sends a spatial query to the Google Earth Engine (GEE) API to filter clouds, compute the annual median composite, and clip the raster image to the analysis boundary. The GeoTIFF byte stream is loaded into temporary memory for the **C/C++ engine** (`exactextract`) to compute area-weighted fractional zonal statistics between the vector grid and the raster.

* **Tier 4:** 
  Executes the spatial econometrics core (Global Moran's I, Local Moran's I / LISA, connected hotspot cluster detection, distance to the economic core, Gini inequality coefficient) and renders the multi-layer interactive map (Folium/Leaflet). Output data are packaged via the data bridge as cell-level and region–year panel CSV files.

### 1.2. Hardware constraints and out-of-memory (OOM) safeguards on Cloud

The target deployment environment of the system is Streamlit Community Cloud (or low-cost docker containers), where resources are strictly constrained to **~1GB RAM** and **1 CPU Core**.

Spatial geometry processing has a memory footprint that grows rapidly with grid resolution. When executing `geopandas.clip()` on a 500m grid for an administrative unit covering $30,000 \, \mathrm{km}^2$, the number of generated polygons can exceed $150,000$. Holding the topology of this many polygons simultaneously in RAM triggers the Linux OOM Killer and crashes the server process.

**Memory safeguards:**

1. **In-memory zip streaming & ephemeral cleanup:** Raster imagery from GEE is downloaded as a compressed byte stream, extracted directly in RAM, and written to a temporary file (`tempfile`). As soon as `exactextract` finishes reading the raster inside the `try...finally` block, the temporary file is forcibly removed from disk to release resources immediately.

2. **Pre-computation grid size fuse:** Estimates the number of grid cells from boundary area and perimeter prior to geometry instantiation to block queries that exceed the memory cap (described in detail in Section 4.1).

3. **FIFO session cache:** The LISA computation cache (`_lisa_cache`) is capped at the 5 most recent parameter configurations using a first-in, first-out (FIFO) policy, ensuring instant switching across parameter sets without causing memory leaks.

### 1.3. Stateless mechanism of web browsers

Streamlit operates on a **stateless** execution model: every user interaction with any UI control forces Python to re-execute the script from top to bottom. The system maintains statefulness through two mechanisms:

1. **Memoization (`@st.cache_data`, `@st.cache_resource`):** GEE authentication initialization, GADM directory scanning, boundary geometry statistics, and satellite raster downloads are hashed by their input parameters for instant reuse from cache.

2. **Session state injection:** The heavy extraction workflow is isolated inside `run_pipeline()` and stored in `st.session_state["result"]`. Subsequent adjustments to colormaps, scaling modes, or map filters read directly from `st.session_state`, decoupling the presentation layer (UI) from the computation backend.

---

## CHAPTER 2: SPATIAL GEOPROCESSING METHODOLOGY

### 2.1. Addressing the modifiable areal unit problem (MAUP)

In empirical spatial economics, using administrative boundaries (provinces, districts, communes) directly introduces statistical bias due to large variations in area and geometric shape, known as the **modifiable areal unit problem (MAUP)** (Openshaw, 1984; Fotheringham & Wong, 1991). The system resolves this problem by standardizing the study area into a uniform square grid matrix (Donaldson & Storeygard, 2016).

**Dynamic coordinate projection algorithm:**

Instead of relying on a hardcoded local EPSG code as in the Phase 1 prototype (`EPSG:32648`), the system dynamically interpolates the optimal **UTM (Universal Transverse Mercator)** zone from the centroid longitude and latitude $(\lambda_{\mathrm{center}}, \phi_{\mathrm{center}})$ of the study area's bounding box:

$$
\mathrm{Zone} = \min\left(60, \, \max\left(1, \, \left\lfloor \frac{\lambda_{\mathrm{center}} + 180}{6} \right\rfloor + 1\right)\right)
$$

The standard EPSG coordinate reference code (in meters) is assigned automatically for both the Northern and Southern hemispheres:

$$
\mathrm{EPSG} = \begin{cases} 32600 + \mathrm{Zone} & \text{if } \phi_{\mathrm{center}} \ge 0 \text{ (Northern hemisphere)} \\ 32700 + \mathrm{Zone} & \text{if } \phi_{\mathrm{center}} < 0 \text{ (Southern hemisphere)} \end{cases}
$$

All grid origin coordinates $(x_0, y_0)$ are snapped to integer multiples of the cell side length $\mathrm{size}$ in flat UTM space, ensuring that grids of adjacent districts align seamlessly when merged.

### 2.2. Cloud masking on GEE and zonal statistics extraction via fractional coverage

The system retrieves monthly composites from the `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` satellite dataset (native resolution $\approx 15\text{ arc-seconds} \approx 463.83\text{ m}$ at the equator). In monsoon tropical regions, heavy cloud cover during rainy months can leave pixels with zero valid observations (`cf_cvg` $= 0$), producing artificial zero radiance values. To eliminate this downward bias, the system applies a cloud-free mask `cf_cvg` $> 0$ to each monthly image prior to computing the **annual median composite** (Elvidge et al., 2017, 2021).

Next, rather than using traditional center-of-pixel raster stats that introduce substantial error when grid cell size approaches the native VIIRS pixel size, the system integrates the C/C++ library `exactextract` (Baston, 2023). The mean radiance $\mathrm{NTL}_i$ of grid cell $i$ is computed as the weighted average weighted by the fractional pixel area $w_{ip} \in [0, 1]$ falling inside polygon cell $i$:

$$
\mathrm{NTL}_i = \frac{\sum_{p \in i} x_p \cdot w_{ip}}{\sum_{p \in i} w_{ip}}
$$

Missing or negative values arising from sensor stray-light correction are clamped to $0.0$. The sum of lights (SOL) of each cell is computed as the product of mean radiance and true clipped area: $\mathrm{SOL}_i = \mathrm{NTL}_i \times A_i$.

---

## CHAPTER 3: SPATIAL ECONOMETRICS CORE (LISA CORE ALGORITHM)

The `lisa_core.py` module is built entirely with array algebra on `numpy` and `pandas`, removing dependencies on heavy GIS packages such as `libpysal` or `esda` while reducing contiguity graph construction complexity to $\mathcal{O}(N \log N)$.

### 3.1. Handling zero-inflated data and border cells

Natural nighttime radiance data typically contain a high proportion of zeros (forests, water bodies, agricultural land) as well as sliver polygons clipped along administrative boundaries. The system addresses both issues through a 3-step procedure:

1. **Border cell masking:** A grid cell $i$ is flagged as a border cell (`is_border_cell = 1` and `is_edge_masked = 1`) and excluded from the contiguity graph if its true clipped area $A_i$ is less than $99\%$ of a full standard cell area:

$$
A_i < 0.99 \times \left(\frac{\mathrm{size}}{1000}\right)^2 \quad (\mathrm{km}^2)
$$

2. **Z-score standardization on the core reference set ($S$):** Let $S$ denote the set of core cells (non-border cells with $A_i \ge 0.99 \times (\mathrm{size}/1000)^2$) eligible for testing. In the default mode (`include_zeros = False`), $S$ consists of core cells with radiance above the threshold ($\mathrm{NTL}_i > \mathrm{threshold}$). In the extended mode (`include_zeros = True`), $S$ includes all core cells. The standardized score $z_i$ is computed using the Bessel-corrected sample standard deviation ($\mathrm{ddof} = 1$):

$$
\mu_S = \frac{1}{\lvert S \rvert} \sum_{i \in S} v_i, \quad \sigma_S = \sqrt{\frac{1}{\lvert S \rvert - 1} \sum_{i \in S} (v_i - \mu_S)^2}, \quad z_i = \frac{v_i - \mu_S}{\sigma_S} \quad \forall i \in S
$$

where $v_i = \ln(\mathrm{NTL}_i)$ (or $\ln(1 + \mathrm{NTL}_i)$ when zeros are included) if log transformation is enabled to compress the right-skewed tail, and $v_i = \mathrm{NTL}_i$ on the raw radiance scale.

3. **Methodological implications of the lit-only testing mode (`lit_only`):** When unlit cells ($\mathrm{NTL}_i \le \mathrm{threshold}$, labeled `DARK`) are excluded from the spatial weight matrix $W$, the mean $\mu_S$ represents the **internal average brightness of illuminated areas**. Consequently:

   * **High-High (HH)** clusters capture contiguous urban and commercial cores with exceptionally high radiance.

   * **Low-Low (LL)** clusters capture contiguous areas of low-intensity illumination (below the lit-area mean, such as peri-urban fringes or sparse settlements), while completely unlit areas are separated into the `DARK` state.

   * **High-Low (HL)** and **Low-High (LH)** classes capture spatial outliers within the illuminated urban structure.

### 3.2. Queen contiguity graph

The spatial weight matrix $W$ is constructed using Queen contiguity (8 surrounding directions: 4 edges and 4 corners) on the regular grid for cells in $S$. From centroid coordinates $(c_{x,i}, c_{y,i})$ in UTM meters, the algorithm maps each cell to integer grid indices $(ix_i, iy_i)$ and computes a unique 1D hash key:

$$
ix_i = \left\lfloor \frac{c_{x,i} + \epsilon}{\mathrm{size}} \right\rfloor, \quad iy_i = \left\lfloor \frac{c_{y,i} + \epsilon}{\mathrm{size}} \right\rfloor, \quad \mathrm{Key}_i = ix_i \cdot H + iy_i
$$

(where $\epsilon = 10^{-6}\text{ m}$ compensates for IEEE-754 floating-point rounding near cell boundaries and $H = \max(iy) - \min(iy) + 4$). Vectorized binary search via `numpy.searchsorted` on the sorted key array identifies all 8 neighbors $(dx, dy) \in \{-1, 0, 1\}^2 \setminus \{(0,0)\}$. Spatial weights $w_{ij}$ are row-standardized:

$$
w_{ij} = \begin{cases} \frac{1}{k_i} & \text{if } j \in N(i) \cap S \\ 0 & \text{otherwise} \end{cases}
$$

where $k_i = \lvert N(i) \cap S \rvert$ is the number of valid neighbors of cell $i$. Only cells $i \in S$ with $k_i \ge k_{\min}$ (default $k_{\min} = 1$) enter the tested set $\mathrm{Focal}$.

### 3.3. Local Moran's I (LISA) test and conditional permutation

The Local Moran's I statistic (Anselin, 1995) and standardized spatial lag ($\mathrm{Spatial\ Lag}\ z$) for each cell $i \in \mathrm{Focal}$ are defined as:

$$
I_i = \frac{z_i}{m_2} \sum_{j \in N(i) \cap S} w_{ij} z_j, \quad \mathrm{Lag}(z_i) = \sum_{j \in N(i) \cap S} w_{ij} z_j, \quad m_2 = \frac{1}{\lvert S \rvert} \sum_{r \in S} z_r^2
$$

**Vectorized conditional permutation:**

Because nighttime light radiance does not follow a normal distribution, the statistical significance of $I_i$ is evaluated via Monte Carlo simulation using $R$ conditional permutations (default $R = 499$, up to $R = 999$). In each permutation $r \in \{1, \dots, R\}$, the focal value $z_i$ is held fixed while $k_i$ neighbor values are drawn at random using `rng.integers` from the pool $S \setminus \{i\}$ to form the simulated statistic $I_i^{(r)}$.

Let $M_i$ denote the number of simulations falling into the nearer extreme tail (accounting for numerical ties within $10^{-12}$):

$$
M_i = \min\left( \sum_{r=1}^R \mathbb{I}\left(I_i^{(r)} \ge I_i - 10^{-12}\right), \; \sum_{r=1}^R \mathbb{I}\left(I_i^{(r)} \le I_i + 10^{-12}\right) \right)
$$

The two-sided pseudo p-value follows the convention of Anselin (1995) and Rey & Anselin (2007):

$$
p_i = \min\left(1.0, \; 2 \times \frac{M_i + 1}{R + 1}\right)
$$

### 3.4. Controlling the false discovery rate (FDR – Benjamini-Hochberg)

When testing $m = \lvert \mathrm{Focal} \rvert$ grid cells simultaneously (often tens of thousands of cells at 500m resolution), applying an unadjusted threshold $\alpha = 0.05$ inflates Type I errors (multiple testing problem) (Caldas de Castro & Singer, 2006). The system implements the false discovery rate (FDR) procedure of Benjamini & Hochberg (1995):

1. Sort the $p_i$ values of the $m$ tested cells in ascending order: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.

2. Find the largest index $k \in \{1, \dots, m\}$ satisfying:

$$
p_{(k)} \le \frac{k}{m} \alpha
$$

3. If such $k$ exists, reject the null hypothesis $H_0$ (declare statistically significant spatial clustering) for all cells with $p_i \le p_{(k)}$.

Because the minimum attainable two-sided pseudo p-value is $p_{\mathrm{floor}} = \frac{2}{R + 1}$, the mathematical necessary condition for the Benjamini–Hochberg procedure to reject at least one hypothesis is that the number of cells reaching $p_{\mathrm{floor}}$ satisfies:

$$
k_{\mathrm{hit}} \ge \left\lceil \frac{p_{\mathrm{floor}} \cdot m}{\alpha} \right\rceil = \left\lceil \frac{2m}{(R + 1)\alpha} \right\rceil
$$

The system automatically computes $k_{\mathrm{hit}}$ (`fdr_min_hits_needed`) and alerts the user to raise $R$ to $999$ when $m$ is large.

### 3.5. Connected hotspot clustering and robust economic core (CBD) identification

To support urban economics models examining density gradients with respect to distance from the urban center, the system extracts connected components of `High-High` cells on the Queen graph using a pointer-jumping label propagation algorithm.

A connected `High-High` component $c$ is recognized as an **urban growth pole / hotspot cluster** if its cell count meets the minimum threshold $n_c \ge n_{\min}$ (default $n_{\min} = 4$ cells). Rather than defining the central business district (CBD) by the single brightest cell $\arg\max_i(\mathrm{NTL}_i)$, which is vulnerable to industrial flares, ports, or airports near the boundary, the core centroid $(\mathrm{CBD}_x, \mathrm{CBD}_y)$ is defined as the **sum-of-lights-weighted centroid (SOL-weighted centroid) of the largest High-High cluster** ($C^{\star}$):

$$
\mathrm{CBD}_x = \frac{\sum_{i \in C^{\star}} c_{x,i} \cdot (\mathrm{NTL}_i \cdot A_i)}{\sum_{i \in C^{\star}} (\mathrm{NTL}_i \cdot A_i)}, \quad \mathrm{CBD}_y = \frac{\sum_{i \in C^{\star}} c_{y,i} \cdot (\mathrm{NTL}_i \cdot A_i)}{\sum_{i \in C^{\star}} (\mathrm{NTL}_i \cdot A_i)}
$$

If a locality has no `High-High` cluster reaching $n_{\min}$, the system falls back to a robust alternative: selecting the non-border core cell with the highest spatial moving average score $0.5 \cdot \mathrm{NTL}_i + 0.5 \cdot \mathrm{Lag}(\mathrm{NTL}_i)$. The Euclidean distance from every cell $i$ to the economic core (in km) is exported as `dist_to_core_km`:

$$
d_{\mathrm{core}, i} = \frac{1}{1000}\sqrt{(c_{x,i} - \mathrm{CBD}_x)^2 + (c_{y,i} - \mathrm{CBD}_y)^2}
$$

---

## CHAPTER 4: MEMORY SAFEGUARD ALGORITHMS

### 4.1. Grid size estimation fuse

Before executing `geopandas.clip()`, the pre-computation fuse estimates the number of clipped grid cells ($N_{\mathrm{clip}}$) and bounding-box cells ($N_{\mathrm{bbox}}$) directly from the administrative boundary's area ($\mathrm{Area}$, $\mathrm{km}^2$) and perimeter ($\mathrm{Perimeter}$, $\mathrm{km}$):

$$
N_{\mathrm{clip}} \approx \frac{\mathrm{Area}}{(\mathrm{size}/1000)^2} + \beta \frac{\mathrm{Perimeter}}{\mathrm{size}/1000}
$$

where $\beta = 0.65$ adjusts for clipped border cells. If $N_{\mathrm{clip}} \ge N_{\max} = 150,000$ (`MAX_CELLS`) or $N_{\mathrm{bbox}} > 4 \times N_{\max}$, the execution button is locked and the next safe grid resolution is suggested.

### 4.2. Dynamic winsorization and browser rendering cap

1. **Dynamic winsorization for heatmap colormaps:** To prevent extreme radiance outliers (ports, heavy industry, gas flares) from washing out residential urban contrast, the display ceiling $v_{\max}$ is dynamically set to the 99th percentile of lit cells $\mathrm{NTL}_{\mathrm{lit}} = \{\mathrm{NTL}_i \mid \mathrm{NTL}_i > 0\}$:

$$
v_{\mathrm{raw}} = \begin{cases} P_{99}(\mathrm{NTL}_{\mathrm{lit}}) & \text{if } \lvert \mathrm{NTL}_{\mathrm{lit}} \rvert > 10 \\ \max_i(\mathrm{NTL}_i) & \text{if } \lvert \mathrm{NTL}_{\mathrm{lit}} \rvert \le 10 \end{cases}, \quad v_{\max} = \begin{cases} v_{\mathrm{raw}} & \text{if } v_{\mathrm{raw}} > 0.1 \\ 1.0 & \text{if } v_{\mathrm{raw}} \le 0.1 \end{cases}
$$

2. **Browser DOM rendering cap (`RENDER_CAP = 30,000`):** When the grid exceeds $30,000$ cells, rendering the full Leaflet SVG/Canvas DOM tree can freeze the client browser. The system prioritizes LISA-significant cells and the brightest cells for map display and rounds geometry coordinates to $10^{-6}$ degrees (`shapely.set_precision`) to shrink GeoJSON payload size. All exported CSV files retain 100% of observations.

---

## CHAPTER 5: PANEL DATA STRUCTURE AND ECONOMETRIC DATA BRIDGE

The primary goal of the system is to provide quantitative variables ready for statistical packages (Python, R, Stata) across two levels of analysis: **cell-level micro regressions (cross-sectional / spatial panel)** and **region–year macro panel regressions**.

### 5.1. Cell-level micro data

The cell-level CSV exports 100% of observations in the locality (including unlit `DARK` cells and clipped `EDGE` cells). Retaining all observations alongside indicator flags (`is_border_cell`, `is_edge_masked`, `is_dark`) allows researchers to explicitly control for **sample selection bias** (Heckman, 1979; Henderson et al., 2012).

**Core micro variable groups:**

* **Radiance intensity and light volume variables (`ntl_mean`, `ntl_sol`, `ntl_log`):**
  The variable `ntl_log` is defined as $\ln(1 + \mathrm{NTL}_i)$, compressing right skewness and dampening extreme outliers in OLS/WLS regressions. However, as shown theoretically by Chen & Roth (2024), transformations of the form $\ln(1 + Y)$ are sensitive to the scaling unit of $Y$ when zeros are prevalent (conflating the *extensive margin* and *intensive margin*). Therefore, the system exports `ntl_mean` and `ntl_sol` in levels alongside `ntl_log` so researchers can estimate **Poisson Pseudo-Maximum Likelihood (PPML)** models as a robustness check.

* **Spatial lag and relative location variables (`ntl_raw_lag`, `ntl_z_lit`, `lisa_lag_z`, `dist_to_core_km`):**
  Directly provides the spatial lag of raw radiance ($\mathrm{Lag}(\mathrm{NTL}_i)$), the spatial lag of standardized scores ($\mathrm{Lag}(z_i)$), and distance to the economic core (`dist_to_core_km`) to estimate spatial spillovers and urban density decay gradients.

* **LISA cluster classification variables (`lisa_I`, `lisa_p_sim`, `lisa_class`, `lisa_significant`, `hh_cluster_id`):**
  Enables constructing categorical dummy variables or analyzing urban boundary effects via spatial regression discontinuity designs (Spatial RDD).

### 5.2. Region–year panel data structure

For macroeconomic studies tracking district or provincial development across years, the system aggregates micro-level data into a single observation row per `(iso3, region_id, year, cell_size_m)` tuple. These aggregate indicators capture the **spatial structure of development**:

1. **Light inequality Gini coefficients (`gini_ntl_core_all`, `gini_ntl_core_lit`, `gini_sol_all`):**
   Building on the Night Light Development Index (NLDI) of Elvidge et al. (2012) and satellite-based spatial inequality studies by Lessmann & Seidel (2017) and Mirza et al. (2021), the Gini coefficient measures the spatial concentration of economic activity:

$$
G = \frac{2 \sum_{i=1}^n i \cdot x_{(i)}}{n \sum_{i=1}^n x_{(i)}} - \frac{n + 1}{n}
$$

(where $x_{(1)} \le x_{(2)} \le \dots \le x_{(n)}$ are values sorted in non-decreasing order). Three variants are exported: `gini_ntl_core_all` (computed across all non-border core cells including dark cells, ensuring identical cell areas), `gini_ntl_core_lit` (inequality within illuminated areas), and `gini_sol_all` (Gini of cell sum of lights $\mathrm{SOL}_i$ across all cells).

2. **Hotspot area share (`hh_area_share`, `hh_cluster_area_share`) and urban polycentricity (`n_hh_clusters`):**
   Measures the share of regional land area falling inside statistically significant `High-High` cells (`hh_area_share`) or contiguous `High-High` clusters meeting the minimum size threshold (`hh_cluster_area_share`):

$$
\mathrm{HH}_{\mathrm{share}} = \frac{\sum_{i \in \mathrm{HH}} A_i}{\sum_{i=1}^N A_i}
$$

This serves as a proxy for **de facto urbanization**, overcoming the limitations of administrative urban classifications. Combined with the number of independent hotspot clusters (`n_hh_clusters`) and the area of the largest cluster (`largest_hh_cluster_km2`), researchers can quantify transitions from monocentric to polycentric urban forms.

3. **Global spatial autocorrelation: Global Moran's I (displayed in the Data tab of `app.py`):**
   Computed across all $N$ grid cells (including $\mathrm{NTL} = 0$ cells) using symmetric binary Queen contiguity weights (Moran, 1950):

$$
I_{\mathrm{global}} = \frac{N}{\sum_{i=1}^N \sum_{j=1}^N w_{ij}} \frac{\sum_{i=1}^N \sum_{j=1}^N w_{ij}(x_i - \bar{x})(x_j - \bar{x})}{\sum_{i=1}^N (x_i - \bar{x})^2}
$$

If $I_{\mathrm{global}} > E[I] = -\frac{1}{N-1}$ and is statistically significant ($p < 0.05$), standard OLS residuals violate spatial independence, requiring spatial econometric specifications such as SAR, SEM, or SDM (LeSage & Pace, 2009) or Conley spatial-autocorrelation-robust standard errors (Conley, 1999).

4. **Internal clustering of illuminated areas: `moran_I_lit` (exported in the panel CSV from `lisa_core.py`):**
   Defined as the mean of Local Moran's I across tested lit cells:

$$
\bar{I}_{\mathrm{lit}} = \frac{1}{\lvert \mathrm{Focal} \rvert} \sum_{i \in \mathrm{Focal}} I_i
$$

This indicator measures the intensity of spatial clustering within the electrified and urbanized footprint of the locality over time.

### 5.3. Region–year panel data dictionary

The table below defines all variables in the exported `ntl_lisa_panel.csv` file:

| Variable name (Column) | Technical & econometric meaning |
| :--- | :--- |
| `iso3`, `region_id`, `region_label`, `year` | Administrative unit and time identifiers for the panel dataset. |
| `cell_size_m` | Square grid cell side length (meters): spatial scale control variable (MAUP). |
| `n_cells`, `n_cells_edge_masked` | Total grid cells in the locality and number of clipped border cells ($A_i < 0.99 \times \mathrm{size}^2$). |
| `n_cells_lit`, `n_cells_tested` | Number of lit cells ($\mathrm{NTL} > \mathrm{threshold}$) and core cells with sufficient neighbors tested in LISA. |
| `area_total_km2` | Total area of the locality summed across clipped grid cells ($\mathrm{km}^2$). |
| `lit_area_share` | Share of territory with nighttime light signal ($\in [0, 1]$): proxy for electrification and infrastructure coverage. |
| `hh_area_share` | Share of total area falling inside statistically significant `High-High` hotspot cells. |
| `hh_area_share_of_tested` | Share of `High-High` area relative to the total area of tested core cells. |
| `hh_cluster_area_share` | Share of total area falling inside contiguous `High-High` clusters meeting `min_cluster_cells`. |
| `ll_area_share`, `hl_area_share`, `lh_area_share` | Share of total area classified as `Low-Low`, `High-Low`, and `Low-High`. |
| `n_hh_clusters` | Number of independent contiguous `High-High` clusters, a proxy for urban polycentricity. |
| `largest_hh_cluster_km2` | Area ($\mathrm{km}^2$) of the largest contiguous `High-High` cluster (primary urban core). |
| `hotspot_dummy` | Binary indicator (`1/0`): equals `1` if `n_hh_clusters > 0`. Ready for Difference-in-Differences (DiD) designs. |
| `gini_ntl_core_all` | Radiance Gini coefficient across all non-border core cells (including dark cells), measuring overall spatial inequality. |
| `gini_ntl_core_lit` | Radiance Gini coefficient across lit core cells only, measuring internal inequality within illuminated areas. |
| `gini_sol_all` | Gini coefficient of cell sum of lights ($\mathrm{SOL}_i = \mathrm{NTL}_i \times A_i$) across all grid cells. |
| `moran_I_lit` | Mean Local Moran's I across tested lit cells, measuring urban spatial clustering. |
| `p_cfg_*`, `p_floor`, `fdr_min_hits_needed` | Hyperparameter metadata recording test configuration (`perms`, `alpha`, `fdr`, `log`, `lit_thr`, `edge_tol`, `min_nbr`, `min_cluster`) for scientific reproducibility. |

---

## CHAPTER 6: SYSTEM LIMITATIONS AND FUTURE EXTENSIONS

### 6.1. Input data limitations

* Due to the optical properties of the VIIRS DNB sensor and atmospheric scattering, light from high-intensity sources (seaports, industrial complexes, major bridges) tends to spill over into adjacent pixels or reflect off water surfaces (Elvidge et al., 2017; Gibson et al., 2021). This can slightly expand the boundaries of `High-High` clusters along coastlines and rivers.

* Clamping negative radiance values to $0$ after stray-light correction ensures physical non-negativity, but reduces informational variance in sparsely populated rural areas where true illumination is near $0$ (Gibson et al., 2021).

* Because the native resolution of monthly VIIRS composites is approximately $463.83\text{ m}$, a $500 \times 500\text{ m}$ grid cell covers roughly $1.16$ native pixels. At this resolution, two adjacent grid cells can share parts of the same VIIRS pixel through fractional extraction (`exactextract`), inducing mechanical spatial autocorrelation. For causal regressions, using a grid size $\ge 1000\text{ m}$ and checking robustness across multiple resolutions is recommended.

### 6.2. Hardware constraints

* Deployment on free cloud infrastructure (~1GB RAM) caps simultaneous polygon processing at `MAX_CELLS` $= 150,000$ cells. Consequently, at ultra-fine resolution ($500\text{ m}$), the system is best suited for districts, counties, or small-to-medium provinces; for large regions or national-scale analysis, users should increase grid resolution to $2000\text{ m} - 5000\text{ m}$ or run the engine on a local workstation.

### 6.3. Future extensions

1. **Multi-year calibrated VIIRS annual composites (Annual VNL V2):** Integrate the background-zeroed and gas-flare-filtered annual composites from the Earth Observation Group (`NOAA/VIIRS/DNB/ANNUAL_V21` / `V22`) (Elvidge et al., 2021) alongside the monthly median composite pipeline, combined with year fixed effects for long-horizon panel regressions.

2. **Spatio-temporal dynamics (Spatio-Temporal LISA – LISTA):** Upgrade `lisa_core.py` to compute spatial Markov transition matrices and local indicators of spatio-temporal association (LISTA) (Rey, Murray, & Anselin, 2011; Ye & Rey, 2013), enabling direct tracking of hotspot expansion trajectories across development stages.

---

## REFERENCES

1. Anselin, L. (1995). Local Indicators of Spatial Association—LISA. *Geographical Analysis*, 27(2), 93–115. https://doi.org/10.1111/j.1538-4632.1995.tb00338.x

2. Baston, D. (2023). *exactextract: Fast and accurate raster/polygon zonal statistics* [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.11396419

3. Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing. *Journal of the Royal Statistical Society: Series B (Methodological)*, 57(1), 289–300. https://doi.org/10.1111/j.2517-6161.1995.tb02031.x

4. Caldas de Castro, M., & Singer, B. H. (2006). Controlling the False Discovery Rate: A New Application to Account for Multiple and Dependent Tests in Local Statistics of Spatial Association. *Geographical Analysis*, 38(2), 180–208. https://doi.org/10.1111/j.0016-7363.2006.00682.x

5. Chen, J., & Roth, J. (2024). Logs with Zeros? Some Problems and Solutions. *The Quarterly Journal of Economics*, 139(2), 891–936. https://doi.org/10.1093/qje/qjad054

6. Chen, X., & Nordhaus, W. D. (2011). Using luminosity data as a proxy for economic statistics. *Proceedings of the National Academy of Sciences*, 108(21), 8589–8594. https://doi.org/10.1073/pnas.1017031108

7. Conley, T. G. (1999). GMM estimation with cross sectional dependence. *Journal of Econometrics*, 92(1), 1–45. https://doi.org/10.1016/S0304-4076(98)00084-0

8. Donaldson, D., & Storeygard, A. (2016). The View from Above: Applications of Satellite Data in Economics. *Journal of Economic Perspectives*, 30(4), 171–198. https://doi.org/10.1257/jep.30.4.171

9. Elvidge, C. D., Baugh, K. E., Anderson, S. J., Sutton, P. C., & Ghosh, T. (2012). The Night Light Development Index (NLDI): a spatially explicit measure of human development from satellite data. *Social Geography*, 7(1), 23–35. https://doi.org/10.5194/sg-7-23-2012

10. Elvidge, C. D., Baugh, K., Zhizhin, M., Hsu, F. C., & Ghosh, T. (2017). VIIRS night-time lights. *International Journal of Remote Sensing*, 38(21), 5860–5879. https://doi.org/10.1080/01431161.2017.1342050

11. Elvidge, C. D., Zhizhin, M., Ghosh, T., Hsu, F. C., & Taneja, J. (2021). Annual Time Series of Global VIIRS Nighttime Lights Derived from Monthly Averages: 2012 to 2019. *Remote Sensing*, 13(5), 922. https://doi.org/10.3390/rs13050922

12. Fotheringham, A. S., & Wong, D. W. S. (1991). The modifiable areal unit problem in multivariate statistical analysis. *Environment and Planning A: Economy and Space*, 23(7), 1025–1044. https://doi.org/10.1068/a231025

13. Gibson, J., Olivia, S., Boe-Gibson, G., & Li, C. (2021). Which night lights data should we use in economics, and where? *Journal of Development Economics*, 149, 102602. https://doi.org/10.1016/j.jdeveco.2020.102602

14. Heckman, J. J. (1979). Sample Selection Bias as a Specification Error. *Econometrica*, 47(1), 153–161. https://doi.org/10.2307/1912352

15. Henderson, J. V., Storeygard, A., & Weil, D. N. (2012). Measuring Economic Growth from Outer Space. *American Economic Review*, 102(2), 994–1028. https://doi.org/10.1257/aer.102.2.994

16. LeSage, J., & Pace, R. K. (2009). *Introduction to Spatial Econometrics*. Chapman and Hall/CRC. https://doi.org/10.1201/9781420064254

17. Lessmann, C., & Seidel, A. (2017). Regional inequality, convergence, and its determinants – A view from outer space. *European Economic Review*, 92, 110–132. https://doi.org/10.1016/j.euroecorev.2016.11.009

18. Mirza, M. U., Xu, C., van Bavel, B., van Nes, E. H., & Scheffer, M. (2021). Global inequality remotely sensed. *Proceedings of the National Academy of Sciences*, 118(18), e1919913118. https://doi.org/10.1073/pnas.1919913118

19. Moran, P. A. P. (1950). Notes on Continuous Stochastic Phenomena. *Biometrika*, 37(1/2), 17–23. https://doi.org/10.1093/biomet/37.1-2.17

20. Openshaw, S. (1984). *The Modifiable Areal Unit Problem*. Concepts and Techniques in Modern Geography (CATMOG), No. 38. Geo Books.

21. Rey, S. J., & Anselin, L. (2007). PySAL: A Python Library of Spatial Analytical Methods. *The Review of Regional Studies*, 37(1), 5–27. https://doi.org/10.52324/001c.8285

22. Rey, S. J., Murray, A. T., & Anselin, L. (2011). Visualizing regional income distribution dynamics. *Letters in Spatial and Resource Sciences*, 4(1), 81–90. https://doi.org/10.1007/s12076-010-0048-2

23. Ye, X., & Rey, S. J. (2013). A framework for exploratory space-time analysis of economic data. *The Annals of Regional Science*, 50(1), 315–339. https://doi.org/10.1007/s00168-011-0470-4
