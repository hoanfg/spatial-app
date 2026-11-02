<a id="top"></a>

# 🗂️ Technical specification: GADM v4.1 data extraction & country classification for spatial econometrics

| Item | Details |
| :--- | :--- |
| **Project** | Nighttime lights (NTL) data extractor & Spatial econometrics engine |
| **Document version** | 1.0 |
| **Objective** | Standardize global administrative boundaries from the GADM v4.1 database (`.gpkg`) into a consistent 3-level structure, for VIIRS nighttime radiance extraction and LISA/Moran's I testing. |
| **Related document** | [📘 Read the technical manual here](README.md) |

The output structure that the whole pipeline is built to produce:

```text
Country
└── Level 1 folder   (state / province)
    └── Level 2 GeoJSON file   (district / county)
```

> [!TIP]
> **⚡ The 20-second version**
>
> - **The problem:** GADM v4.1 is not as clean as it looks. Missing values are stored as the text `"NA"`, lakes show up as administrative units, some units share names, some countries have units that are far too small, and others are missing an intermediate level altogether.
> - **If you ignore it:** you get garbage folders, wrongly merged giant polygons, samples that mix several administrative levels, and distorted regression results.
> - **The fix:** don't guess. Use a **declarative rules table for each country group** (4 groups, see [Section 3](#s3)), and run every output file through **5 automated quality checks** (see [Section 4](#s4)).

<details>
<summary><b>📖 A few terms you will meet (click to expand)</b></summary>

<br>

| Term | Meaning |
| :--- | :--- |
| **GADM** | A database of global administrative boundaries. |
| **`.gpkg`** | A GeoPackage file holding spatial data, one per country (`gadm41_XXX.gpkg`). |
| **`ADM_ADM_1`, `ADM_ADM_2`, `ADM_ADM_3`** | Layers inside the `.gpkg` file, matching administrative levels 1, 2 and 3. |
| **`NAME_x`** | Name of the administrative unit at level *x*. Can repeat. |
| **`GID_x`** | **Unique** identifier of the unit at level *x*. |
| **`TYPE_x`, `ENGTYPE_x`** | Unit type (local and English), for example County, Independent City, Water body. |
| **ETL** | Extract – Transform – Load: the process of extracting, transforming and writing data. |

</details>

---

<a id="s1"></a>

## 🔍 1. Diagnosing the root causes of garbage data in GADM v4.1

When GeoPackage files (`gadm41_XXX.gpkg`) are processed automatically, there are 5 technical pitfalls that make conventional extraction scripts generate garbage data or distort spatial regression results.

### 🪤 Pitfall 1: the `"NA"` string (literal string `"NA"` vs. SQL `NULL`)

The GADM v4.1 database was exported from an R environment (`terra` / `sf`). There, many missing values in the `NAME_1`, `NAME_2`, `NAME_3`, `TYPE_2`, and `ENGTYPE_2` columns are not `NULL` (`NaN`) but are stored as the **text string `"NA"`** (or `"?"`, `"Unknown"`). Pandas' `.dropna()` therefore misses these rows completely, which leads to:

- A garbage folder named `NA` (when `NAME_1 == "NA"`).
- Dozens of unrelated urban districts (all sharing `NAME_2 == "NA"`) merged into one giant multipolygon weighing tens of MB.

### 🪤 Pitfall 2: inland water polygons (`Water body` / `Lake`)

In GADM v4.1, many large lakes, bays, or inland waters are cut into separate polygons in the `ADM_2` and `ADM_3` layers. Their `ENGTYPE_2` / `ENGTYPE_3` columns hold values such as `"Water body"`, `"Lake"`, and `"Inland water"`.

If these rows are not filtered out before exporting the files, the econometric model will put entire lakes into the analysis sample with a nighttime light radiance of $\mathrm{NTL} = 0$. The result is a severe bias in the light Gini coefficient and in economic density.

### 🪤 Pitfall 3: the administrative-unit name collision (when `GID_x` is not used)

If the extraction loop only calls `.unique()` on the `NAME_2` or `NAME_3` column, different administrative units that share the same Latin-transliterated name within one state/province get merged into a single `.geojson` file.

