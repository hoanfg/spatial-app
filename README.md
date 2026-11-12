<a id="top"></a>

[A02 data semantics: implementation, evidence and pending live validation](validation/DATA_SEMANTICS_A02.md)

<div align="center">

# Technical manual and methodological framework

**Nighttime lights (NTL) data extractor & spatial econometrics engine**

[ 🇬🇧 English ](README.md) &nbsp;|&nbsp; [ 🇻🇳 Tiếng Việt ](README-vi.md) &nbsp;|&nbsp; [ 🚀 Live demo ](https://spatial-app.streamlit.app/?)

</div>

---

> [!TIP]
> **⚡ TL;DR: got 30 seconds?**
>
> No time for a 10-page academic manual? Here is what this engine does, in plain words.
>
> - **The problem.** Satellite nighttime lights (NTL) are a standard stand-in for GDP in economics. **But** the data is huge. Processing it usually crashes an ordinary computer (RAM runs out), and doing it by hand takes weeks.
> - **What the app does.** You pick a region $\rightarrow$ the app fetches the data from *Google Earth Engine* $\rightarrow$ a C/C++ backend crushes millions of pixels into grid cells $\rightarrow$ **resource guards limit the workload; reliable operation within 1GB still requires a full deployment benchmark.**
> - **What you get.** One click gives you a CSV of ready-to-use economic indicators: where is the true urban core? where are the economic hotspots (LISA)? how unequal is the distribution (Gini)? Download it and drop it straight into your regression models.
> - 👉 **[TRY THE LIVE DEMO](https://spatial-app.streamlit.app/?)**

```mermaid
flowchart LR
    A["🗺️ Pick a region<br/>(GADM boundaries)"] --> B["🛰️ Google Earth Engine<br/>(VIIRS imagery)"]
    B --> C["⚙️ exactextract (C/C++)<br/>pixels into grid cells"]
    C --> D["📍 LISA & Moran's I<br/>hotspots, urban core, Gini"]
    D --> E["📄 CSV at cell level<br/>and region–year level"]
```

This project is a system for **spatial econometrics**. It combines a spatial grid infrastructure with a nighttime lights (NTL) extraction pipeline.

The app covers three stages: it turns irregular administrative boundaries into uniform square grids; it connects directly to Google Earth Engine (GEE) to pull raster data (SNPP-VIIRS); and it automatically computes micro-level spatial statistics (LISA) and exports panel datasets for macroeconomic models.

### 🧭 Where should you start?

| If you are... | Read |
| :--- | :--- |
| 🧑‍💼 A policymaker or a non-technical reader | The TL;DR above, [Section I](#s1) and [Section VI](#s6) |
| 📈 An economist who needs variables for regressions | [Section V](#s5), then [Section III](#s3) to see where the indicators come from |
| 🔬 A researcher checking the methodology | [Section II](#s2) and [Section III](#s3) |
| 🛠️ Deploying or operating the system | [Section I](#s1), [Section IV](#s4) and [Section VI](#s6) |

<details>
<summary><b>📖 Quick glossary (click to expand)</b></summary>

<br>

| Term | In plain words |
| :--- | :--- |
| **NTL** (Nighttime Lights) | Light observed from satellites at night. Here, the mean radiance of a grid cell. |
| **VIIRS** | The satellite sensor/dataset that supplies the nighttime imagery used by the system. |
| **GEE** | Google Earth Engine, where the satellite imagery is fetched from. |
| **Vector / Raster** | Vector data are boundary polygons (provinces, districts...). Raster data are images made of pixels. |
| **SOL** (Sum of Lights) | Total light of a cell = mean radiance × cell area. |
| **LISA** | An indicator that tells whether *each grid cell* clusters with its surroundings (a bright cluster, a dim cluster, or an odd one out). |
| **HH / LL / HL / LH** | The four LISA labels: High-High, Low-Low, High-Low, Low-High (see [Section 3.1](#s3)). |
| **MAUP** | The statistical bias that appears when you compare administrative units whose areas and shapes differ wildly. |
| **FDR** | A way to keep the number of false discoveries in check when thousands of cells are tested at once. |
| **CBD** | Central Business District, the economic core of a region. |
| **Gini** | A measure of concentration/inequality. Near 0 means evenly spread; near 1 means concentrated in very few cells. |
| **UTM** | A flat coordinate system measured in meters, convenient for areas and distances. |
| **OOM** | Out-Of-Memory: RAM runs out and the operating system forcibly kills the process. |

</details>

---

<a id="s1"></a>

## 🏗️ I. System architecture overview and resource management

The system is more than a remote sensing data extractor. It is a web-based spatial processing engine that links geographic preprocessing (GIS) workflows directly to spatial econometric models.

### 1.1. Four-tier architecture

The job mixes three very different kinds of data: **vector** (administrative boundaries), **raster** (VIIRS satellite imagery) and **spatial inferential statistics**. To keep this manageable, the workflow is split into 4 independent tiers:

| Tier | What it does | Key techniques / tools |
| :--- | :--- | :--- |
| **Tier 1**<br>📂 Data discovery | Recursively scans the local GADM directory structure, infers ISO3 identifiers, standardizes administrative names and loads them into the user interface (UI), without relying on a static database. | Pattern recognition, Unicode normalization (NFC/NFD), the `pycountry` library |
| **Tier 2**<br>📐 Geometry | Handles polygon geometry: projects all vector data into a dynamic flat UTM (Universal Transverse Mercator) coordinate system chosen from the centroid longitude and latitude of the bounding box, then builds a regular spatial grid. | Vectorization with `numpy.meshgrid` and `shapely.box` |
| **Tier 3**<br>🛰️ Raster | Sends a spatial query to the Google Earth Engine (GEE) API to filter clouds, compute the annual median composite and clip the raster image to the analysis boundary. The GeoTIFF byte stream is loaded into temporary memory so the **C/C++ engine** can compute area-weighted fractional zonal statistics between the vector grid and the raster. | GEE API, the **C/C++ engine** `exactextract` |
| **Tier 4**<br>📊 Econometrics & rendering | Runs the spatial econometrics core (Global Moran's I, Local Moran's I / LISA, connected hotspot cluster detection, distance to the economic core, Gini inequality coefficient) and renders the multi-layer interactive map. Output is packaged through the data bridge as cell-level and region–year panel CSV files. | Folium/Leaflet |

> [!NOTE]
> 📎 How the system recognizes and classifies countries, and how it handles the quirks of GADM data, is covered in a separate document: [read the technical specification for country classification here](https://github.com/hoanfg/spatial-app/blob/main/docs/GADM_v41%20pipeline%20specification.md).

### 1.2. Hardware constraints and out-of-memory (OOM) safeguards on Cloud

The target deployment environment is Streamlit Community Cloud (or low-cost docker containers), where resources are strictly limited to **~1GB RAM** and **1 CPU Core**.

The memory footprint of spatial geometry processing grows rapidly with grid resolution.

> [!WARNING]
> **A typical way to crash the server.** When executing `geopandas.clip()` on a 500m grid for an administrative unit covering $38,000 \, \mathrm{km}^2$, the number of clipped polygons ($N_{\mathrm{clip}} > 152,000$) exceeds the $150,000$ cap (while the pre-clip bounding-box grid $N_{\mathrm{bbox}}$ can exceed $250,000$ polygons). Holding the topology of that many polygons in RAM at once triggers the Linux OOM Killer and takes down the server process.

Three layers of defense prevent this:

| # | Safeguard | How it works |
| :---: | :--- | :--- |
| 1 | **In-memory zip streaming & ephemeral cleanup** | Raster imagery from GEE is downloaded as a compressed byte stream, extracted directly in RAM and written to a temporary file (`tempfile`). As soon as `exactextract` finishes reading the raster inside the `try...finally` block, the temporary file is forcibly removed from disk, releasing resources immediately. |
| 2 | **Pre-computation grid size fuse** | Estimates the number of grid cells from boundary area and perimeter *before* any geometry is created, so queries that exceed the memory cap are blocked (details in [Section 4.1](#s4)). |
| 3 | **FIFO session cache** | The LISA computation cache (`_lisa_cache`) holds at most the 5 most recent parameter configurations, evicted first-in, first-out (FIFO). Users can switch between parameter sets instantly, with no memory leak. |

### 1.3. Stateless mechanism of web browsers

Streamlit runs on a **stateless** model: every time a user touches any UI control, Python re-executes the script from top to bottom. The system keeps its state through two mechanisms:

| Mechanism | What it is used for |
| :--- | :--- |
| **Memoization**<br>(`@st.cache_data`, `@st.cache_resource`) | GEE authentication initialization, GADM directory scanning, boundary geometry statistics and satellite raster downloads. Results are hashed by their input parameters and reused straight from cache. |
| **Session state injection** | The heavy extraction workflow is isolated inside `run_pipeline()` and its output is stored in `st.session_state["result"]`. Later changes to colormaps, scaling modes or map filters read directly from `st.session_state`, so the presentation layer (UI) is fully decoupled from the computation backend. |

<sub>[↑ Back to top](#top)</sub>

---

<a id="s2"></a>

## 🗺️ II. Spatial geoprocessing methodology

### 2.1. Addressing the modifiable areal unit problem (MAUP)

In empirical spatial economics, using administrative boundaries (provinces, districts, communes) directly introduces statistical bias, because the units differ enormously in area and shape. This is known as the **modifiable areal unit problem (MAUP)** (Openshaw, 1984; Fotheringham & Wong, 1991). The system deals with it by standardizing the study area into a uniform square grid matrix (Donaldson & Storeygard, 2016).

> 💡 **In plain words:** comparing the brightness of a district as large as a small province with that of an inner-city ward of a few dozen km² is not a fair fight. Cut everything into equal squares and every place starts from the same line.

#### 🧭 Dynamic coordinate projection algorithm

The Phase 1 prototype hardcoded a local EPSG code (`EPSG:32648`). The current version instead works out the optimal **UTM (Universal Transverse Mercator)** zone from the centroid longitude and latitude $(\lambda_{\mathrm{center}}, \phi_{\mathrm{center}})$ of the study area's bounding box.

**Step 1: find the zone.**

$$
\mathrm{Zone} = \min\left(60, \max\left(1, \left\lfloor \frac{\lambda_{\mathrm{center}} + 180}{6} \right\rfloor + 1\right)\right)
$$

**Step 2: assign the EPSG code** (in meters), automatically for both the Northern and Southern hemispheres:

$$
\mathrm{EPSG} = \begin{cases} 32600 + \mathrm{Zone} & \text{if } \phi_{\mathrm{center}} \ge 0 \text{ (Northern hemisphere)} \\ 32700 + \mathrm{Zone} & \text{if } \phi_{\mathrm{center}} < 0 \text{ (Southern hemisphere)} \end{cases}
$$

> 🧪 **Quick example:** a study area centered at longitude $105^\circ\mathrm{E}$ in the Northern hemisphere gives $\mathrm{Zone} = \lfloor 285 / 6 \rfloor + 1 = 48$ and $\mathrm{EPSG} = 32648$, which is exactly the code the Phase 1 prototype hardcoded.

**Grid alignment.** All grid origin coordinates $(x_0, y_0)$ are snapped to integer multiples of the cell side length $\mathrm{size}$ in flat UTM space. Grids of adjacent districts therefore fit together without gaps or overlaps when merged.

### 2.2. Cloud masking on GEE and zonal statistics extraction via fractional coverage

#### ☁️ Step 1: mask clouds before taking the median

| Item | Value |
| :--- | :--- |
| Data source | Monthly composites from `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` |
| Native resolution | $\approx 15\text{ arc-seconds} \approx 463.83\text{ m}$ at the equator |
| Cloud-free mask | `cf_cvg` $> 0$, applied to each monthly image |
| Compositing | **Annual median composite** (Elvidge et al., 2017, 2021) |

Why the mask is needed: in monsoon tropical regions, heavy cloud cover during rainy months can leave a pixel with no valid observation at all (`cf_cvg` $= 0$), and the radiance gets recorded as an artificial $0$. The cloud-free mask removes this downward bias before the median is taken.

#### 🎯 Step 2: zonal statistics via fractional coverage

Traditional center-of-pixel raster stats introduce substantial error when the grid cell size approaches the native VIIRS pixel size. The system therefore uses the C/C++ library `exactextract` (Baston, 2023). The mean radiance $\mathrm{NTL}\_{i}$ of grid cell $i$ is a weighted average, with weights given by the fractional pixel area $w\_{ip} \in [0, 1]$ that actually falls inside polygon cell $i$:

$$
\mathrm{NTL}_i = \frac{\sum_{p \in i} x_p \cdot w_{ip}}{\sum_{p \in i} w_{ip}}
$$

> 💡 **In plain words:** each pixel counts only for the part that lies inside the cell. A pixel with 60% of its area inside the cell carries a weight of $0.6$; a pixel that merely clips the edge barely matters.

Missing or negative values arising from sensor stray-light correction are clamped to $0.0$. The sum of lights (SOL) of each cell is the product of mean radiance and true clipped area:

$$\mathrm{SOL}_i = \mathrm{NTL}_i \times A_i$$

<sub>[↑ Back to top](#top)</sub>

---

<a id="s3"></a>

## 📍 III. Spatial econometrics core (LISA core algorithm)

The `ntl/lisa_core.py` module is built entirely with array algebra on `numpy` and `pandas`. It needs no heavy GIS packages such as `libpysal` or `esda`, and it brings the complexity of contiguity graph construction down to $\mathcal{O}(N \log N)$.

> 💡 **LISA in one sentence:** instead of a single number for the whole region, LISA gives *each grid cell* a label saying whether that cell and its surroundings are bright together, dim together, or at odds with each other.

### 3.1. Handling zero-inflated data and border cells

Natural nighttime radiance data contain a high proportion of zeros (forests, water bodies, agricultural land). They also contain sliver polygons clipped along administrative boundaries. The system tackles both problems in 3 steps.

#### Step 1. Border cell masking

A grid cell $i$ is flagged as a border cell (`is_border_cell = 1` and `is_edge_masked = 1`) and excluded from the contiguity graph if its true clipped area $A_i$ is less than $99\%$ of a full standard cell area:

$$
A_i < 0.99 \times \left(\frac{\mathrm{size}}{1000}\right)^2 \quad (\mathrm{km}^2)
$$

#### Step 2. Z-score standardization on the core reference set $S$

Let $S$ denote the set of core cells (non-border cells, meaning $A_i \ge 0.99 \times (\mathrm{size}/1000)^2$) eligible for testing. Depending on the mode, $S$ consists of:

| Mode | $S$ consists of |
| :--- | :--- |
| Default (`include_zeros = False`) | Core cells with radiance above the threshold ($\mathrm{NTL}_i > \mathrm{threshold}$) |
| Extended (`include_zeros = True`) | All core cells |

The standardized score $z_i$ uses the Bessel-corrected sample standard deviation ($\mathrm{ddof} = 1$):

$$
\mu_S = \frac{1}{\lvert S \rvert} \sum_{i \in S} v_i, \quad \sigma_S = \sqrt{\frac{1}{\lvert S \rvert - 1} \sum_{i \in S} (v_i - \mu_S)^2}, \quad z_i = \frac{v_i - \mu_S}{\sigma_S} \quad \forall i \in S
$$

Here $v_i$ depends on whether the log transformation is enabled (it compresses the right-skewed tail):

| Option | Value of $v_i$ |
| :--- | :--- |
| Log transformation on | $v_i = \ln(\mathrm{NTL}_i)$ |
| Log transformation on, zeros included | $\ln(1 + \mathrm{NTL}_i)$ |
| Raw radiance scale | $v_i = \mathrm{NTL}_i$ |

#### Step 3. Methodological implications of the lit-only testing mode (`lit_only`)

When unlit cells ($\mathrm{NTL}_i \le \mathrm{threshold}$, labeled `DARK`) are excluded from the spatial weight matrix $W$, the mean $\mu_S$ represents the **internal average brightness of illuminated areas**. The LISA labels then read as follows:

| Label | Meaning in `lit_only` mode |
| :--- | :--- |
| 🔴 **High-High (HH)** | Contiguous urban and commercial cores with exceptionally high radiance. |
| 🔵 **Low-Low (LL)** | Contiguous areas of low-intensity illumination (below the lit-area mean, such as peri-urban fringes or sparse settlements). Completely unlit areas are separated into the `DARK` state. |
| 🟠 **High-Low (HL)** and 🟣 **Low-High (LH)** | Spatial outliers within the illuminated urban structure. |

### 3.2. Queen contiguity graph

The spatial weight matrix $W$ is built with **Queen** contiguity on the regular grid, for cells in $S$. Queen counts 8 surrounding directions: 4 edges and 4 corners.

```text
┌───┬───┬───┐
│ ↖ │ ↑ │ ↗ │
├───┼───┼───┤
│ ← │ ■ │ → │      ■ = the cell being examined; the 8 cells around it are its neighbors
├───┼───┼───┤
│ ↙ │ ↓ │ ↘ │
└───┴───┴───┘
```

From the centroid coordinates $(c_{x,i}, c_{y,i})$ in UTM meters, the algorithm maps each cell to integer grid indices $(ix_i, iy_i)$ and computes a unique 1D hash key:

$$
ix_i = \left\lfloor \frac{c_{x,i} + \epsilon}{\mathrm{size}} \right\rfloor, \quad iy_i = \left\lfloor \frac{c_{y,i} + \epsilon}{\mathrm{size}} \right\rfloor, \quad \mathrm{Key}_i = ix_i \cdot H + iy_i
$$

Here $\epsilon = 10^{-6}\text{ m}$ compensates for IEEE-754 floating-point rounding near cell boundaries, and $H = \max(iy) - \min(iy) + 4$.

> 💡 **In plain words:** every cell gets a unique "house number". The algorithm sorts the house numbers, then uses vectorized binary search via `numpy.searchsorted` to look up all 8 neighbors $(dx, dy) \in \{-1, 0, 1\}^2 \setminus \{(0,0)\}$ of every cell at once, instead of comparing cells pair by pair. That is why the complexity stays at $\mathcal{O}(N \log N)$.

Spatial weights $w_{ij}$ are row-standardized:

$$
w_{ij} = \begin{cases} \frac{1}{k_i} & \text{if } j \in N(i) \cap S \\ 0 & \text{otherwise} \end{cases}
$$

where $k_i = \lvert N(i) \cap S \rvert$ is the number of valid neighbors of cell $i$. Only cells $i \in S$ with $k_i \ge k_{\min}$ (default $k_{\min} = 1$) enter the tested set $\mathrm{Focal}$.

> Method update (11 November 2026): Local I now uses ESDA normalization and conditional sampling without replacement. Recompute earlier LISA/panel exports; see [audit corrections and migration](docs/audit-fixes-2026-11-11.md).

### 3.3. Local Moran's I (LISA) test and conditional permutation

The Local Moran's I statistic (Anselin, 1995) and the standardized spatial lag ($\mathrm{Spatial\ Lag}\ z$) for each cell $i \in \mathrm{Focal}$ are defined as:

$$
I_i = \frac{z_i}{m_2} \sum_{j \in N(i) \cap S} w_{ij} z_j, \quad \mathrm{Lag}(z_i) = \sum_{j \in N(i) \cap S} w_{ij} z_j, \quad m_2 = \frac{1}{\lvert S \rvert - 1} \sum_{r \in S} z_r^2
$$

> 💡 **In plain words:** the spatial lag $\mathrm{Lag}(z_i)$ is the "average" brightness of the neighboring cells. A large positive $I_i$ means the cell and its neighbors move together (both bright or both dim). A negative $I_i$ means they pull in opposite directions.

#### 🎲 Vectorized conditional permutation

Nighttime light radiance does not follow a normal distribution, so the statistical significance of $I_i$ is evaluated by Monte Carlo simulation with $R$ conditional permutations:

| Parameter | Value |
| :--- | :--- |
| Number of permutations $R$ | Default $R = 499$, up to $R = 999$ |
| Tie tolerance | $10^{-12}$ |

In each permutation $r \in \{1, \dots, R\}$, the focal value $z_i$ is held fixed while $k_i$ neighbor values are drawn uniformly **without replacement within each replicate**, using sequential rejection sampling from the pool $S \setminus \{i\}$. This produces the simulated statistic $I_i^{(r)}$.

Let $M_i$ denote the number of simulations falling into the nearer extreme tail (numerical ties are handled within $10^{-12}$):

$$
M_i = \min\left( \sum_{r=1}^R \mathbb{I}\left(I_i^{(r)} \ge I_i - 10^{-12}\right); \sum_{r=1}^R \mathbb{I}\left(I_i^{(r)} \le I_i + 10^{-12}\right) \right)
$$

The app retains its doubled smaller-tail pseudo p-value with inclusive ties and a +1 correction (distinct from ESDA's raw one-tail `p_sim`):

$$
p_i = \min\left(1.0; 2 \times \frac{M_i + 1}{R + 1}\right)
$$

### 3.4. Controlling the false discovery rate (FDR – Benjamini-Hochberg)

At 500m resolution, one run can test $m = \lvert \mathrm{Focal} \rvert$ grid cells, often tens of thousands of them. Applying an unadjusted threshold $\alpha = 0.05$ to each cell inflates Type I errors (the multiple testing problem) (Caldas de Castro & Singer, 2006).

> 💡 **In plain words:** test 10,000 cells at a 5% threshold and, even if the region has no real clusters at all, you would still expect about 500 cells to be flagged as "significant" by pure chance.

The system implements the false discovery rate (FDR) procedure of Benjamini & Hochberg (1995):

1. Sort the $p_i$ values of the $m$ tested cells in ascending order: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.

2. Find the largest index $k \in \{1, \dots, m\}$ satisfying:

$$
p_{(k)} \le \frac{k}{m} \alpha
$$

3. If such $k$ exists, reject the null hypothesis $H_0$ (declare statistically significant spatial clustering) for all cells with $p_i \le p_{(k)}$.

#### 🚧 The minimum requirement for catching any cluster at all

The minimum attainable two-sided pseudo p-value is $p_{\mathrm{floor}} = \frac{2}{R + 1}$. So for the Benjamini–Hochberg procedure to reject even one hypothesis, the number of cells reaching $p_{\mathrm{floor}}$ must satisfy this mathematically necessary condition:

$$
k_{\mathrm{hit}} \ge \left\lceil \frac{p_{\mathrm{floor}} \cdot m}{\alpha} \right\rceil = \left\lceil \frac{2m}{(R + 1)\alpha} \right\rceil
$$

The system computes $k_{\mathrm{hit}}$ (`fdr_min_hits_needed`) automatically and warns the user to raise $R$ to $999$ when $m$ is large.

> 🧪 **Worked example:** with $m = 10{,}000$ cells and $\alpha = 0.05$, at least 800 cells must hit the floor if $R = 499$, but only 400 if $R = 999$. More permutations lower the p-value floor, which makes the condition easier to meet.

### 3.5. Connected hotspot clustering and robust economic core (CBD) identification

Urban economics models often study density gradients with respect to distance from the urban center. To support them, the system extracts connected components of `High-High` cells on the Queen graph using a pointer-jumping label propagation algorithm.

Getting from clusters to a core takes three steps:

1. **Recognize hotspots.** A connected `High-High` component $c$ counts as an **urban growth pole / hotspot cluster** if its cell count meets the minimum threshold $n_c \ge n_{\min}$ (default $n_{\min} = 4$ cells).

2. **Pick the economic core (CBD).** The core centroid $(\mathrm{CBD}_x, \mathrm{CBD}_y)$ is the **sum-of-lights-weighted centroid (SOL-weighted centroid) of the largest High-High cluster** ($C^{\star}$):

$$
\mathrm{CBD}_x = \frac{\sum_{i \in C^{\star}} c_{x,i} \cdot (\mathrm{NTL}_i \cdot A_i)}{\sum_{i \in C^{\star}} (\mathrm{NTL}_i \cdot A_i)}, \quad \mathrm{CBD}_y = \frac{\sum_{i \in C^{\star}} c_{y,i} \cdot (\mathrm{NTL}_i \cdot A_i)}{\sum_{i \in C^{\star}} (\mathrm{NTL}_i \cdot A_i)}
$$

3. **Fallback.** If a locality has no `High-High` cluster reaching $n_{\min}$, the system falls back to a robust alternative: it selects the non-border core cell with the highest spatial moving average score $0.5 \cdot \mathrm{NTL}_i + 0.5 \cdot \mathrm{Lag}(\mathrm{NTL}_i)$.

> [!NOTE]
> **Why not simply take the brightest cell** $\arg\max_i(\mathrm{NTL}_i)$**?** The brightest cell is easily an industrial flare, a port or an airport near the boundary, and it would drag the core away from the true center. The centroid of a whole cluster is far more stable.

From the core, the Euclidean distance from every cell $i$ to the economic core (in km) is exported as `dist_to_core_km`:

$$
d_{\mathrm{core}, i} = \frac{1}{1000}\sqrt{(c_{x,i} - \mathrm{CBD}_x)^2 + (c_{y,i} - \mathrm{CBD}_y)^2}
$$

### 3.6. Frontier spatial econometric modules

`ntl/lisa_core.py` goes beyond static exploratory spatial data analysis (ESDA). To support modern causal and structural identification, it automatically computes 5 frontier econometric modules:

| # | Module | Question it answers | Output variable |
| :---: | :--- | :--- | :--- |
| 1 | Top-lights Pareto tail exponent | How strongly are the brightest cells concentrated? | — |
| 2 | Urban density decay gradient | How fast does light fall off away from the core? | `urban_gradient_decay`, `monocentric_r2` |
| 3 | Recentered market access | What is a cell's market potential once the part due to a central location is removed? | `recentered_market_access` |
| 4 | Spillover rings & signed boundary distance | Where is the hotspot boundary, and how far do spillovers reach? | `signed_dist_hh_km` |
| 5 | Spatial unit-root diagnostics & Spatial Markov | How persistent is the spatial structure, and how does it change between two periods? | `spatial_ar1_persistence` |

Details of each module:

**1. Top-lights Pareto tail exponent** ($\hat{\zeta}_{\mathrm{Hill}}$, Bluhm & Krause, 2022; Bluhm et al., 2025)

Applies the Hill extreme-value estimator to the brightest $k = \lfloor 0.10 \lvert S_{\mathrm{lit}} \rvert \rfloor$ core cells to quantify upper-tail agglomeration intensity:

$$
\hat{\zeta}_{\mathrm{Hill}} = \left[ \frac{1}{k} \sum_{j=1}^{k} \ln\left(\frac{\mathrm{NTL}_{(j)}}{\mathrm{NTL}_{(k+1)}}\right) \right]^{-1}
$$

**2. Endogenous urban density decay gradient** ($\hat{\gamma}$, Duranton & Puga, 2023)

Estimates the structural spatial decay equation by area-weighted WLS across core cells:

$$\ln(1 + \mathrm{NTL}\_{i}) = \alpha\_{0} - \gamma \cdot d\_{\mathrm{core}, i} + u\_{i}$$

It exports both the decay rate $\hat{\gamma}$ (`urban_gradient_decay`) and the monocentricity goodness-of-fit $R^2_{\mathrm{gradient}}$ (`monocentric_r2`).

**3. Recentered market access** ($\widetilde{\mathrm{MA}}_i$, Borusyak & Hull, 2023)

Computes the gravity-weighted market potential $\mathrm{MA}\_{i} = \sum\_{j \ne i} \mathrm{SOL}\_{j} \exp(-\tau d\_{ij})$ over a symmetric UTM grid stencil, then subtracts its exact analytical expectation under spatial permutation $\mathbb{E}\_{\pi}[\mathrm{MA}\_{i}] = \overline{\mathrm{SOL}}\_{\mathrm{Core}} \sum\_{j \ne i} \exp(-\tau d\_{ij})$ to purge geographic centrality bias (`recentered_market_access`).

**4. Concentric spillover rings and signed boundary distance for Spatial RDD** (Vazquez-Bare, 2023; Butts, 2024)

Computes the signed Euclidean distance to the nearest hotspot boundary, `signed_dist_hh_km` ($d < 0$ inside the core, $d > 0$ outside the core). It serves as the running variable for Spatial Regression Discontinuity Designs (Spatial RDD). The locality is also partitioned into 5 concentric exposure rings, from `0_Treated_HH` through `4_Pure_Control_gt10km`, to isolate uncontaminated control units.

**5. Spatial unit-root diagnostics and two-period Spatial Markov dynamics** (Müller & Watson, 2022, 2024; Rey, Arribas-Bel, & Wolf, 2023; Borusyak, Jaravel, & Spiess, 2024)

Diagnoses first-order spatial autoregression persistence (`spatial_ar1_persistence`) and enables two-period ($t_0 \rightarrow t_1$) directional LISA analysis, to quantify *Agglomeration Shadow* effects and conditional Spatial Markov transition matrices.

<sub>[↑ Back to top](#top)</sub>

---

<a id="s4"></a>

## ✅ Data quality, robustness and external validation

Three additions that report how much the result depends on pipeline and analytic choices. None of them changes NTL values.

- **Data-quality report** (Data tab): share of NaN and negative pixels, cells with no extracted value, share of zero cells, and (on demand) the number of cloud-free months per pixel. The same figures and the pipeline provenance (`ntl_composite`, `ntl_negative_handling`, `ntl_nodata_handling`) are written to the panel CSV as `dq_*` columns. An on-demand button re-extracts cell means without clipping negatives and compares them with the clipped version.
- **Robustness checks** (LISA tab): re-runs LISA under Rook weights, higher lit thresholds, P99 / asinh / ln transforms, other α, with and without FDR, a 2×2 coarser grid (MAUP) and adjacent years, then reports the Jaccard overlap of the High-High set with the baseline and the area that is HH in at least 80% of runs. Output columns: `rob_*`. The verdict cut-offs (median Jaccard 0.70 and 0.50) are rules of thumb, not statistical thresholds.
- **External validation** (Data tab): Spearman ρ with a spatial block-bootstrap CI and AUC between NTL and GHSL built-up surface or population on the same cells. GHSL epochs are 5-yearly, so the epoch used can differ from the NTL year. Output columns: `val_*`.

Code: `ntl/data_quality.py`, `ntl/robustness.py`, `ntl/validation.py`, `ntl/zonal.py`, `ntl/ee_extra.py`; tests in `tests/test_robustness.py` and `tests/test_zonal.py`. The Earth Engine fetch code (valid-month count, GHSL) and the UI panels have not been run against live data.

## 🛡️ IV. Memory safeguard algorithms

### 4.1. Grid size estimation fuse

Before `geopandas.clip()` is allowed to run, a pre-computation fuse estimates the number of clipped grid cells ($N_{\mathrm{clip}}$) and bounding-box cells ($N_{\mathrm{bbox}}$) directly from the administrative boundary's area ($\mathrm{Area}$, $\mathrm{km}^2$) and perimeter ($\mathrm{Perimeter}$, $\mathrm{km}$):

$$
N_{\mathrm{clip}} \approx \frac{\mathrm{Area}}{(\mathrm{size}/1000)^2} + \beta \frac{\mathrm{Perimeter}}{\mathrm{size}/1000}
$$

Here $\beta = 0.65$ adjusts for clipped border cells.

> 💡 **In plain words:** the number of cells is roughly the region's area divided by the area of one cell, plus an allowance for the cells that get cut along the outline (the longer the perimeter, the bigger the allowance).

| Condition (either one is enough) | Action |
| :--- | :--- |
| $N_{\mathrm{clip}} \ge N_{\max} = 150,000$ (`MAX_CELLS`) | 🔒 The execution button is locked and the next safe grid resolution is suggested |
| $N_{\mathrm{bbox}} > 4 \times N_{\max}$ | 🔒 Same |

### 4.2. Dynamic winsorization and browser rendering cap

#### 🎨 Dynamic winsorization for heatmap colormaps

Ports, heavy industry and gas flares can be bright enough to wash out the contrast of residential urban areas on the map. To prevent that, the display ceiling $v_{\max}$ is set dynamically at the 99th percentile of lit cells $\mathrm{NTL}_{\mathrm{lit}} = \{\mathrm{NTL}_i \mid \mathrm{NTL}_i > 0\}$:

$$
v_{\mathrm{raw}} = \begin{cases} P_{99}(\mathrm{NTL}_{\mathrm{lit}}) & \text{if } \lvert \mathrm{NTL}_{\mathrm{lit}} \rvert > 10 \\ \max_i(\mathrm{NTL}_i) & \text{if } \lvert \mathrm{NTL}_{\mathrm{lit}} \rvert \le 10 \end{cases}, \quad v_{\max} = \begin{cases} v_{\mathrm{raw}} & \text{if } v_{\mathrm{raw}} > 0.1 \\ 1.0 & \text{if } v_{\mathrm{raw}} \le 0.1 \end{cases}
$$

#### 🧱 Browser DOM rendering cap (`RENDER_CAP = 30,000`)

When the grid exceeds $30,000$ cells, rendering the full Leaflet SVG/Canvas DOM tree can freeze the client browser. The system handles it like this:

- It prioritizes LISA-significant cells and the brightest cells for the map display.
- It rounds geometry coordinates to $10^{-6}$ degrees (`shapely.set_precision`) to shrink the GeoJSON payload.

> [!IMPORTANT]
> Only the map is trimmed. **All exported CSV files retain 100% of observations.**

<sub>[↑ Back to top](#top)</sub>

---

<a id="s5"></a>

## 📦 V. Panel data structure and econometric data bridge

The primary goal of the system is to provide quantitative variables ready for statistical packages (Python, R, Stata) at two levels of analysis:

| Level | Type of regression | Data file |
| :--- | :--- | :--- |
| 🔬 **Micro** | Cell-level regressions (cross-sectional / spatial panel) | Cell-level CSV |
| 🌏 **Macro** | Region–year panel regressions | `ntl_lisa_panel.csv` |

### 5.1. Cell-level micro data

The cell-level CSV exports **100% of observations** in the locality, including unlit `DARK` cells and clipped `EDGE` cells. Keeping every observation alongside the indicator flags (`is_border_cell`, `is_edge_masked`, `is_dark`) lets researchers explicitly control for **sample selection bias** (Heckman, 1979; Henderson et al., 2012).

**Core micro variable groups:**

| Group | Variables | What they are for |
| :--- | :--- | :--- |
| **Radiance intensity and light volume** | `ntl_mean`, `ntl_sol`, `ntl_log` | Measure how bright a cell is and how much light it emits in total, on both the raw and the log scale. |
| **Spatial lag and relative location** | `ntl_raw_lag`, `ntl_z_lit`, `lisa_lag_z`, `dist_to_core_km` | Directly provide the spatial lag of raw radiance ($\mathrm{Lag}(\mathrm{NTL}_i)$), the spatial lag of standardized scores ($\mathrm{Lag}(z_i)$) and the distance to the economic core, for estimating spatial spillovers and urban density decay gradients. |
| **LISA cluster classification** | `lisa_I`, `lisa_p_sim`, `lisa_class`, `lisa_significant`, `hh_cluster_id` | Build categorical dummy variables, or analyze urban boundary effects with spatial regression discontinuity designs (Spatial RDD). |

> [!NOTE]
> **Why export both a log version and a levels version?** The variable `ntl_log` is defined as $\ln(1 + \mathrm{NTL}_i)$. It compresses right skewness and dampens extreme outliers in OLS/WLS regressions. However, as shown theoretically by Chen & Roth (2024), transformations of the form $\ln(1 + Y)$ are sensitive to the scaling unit of $Y$ when zeros are prevalent, because the estimate conflates the *extensive margin* and the *intensive margin*. The system therefore also exports `ntl_mean` and `ntl_sol` in levels, so researchers can estimate **Poisson Pseudo-Maximum Likelihood (PPML)** models as a robustness check.

### 5.2. Region–year panel data structure

For macroeconomic studies tracking district or provincial development across years, the system aggregates micro-level data into **a single observation row** per `(iso3, region_id, year, cell_size_m)` tuple. These aggregate indicators capture the **spatial structure of development**.

#### 1️⃣ Light inequality Gini coefficients

Building on the Night Light Development Index (NLDI) of Elvidge et al. (2012) and the satellite-based spatial inequality studies of Lessmann & Seidel (2017) and Mirza et al. (2021), the Gini coefficient measures how concentrated economic activity is:

$$
G = \frac{2 \sum_{i=1}^n i \cdot x_{(i)}}{n \sum_{i=1}^n x_{(i)}} - \frac{n + 1}{n}
$$

(where $x_{(1)} \le x_{(2)} \le \dots \le x_{(n)}$ are values sorted in non-decreasing order). Three variants are exported:

| Variable | Computed over | Measures |
| :--- | :--- | :--- |
| `gini_ntl_core_all` | All non-border core cells, dark cells included (so every cell has an identical area) | Overall spatial inequality |
| `gini_ntl_core_lit` | Lit core cells only | Inequality within illuminated areas |
| `gini_sol_all` | The cell sum of lights $\mathrm{SOL}_i$ across all cells | Concentration of total light |

#### 2️⃣ Hotspot area share and urban polycentricity

The variables `hh_area_share` and `hh_cluster_area_share` measure the share of regional land area falling inside:

- statistically significant `High-High` cells (`hh_area_share`), or
- contiguous `High-High` clusters meeting the minimum size threshold (`hh_cluster_area_share`).

$$
\mathrm{HH}_{\mathrm{share}} = \frac{\sum_{i \in \mathrm{HH}} A_i}{\sum_{i=1}^N A_i}
$$

This serves as a proxy for **de facto urbanization**, overcoming the limitations of administrative urban classifications. Combined with the number of independent hotspot clusters (`n_hh_clusters`) and the area of the largest cluster (`largest_hh_cluster_km2`), researchers can quantify transitions from monocentric to polycentric urban forms.

#### 3️⃣ Global spatial autocorrelation: Global Moran's I

This indicator is displayed in the Data tab of `app.py`. It is computed across all $N$ grid cells (including $\mathrm{NTL} = 0$ cells) using symmetric binary Queen contiguity weights (Moran, 1950):

$$
I_{\mathrm{global}} = \frac{N}{\sum_{i=1}^N \sum_{j=1}^N w_{ij}} \frac{\sum_{i=1}^N \sum_{j=1}^N w_{ij}(x_i - \bar{x})(x_j - \bar{x})}{\sum_{i=1}^N (x_i - \bar{x})^2}
$$

> [!WARNING]
> If $I_{\mathrm{global}} > E[I] = -\frac{1}{N-1}$ and is statistically significant ($p < 0.05$), standard OLS residuals violate spatial independence. Researchers then need spatial econometric specifications such as SAR, SEM, or SDM (LeSage & Pace, 2009), or Conley spatial-autocorrelation-robust standard errors (Conley, 1999).

#### 4️⃣ Internal clustering of illuminated areas: `moran_I_lit`

This indicator is exported in the panel CSV from `ntl/lisa_core.py`. It is the mean of Local Moran's I across tested lit cells:

$$
\bar{I}_{\mathrm{lit}} = \frac{1}{\lvert \mathrm{Focal} \rvert} \sum_{i \in \mathrm{Focal}} I_i
$$

It measures the intensity of spatial clustering within the electrified and urbanized footprint of the locality over time.

### 5.3. Region–year panel data dictionary

The tables below define all variables in the exported `ntl_lisa_panel.csv` file, grouped for easier lookup.

**🪪 Identifiers and scale**

| Variable name (Column) | Technical & econometric meaning |
| :--- | :--- |
| `iso3`, `region_id`, `region_label`, `year` | Administrative unit and time identifiers for the panel dataset. |
| `cell_size_m` | Square grid cell side length (meters): spatial scale control variable (MAUP). |
| `n_cells`, `n_cells_edge_masked` | Total grid cells in the locality and number of clipped border cells ($A_i < 0.99 \times (\mathrm{size}/1000)^2 \, \mathrm{km}^2$). |
| `n_cells_lit`, `n_cells_tested` | Number of lit cells ($\mathrm{NTL} > \mathrm{threshold}$) and core cells with sufficient neighbors tested in LISA. |
| `area_total_km2` | Total area of the locality summed across clipped grid cells ($\mathrm{km}^2$). |

**🔥 Light coverage and hotspots**

| Variable name (Column) | Technical & econometric meaning |
| :--- | :--- |
| `lit_area_share` | Share of territory with nighttime light signal ($\in [0, 1]$): proxy for electrification and infrastructure coverage. |
| `hh_area_share` | Share of total area falling inside statistically significant `High-High` hotspot cells. |
| `hh_area_share_of_tested` | Share of `High-High` area relative to the total area of tested core cells. |
| `hh_cluster_area_share` | Share of total area falling inside contiguous `High-High` clusters meeting `min_cluster_cells`. |
| `ll_area_share`, `hl_area_share`, `lh_area_share` | Share of total area classified as `Low-Low`, `High-Low`, and `Low-High`. |
| `n_hh_clusters` | Number of independent contiguous `High-High` clusters, a proxy for urban polycentricity. |
| `largest_hh_cluster_km2` | Area ($\mathrm{km}^2$) of the largest contiguous `High-High` cluster (primary urban core). |
| `hotspot_dummy` | Binary indicator (`1/0`): equals `1` if `n_hh_clusters > 0`. Ready for Difference-in-Differences (DiD) designs. |

**⚖️ Inequality and autocorrelation**

| Variable name (Column) | Technical & econometric meaning |
| :--- | :--- |
| `gini_ntl_core_all` | Radiance Gini coefficient across all non-border core cells (including dark cells), measuring overall spatial inequality. |
| `gini_ntl_core_lit` | Radiance Gini coefficient across lit core cells only, measuring internal inequality within illuminated areas. |
| `gini_sol_all` | Gini coefficient of cell sum of lights ($\mathrm{SOL}_i = \mathrm{NTL}_i \times A_i$) across all grid cells. |
| `moran_I_lit` | Mean Local Moran's I across tested lit cells, measuring urban spatial clustering. |

**🔁 Hyperparameters (reproducibility)**

| Variable name (Column) | Technical & econometric meaning |
| :--- | :--- |
| `p_cfg_*`, `p_floor`, `fdr_min_hits_needed` | Hyperparameter metadata recording the test configuration (`perms`, `alpha`, `fdr`, `log`, `lit_thr`, `edge_tol`, `min_nbr`, `min_cluster`) for scientific reproducibility. |

<sub>[↑ Back to top](#top)</sub>

---

<a id="s6"></a>

## 🚧 VI. System limitations and future extensions

### 6.1. Input data limitations

| # | Limitation | Cause and consequence |
| :---: | :--- | :--- |
| 1 | **Light spillover and reflection** | Because of the optical properties of the VIIRS DNB sensor and atmospheric scattering, light from high-intensity sources (seaports, industrial complexes, major bridges) tends to spill over into adjacent pixels or reflect off water surfaces (Elvidge et al., 2017; Gibson et al., 2021). This can slightly expand the boundaries of `High-High` clusters along coastlines and rivers. |
| 2 | **Clamping negatives to $0$** | Clamping negative radiance values to $0$ after stray-light correction keeps the data physically sensible, but reduces informational variance in sparsely populated rural areas where true illumination is near $0$ (Gibson et al., 2021). |
| 3 | **Mechanical autocorrelation on fine grids** | The native resolution of monthly VIIRS composites is approximately $463.83\text{ m}$, so a $500 \times 500\text{ m}$ grid cell covers roughly $1.16$ native pixels. Two adjacent grid cells can share parts of the same VIIRS pixel through fractional extraction (`exactextract`), which induces mechanical spatial autocorrelation. |

> [!TIP]
> **Recommendation for causal regressions:** use a grid size $\ge 1000\text{ m}$ and check robustness across multiple resolutions.

### 6.2. Hardware constraints

Deployment on free cloud infrastructure (~1GB RAM) caps simultaneous polygon processing at `MAX_CELLS` $= 150,000$ cells. This shapes the scale of analysis you can choose:

| Region scale | What works |
| :--- | :--- |
| Districts, counties, or small-to-medium provinces | Fine for ultra-fine resolution ($500\text{ m}$) |
| Large regions or national-scale analysis | Increase the grid resolution to $2000\text{ m} - 5000\text{ m}$, or run the engine on a local workstation |

### 6.3. Future extensions

1. **Multi-year calibrated VIIRS annual composites (Annual VNL V2).** Add the background-zeroed and gas-flare-filtered annual composites from the Earth Observation Group (`NOAA/VIIRS/DNB/ANNUAL_V21` / `V22`) (Elvidge et al., 2021) alongside the current monthly median composite pipeline, combined with year fixed effects for long-horizon panel regressions.

2. **Multi-period spatial Markov chains and space-time cointegration.** Extend the current two-period ($t_0 \rightarrow t_1$) dynamic module into a continuous multi-period panel time-series model (2014–2025) that incorporates spatial unit root tests.

<sub>[↑ Back to top](#top)</sub>

---

<a id="refs"></a>

## 📚 References

1. Anselin, L. (1995). Local Indicators of Spatial Association—LISA. *Geographical Analysis*, 27(2), 93–115. https://doi.org/10.1111/j.1538-4632.1995.tb00338.x

2. Baston, D. (2023). *exactextract: Fast and accurate raster/polygon zonal statistics* [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.11396419

3. Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing. *Journal of the Royal Statistical Society: Series B (Methodological)*, 57(1), 289–300. https://doi.org/10.1111/j.2517-6161.1995.tb02031.x

4. Bluhm, R., & Krause, M. (2022). Top lights: Bright cities and their contribution to economic development. *Journal of Development Economics*, 157, 102880. https://doi.org/10.1016/j.jdeveco.2022.102880

5. Bluhm, R., Dreher, A., Fuchs, A., Parks, B. C., Strange, A. M., & Tierney, M. J. (2025). Connective financing: Chinese infrastructure projects and the diffusion of economic activity in developing countries. *Journal of Urban Economics*, 145, 103730. https://doi.org/10.1016/j.jue.2024.103730

6. Borusyak, K., & Hull, P. (2023). Nonrandom Exposure to Exogenous Shocks. *Econometrica*, 91(6), 2155–2185. https://doi.org/10.3982/ECTA19367

7. Borusyak, K., Jaravel, X., & Spiess, J. (2024). Revisiting Event-Study Designs: Robust and Efficient Estimation. *The Review of Economic Studies*, 91(6), 3253–3285. https://doi.org/10.1093/restud/rdae007

8. Butts, K. (2024). Difference-in-Differences with Spatial Spillovers. *Working Paper / arXiv*. https://doi.org/10.48550/arXiv.2105.03737

9. Caldas de Castro, M., & Singer, B. H. (2006). Controlling the False Discovery Rate: A New Application to Account for Multiple and Dependent Tests in Local Statistics of Spatial Association. *Geographical Analysis*, 38(2), 180–208. https://doi.org/10.1111/j.0016-7363.2006.00682.x

10. Chen, J., & Roth, J. (2024). Logs with Zeros? Some Problems and Solutions. *The Quarterly Journal of Economics*, 139(2), 891–936. https://doi.org/10.1093/qje/qjad054

11. Conley, T. G. (1999). GMM estimation with cross sectional dependence. *Journal of Econometrics*, 92(1), 1–45. https://doi.org/10.1016/S0304-4076(98)00084-0

12. Donaldson, D., & Storeygard, A. (2016). The View from Above: Applications of Satellite Data in Economics. *Journal of Economic Perspectives*, 30(4), 171–198. https://doi.org/10.1257/jep.30.4.171

13. Duranton, G., & Puga, D. (2023). Urban Growth and Its Aggregate Implications. *Econometrica*, 91(6), 2219–2259. https://doi.org/10.3982/ECTA17936

14. Elvidge, C. D., Baugh, K. E., Anderson, S. J., Sutton, P. C., & Ghosh, T. (2012). The Night Light Development Index (NLDI): a spatially explicit measure of human development from satellite data. *Social Geography*, 7(1), 23–35. https://doi.org/10.5194/sg-7-23-2012

15. Elvidge, C. D., Baugh, K., Zhizhin, M., Hsu, F. C., & Ghosh, T. (2017). VIIRS night-time lights. *International Journal of Remote Sensing*, 38(21), 5860–5879. https://doi.org/10.1080/01431161.2017.1342050

16. Elvidge, C. D., Zhizhin, M., Ghosh, T., Hsu, F. C., & Taneja, J. (2021). Annual Time Series of Global VIIRS Nighttime Lights Derived from Monthly Averages: 2012 to 2019. *Remote Sensing*, 13(5), 922. https://doi.org/10.3390/rs13050922

17. Fotheringham, A. S., & Wong, D. W. S. (1991). The modifiable areal unit problem in multivariate statistical analysis. *Environment and Planning A: Economy and Space*, 23(7), 1025–1044. https://doi.org/10.1068/a231025

18. Gibson, J., Olivia, S., Boe-Gibson, G., & Li, C. (2021). Which night lights data should we use in economics, and where? *Journal of Development Economics*, 149, 102602. https://doi.org/10.1016/j.jdeveco.2020.102602

19. Heckman, J. J. (1979). Sample selection bias as a specification error. *Econometrica*, 47(1), 153–161. https://doi.org/10.2307/1912352

20. Henderson, J. V., Storeygard, A., & Weil, D. N. (2012). Measuring Economic Growth from Outer Space. *American Economic Review*, 102(2), 994–1028. https://doi.org/10.1257/aer.102.2.994

21. LeSage, J., & Pace, R. K. (2009). *Introduction to Spatial Econometrics*. Chapman and Hall/CRC. https://doi.org/10.1201/9781420064254

22. Lessmann, C., & Seidel, A. (2017). Regional inequality, convergence, and its determinants – A view from outer space. *European Economic Review*, 92, 110–132. https://doi.org/10.1016/j.euroecorev.2016.11.009

23. Mirza, M. U., Xu, C., van Bavel, B., van Nes, E. H., & Scheffer, M. (2021). Global inequality remotely sensed. *Proceedings of the National Academy of Sciences*, 118(18), e1919913118. https://doi.org/10.1073/pnas.1919913118

24. Moran, P. A. P. (1950). Notes on Continuous Stochastic Phenomena. *Biometrika*, 37(1/2), 17–23. https://doi.org/10.1093/biomet/37.1-2.17

25. Müller, U. K., & Watson, M. W. (2022). Spatial Correlation Robust Inference. *Econometrica*, 90(6), 2901–2935. https://doi.org/10.3982/ECTA19465

26. Müller, U. K., & Watson, M. W. (2024). Spatial Unit Roots and Spurious Regression. *Econometrica*, 92(5), 1661–1695. https://doi.org/10.3982/ECTA21654

27. Openshaw, S. (1984). *The Modifiable Areal Unit Problem*. Concepts and Techniques in Modern Geography (CATMOG), No. 38. Geo Books.

28. Rey, S. J., & Anselin, L. (2007). PySAL: A Python Library of Spatial Analytical Methods. *The Review of Regional Studies*, 37(1), 5–27. https://doi.org/10.52324/001c.8285

29. Rey, S. J., Arribas-Bel, D., & Wolf, L. J. (2023). *Geographic Data Science with Python*. Chapman and Hall/CRC. https://doi.org/10.1201/9780429292507

30. Vazquez-Bare, G. (2023). Identification and estimation of spillover effects in randomized experiments. *Journal of Econometrics*, 237(1), 105237. https://doi.org/10.1016/j.jeconom.2021.10.014