- **United States (`USA`).** Independent cities in Virginia, Maryland, and Missouri share names with the counties surrounding them. They have the same `NAME_2` and are distinguished only by `GID_2` and `ENGTYPE_2`:

  | Independent city | Same-named county |
  | :--- | :--- |
  | *Fairfax City* | *Fairfax County* |
  | *Baltimore City* | *Baltimore County* |
  | *St. Louis City* | *St. Louis County* |

- **China (`CHN`) and Vietnam (`VNM`).** When diacritics are removed or Pinyin transliteration is used in GADM, many districts/counties with different Chinese characters or administrative types (`Shi` vs `Xian`) end up with the same string in `NAME_3` / `NAME_2`.

> [!IMPORTANT]
> **Mandatory rule:** always group (`groupby`) by the unique identifier key `GID_x` (such as `GID_2`, `GID_3`), never by `NAME_x`. If two different `GID_x` values in the same folder have the same `NAME_x`, automatically append a suffix built from `ENGTYPE_x` or the `GID_x` code.

### 🪤 Pitfall 4: micro-fragmentation

| Parameter | Value |
| :--- | :--- |
| Native resolution of monthly VIIRS DNB imagery | $\approx 463.83 \text{ m}$ (pixel area $\approx 0.215 \text{ km}^2$) |
| Minimum number of grid cells for LISA/Moran's I to make meaningful inferences | $N \ge 30$ |
| Standard grids | $500 \text{ m}$ - $1000 \text{ m}$ |
| Ideal area of an analysis unit (district/county/city level) | $10 \text{ km}^2$ to $5,000 \text{ km}^2$ |
| Area of a unit at commune/ward level | $0.2 - 5 \text{ km}^2$ |

If a script automatically reads the deepest layer (`ADM_3` or `ADM_4`) for every country, countries such as Vietnam, France, Thailand, and Indonesia get pushed down to the commune/ward level. At that scale each unit is so small that LISA testing is crippled.

### 🪤 Pitfall 5: the urban-rural administrative hierarchy asymmetry

Some countries have large metropolitan areas directly under the central government, or urban counties with a missing intermediate level:

| Country | What shows up |
| :--- | :--- |
| `GBR` | Metropolitan counties and Unitary authorities have `NAME_2 == "NA"`. |
| `CHN` | The four centrally administered municipalities of Beijing, Shanghai, Tianjin, and Chongqing appear directly in `NAME_1`. |

<sub>[↑ Back to top](#top)</sub>

---

<a id="s2"></a>

## ⚖️ 2. Architectural trade-off analysis

The table below compares 3 architectural approaches for the data pipeline (🔴 weak, 🟡 acceptable, 🟢 strong):

| Evaluation criterion | Approach 1: Blind dynamic self-healing<br><sub>(automatically read the deepest layer + skip columns when encountering `'NA'`)</sub> | Approach 2: Simple strict extractor + front-end alias JSON<br><sub>(hard-coded extraction + name mapping in the UI)</sub> | ⭐ Approach 3 (recommended): Declarative rule-driven ETL<br><sub>(extraction controlled by a country rules table)</sub> |
| :--- | :--- | :--- | :--- |
| **Geometry quality** | 🔴 **Low:** large county-level polygons can easily be mixed with small commune/district-level polygons within the same country when only some rows have `NAME_2 == 'NA'`. | 🔴 **Low (if the source data is asymmetric):** the JSON file in the front end can only change display labels; it cannot split an incorrectly merged 37MB `NA` polygon already written to disk. | 🟢 **Complete:** fully resolves geometry merging/splitting (`dissolve` by `GID`) at the moment the `.geojson` file is created. |
| **Econometric consistency** | 🔴 **Poor:** causes *cross-level mixing* (rows in the panel are not at the same administrative level, violating the assumption of homogeneous observational units). | 🟡 **Good** for homogeneous countries (`CHN`, `VNM`), but **fails** for hybrid cases (`GBR`, `TWN`). | 🟢 **Optimal:** ensures that 100% of `.geojson` files within a country represent economically equivalent units. |
| **Runtime performance on Streamlit Cloud (~1GB RAM)** | 🔴 **Risk of memory overflow:** generates tens of thousands of commune/ward-level files for countries with `ADM_3`/`ADM_4`. | 🟡 **Fast:** the front end is lightweight, but a huge JSON file with tens of thousands of rows must be maintained if each district name needs to be corrected. | 🟢 **Optimal:** all computationally intensive processing is done offline, once. `app.py` keeps its current, very light folder-reading structure. |
| **Maintainability** | 🔴 Hard to control hidden errors when adding new countries. | 🟡 Both the extraction script and the JSON file in the front end must be modified. | 🟢 Only one rule declaration (5 attributes) needs to be added to the `COUNTRY_RULES` dictionary in the ETL script. |

> [!IMPORTANT]
> **Architectural conclusion.** Do not place geometry-fixing logic in the front end, and do not let the extractor blindly guess the deepest layer. Use a **declarative rule-driven extractor** that states explicitly, for each country group:
>
> | Attribute | What it specifies |
> | :--- | :--- |
> | `layer` | Which layer to read |
> | `folder_expr` | Which column is used for the folder |
> | `file_expr` | Which column is used for the file |
> | `gid_col` | The unique grouping key |

<sub>[↑ Back to top](#top)</sub>

---

<a id="s3"></a>

## 🌍 3. GADM v4.1 country classification table

All countries and territories (matching the `COUNTRY_NAMES` list in `app.py`) are classified into **4 structural groups**:

| Group | Name | Used for | Layer read | Folder | File |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | `STANDARD_ADM2` | ~85% of countries, level 2 is a standard district/county | `ADM_ADM_2` | `NAME_1` | `NAME_2` |
| **2** | `SHIFTED_ADM3_PREFECTURE` | Level 1 is too broad and districts/counties sit at level 3 (typical case: `CHN`) | `ADM_ADM_3` | Prefecture level (see [Group 2](#group2)) | `NAME_3` |
| **3** | `ASYMMETRIC_HYBRID` | Missing intermediate level `NAME_2 = "NA"` (`GBR`, `TWN`) | `ADM_ADM_3` (for `GBR`; `TWN` has its own setup) | `NAME_1` (for `GBR`) | `COALESCE(NAME_3, NAME_2)` (for `GBR`) |
| **4** | `SHALLOW_ADM1_CITY_STATE` | City-states and small countries that only use level 1 | `ADM_ADM_1` | Country name or a larger region | `NAME_1` |

### 🟦 Group 1: `STANDARD_ADM2` (standard Level 2, covering ~85% of countries)

**Characteristics:** Level 1 (`NAME_1`) is a state/province/centrally administered city. Level 2 (`NAME_2`) is a district/county/county-equivalent/city within a province, covers 100% of the territory, and has an ideal area scale for the NTL grid (grid resolution $500 \text{ m}$ - $2000 \text{ m}$).

**Extraction configuration:**

| Parameter | Value |
| :--- | :--- |
| `layer` | `ADM_ADM_2` |
| Folder (State/Province) | `NAME_1` |
| File (District/County) | `NAME_2` (group by `GID_2`; use `ENGTYPE_2` to distinguish duplicate `NAME_2` values) |

**Applicable countries:**

<details open>
<summary><b>🌏 Southeast Asia</b></summary>

<br>

| Code | Country | Level 1 (folder) | Level 2 (file) |
| :---: | :--- | :--- | :--- |
| `VNM` | Vietnam | 63 provinces | 705 districts |
| `THA` | Thailand | 77 provinces | 928 Amphoe/Khet |
| `IDN` | Indonesia | 34 provinces | 514 Kabupaten/Kota |
| `MYS` | Malaysia | 16 states | 160 Daerah |
| `PHL` | Philippines | 81 provinces + Metro Manila | 1,634 municipalities |
| `KHM` | Cambodia | 25 provinces | 197 districts |
| `LAO` | Laos | 18 provinces | 148 districts |
| `MMR` | Myanmar | 15 states/regions | 330 townships |
| `TLS` | Timor-Leste | 13 municipalities | 65 subdistricts |

</details>

<details>
<summary><b>🏯 East Asia & South Asia</b></summary>

<br>

| Code | Country | Level 1 (folder) | Level 2 (file) |
| :---: | :--- | :--- | :--- |
| `JPN` | Japan | 47 prefectures | ~1,741 Shi/Ku/Machi/Mura |
| `KOR` | South Korea | 17 provinces/cities | ~250 Si/Gun/Gu |
| `PRK` | North Korea | — | — |
| `MNG` | Mongolia | 22 provinces | 339 Sums |
| `IND` | India | 36 states/UTs | ~676 districts |
| `BGD` | Bangladesh | 8 Divisions | 64 Districts; or `ADM_3` for 544 Upazilas |
| `PAK` | Pakistan | 8 Level 1 units | ~36 Divisions in `ADM_2` or ~160 Districts in `ADM_3` |
| `LKA` | Sri Lanka | 25 Districts in `ADM_1` | 331 DS Divisions in `ADM_2` |
| `NPL` | Nepal | — | — |

</details>

<details>
<summary><b>🗽 The Americas</b></summary>

<br>

| Code | Country | Level 1 (folder) | Level 2 (file) |
| :---: | :--- | :--- | :--- |
| `USA` | United States | 50 states + DC | 3,143 Counties/Independent Cities |
| `CAN` | Canada | 13 provinces/territories | 293 Census Divisions |
| `MEX` | Mexico | 32 states | 2,469 Municipios |
| `BRA` | Brazil | 27 states | 5,570 Municípios |
| `ARG` | Argentina | 24 provinces | 528 Departamentos/Partidos |
| `CHL` | Chile | 16 regions | 56 provinces in `ADM_2` or 346 Comunas in `ADM_3` |
| `COL` | Colombia | 33 regions | 1,122 Municipios |
| `PER` | Peru | 26 regions | 196 Provincias |
| `VEN`, `CUB` | Venezuela, Cuba | — | — |

</details>

<details>
<summary><b>🏰 Europe</b></summary>

<br>

| Code | Country | Level 1 (folder) | Level 2 (file) |
| :---: | :--- | :--- | :--- |
| `DEU` | Germany | 16 states | 401 Kreise/Kreisfreie Städte |
| `FRA` | France | 13 regions | 96 Départements in `ADM_2` |
| `ITA` | Italy | 20 regions | 107 provinces/metropolitan cities in `ADM_2` |
| `ESP` | Spain | 17 autonomous communities | 52 provinces in `ADM_2` or 326 Comarcas in `ADM_3` |
| `POL` | Poland | 16 provinces | 380 Powiaty |
| `NLD` | Netherlands | 12 provinces | 342 Gemeenten |
| `BEL` | Belgium | 3 regions | 11 provinces/Arrondissements |
| `CHE` | Switzerland | 26 Cantons | 143 Bezirke |
| `AUT` | Austria | 9 states | 94 Bezirke |
| `SWE` | Sweden | 21 counties | 290 Kommuner |
| `NOR` | Norway | 11 counties | 356 Kommuner |
| `DNK` | Denmark | 5 regions | 99 Kommuner |
| `RUS` | Russia | ~85 federal subjects | ~2,350 Raions/Cities |
| `TUR` | Turkey | 81 provinces | 973 Ilçe |
| `CZE`, `HUN`, `ROU`, `BGR`, `GRC`, `PRT`, `FIN`, `UKR` | — | — | — |

</details>

<details>
<summary><b>🦘 Oceania, the Middle East & Africa</b></summary>

<br>

| Code | Country | Level 1 (folder) | Level 2 (file) |
| :---: | :--- | :--- | :--- |
| `AUS` | Australia | 8 states/territories | 562 Local Government Areas |
| `NZL` | New Zealand | 16 regions | 67 Territorial Authorities |
| `NGA` | Nigeria | 37 states | 774 LGAs |
| `SAU`, `EGY`, `ZAF`, `KEN`, `ETH`, `MAR`, `DZA`, `GHA`, `TZA`, `KAZ`, `UZB`, `IRN`, `IRQ` | — | — | — |

</details>

---

<a id="group2"></a>

### 🟧 Group 2: `SHIFTED_ADM3_PREFECTURE` (shifted Level 3: prefecture-level unit as folder, district/county as file)

**Characteristics:**

- `ADM_1` is too broad (a population of 50–120 million, comparable to a European country).
- `ADM_2` consists of prefecture-level cities (such as Shenzhen, Guangzhou, Wuhan, Suzhou) or large subdivisions.
- The core urban districts and counties (`Qu` / `Xian` / `Xianjishi`) are located at **`ADM_3`**.

#### 🇨🇳 Most representative case: China (`CHN`)

If exported at `ADM_2`, the entire city of Shenzhen or Guangzhou would be represented by a single file. It would then be impossible to analyze differences between core districts (Nanshan, Futian, Tianhe) and peripheral areas.

**Handling exceptions for the 4 centrally administered municipalities (`Beijing`, `Shanghai`, `Tianjin`, `Chongqing`) and counties directly under provinces (`NAME_2 == "NA"`).** In these 4 municipalities, the city name appears directly in `NAME_1`. The most accurate folder-naming formula for `CHN` is therefore:

| Case | Folder |
| :--- | :--- |
| `NAME_1` belongs to `{"Beijing", "Shanghai", "Tianjin", "Chongqing"}`, or `NAME_2` is `"NA"` / matches `NAME_1` | `NAME_1` |
| The remaining 27 provinces/autonomous regions | `NAME_1 + " - " + NAME_2` (e.g., `Guangdong - Shenzhen`, `Guangdong - Guangzhou`, `Jiangsu - Suzhou`) |

This naming convention lets users search by province easily in the Streamlit selector while keeping each prefecture-level city separate. The files inside contain all districts/counties in `NAME_3` (grouped by `GID_3`).

#### 🌐 Other countries that may use Group 2 (or an `ADM_3` configuration)

| Code | To analyze at the level of... | Instead of... | Setup |
| :---: | :--- | :--- | :--- |
| `PAK` | 160 `Districts` in `ADM_3` | 36 `Divisions` in `ADM_2` | Folder = `NAME_1`, File = `NAME_3` |
| `BGD` | 544 `Upazilas` in `ADM_3` | 64 `Districts` in `ADM_2` | — |
| `FRA` | 333 `Arrondissements` in `ADM_3` | — | Folder = `NAME_2` (Département) |

---

### 🟨 Group 3: `ASYMMETRIC_HYBRID` (asymmetric / missing intermediate level `NAME_2 = "NA"`)

**Characteristics:** a hybrid administrative system that combines the two-tier shire county model with the single-tier model (Single-tier Unitary Authorities / Metropolitan Boroughs).

#### 🇬🇧 Case 1: United Kingdom (`GBR`)

**Actual structure in `gadm41_GBR.gpkg`:**

| Layer | Contents |
| :--- | :--- |
| `ADM_ADM_1` | The 4 constituent countries: `England`, `Scotland`, `Wales`, `Northern Ireland`. |
| `ADM_ADM_2` | Only two-tier rural counties (such as `Kent`, `Essex`, `West Sussex`). All 33 boroughs of Greater London, the 36 districts of the 6 metropolitan counties (Greater Manchester, West Midlands, Merseyside, South Yorkshire, West Yorkshire, Tyne and Wear), all Unitary Authorities in England, and many areas of Scotland/Wales are assigned `NAME_2 = "NA"`. |
| `ADM_ADM_3` | **100% of the standard local government districts/counties** (Local Authority Districts / London Boroughs / Metropolitan Districts / Unitary Authorities / Council Areas) across the United Kingdom. Where `NAME_2` is missing (`"NA"`), the district name is in `NAME_3`. In a few small single-tier counties where `NAME_3` is missing (`"NA"`), the name is in `NAME_2`. |

**Standard extraction solution for `GBR`:**

| Parameter | Value |
| :--- | :--- |
| Layer read | **`ADM_ADM_3`** |
| Folder (State/Region) | `NAME_1` (`England`, `Scotland`, `Wales`, `Northern Ireland`). To subdivide `England` by county, use `COALESCE(NAME_2, "England_Unitary_and_Metro")`. To remain consistent with the 4 constituent countries in your current interface, set Folder = `NAME_1`. |
| File (District/Borough) | The coalescing function **`COALESCE(NAME_3, NAME_2)`** (take `NAME_3` if valid; if `NAME_3` is `"NA"`, fall back to `NAME_2`), grouped by the unique key `COALESCE(GID_3, GID_2)`. |

> [!NOTE]
> **Result:** no London or Manchester districts are lost, no 37MB `NA` polygons are generated, and 100% of the exported files represent local authority districts at the same administrative level.

#### 🇹🇼 Case 2: Taiwan (`TWN`)

In GADM v4.1, some counties/cities have a level mismatch between `NAME_1` and `NAME_2` (because `NAME_1` holds the two nominal provinces `Fujian` and `Taiwan` alongside the centrally administered cities).

**Solution for `TWN`:** read Taiwan's deepest layer (`ADM_ADM_2` or `ADM_ADM_3`, depending on the packaged version).

| Parameter | Value |
| :--- | :--- |
| Folder | `COALESCE(NAME_2, NAME_1)`: 22 counties/cities such as *Taipei, New Taipei, Taichung, Kaohsiung, Hsinchu* |
| File | The next level: 368 districts/townships/towns (*Qu/Xiang/Zhen*) |

---

### 🟥 Group 4: `SHALLOW_ADM1_CITY_STATE` (city-states & small countries using Level 1 only)

**Characteristics:** the country is small, or is an urban city-state. The `ADM_ADM_2` layer either does not exist in the `.gpkg`, or, if it does, contains only tiny neighborhood-level units of a few hundred square meters.

**Extraction configuration:**

| Parameter | Value |
| :--- | :--- |
| Layer read | **`ADM_ADM_1`** (or an automatic fallback to `ADM_ADM_1` when `ADM_ADM_2` is unavailable) |
| Folder | Country name (`COUNTRY` / `NAME_0`) or a larger region |
| File | `NAME_1` (group by `GID_1`) |

**Applicable countries:**

| Code | Country | Details |
| :---: | :--- | :--- |
| `SGP` | Singapore | 5 planning areas in `ADM_1` |
| `HKG` | Hong Kong | 18 administrative districts directly in `ADM_1` |
| `MAC` | Macau | Areas located in `ADM_1` |
| `BRN` | Brunei | 4 Daerah districts in `ADM_1`, or use `ADM_2` for 38 Mukim |
| `QAT` | Qatar | 8 Baladiyat municipalities in `ADM_1` |
| `MDV` | Maldives | 21 Atolls in `ADM_1` |
| `ISR` | Israel | 6 Districts in `ADM_1`, or 15 Sub-districts in `ADM_2` |
| `IRL` | Ireland | 26 traditional Counties in `ADM_1`; the `ADM_2` layer contains Municipal Districts |

<sub>[↑ Back to top](#top)</sub>

---

<a id="s4"></a>

## ✅ 4. Output data quality assurance procedure

Before being written to disk for use in `app.py`, every `.geojson` file must pass **5 automated validation checks** in the extraction script:

```mermaid
flowchart LR
    S["📥 Data from<br/>.gpkg"] --> C1["1️⃣ Garbage<br/>strings"]
    C1 --> C2["2️⃣ Hydrological<br/>filter"]
    C2 --> C3["3️⃣ Merge<br/>by GID"]
    C3 --> C4["4️⃣ No duplicate-name<br/>overwrites"]
    C4 --> C5["5️⃣ Minimum<br/>area"]
    C5 --> G["📄 Valid<br/>.geojson"]
```

### 1️⃣ Check 1: garbage strings

Every value in the set `{"NA", "N/A", "NULL", "NONE", "UNKNOWN", "?", "", "NAN"}` (case-insensitive, with surrounding whitespace trimmed) is converted to an actual `None` before processing. Every row with `NAME_1 is None` (such as the `NA` state in `gadm41_GBR.gpkg`) is removed, or reassigned from a child level if that is valid.

### 2️⃣ Check 2: hydrological filter

Completely remove polygons whose `TYPE_x` or `ENGTYPE_x` contains any of the keywords `Water body`, `Lake`, `Inland water`, `Sea`, or `Estuary`.

### 3️⃣ Check 3: geometry merging by identifier

Fix self-intersections with `shapely.make_valid()`, then merge (`dissolve`) by the correct target `GID`, so that one administrative unit corresponds to exactly one `.geojson` file.

### 4️⃣ Check 4: prevent overwriting files with duplicate names

If two units with different `GID` codes but the same display name exist in the same province/state folder (e.g., *Fairfax County* and *Fairfax City*), the system automatically appends a distinguishing suffix taken from `ENGTYPE_x`:

```text
USA_Virginia_Fairfax_County.geojson
USA_Virginia_Fairfax_Independent_City.geojson
```

This naming is compatible with the `list_counties()` and `split_county()` functions in `app.py`.

### 5️⃣ Check 5: minimum area check for VIIRS

Issue a warning if a polygon has an area of $< 0.25 \text{ km}^2$, which is smaller than one $500 \times 500 \text{ m}$ grid cell.

<sub>[↑ Back to top](#top)</sub>
