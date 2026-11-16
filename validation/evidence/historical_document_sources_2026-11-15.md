# Historical document sources — 15 November 2026

These are original document bytes retained for audit provenance. Current guidance is in the README pairs at the repository root, docs/ and validation/. Time-specific pending statements below are historical.

---

## Source: docs/GADM_v41 pipeline specification.md

<!-- BEGIN ORIGINAL -->
<a id="top"></a>

# 🗂️ Technical specification: GADM v4.1 data extraction & country classification for spatial econometrics

| Item | Details |
| :--- | :--- |
| **Project** | Nighttime lights (NTL) data extractor & Spatial econometrics engine |
| **Objective** | Standardize global administrative boundaries from the GADM v4.1 database (`.gpkg`) into a consistent 3-level structure, for VIIRS nighttime radiance extraction and LISA/Moran's I testing. |
| **Related document** | [📘 Read the technical manual here](https://github.com/hoanfg/spatial-app/blob/main/README.md) |

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
> **Architectural conclusion.** Do not place geometry-fixing logic in the front end, and do not let the extractor blindly guess the deepest layer. Use a **declarative rule-driven extractor** specifying 5 attributes for each country group:
>
> | Attribute | What it specifies |
> | :--- | :--- |
> | `layer` | Which layer to read |
> | `folder_expr` | Which column is used for the folder |
> | `file_expr` | Which column is used for the file |
> | `gid_col` | The unique grouping key |
> | `type_col` / `ENGTYPE_x` | Administrative type column (for hydrological filtering and duplicate-name disambiguation) |

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

<!-- END ORIGINAL -->

---

## Source: docs/GADM_v41-vi pipeline specification.md

<!-- BEGIN ORIGINAL -->
<a id="top"></a>

# 🗂️ Đặc tả kỹ thuật: trích xuất dữ liệu GADM v4.1 & phân loại quốc gia cho kinh tế lượng không gian

| Hạng mục | Nội dung |
| :--- | :--- |
| **Dự án** | Nighttime lights (NTL) data extractor & Spatial econometrics engine |
| **Mục tiêu** | Chuẩn hóa ranh giới hành chính toàn cầu từ cơ sở dữ liệu GADM v4.1 (`.gpkg`) sang cấu trúc 3 cấp đồng nhất, phục vụ trích xuất bức xạ đêm VIIRS và kiểm định LISA/Moran's I. |
| **Tài liệu liên quan** | [📘 Đọc sổ tay kỹ thuật tại đây](https://github.com/hoanfg/spatial-app/blob/main/README-vi.md) |

Cấu trúc đầu ra mà toàn bộ quy trình hướng tới:

```text
Quốc gia
└── Thư mục Cấp 1   (tỉnh / bang)
    └── Tệp GeoJSON Cấp 2   (quận / huyện / hạt)
```

> [!TIP]
> **⚡ Đọc nhanh trong 20 giây**
>
> - **Vấn đề:** dữ liệu GADM v4.1 không "sạch" như vẻ ngoài. Có giá trị khuyết bị lưu thành chữ `"NA"`, có cả hồ nước bị tính như một đơn vị hành chính, có những đơn vị trùng tên, có nước thì cấp hành chính quá nhỏ, có nước lại thiếu hẳn một cấp trung gian.
> - **Nếu bỏ qua:** thư mục rác, đa giác khổng lồ ghép sai, mẫu phân tích lẫn lộn nhiều cấp hành chính, và kết quả hồi quy lệch.
> - **Cách giải:** không đoán mò, mà dùng một **bảng quy tắc khai báo theo từng nhóm quốc gia** (4 nhóm, xem [Mục 3](#s3)), rồi cho mọi tệp đầu ra đi qua **5 lần kiểm định chất lượng** (xem [Mục 4](#s4)).

<details>
<summary><b>📖 Vài ký hiệu hay gặp (bấm để mở)</b></summary>

<br>

| Ký hiệu | Ý nghĩa |
| :--- | :--- |
| **GADM** | Cơ sở dữ liệu ranh giới hành chính toàn cầu. |
| **`.gpkg`** | Tệp GeoPackage chứa dữ liệu không gian, mỗi quốc gia một tệp (`gadm41_XXX.gpkg`). |
| **`ADM_ADM_1`, `ADM_ADM_2`, `ADM_ADM_3`** | Các lớp (layer) trong tệp `.gpkg`, ứng với cấp hành chính 1, 2, 3. |
| **`NAME_x`** | Tên đơn vị hành chính ở cấp *x*. Có thể trùng nhau. |
| **`GID_x`** | Mã định danh **duy nhất** của đơn vị ở cấp *x*. |
| **`TYPE_x`, `ENGTYPE_x`** | Loại hình đơn vị (bản địa và bản tiếng Anh), ví dụ County, Independent City, Water body. |
| **ETL** | Extract – Transform – Load: quy trình trích xuất, biến đổi và ghi dữ liệu. |

</details>

---

<a id="s1"></a>

## 🔍 1. Chẩn đoán nguyên nhân gốc rễ của dữ liệu rác trong GADM v4.1

Khi xử lý tự động các tệp GeoPackage (`gadm41_XXX.gpkg`), có 5 cái bẫy kỹ thuật khiến các kịch bản trích xuất thông thường sinh ra dữ liệu rác, hoặc làm méo kết quả hồi quy không gian.

### 🪤 Bẫy 1: chuỗi `"NA"` (literal string `"NA"` so với SQL `NULL`)

Cơ sở dữ liệu GADM v4.1 được xuất từ môi trường R (`terra` / `sf`). Ở đó, rất nhiều giá trị khuyết trong các cột `NAME_1`, `NAME_2`, `NAME_3`, `TYPE_2`, `ENGTYPE_2` không phải `NULL` (`NaN`) mà được lưu thành **chuỗi văn bản `"NA"`** (hoặc `"?"`, `"Unknown"`). Hàm `.dropna()` của Pandas vì thế bỏ lọt hoàn toàn những dòng này, và hậu quả là:

- Sinh ra một thư mục rác tên `NA` (khi `NAME_1 == "NA"`).
- Gộp hàng chục quận đô thị chẳng liên quan gì nhau (cùng có `NAME_2 == "NA"`) thành một siêu đa giác nặng hàng chục MB.

### 🪤 Bẫy 2: đa giác mặt nước nội địa (`Water body` / `Lake`)

Trong GADM v4.1, nhiều hồ lớn, vịnh hoặc vùng nước nội thủy được cắt thành các đa giác riêng ở lớp `ADM_2` và `ADM_3`. Cột `ENGTYPE_2` / `ENGTYPE_3` của chúng mang các giá trị như `"Water body"`, `"Lake"`, `"Inland water"`.

Nếu không lọc bỏ những dòng này trước khi xuất file, mô hình kinh tế lượng sẽ đưa cả mặt hồ vào mẫu phân tích với bức xạ $\mathrm{NTL} = 0$. Hệ quả là hệ số Gini ánh sáng và mật độ kinh tế bị lệch nghiêm trọng.

### 🪤 Bẫy 3: trùng tên đơn vị hành chính (name collision khi không dùng `GID_x`)

Nếu vòng lặp trích xuất chỉ dùng `.unique()` trên cột `NAME_2` hoặc `NAME_3`, các đơn vị hành chính khác nhau nhưng cùng tên phiên âm Latinh trong một bang/tỉnh sẽ bị gộp vào một tệp `.geojson` duy nhất.

- **Hoa Kỳ (`USA`).** Các thành phố độc lập (*Independent cities*) ở Virginia, Maryland và Missouri trùng tên với hạt bao quanh chúng. Chúng có cùng `NAME_2`, chỉ phân biệt được qua `GID_2` và `ENGTYPE_2`:

  | Thành phố độc lập | Hạt trùng tên |
  | :--- | :--- |
  | *Fairfax City* | *Fairfax County* |
  | *Baltimore City* | *Baltimore County* |
  | *St. Louis City* | *St. Louis County* |

- **Trung Quốc (`CHN`) và Việt Nam (`VNM`).** Khi bỏ dấu hoặc phiên âm Pinyin trong GADM, nhiều quận/huyện khác chữ Hán, hoặc khác cấp loại hình (`Shi` so với `Xian`), lại có cùng chuỗi ký tự trong `NAME_3` / `NAME_2`.

> [!IMPORTANT]
> **Quy tắc bắt buộc:** luôn nhóm (`groupby`) theo khóa định danh duy nhất `GID_x` (như `GID_2`, `GID_3`), không nhóm theo `NAME_x`. Nếu trong cùng một thư mục có hai `GID_x` khác nhau nhưng trùng `NAME_x`, tự động thêm hậu tố bằng `ENGTYPE_x` hoặc mã `GID_x`.

### 🪤 Bẫy 4: phân mảnh vi mô

| Thông số | Giá trị |
| :--- | :--- |
| Độ phân giải gốc của ảnh VIIRS DNB hàng tháng | $\approx 463.83 \text{ m}$ (diện tích một điểm ảnh $\approx 0.215 \text{ km}^2$) |
| Số ô lưới tối thiểu để kiểm định LISA/Moran's I suy diễn có ý nghĩa | $N \ge 30$ |
| Lưới tiêu chuẩn | $500 \text{ m}$ - $1000 \text{ m}$ |
| Diện tích lý tưởng của một đơn vị phân tích (cấp Quận/Huyện/Thành phố) | $10 \text{ km}^2$ đến $5,000 \text{ km}^2$ |
| Diện tích đơn vị ở cấp Xã/Phường | $0.2 - 5 \text{ km}^2$ |

Nếu kịch bản cứ tự động đọc lớp sâu nhất (`ADM_3` hoặc `ADM_4`) cho mọi quốc gia, các nước như Việt Nam, Pháp, Thái Lan, Indonesia sẽ bị đẩy xuống cấp Xã/Phường. Ở quy mô đó, mỗi đơn vị quá nhỏ và kiểm định LISA gần như tê liệt.

### 🪤 Bẫy 5: bất đối xứng phân cấp giữa đô thị và nông thôn

Một số quốc gia có đại đô thị trực thuộc trung ương, hoặc hạt đô thị bị khuyết cấp trung gian:

| Quốc gia | Biểu hiện |
| :--- | :--- |
| `GBR` | Các Metropolitan counties và Unitary authorities có `NAME_2 == "NA"`. |
| `CHN` | 4 thành phố trực thuộc trung ương (Bắc Kinh, Thượng Hải, Thiên Tân, Trùng Khánh) nằm ngay ở `NAME_1`. |

<sub>[↑ Về đầu trang](#top)</sub>

---

<a id="s2"></a>

## ⚖️ 2. Đánh đổi kiến trúc (architectural trade-off analysis)

Bảng dưới đây so sánh 3 phương án kiến trúc cho đường ống dữ liệu (🔴 yếu, 🟡 tạm được, 🟢 tốt):

| Tiêu chí đánh giá | Phương án 1: Blind dynamic self-healing<br><sub>(tự động đọc lớp sâu nhất + nhảy cột khi gặp `'NA'`)</sub> | Phương án 2: Simple strict extractor + front-end alias JSON<br><sub>(cắt cứng + ánh xạ tên ở UI)</sub> | ⭐ Phương án 3 (khuyến nghị): Declarative rule-driven ETL<br><sub>(trích xuất điều khiển bằng bảng quy tắc quốc gia)</sub> |
| :--- | :--- | :--- | :--- |
| **Chất lượng hình học** | 🔴 **Thấp:** dễ trộn đa giác cấp Hạt (lớn) với cấp Xã/Quận (nhỏ) trong cùng một quốc gia, khi chỉ một số dòng có `NAME_2 == 'NA'`. | 🔴 **Thấp (nếu dữ liệu gốc bất đối xứng):** file JSON ở front-end chỉ đổi được nhãn hiển thị, không thể tách một đa giác `NA` 37MB đã bị gộp sai dưới ổ cứng. | 🟢 **Triệt để:** xử lý dứt điểm việc gộp/tách hình học (`dissolve` theo `GID`) ngay ở bước tạo file `.geojson`. |
| **Tính đồng nhất kinh tế lượng** | 🔴 **Kém:** gây hiện tượng *cross-level mixing* (các dòng trong bảng panel không cùng cấp hành chính, vi phạm giả định đồng nhất đơn vị quan sát). | 🟡 **Tốt** với các nước đồng nhất (`CHN`, `VNM`), nhưng **thất bại** với các nước lai ghép (`GBR`, `TWN`). | 🟢 **Tối ưu:** đảm bảo 100% các tệp `.geojson` trong một quốc gia đại diện cho các đơn vị kinh tế tương đương. |
| **Hiệu năng runtime trên Streamlit Cloud (~1GB RAM)** | 🔴 **Rủi ro tràn bộ nhớ:** sinh ra hàng chục ngàn file cấp xã/phường cho các nước có `ADM_3`/`ADM_4`. | 🟡 **Nhanh:** front-end nhẹ, nhưng phải duy trì một file JSON khổng lồ hàng chục ngàn dòng nếu muốn sửa tên từng quận. | 🟢 **Tối ưu nhất:** toàn bộ chi phí xử lý nặng làm offline đúng 1 lần. `app.py` giữ nguyên cấu trúc đọc thư mục cực nhẹ hiện tại. |
| **Khả năng bảo trì** | 🔴 Khó kiểm soát lỗi ngầm khi thêm quốc gia mới. | 🟡 Phải sửa cả script trích xuất lẫn file JSON ở front-end. | 🟢 Chỉ cần thêm 1 dòng khai báo quy tắc (5 thuộc tính) vào từ điển `COUNTRY_RULES` trong script ETL. |

> [!IMPORTANT]
> **Kết luận kiến trúc.** Không đặt logic chữa lỗi hình học ở front-end, và không để trình trích xuất tự đoán lớp sâu nhất một cách mù quáng. Hãy dùng **trình trích xuất điều khiển bằng quy tắc khai báo** với đủ 5 thuộc tính cho mỗi nhóm quốc gia:
>
> | Thuộc tính | Quy định |
> | :--- | :--- |
> | `layer` | Đọc lớp nào |
> | `folder_expr` | Cột nào làm thư mục |
> | `file_expr` | Cột nào làm tệp |
> | `gid_col` | Khóa định danh nhóm duy nhất |
> | `type_col` / `ENGTYPE_x` | Cột loại hình đơn vị (để lọc đa giác mặt nước và gắn hậu tố phân biệt khi trùng tên) |

<sub>[↑ Về đầu trang](#top)</sub>

---

<a id="s3"></a>

## 🌍 3. Bảng phân loại quốc gia GADM v4.1

Toàn bộ các quốc gia và vùng lãnh thổ (khớp với danh mục `COUNTRY_NAMES` trong `app.py`) được phân vào **4 nhóm cấu trúc**:

| Nhóm | Tên | Dùng cho | Lớp đọc | Thư mục | Tệp |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | `STANDARD_ADM2` | Chiếm ~85% quốc gia, cấp 2 là quận/huyện chuẩn | `ADM_ADM_2` | `NAME_1` | `NAME_2` |
| **2** | `SHIFTED_ADM3_PREFECTURE` | Cấp 1 quá rộng, quận/huyện nằm ở cấp 3 (điển hình: `CHN`) | `ADM_ADM_3` | Cấp địa khu (xem [Nhóm 2](#nhom2)) | `NAME_3` |
| **3** | `ASYMMETRIC_HYBRID` | Khuyết cấp trung gian `NAME_2 = "NA"` (`GBR`, `TWN`) | `ADM_ADM_3` (cho `GBR`; `TWN` có cấu hình riêng) | `NAME_1` (cho `GBR`) | `COALESCE(NAME_3, NAME_2)` (cho `GBR`) |
| **4** | `SHALLOW_ADM1_CITY_STATE` | Thành bang và quốc gia nhỏ chỉ dùng cấp 1 | `ADM_ADM_1` | Tên quốc gia hoặc vùng lớn | `NAME_1` |

### 🟦 Nhóm 1: `STANDARD_ADM2` (chuẩn cấp 2, chiếm ~85% quốc gia)

**Đặc điểm:** Cấp 1 (`NAME_1`) là Bang / Tỉnh / Thành phố trực thuộc trung ương. Cấp 2 (`NAME_2`) là Quận / Huyện / Hạt / Thành phố thuộc tỉnh, phủ kín 100% lãnh thổ và có quy mô diện tích lý tưởng cho lưới NTL (cạnh ô lưới $500 \text{ m}$ - $2000 \text{ m}$).

**Cấu hình trích xuất:**

| Tham số | Giá trị |
| :--- | :--- |
| `layer` | `ADM_ADM_2` |
| Thư mục (State/Province) | `NAME_1` |
| Tệp (District/County) | `NAME_2` (nhóm theo `GID_2`, dùng `ENGTYPE_2` để phân biệt nếu trùng `NAME_2`) |

**Danh sách quốc gia áp dụng:**

<details open>
<summary><b>🌏 Đông Nam Á</b></summary>

<br>

| Mã | Quốc gia | Cấp 1 (thư mục) | Cấp 2 (tệp) |
| :---: | :--- | :--- | :--- |
| `VNM` | Việt Nam | 63 tỉnh | 705 quận/huyện |
| `THA` | Thái Lan | 77 tỉnh | 928 Amphoe/Khet |
| `IDN` | Indonesia | 34 tỉnh | 514 Kabupaten/Kota |
| `MYS` | Malaysia | 16 bang | 160 Daerah |
| `PHL` | Philippines | 81 tỉnh + Metro Manila | 1,634 đô thị |
| `KHM` | Campuchia | 25 tỉnh | 197 huyện |
| `LAO` | Lào | 18 tỉnh | 148 huyện |
| `MMR` | Myanmar | 15 bang/vùng | 330 townships |
| `TLS` | Đông Timor | 13 đô thị | 65 subdistricts |

</details>

<details>
<summary><b>🏯 Đông Á & Nam Á</b></summary>

<br>

| Mã | Quốc gia | Cấp 1 (thư mục) | Cấp 2 (tệp) |
| :---: | :--- | :--- | :--- |
| `JPN` | Nhật Bản | 47 tỉnh | ~1,741 Shi/Ku/Machi/Mura |
| `KOR` | Hàn Quốc | 17 tỉnh/thành | ~250 Si/Gun/Gu |
| `PRK` | Triều Tiên | — | — |
| `MNG` | Mông Cổ | 22 tỉnh | 339 Sums |
| `IND` | Ấn Độ | 36 bang/UT | ~676 Districts |
| `BGD` | Bangladesh | 8 Divisions | 64 Districts; hoặc `ADM_3` cho 544 Upazilas |
| `PAK` | Pakistan | 8 đơn vị cấp 1 | ~36 Divisions ở `ADM_2` hoặc ~160 Districts ở `ADM_3` |
| `LKA` | Sri Lanka | 25 Districts ở `ADM_1` | 331 DS Divisions ở `ADM_2` |
| `NPL` | Nepal | — | — |

</details>

<details>
<summary><b>🗽 Châu Mỹ</b></summary>

<br>

| Mã | Quốc gia | Cấp 1 (thư mục) | Cấp 2 (tệp) |
| :---: | :--- | :--- | :--- |
| `USA` | Hoa Kỳ | 50 bang + DC | 3,143 Counties/Independent Cities |
| `CAN` | Canada | 13 tỉnh/lãnh thổ | 293 Census Divisions |
| `MEX` | Mexico | 32 bang | 2,469 Municipios |
| `BRA` | Brazil | 27 bang | 5,570 Municípios |
| `ARG` | Argentina | 24 tỉnh | 528 Departamentos/Partidos |
| `CHL` | Chile | 16 vùng | 56 tỉnh ở `ADM_2` hoặc 346 Comunas ở `ADM_3` |
| `COL` | Colombia | 33 vùng | 1,122 Municipios |
| `PER` | Peru | 26 vùng | 196 Provincias |
| `VEN`, `CUB` | Venezuela, Cuba | — | — |

</details>

<details>
<summary><b>🏰 Châu Âu</b></summary>

<br>

| Mã | Quốc gia | Cấp 1 (thư mục) | Cấp 2 (tệp) |
| :---: | :--- | :--- | :--- |
| `DEU` | Đức | 16 bang | 401 Kreise/Kreisfreie Städte |
| `FRA` | Pháp | 13 vùng | 96 Départements ở `ADM_2` |
| `ITA` | Ý | 20 vùng | 107 tỉnh/thành phố đô thị ở `ADM_2` |
| `ESP` | Tây Ban Nha | 17 cộng đồng tự trị | 52 tỉnh ở `ADM_2` hoặc 326 Comarcas ở `ADM_3` |
| `POL` | Ba Lan | 16 tỉnh | 380 Powiaty |
| `NLD` | Hà Lan | 12 tỉnh | 342 Gemeenten |
| `BEL` | Bỉ | 3 vùng | 11 tỉnh/Arrondissements |
| `CHE` | Thụy Sĩ | 26 Cantons | 143 Bezirke |
| `AUT` | Áo | 9 bang | 94 Bezirke |
| `SWE` | Thụy Điển | 21 hạt | 290 Kommuner |
| `NOR` | Na Uy | 11 hạt | 356 Kommuner |
| `DNK` | Đan Mạch | 5 vùng | 99 Kommuner |
| `RUS` | Nga | ~85 chủ thể liên bang | ~2,350 Raions/Cities |
| `TUR` | Thổ Nhĩ Kỳ | 81 tỉnh | 973 Ilçe |
| `CZE`, `HUN`, `ROU`, `BGR`, `GRC`, `PRT`, `FIN`, `UKR` | — | — | — |

</details>

<details>
<summary><b>🦘 Châu Đại Dương, Trung Đông & Châu Phi</b></summary>

<br>

| Mã | Quốc gia | Cấp 1 (thư mục) | Cấp 2 (tệp) |
| :---: | :--- | :--- | :--- |
| `AUS` | Úc | 8 bang/lãnh thổ | 562 Local Government Areas |
| `NZL` | New Zealand | 16 vùng | 67 Territorial Authorities |
| `NGA` | Nigeria | 37 bang | 774 LGAs |
| `SAU`, `EGY`, `ZAF`, `KEN`, `ETH`, `MAR`, `DZA`, `GHA`, `TZA`, `KAZ`, `UZB`, `IRN`, `IRQ` | — | — | — |

</details>

---

<a id="nhom2"></a>

### 🟧 Nhóm 2: `SHIFTED_ADM3_PREFECTURE` (dịch chuyển cấp 3: cấp địa khu làm thư mục, cấp quận/huyện làm tệp)

**Đặc điểm:**

- `ADM_1` quá rộng (quy mô 50–120 triệu dân, tương đương một quốc gia châu Âu).
- `ADM_2` mới là các thành phố cấp địa khu (Prefecture-level cities như Thâm Quyến, Quảng Châu, Vũ Hán, Tô Châu) hoặc phân vùng lớn.
- Các quận đô thị lõi và huyện (`Qu` / `Xian` / `Xianjishi`) nằm ở **`ADM_3`**.

#### 🇨🇳 Trường hợp điển hình nhất: Trung Quốc (`CHN`)

Nếu xuất ở `ADM_2`, toàn bộ thành phố Thâm Quyến hay Quảng Châu chỉ là một file duy nhất. Khi đó không thể phân tích sự phân hóa giữa các quận lõi (Nam Sơn, Phúc Điền, Thiên Hà) và vùng ven.

**Xử lý ngoại lệ cho 4 thành phố trực thuộc trung ương (`Beijing`, `Shanghai`, `Tianjin`, `Chongqing`) và các huyện trực thuộc tỉnh (`NAME_2 == "NA"`).** Ở 4 đô thị này, tên thành phố nằm ngay ở `NAME_1`. Do đó, công thức đặt tên Thư mục chuẩn xác nhất cho `CHN` là:

| Trường hợp | Thư mục |
| :--- | :--- |
| `NAME_1` thuộc `{"Beijing", "Shanghai", "Tianjin", "Chongqing"}`, hoặc `NAME_2` là `"NA"` / trùng `NAME_1` | `NAME_1` |
| 27 tỉnh/khu tự trị còn lại | `NAME_1 + " - " + NAME_2` (ví dụ: `Guangdong - Shenzhen`, `Guangdong - Guangzhou`, `Jiangsu - Suzhou`) |

Cách đặt tên này giúp người dùng vừa tìm theo Tỉnh dễ dàng trên thanh chọn của Streamlit, vừa tách biệt từng thành phố địa khu. Các tệp bên trong là toàn bộ Quận/Huyện ở `NAME_3` (nhóm theo `GID_3`).

#### 🌐 Các quốc gia khác có thể áp dụng Nhóm 2 (hoặc cấu hình `ADM_3`)

| Mã | Muốn phân tích ở cấp... | Thay vì... | Cấu hình |
| :---: | :--- | :--- | :--- |
| `PAK` | 160 `Districts` tại `ADM_3` | 36 `Divisions` tại `ADM_2` | Thư mục = `NAME_1`, Tệp = `NAME_3` |
| `BGD` | 544 `Upazilas` tại `ADM_3` | 64 `Districts` tại `ADM_2` | — |
| `FRA` | 333 `Arrondissements` tại `ADM_3` | — | Thư mục = `NAME_2` (Département) |

---

### 🟨 Nhóm 3: `ASYMMETRIC_HYBRID` (bất đối xứng / khuyết cấp trung gian `NAME_2 = "NA"`)

**Đặc điểm:** hệ thống hành chính lai ghép giữa mô hình hai cấp (two-tier shire counties) và mô hình một cấp (single-tier Unitary Authorities / Metropolitan Boroughs).

#### 🇬🇧 Trường hợp 1: Vương quốc Anh (`GBR`)

**Cấu trúc thực tế trong `gadm41_GBR.gpkg`:**

| Lớp | Nội dung |
| :--- | :--- |
| `ADM_ADM_1` | 4 quốc gia cấu thành: `England`, `Scotland`, `Wales`, `Northern Ireland`. |
| `ADM_ADM_2` | Chỉ chứa các hạt nông thôn hai cấp (như `Kent`, `Essex`, `West Sussex`). Toàn bộ 33 quận của Đại London, 36 quận của 6 hạt đô thị lớn (Greater Manchester, West Midlands, Merseyside, South Yorkshire, West Yorkshire, Tyne and Wear), toàn bộ các Unitary Authorities của England, cùng nhiều vùng của Scotland/Wales đều bị gán `NAME_2 = "NA"`. |
| `ADM_ADM_3` | Chứa **đầy đủ 100% các đơn vị chính quyền địa phương cấp Quận/Hạt chuẩn** (Local Authority Districts / London Boroughs / Metropolitan Districts / Unitary Authorities / Council Areas) trên toàn Vương quốc Anh. Ở các vùng khuyết `NAME_2` (`"NA"`), tên quận nằm ở `NAME_3`. Ở một vài hạt đơn nhất nhỏ khuyết `NAME_3` (`"NA"`), tên nằm ở `NAME_2`. |

**Giải pháp trích xuất chuẩn cho `GBR`:**

| Tham số | Giá trị |
| :--- | :--- |
| Lớp đọc | **`ADM_ADM_3`** |
| Thư mục (State/Region) | `NAME_1` (`England`, `Scotland`, `Wales`, `Northern Ireland`). Nếu muốn chia nhỏ `England` theo hạt thì dùng `COALESCE(NAME_2, "England_Unitary_and_Metro")`. Để đồng nhất với 4 bang trong giao diện hiện tại của bạn, đặt Thư mục = `NAME_1`. |
| Tệp (District/Borough) | Hàm hợp nhất **`COALESCE(NAME_3, NAME_2)`** (lấy `NAME_3` nếu hợp lệ, nếu `NAME_3` là `"NA"` thì lùi về `NAME_2`), nhóm theo khóa duy nhất `COALESCE(GID_3, GID_2)`. |

> [!NOTE]
> **Kết quả:** không mất bất kỳ quận nào của London hay Manchester, không sinh ra đa giác `NA` 37MB nào, và 100% tệp xuất ra đều là các Local Authority Districts đồng cấp.

#### 🇹🇼 Trường hợp 2: Đài Loan (`TWN`)

Trong GADM v4.1, một số huyện/thành phố bị lệch cấp giữa `NAME_1` và `NAME_2` (do `NAME_1` có hai tỉnh danh nghĩa `Fujian` và `Taiwan` bên cạnh các thành phố trực thuộc trung ương).

**Giải pháp cho `TWN`:** đọc lớp sâu nhất của Đài Loan (`ADM_ADM_2` hoặc `ADM_ADM_3`, tùy bản đóng gói).

| Tham số | Giá trị |
| :--- | :--- |
| Thư mục | `COALESCE(NAME_2, NAME_1)`: 22 Huyện/Thành phố như *Taipei, New Taipei, Taichung, Kaohsiung, Hsinchu* |
| Tệp | Cấp kế tiếp: 368 Quận/Hương/Trấn (*Qu/Xiang/Zhen*) |

---

### 🟥 Nhóm 4: `SHALLOW_ADM1_CITY_STATE` (thành bang & quốc gia diện tích nhỏ chỉ dùng cấp 1)

**Đặc điểm:** quốc gia có diện tích nhỏ hoặc là thành bang đô thị. Lớp `ADM_ADM_2` hoặc không tồn tại trong `.gpkg`, hoặc nếu có thì chỉ gồm các tổ dân phố nhỏ vài trăm mét vuông.

**Cấu hình trích xuất:**

| Tham số | Giá trị |
| :--- | :--- |
| Lớp đọc | **`ADM_ADM_1`** (hoặc tự động lùi về `ADM_ADM_1` khi không có `ADM_ADM_2`) |
| Thư mục | Tên quốc gia (`COUNTRY` / `NAME_0`) hoặc vùng lớn |
| Tệp | `NAME_1` (nhóm theo `GID_1`) |

**Danh sách quốc gia áp dụng:**

| Mã | Quốc gia | Chi tiết |
| :---: | :--- | :--- |
| `SGP` | Singapore | 5 vùng quy hoạch ở `ADM_1` |
| `HKG` | Hồng Kông | 18 quận hành chính nằm ngay ở `ADM_1` |
| `MAC` | Ma Cao | Các khu vực nằm ở `ADM_1` |
| `BRN` | Brunei | 4 quận Daerah ở `ADM_1`, hoặc dùng `ADM_2` cho 38 Mukim |
| `QAT` | Qatar | 8 đô thị Baladiyat ở `ADM_1` |
| `MDV` | Maldives | 21 Atolls ở `ADM_1` |
| `ISR` | Israel | 6 Districts ở `ADM_1`, hoặc 15 Sub-districts ở `ADM_2` |
| `IRL` | Ireland | 26 Counties truyền thống nằm ở `ADM_1`; lớp `ADM_2` là các Municipal Districts |

<sub>[↑ Về đầu trang](#top)</sub>

---

<a id="s4"></a>

## ✅ 4. Quy trình kiểm định chất lượng dữ liệu đầu ra

Mỗi tệp `.geojson` trước khi được ghi xuống ổ cứng để đưa vào `app.py` đều phải đi qua **5 lần kiểm định tự động** trong tập lệnh trích xuất:

```mermaid
flowchart LR
    S["📥 Dữ liệu từ<br/>.gpkg"] --> C1["1️⃣ Chuỗi rác"]
    C1 --> C2["2️⃣ Thủy văn"]
    C2 --> C3["3️⃣ Hợp nhất<br/>theo GID"]
    C3 --> C4["4️⃣ Chống ghi đè<br/>trùng tên"]
    C4 --> C5["5️⃣ Diện tích<br/>tối thiểu"]
    C5 --> G["📄 Tệp .geojson<br/>hợp lệ"]
```

### 1️⃣ Lần 1: kiểm tra chuỗi rác

Mọi giá trị thuộc tập `{"NA", "N/A", "NULL", "NONE", "UNKNOWN", "?", "", "NAN"}` (không phân biệt hoa thường, đã cắt khoảng trắng hai đầu) đều bị ép về `None` thực sự trước khi phân tích. Mọi dòng có `NAME_1 is None` (như `bang NA` trong `gadm41_GBR.gpkg`) bị loại bỏ, hoặc được gán lại từ cấp con nếu hợp lệ.

### 2️⃣ Lần 2: bộ lọc thủy văn

Loại bỏ hoàn toàn các đa giác có `TYPE_x` hoặc `ENGTYPE_x` chứa một trong các từ khóa `Water body`, `Lake`, `Inland water`, `Sea`, `Estuary`.

### 3️⃣ Lần 3: hợp nhất hình học theo mã định danh

Sửa lỗi tự cắt (self-intersection) bằng `shapely.make_valid()`, rồi gộp (`dissolve`) theo đúng mã `GID` mục tiêu, để đảm bảo một đơn vị hành chính ứng với đúng một tệp `.geojson`.

### 4️⃣ Lần 4: chống ghi đè trùng tên

Nếu trong cùng một thư mục Tỉnh/Bang có hai đơn vị khác mã `GID` nhưng trùng tên hiển thị (ví dụ: *Fairfax County* và *Fairfax City*), hệ thống tự động gắn hậu tố phân biệt lấy từ `ENGTYPE_x`:

```text
USA_Virginia_Fairfax_County.geojson
USA_Virginia_Fairfax_Independent_City.geojson
```

Cách đặt tên này tương thích với hàm `list_counties()` và `split_county()` trong `app.py`.

### 5️⃣ Lần 5: kiểm tra diện tích tối thiểu cho VIIRS

Cảnh báo nếu một đa giác có diện tích $< 0.25 \text{ km}^2$, tức nhỏ hơn một ô lưới $500 \times 500 \text{ m}$.

<sub>[↑ Về đầu trang](#top)</sub>

<!-- END ORIGINAL -->

---

## Source: docs/VALIDATION MASTER.md

<!-- BEGIN ORIGINAL -->
<a id="top"></a>

# Spatial-app: Validation specification and evidence register

| Field | Description |
|:---|:---|
| Project | Spatial econometrics and VIIRS nighttime-lights extraction |
| Repository | `hoanfg/spatial-app` |
| Document | Validation specification |
| Version | 1.0: 11 November 2026 |
| Reference implementation | Main branch, following pull requests #10, #11, #12 and #13 |
| Reference study | Yanqing District, Beijing, China, 2014–2020 |
| Scope | Methods, numerical findings, acceptance criteria, limitations and future verification |
| Maintenance | This document is revised through pull requests; previous findings remain traceable |

> **Subsequent review (12 November 2026):** The original 11 November reference scope is preserved below. After PRs #19–#22, consult [Major validation review — coverage and evidence reconciliation](../validation/MAJOR_REVIEW_COVERAGE_EVIDENCE_2026-11.md) for current synthetic/CI coverage, archive integrity checks and outstanding field-evidence limitations. V11 cross-location, GHSL independent validation and cloud operational checks are not marked complete by those merges.

> **Scope of assurance.** The principal raster extraction and spatial statistics have been reproduced for the specified Yanqing study. This does not establish universal validity for other locations, years, economic interpretations or the production hosting environment. This document records both successful tests and material sensitivities.

## Contents

1. [Purpose and validation standards](#s1)
2. [Reference datasets and reproducibility](#s2)
3. [GADM boundary audit](#s3)
4. [Statistical implementation and Local Moran validation](#s4)
5. [Independent VIIRS extraction - 2020](#s5)
6. [Independent VIIRS extraction - 2014](#s6)
7. [Measurement sensitivity](#s7)
8. [Transformation sensitivity](#s8)
9. [Spatial robustness](#s9)
10. [Temporal validation and Spatial Markov](#s10)
11. [GHSL convergent validation](#s11)
12. [Regression tests and corrective changes](#s12)
13. [Validation status and remaining work](#s13)
14. [Evidence register](#s14)
15. [Update protocol and change log](#s15)

---

<a id="s1"></a>
## 1. Purpose and validation standards

### 1.1. Research objective

The application integrates GADM 4.1 administrative boundaries, VIIRS Day/Night band radiance, regularly spaced analytical grids, zonal statistics, spatial autocorrelation, Local Indicators of Spatial Association (LISA), GHSL reference variables, and two-period spatial dynamics. Verification must distinguish **numerical correctness** from **sensitivity to methodological choices**, **validity of a proxy for economic activity**, and **operational reliability**.

The verification programme uses the following categories:

| Category | Meaning | What it does not imply |
|---|---|---|
| PASS: tested scope | Independent calculation agrees with the specified implementation within a prespecified numerical tolerance | General performance in all locations |
| SENSITIVITY CHARACTERIZED | Effects of alternative definitions have been quantified | All specifications are interchangeable |
| FIXED | A documented defect or interpretation problem was corrected and regression-tested | Every possible downstream use is validated |
| PARTIAL | Relevant results exist, but part of the independent comparison is missing | End-to-end verification |
| PENDING | No sufficient independent evidence is currently recorded | Failure or lack of scientific utility |

### 1.2. Evidence hierarchy

The assessment distinguishes (1) deterministic formula and geometry checks, (2) independent recomputation of Monte Carlo procedures, (3) independent raster-to-polygon benchmarks on actual Earth Engine products, (4) external comparisons with independent datasets, and (5) production execution tests. Agreement in one category must not be substituted for another.

The validation reports were generated on 11 November 2026 and consolidated into this specification. Their original CSVs, GeoTIFFs, Python scripts and evidence packages are identified in Section 14. Unless explicitly stated, those binary files are **not committed to this repository**. A clone of the repository alone does not reproduce all reported numbers.

<a id="s2"></a>
## 2. Reference datasets and reproducibility

### 2.1. Golden reference case

| Parameter | Value |
|---|---|
| Country and administrative district | China - Beijing - Yanqing |
| GADM identifier | `GID_2 = CHN.2.1.11_1` |
| Boundary source | `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Beijing/CHN_Beijing_Yanqing_District.geojson` |
| VIIRS source | `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` |
| VIIRS radiance and coverage bands | `avg_rad` and `cf_cvg` |
| Calendar years | 2014 and 2020 |
| Annual aggregation | Median of monthly composites after masking `cf_cvg == 0` |
| Application raster export | EPSG:4326, nominal scale **463.83 metres** |
| Grid projection | UTM zone 50N, EPSG:32650 |
| Baseline analytical grid | 500 m × 500 m, clipped to the district boundary |
| Number of clipped cells | **8,333** |
| Total grid area | Approximately **2,003.51 km²** |
| Border-cell exclusion rule | Area < 99% × 0.25 km² |
| Excluded border cells | **600** |
| Cells tested by LISA | **7,733** |
| Local Moran weights | Row-standardized binary Queen adjacency, with eligible neighbors |
| Monte Carlo parameters | 999 permutations, seed 42 for baseline |
| Inference | Conditional permutations without replacement; app-specific inclusive two-sided pseudo-p; Benjamini–Hochberg FDR at 5% |

### 2.2. Provenance and alignment

The application fetches a bounding-box annual GeoTIFF from Earth Engine. It converts radiance values into floating-point raster data, preserves invalid raster masks, clips negative **valid** radiance to zero and computes a coverage-weighted zonal mean for each actual grid polygon using `exactextract`.

The 500 m analytical grid is **not** the original VIIRS grid. Its UTM polygon boundaries intersect multiple pixels from the EPSG:4326 Earth Engine image. Therefore a center-pixel sample, a point extraction, or a grid overlay without a common raster affine transform is **not** a valid substitute for the original zonal mean.

Both the GADM polygon coordinates and the raster geotransform must be reproduced at full available precision. Early verification of border cells used rounded geometry, causing a slight discrepancy. Reconstructing the exact polygon eliminated it.

### 2.3. Reported source files

The primary CSVs were:

- `dien_khanh_NTL_2020_500m.csv`;
- `CHN_beijing_yanqing_2020_500m_lisa_cells.csv`;
- `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv`.

Earth Engine reference files were `yanqing_viirs_2020_reference.tif`, `yanqing_valid_months_2020.tif`, `yanqing_viirs_2020_annual_mean.tif`, `yanqing_viirs_2020_masked_median.tif`, `yanqing_viirs_2014_reference.tif`, `yanqing_valid_months_2014.tif` and `yanqing_viirs_2014_masked_median.tif`.

Because CSV radiance is exported to four decimal places, `5×10⁻⁵ nW/cm²/sr` is the natural absolute tolerance for a raster benchmark when comparing the unrounded reference mean to exported cell-level values.

<a id="s3"></a>
## 3. GADM boundary audit

### 3.1. Audit design

The audited China collection contains **2,420 curated GeoJSON files**. Each was compared against an official full-resolution GADM 4.1 China GeoPackage using administrative identifiers and geometry. Checks covered missing/invalid polygons, duplicate identifiers, topology agreement and measurable overlaps above the adopted 1 m² screening threshold.

### 3.2. Findings

- All **2,420** curated geometries and identifiers matched their GADM counterparts within the tested tolerance.
- No invalid geometry, duplicate GID or overlap exceeding the screening threshold was found in the audited set.
- **2,419/2,420** name values matched the source; the exceptional record was investigated.
- `GID_2 = CHN.14.10.2_1` had an incorrect curated name (`Yiyang`) where source data specified `Nan`. Pull request #10 corrected the metadata while retaining the geometry and file identity.
- One source GADM unit with an `NA` name was not represented by the curated export. Accordingly, a geometrically accurate curated dataset is not necessarily a one-to-one enumeration of every record in the source GeoPackage.

### 3.3. Resource-aware unit selection

Administrative subdivisions of major municipalities are intentionally analysed at district level. Beijing, Shanghai, Tianjin and Chongqing were split into manageable curated units to protect the Streamlit Community Cloud memory budget. This is a deliberate safeguard, **not** evidence of a missing city-level calculation. Studies requiring citywide estimates must specify an aggregation method across district units.

### 3.4. Verdict

**PASS for geometry and identifier consistency within the audited China export.** Cross-country GADM harmonization, naming conventions and socioeconomic comparability remain broader research questions outside this specific audit.

<a id="s4"></a>
## 4. Statistical implementation and independent Local Moran verification

### 4.1. Analysis sample and spatial adjacency

The baseline computes the lit-cell standardized score on non-edge analysis cells. A Queen adjacency relation includes neighbors sharing an edge **or** corner. Eligible cells constitute the membership pool for lag and conditional permutations; edge-masked or otherwise ineligible cells are not valid members of the neighbor graph.

For a focal cell \(i\) and valid set of neighbors \(N_i\), the row-standardized spatial lag is

\[
(Wz)_i = \frac{1}{|N_i|}\sum_{j\in N_i}z_j.
\]

The local Moran statistic follows the ESDA-style denominator:

\[
I_i = \frac{z_i(Wz)_i}{\sum_{j\in M}z_j^2/(|M|-1)},
\]

where \(M\) is the common set of eligible analysis cells. Raw values and transformed values are standardized separately when conducting sensitivity analyses.

### 4.2. Conditional Monte Carlo inference

The corrected algorithm samples **distinct non-focal member cells without replacement** for each permutation, keeping the focal standardized score fixed. This corrects an earlier with-replacement issue documented in PR #10.

The application uses a **two-sided, inclusive-tail Monte Carlo convention**: counts from simulated statistics at or beyond the observed statistic in either tail are converted into a pseudo-p with the +1 correction and twice the smaller tail, capped at one. For 999 simulations, the nominal smallest two-sided p-value is `2/(999+1) = 0.002`. Its tie handling and two-sided definition need not equal the default one-tail `esda.Moran_Local.p_sim`; comparisons must align conventions first.

Benjamini–Hochberg is then applied over the eligible focal cells at \(\alpha=0.05\). Quadrants are defined by the signs of the focal z-score and neighbor lag, and final HH/LL/HL/LH labels require statistical significance.

### 4.3. Deterministic audit

| Test | Observed result |
|---|---|
| Total cell rows | 8,333 |
| Excluded border cells | 600 |
| Eligible focal cells | 7,733 |
| Queen neighbor count per cell | **8,333/8,333 agreement** |
| Raw HH/LL/HL/LH quadrant assignments | **7,733/7,733 agreement** |
| Maximum absolute Local Moran I difference | Approximately **0.00016805** using rounded CSV inputs |
| FDR decisions reconstructed from exported `lisa_p_sim` | **100% agreement** |
| Significant HH | **370** |
| Significant LL | **2,510** |
| Not significant | **4,853** |
| Edge masked | **600** |

The small Local Moran difference should not be interpreted as a numerical defect because exported `ntl_mean` and `lisa_I` were rounded.

### 4.4. Independent seed and repeatability

A separate 999-permutation run with seed `20261111` produced pseudo-p Pearson correlation **~0.9967** with the exported values. The alternative seed yielded **2,879** significant cells versus **2,880** in the application, **375 HH** versus **370** (Jaccard **~0.935**) and **2,504 LL** versus **2,510** (Jaccard **~0.940**). These differences are consistent with Monte Carlo variability close to FDR thresholds; identical seed and permutation order are needed to demand exact p-value equality.

Later sensitivity work, using the original seed and matching algorithm, reproduced all baseline LISA labels and exported p-values. The independent-seed results and exact same-seed replication are complementary, not contradictory.

### 4.5. Verdict and limitations

**PASS within the reference configuration** for grid adjacency, deterministic Local Moran, permutation and BH-FDR behavior. This does not make the local hotspot map invariant to weights, transformations, grid sizes or the inference convention.

<a id="s5"></a>
## 5. Independent VIIRS extraction: 2020

### 5.1. Independent Earth Engine reference

The validation reproduced the annual median by selecting all monthly images between `2020-01-01` and `2021-01-01`, masking `avg_rad` where `cf_cvg <= 0`, taking the median and applying the same zero-fill policy as the application. A separate GeoTIFF was exported from Earth Engine for the common Yanqing bounding box.

### 5.2. Polygon reconstruction and raster benchmark

The complete GADM district polygon was projected into EPSG:32650 and intersected with the aligned 500 m grid. That reconstruction yielded exactly **8,333 polygons** with an area sum agreeing with the application's exported grid to within the geometry/CSV rounding tolerance. Each polygon's coverage-weighted mean was computed from the independent raster using pixel intersection area.

An interim check had validated **7,703 full cells**, with approximately **30 lightly clipped cells** and **600 border cells** requiring exact polygons. A single remaining apparent outlier at `grid_id=349` disappeared once unrounded GADM coordinates were used. The final result supersedes the earlier partial checks.

### 5.3. Final results

| Metric | Result |
|---|---:|
| Compared cells | **8,333** |
| Cells within exported-precision tolerance | **8,333/8,333** |
| Absolute tolerance | **0.00005 nW/cm²/sr** |
| Mean absolute error | Approximately **0.000025 nW/cm²/sr** |
| Maximum absolute error | Approximately **0.000050 nW/cm²/sr** |
| Pearson correlation | Approximately **0.99999999997** |
| Border-masked cells included in raster verification | **600/600** |
| Raster size | 217 × 142 = **30,814 pixels** |

The separate valid-month raster indicated **12 months with `cf_cvg > 0` at every exported pixel**. This counts monthly composites meeting the criterion, **not** the total number of satellite observations. The masked annual median contained no missing pixels in this bounding-box export.

### 5.4. Verdict

**PASS:** the complete 2020 VIIRS raster-to-cell extraction pipeline was independently reproduced at CSV output precision, including all clipped border polygons. No inference is made about missing data or calibration in other years or regions.

<a id="s6"></a>
## 6. Independent VIIRS extraction: 2014

### 6.1. Reference image and quality control

A separate 2014 annual median was built with the same Earth Engine collection, `cf_cvg > 0` mask, median aggregation, spatial bounds, raster scale and zonal-statistic rule.

The 2014 reference, masked median and valid-month rasters were all **217 × 142 pixels**, aligned with the 2020 reference. The coverage raster again indicated **12 valid monthly composites at all 30,814 exported pixels** and no missing annual-median pixels.

One 2014 VIIRS pixel had a **slightly negative radiance**. Two analytical cells intersected that pixel. The application clips **valid negative values to zero** before `exactextract`; reproducing this step resolved their discrepancies.

### 6.2. Results

| Metric | Result |
|---|---:|
| Compared grid cells | **8,333** |
| Cells within CSV rounding tolerance | **8,333/8,333** |
| Mean absolute error | Approximately **0.00002505 nW/cm²/sr** |
| Maximum absolute error | Approximately **0.00004999 nW/cm²/sr** |
| Pearson correlation | Approximately **0.9999999998** |
| Border cells successfully compared | **600/600** |
| Negative-radiance source pixels | **1** |
| Affected grid cells | **2** |

### 6.3. Two-year interpretation

The unweighted mean NTL across the common grid rose from **~0.4452 (2014)** to **~1.4137 (2020)**, or roughly **3.18 times** the 2014 level. Across 8,333 cells, **8,221 increased** and **112 decreased** in absolute radiance.

**PASS for 2014 raster extraction and the two-year radiance comparison.** An increase in absolute nighttime radiance should not automatically be described as economic or GDP growth.

<a id="s7"></a>
## 7. Measurement sensitivity: annual aggregation and missingness

### 7.1. Experimental design

The baseline takes the median of valid monthly radiance composites. Two alternatives were computed independently from Earth Engine: (a) an **unweighted mean of the monthly composites**, and (b) the **annual median with missing pixels preserved** rather than zero-filled. The same polygon grid, baseline inference parameters, and raster-to-cell extraction procedure were retained.

This annual mean is not an observation-count-weighted mean of raw satellite acquisitions; it is a mean of the valid monthly composite values.

### 7.2. Results

| Statistic | Annual median | Annual mean | Masked median |
|---|---:|---:|---:|
| Mean cell radiance | **1.4137** | **1.4754** | **1.4137** |
| Gini coefficient | **0.6809** | **0.6861** | **0.6809** |
| Global Moran I (binary Queen, same 8,333-cell sample) | **0.91413** | **0.91456** | **0.91413** |
| Significant HH | **370** | **385** | **370** |
| Significant LL | **2,510** | **2,499** | **2,510** |
| HH share of district area | **4.617%** | **4.804%** | **4.617%** |

The annual mean raised mean radiance by approximately **4.37%** relative to the median. Yet the geographical HH and LL sets remained similar: Jaccard **~0.961 (HH)** and **~0.962 (LL)**.

The masked and zero-filled medians agreed exactly over this pilot because the validated raster had no missing pixels. Therefore the comparison **does not test the impact of filling genuine missing pixels in a dataset with coverage gaps**.

### 7.3. Interpretation

The choice of annual aggregation influences radiance magnitude and inequality modestly, while preserving the main local clusters for this pilot. The application retains **annual median as the specified baseline**. Annual mean remains a sensitivity specification rather than a replacement.

<a id="s8"></a>
## 8. Transformation sensitivity: raw, P99 and log

### 8.1. Specifications

The tests used the 2020 annual median, 500 m grid, Queen neighbors, 999 permutations, seed 42 and FDR 5%. P99 caps positive NTL values at the **99th percentile of lit cells** before z-standardization. The log alternative applies the natural logarithm **on positive NTL values** in the lit-cell LISA computation. It is **not** the `log1p(NTL)` transform employed in the two-period dynamics module.

### 8.2. Results

| Statistic | Raw | P99 | Natural log |
|---|---:|---:|---:|
| Significant HH | **370** | **457** | **1,050** |
| Significant LL | **2,510** | **2,510** | **2,441** |
| Total significant cells | **2,880** | **2,967** | **3,491** |
| HH district area share | **~4.62%** | **~5.70%** | **~13.10%** |
| Raw-quadrant HH before significance | **1,072** | **1,135** | **2,517** |

**HH Jaccard:** raw–P99 **0.810**, raw–log **0.352**, P99–log **0.435**.

All **370 raw HH cells** also remained HH under the logarithmic specification, while the log alternative identified **680 additional HH cells**. The median untransformed NTL was approximately **13.259** among original raw HH cells and **2.731** among the additional log HH cells. Around **20.38%** of tested cells changed their raw-quadrant classification between the raw and log specifications.

### 8.3. Statistical interpretation

The NTL distribution is heavily right-skewed. Extremely bright cells strongly influence the raw mean and standard deviation. Logging compresses the upper tail and changes which cells have positive relative scores; it also affects the spatial lag signs and the resulting quadrants. The low Jaccard thus reflects a material **change in the underlying statistical definition**, not simply sampling noise or an implementation error.

### 8.4. Decision

Retain **raw NTL** as the baseline for absolute radiance concentration, **P99** as a robustness measure against extreme values, and **log NTL** as an alternative representation of relative light intensity. A specification must not be selected solely because it identifies more or fewer HH clusters. Findings sensitive to transformation should be reported as such.

<a id="s9"></a>
## 9. Spatial robustness: Queen/Rook and 500/1,000 m

### 9.1. Study design

Queen weights include edge- and corner-sharing cells; Rook weights include edge-sharing cells only. The 1,000 m grid was reconstructed from the original GADM geometry and the **source VIIRS raster**, not estimated by simply averaging 500 m CSV cells. All variants used raw annual median, 999 permutations, seed 42 and FDR 5%.

### 9.2. Comparison

| Spatial configuration | Tested cells | HH | LL | HH area share |
|---|---:|---:|---:|---:|
| Queen 500 m (baseline) | **7,733** | **370** | **2,510** | **4.62%** |
| Rook 500 m | **7,733** | **187** | **906** | **2.33%** |
| Queen 1,000 m | **1,865** | **92** | **562** | **4.59%** |
| Rook 1,000 m | **1,865** | **46** | **210** | **2.30%** |

The complete clipped 1,000 m grid contains **2,162 polygons**; the **1,865** figures are the eligible focal cells after edge masking.

At 500 m, all **187 Rook HH cells** belonged to the Queen HH set. Changing neighbor definition approximately halved HH area.

Between 500 m and 1,000 m, the Queen HH area was approximately **92.5 km² → 92.0 km²** and the Rook HH area **46.75 km² → 46.0 km²**. Similar totals do not imply identical locations. Direct polygon intersection gave **spatial Jaccard 0.655** for Queen (about **73.0 km²** shared HH area) and **0.686** for Rook (about **37.75 km²** shared HH area).

### 9.3. Verdict

**SENSITIVITY CHARACTERIZED.** HH area is relatively stable across these cell scales but the boundaries change materially; results are more sensitive to Queen versus Rook adjacency. Neither weight system is universally correct. Scientific use must specify the chosen neighborhood definition and report robustness where that choice matters.

<a id="s10"></a>
## 10. Temporal validation and Spatial Markov from 2014 to 2020

### 10.1. Temporal transform and directional vector

The module first computes

\[
v_{it} = \log(1+\max(\mathrm{NTL}_{it},0))
\]

and standardizes values **separately within each year**, across valid, non-edge cells:

\[
z_{it}=\frac{v_{it}-\bar v_{t}}{s_{v,t}}.
\]

It then calculates year-specific Queen neighbor means and movement components:

\[
\Delta z_i=z_{i,2020}-z_{i,2014},\qquad
\Delta Wz_i=(Wz)_{i,2020}-(Wz)_{i,2014},
\]

\[
m_i=\sqrt{(\Delta z_i)^2+(\Delta Wz_i)^2}.
\]

A directional regime is assigned only to eligible cells with **\(m_i\geq 0.05\)**. This number is a **descriptive movement threshold**, **not** a p-value or FDR significance threshold.

### 10.2. Regime definitions

| Stored CSV code (retained for compatibility) | Display interpretation | Sign rule |
|---|---|---|
| `1_Synergistic_Growth` | Synergistic Relative Growth | Δz ≥ 0, ΔWz ≥ 0 |
| `2_Agglomeration_Shadow` | Focal Relative Decline / Neighbor Relative Growth | Δz < 0, ΔWz ≥ 0 |
| `3_Emergent_Pioneer` | Focal Relative Growth / Neighbor Relative Decline | Δz ≥ 0, ΔWz < 0 |
| `4_Synchronized_Decline` | **Synchronized Relative Decline** | Δz < 0, ΔWz < 0 |
| `Excluded_or_Static` | Excluded or movement below threshold | Ineligible or m < 0.05 |

### 10.3. Observed outcomes

| Regime | Cells | Absolute radiance increased | Absolute radiance decreased |
|---|---:|---:|---:|
| Synergistic Relative Growth | **1,456** | 1,456 | 0 |
| Neighbor Relative Growth / Focal Relative Decline | **75** | 75 | 0 |
| Focal Relative Growth / Neighbor Relative Decline | **194** | 194 | 0 |
| **Synchronized Relative Decline** | **4,711** | **4,624** | **87** |
| Excluded / Static | **1,897** | 1,872 | 25 |
| **Total** | **8,333** | **8,221** | **112** |

**4,624 of 4,711 cells (approximately 98.15%)** in the stored `4_Synchronized_Decline` category experienced **positive absolute radiance growth**. There is no contradiction: their position in the **separately standardized within-year distribution** declined relative to their comparison population, as did that of their neighbors.

### 10.4. Threshold sensitivity

| Descriptive movement cutoff | Cells in synchronized relative decline |
|---|---:|
| 0.025 | **5,242** |
| 0.050 | **4,711** |
| 0.100 | **2,949** |
| 0.200 | **1,111** |

The classification is substantially sensitive to cutoff. It must not be described as independently statistically significant merely because a regime was assigned.

### 10.5. Spatial Markov

The module ranks cells into year-specific quartiles of `log1p(NTL)` and estimates transition matrices, including subsets conditioned on above- and below-median initial neighboring z-scores. Approximately **74.90%** of analyzed cells remained in their same radiance **quartile** from 2014 to 2020. This indicates persistence in relative spatial position, **not** unchanged absolute brightness.

### 10.6. Reproducibility and rounding

The Space-Time formulas, directional labels and Markov statistics were independently reconstructed from the exported CSV. One cell (`grid_id=3922`) sat very near the **0.05** threshold; recomputing from four-decimal-place NTL values could change its category. Using the application-exported movement information recovered all **8,333/8,333** regime labels. The discrepancy is attributable to export precision rather than evidence of a new algorithm defect.

### 10.7. Corrective interpretation

The initial interface term “Synchronized Decline” was ambiguous and could be misconstrued as economic or absolute light decline. **PR #11**, now merged, updates the bilingual UI wording and documents the relative nature of the method while preserving legacy machine-readable CSV identifiers and all numerical computations.

### 10.8. Remaining temporal questions

Independent raster benchmarks currently cover **two endpoint years (2014 and 2020)**, not a fully audited annual time series. Effects of interannual coverage, sensor calibration, background radiance and compositing policy across all years remain outside the completed tests.

<a id="s11"></a>
## 11. GHSL convergent validation

### 11.1. Reported pilot findings

The application's quality panel compared NTL with two GHSL measures at Yanqing in 2020.

| External reference | Spearman correlation | Spatial block-bootstrap 95% CI | AUC for top quartile |
|---|---:|---|---:|
| GHSL built-up surface | **0.629** | **~0.59–0.68** | **0.867** |
| GHSL population | **0.616** | **~0.58–0.66** | **0.851** |

Approximately **63%** of GHSL grid-level measurements in the displayed pilot were zero, depending on the layer and definition. The correlations are positive and informative as a preliminary convergent check.

### 11.2. Validation status

**PARTIAL.** Independent reconstruction of the exact GHSL source rasters, resampling/grid alignment, zero handling, Spearman, AUC and spatial block-bootstrap was **not** completed. The figures above are **application-reported**, not independently benchmarked in the same way as VIIRS extraction. GHSL built-up area and population are not substitutes for independent local GDP or economic activity.

### 11.3. Required benchmark

Use identical grid polygons, GHSL product versions, epoch, source projection and aggregation logic; report the number of zero cells; recompute rank correlations and AUC using explicit positive labels; reproduce block definitions, bootstrap draws and confidence-interval procedure. Assess spatial resolution mismatch and uncertainty.

<a id="s12"></a>
## 12. Regression tests and corrective changes

### 12.1. Source-level audit

The initial code audit found that the former conditional Local Moran routine sampled neighbors with replacement rather than from a distinct non-focal pool. It also identified a possible loss of finite NoData sentinel masks during raster conversion and the above GADM metadata naming issue.

**[Pull request #10](https://github.com/hoanfg/spatial-app/pull/10)** implemented the conditional without-replacement sampling, ESDA Local Moran scale convention, preservation of valid raster masks, metadata correction, documentation and regression coverage.

### 12.2. CI outcomes

After PR #10 was merged, two GitHub Actions test groups reported **32 passed** and **22 passed**, for **54 passed tests** in the associated CI runs. This establishes regression behavior for the covered code paths; it is not an Earth Engine execution benchmark.

**[Pull request #11](https://github.com/hoanfg/spatial-app/pull/11)** clarified Space-Time regime presentation, the `0.05` descriptive threshold, and retained CSV compatibility. Its GitHub Actions run completed successfully. The changes were display/documentation-only and did not modify numerical classifications.

### 12.3. Reproducibility caveats

Static fixtures alone cannot confirm performance on all source data, and agreement with a single implementation can propagate shared design assumptions. The independent raster-to-polygon comparisons at Yanqing supply a separate and stronger check of real data extraction. Both levels of evidence are retained.

<a id="s13"></a>
## 13. Validation status and outstanding programme

| ID | Topic | Current status | Principal outstanding requirement |
|---|---|---|---|
| V01 | Curated China GADM geometry/GIDs | PASS: audited China set | Extend scope when adding other countries |
| V02 | Automated tests / regression fixes | PASS: covered CI runs | Continuous verification on future commits |
| V03 | Independent LISA and BH-FDR | PASS: Yanqing 2020 | Additional geographies and Monte Carlo stability |
| V04 | VIIRS 2020 raster-to-polygon | PASS: all 8,333 cells | Geographic transferability |
| V05 | VIIRS 2014 raster-to-polygon | PASS: all 8,333 cells | Longer series and varying coverage |
| V06 | Aggregation and missingness | SENSITIVITY CHARACTERIZED | Cases containing genuine missing pixels |
| V07 | Raw/P99/log transformations | SENSITIVITY CHARACTERIZED | Interpretation across locations |
| V08 | Queen/Rook and cell size | SENSITIVITY CHARACTERIZED | Other morphologies, resolutions and weights |
| V09 | Two-period dynamics / Markov | PASS computation; interpretation FIXED | Broader temporal tests |
| V10 | GHSL comparison | PARTIAL | Independent GHSL benchmark |
| V11 | Cross-location validation | PENDING | At least 2–3 contrasting locations |
| V12 | Continuous multi-year stability | PARTIAL | Annual reference series and quality flags |
| V13 | External economic construct validity | PENDING | Comparable independently published economic indicators |
| V14 | Streamlit Cloud operational checks | PENDING | RAM, runtime, failure modes and export tests |

### 13.1. Recommended priority sequence

1. **Cross-location validation:** a bright urban core, an industrial/peri-urban area, and a low-light rural area. Document selection rationale and use available administrative subdivisions without overriding RAM safeguards.
2. **Independent GHSL pipeline:** align GHSL to the exact tested cells and independently reproduce the quality-panel diagnostics.
3. **Continuous multi-year series:** apply a stable geometry/grid while auditing missingness, anomalous changes and annual composites.
4. **Operational benchmark:** document peak memory, execution time, Earth Engine failures/retries, and output reproducibility on Streamlit Community Cloud.
5. **Economic construct validation:** compare radiance and hotspot measures against suitable independent economic indicators with explicit limitations and without causal claims.

A scientifically useful validation programme does not require all correlations to be high. It requires correct computation, transparent methodology, defined scope, meaningful uncertainty checks and clear disclosure where indicators respond to modeling choices.

<a id="s14"></a>
## 14. Evidence register and custody

### 14.1. Primary results

| Work package | Original Markdown report | Additional evidence names |
|---|---|---|
| Repository audit | `verification-report.md`; `Báo cáo kiểm chứng NTL spatial econometrics.md` | `spatial-app-audit-evidence.zip` |
| Local Moran/FDR | `yanqing_validation_report.md` | `yanqing_validation_evidence.zip`; `yanqing_lisa_independent_cell_comparison.csv` |
| VIIRS 2020 preliminary | `yanqing_viirs_validation_report.md` | `yanqing_viirs_validation_evidence.zip`; `yanqing_viirs_reference_interior_comparison.csv` |
| VIIRS 2020 final | `yanqing_viirs_all_cells_validation_report.md` | `yanqing_viirs_all_cells_validation_evidence.zip`; `yanqing_viirs_all_8333_polygon_comparison.csv` |
| VIIRS 2014 | `yanqing_2014_temporal_raster_validation_report.md` | `yanqing_2014_temporal_raster_validation_evidence.zip`; `yanqing_2014_viirs_cell_validation.csv` |
| Measurement sensitivity | `yanqing_2020_measurement_sensitivity_report.md` | `yanqing_2020_measurement_sensitivity_evidence.zip`; `yanqing_2020_measurement_sensitivity_cells.csv` |
| Transformation sensitivity | `yanqing_2020_transformation_sensitivity_report.md` | `yanqing_2020_transformation_sensitivity_evidence.zip`; `yanqing_2020_transformation_sensitivity_cells.csv` |
| Spatial robustness | `yanqing_spatial_robustness_validation_report.md` | `yanqing_spatial_robustness_evidence.zip`; `yanqing_spatial_robustness_500m_cells.csv`; `yanqing_spatial_robustness_1000m_cells.csv` |
| Temporal validation | `yanqing_temporal_validation_report.md` | `yanqing_temporal_validation_evidence.zip`; `yanqing_temporal_validation_by_cell.csv`; `yanqing_temporal_regime_summary.csv`; `yanqing_temporal_markov_counts.csv` |

### 14.2. What is and is not stored

The validation evidence repository now includes **a partial, individually verifiable data deposit** at [validation/evidence/yanqing](../validation/evidence/yanqing/README.md): source 8,333-cell application CSVs, independent Local Moran and 2020 polygon comparisons, a reproducibility archive for Local Moran, and the independent 2014 VIIRS reference TIFF. The index records Git blob identifiers and SHA-256 checksums for available binary materials. This deposit **does not yet contain** every source raster, all scripts, the original grid GeoJSON, or all complete sensitivity runs. A 73-file consolidated evidence ZIP has been assembled separately with per-member SHA-256 hashes but is **not deposited here**. Public end-to-end reproduction of all reported results therefore remains incomplete; the evidence index states precisely what can currently be inspected and what is still outstanding.

### 14.3. Historical interim results

A preliminary 2020 raster check initially covered whole cells and only approximated border polygons. It was **superseded** by the full-precision GADM reconstruction covering **8,333/8,333** cells. Both stages may be retained in external evidence archives, but the latter is the current authoritative 2020 verdict. Likewise, a different permutation seed gives expected stochastic differences; it does not contradict identical-seed reproducibility.

<a id="s15"></a>
## 15. Updating this specification

### 15.1. Requirements for a new validation entry

Every new campaign must record:

1. Date, repository commit/PR, validation identifier and scientific question.
2. Administrative location/GID, years, source product, imagery bands, spatial scale and CRS.
3. Data masks, zero/negative treatment, original and alternative specifications.
4. Grid construction, edge rules, neighbor weights, seeds, number of permutations, p-value/FDR conventions.
5. Numerical acceptance criteria, per-cell/sample counts, errors, overlap, exceptions and uncertainties.
6. Reproducible method/script locator, input manifest and immutable hashes when available.
7. Result status with **scope-limited** conclusion, limitations and further actions.

Update the status table in Section 13, add the detailed findings to the relevant section (or create a numbered section) and append an entry to the change log. Do not silently delete contradictory or superseded findings; explain the replacement.

### 15.2. Entry template

```markdown
### YYYY-MM-DD - Vxx: Study name
- Repository commit / pull request:
- Study area (GID), years, satellite products:
- Source rasters, masks, grids, projection:
- Baseline / sensitivity configurations:
- Reproduction script, input hashes, evidence location:
- Seed, permutations, significance method:
- Acceptance criterion:
- Detailed results and exceptions:
- Interpretation and unresolved limitations:
- Status change and next action:
```

### 15.3. Revision log

| Date | Change | Reference |
|---|---|---|
| 2026-11-11 | China boundary audit, Local Moran/NoData implementation corrections | [PR #10](https://github.com/hoanfg/spatial-app/pull/10) |
| 2026-11-11 | Yanqing VIIRS 2014/2020 and spatial, statistical and temporal benchmarks | Study evidence register above |
| 2026-11-11 | Clarified relative Space-Time regimes and descriptive cutoff | [PR #11](https://github.com/hoanfg/spatial-app/pull/11) |
| 2026-11-11 | Established a single validation register | [PR #12](https://github.com/hoanfg/spatial-app/pull/12) |
| 2026-11-11 | Expanded the register into a full technical compilation | [PR #13](https://github.com/hoanfg/spatial-app/pull/13) |
| 2026-11-11 | Separated complete English and Vietnamese validation specifications | Current documentation revision |

---

**Overall conclusion:** VIIRS extraction, Local Moran inference and the two-year directional calculations are supported by strong independent evidence for the specified Yanqing pilot. Important sensitivity to transformation, spatial weights and temporal threshold is documented. General validity across cities, independently extracted GHSL variables, continuous multi-year data, economic proxies and production Cloud runtime **remains unverified**.

[Return to top](#top)


## Audit evidence update — 2026-11-15

See [consolidated evidence](../validation/CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) for the latest evidence inventory. Historical PENDING statements above describe the earlier stage: V11 now has repository aggregate results, while source pairs and per-cell outputs for all three locations remain unavailable in this revision. The retrievable Bao'an CSV and profiler are published with hashes; this does not establish full V11/GHSL or post-PR-27 acceptance.

<!-- END ORIGINAL -->

---

## Source: docs/VALIDATION MASTER-vi.md

<!-- BEGIN ORIGINAL -->
<a id="top"></a>

# Spatial-app: Kiểm chứng và hồ sơ bằng chứng

| Mục | Nội dung |
|:---|:---|
| Dự án | Trích xuất ánh sáng ban đêm VIIRS và kinh tế lượng không gian |
| Repository | `hoanfg/spatial-app` |
| Tài liệu | Đặc tả kiểm chứng |
| Phiên bản | 1.0: 11/11/2026 |
| Phiên bản mã nguồn tham chiếu | Nhánh `main`, sau các PR #10, #11, #12 và #13 |
| Trường hợp thực nghiệm | Diên Khánh (Yanqing), Bắc Kinh, Trung Quốc; 2014–2020 |
| Phạm vi | Phương pháp, kết quả số, tiêu chí chấp nhận, giới hạn và kế hoạch kiểm chứng tiếp |
| Bảo trì | Các đợt kiểm chứng bổ sung được cập nhật vào chính tài liệu này bằng PR |

> **Cập nhật rà soát (12/11/2026):** Phần nội dung bên dưới vẫn giữ mốc kiểm chứng gốc ngày 11/11. Sau các PR #19–#22, xem [Major validation review — coverage and evidence reconciliation](../validation/MAJOR_REVIEW_COVERAGE_EVIDENCE_2026-11.md) để phân biệt mức độ kiểm thử CI/dữ liệu tổng hợp, kết quả đối chiếu archive và các giới hạn bằng chứng. V11 Cross-location, GHSL độc lập và vận hành Cloud chưa được xác nhận hoàn thành.

> **Phạm vi bảo đảm.** Các phép tính trích xuất raster và thống kê không gian chính đã được tái lập tại trường hợp Diên Khánh với dữ liệu thực. Kết quả này **không** chứng minh tính đúng đắn trên mọi địa phương, mọi năm hoặc tính phù hợp của NTL như chỉ báo kinh tế. Tài liệu ghi nhận cả những phép kiểm thành công lẫn các lựa chọn phương pháp có độ nhạy lớn.

## Mục lục

1. [Mục tiêu và tiêu chuẩn kiểm chứng](#s1)
2. [Bộ dữ liệu chuẩn và điều kiện tái lập](#s2)
3. [Kiểm chứng ranh giới GADM](#s3)
4. [Kiểm chứng Local Moran và suy luận thống kê](#s4)
5. [Kiểm chứng trích xuất VIIRS năm 2020](#s5)
6. [Kiểm chứng trích xuất VIIRS năm 2014](#s6)
7. [Độ nhạy theo phương pháp tổng hợp ảnh và dữ liệu thiếu](#s7)
8. [Độ nhạy theo phép biến đổi NTL](#s8)
9. [Độ vững theo cấu trúc không gian](#s9)
10. [Kiểm chứng động học không–thời gian và Spatial Markov](#s10)
11. [Đối chiếu hội tụ với GHSL](#s11)
12. [Kiểm thử hồi quy và các thay đổi đã sửa](#s12)
13. [Trạng thái toàn chương trình và công việc còn lại](#s13)
14. [Danh mục và bảo quản bằng chứng](#s14)
15. [Quy trình bổ sung kiểm chứng và lịch sử phiên bản](#s15)

---

<a id="s1"></a>
## 1. Mục tiêu và tiêu chuẩn kiểm chứng

### 1.1. Mục đích nghiên cứu

Ứng dụng tích hợp ranh giới hành chính GADM 4.1, bức xạ ánh sáng ban đêm VIIRS, lưới phân tích, thống kê theo vùng, tự tương quan không gian, Local Indicators of Spatial Association (LISA), dữ liệu đối chứng GHSL và phân tích động học hai thời điểm.

Kiểm chứng phải phân biệt bốn loại khẳng định:

- **Độ chính xác số học:** Kết quả có khớp với phép tính độc lập trên cùng đầu vào và cùng quy ước không?
- **Độ nhạy phương pháp:** Kết quả thay đổi thế nào khi đổi phép tổng hợp ảnh, biến đổi dữ liệu, định nghĩa láng giềng, kích thước ô và ngưỡng?
- **Giá trị đo lường:** NTL và các chỉ số liên quan có phản ánh hiện tượng nghiên cứu phù hợp không?
- **Độ tin cậy vận hành:** Ứng dụng có xử lý ổn định trên môi trường triển khai thực, trong giới hạn tài nguyên đã thiết kế không?

| Trạng thái | Ý nghĩa | Không hàm ý |
|---|---|---|
| **ĐẠT: trong phạm vi thử** | Tính toán độc lập khớp trong dung sai hoặc tiêu chí đã công bố | Tất cả địa phương và năm đều đạt |
| **ĐÃ ĐÁNH GIÁ ĐỘ NHẠY** | Ảnh hưởng của giả định thay thế được định lượng | Mọi cấu hình đều có thể thay cho nhau |
| **MỘT PHẦN** | Có bằng chứng sơ bộ nhưng thiếu kiểm chứng độc lập của một khâu | Toàn bộ pipeline đã đạt |
| **CHƯA THỰC HIỆN** | Chưa có đủ bằng chứng kiểm thử | Khâu đó nhất thiết bị lỗi |
| **ĐÃ KHẮC PHỤC** | Có PR điều chỉnh và kiểm thử liên quan | Không còn giới hạn khoa học nào khác |

### 1.2. Nguyên tắc kết luận

Mỗi kết quả phải gắn với phiên bản mã, dữ liệu đầu vào, khu vực, năm, độ phân giải, quy ước xử lý giá trị thiếu, quy tắc thống kê và dung sai. Không thể dùng một kết quả kiểm thử đơn vị để thay cho đối chiếu vệ tinh thực; cũng không thể dùng tương quan với GHSL như bằng chứng quan hệ nhân quả hoặc xác thực GDP.

**Kết quả kiểm chứng hiện tại tập trung vào một địa bàn tham chiếu**. Phạm vi này phù hợp để kiểm tra số học sâu, nhưng chưa đủ để kết luận khả năng khái quát của ứng dụng.

<a id="s2"></a>
## 2. Bộ dữ liệu chuẩn và điều kiện tái lập

### 2.1. Trường hợp chuẩn

| Tham số | Giá trị |
|---|---|
| Địa bàn | Trung Quốc - Bắc Kinh - Diên Khánh (Yanqing) |
| Mã địa giới | `GID_2 = CHN.2.1.11_1` |
| Nguồn ranh giới | `data/gadm41_CHN_gpkg/CHN_Curated_Boundaries/Beijing/CHN_Beijing_Yanqing_District.geojson` |
| Bộ dữ liệu vệ tinh | `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` |
| Band | `avg_rad` và `cf_cvg` |
| Năm | 2014, 2020 |
| Phép tổng hợp năm | Trung vị của các ảnh tháng sau khi loại pixel có `cf_cvg == 0` |
| Raster từ ứng dụng | `EPSG:4326`, scale danh nghĩa **463,83 mét** |
| Hệ tọa độ lưới | UTM 50N `EPSG:32650` |
| Lưới phân tích chính | 500 m × 500 m, cắt theo ranh giới |
| Tổng số ô | **8.333** |
| Diện tích | Khoảng **2.003,51 km²** |
| Quy tắc loại ô biên | Diện tích < 99% × 0,25 km² |
| Ô bị loại khỏi LISA | **600** |
| Ô tham gia LISA | **7.733** |
| Trọng số không gian | Queen; trung bình theo số láng giềng hợp lệ |
| Hoán vị Monte Carlo | 999 lượt; seed 42 cho baseline |
| Kiểm định | Hoán vị có điều kiện, lấy mẫu không hoàn lại; p hai phía theo quy ước ứng dụng; Benjamini–Hochberg FDR ở 5% |

### 2.2. Quy trình tạo và căn chỉnh dữ liệu

Ứng dụng tải GeoTIFF annual median trong bounding box từ Earth Engine, chuyển giá trị bức xạ sang kiểu số thực, giữ mask pixel không hợp lệ, **cắt giá trị bức xạ âm hợp lệ về 0** và tính trung bình theo tỷ lệ diện tích pixel giao với từng đa giác ô lưới bằng `exactextract`.

Lưới phân tích UTM 500 m **không phải** lưới pixel VIIRS nguyên thủy. Một ô có thể giao với nhiều pixel của raster `EPSG:4326`. Vì vậy, phép lấy giá trị tại tâm ô, lấy pixel gần nhất hoặc ghép hai lưới chưa căn chỉnh không thay được trung bình theo phần diện tích giao nhau.

Để tái lập chính xác các ô biên, phải giữ toàn bộ chữ số tọa độ ranh giới GADM và phép biến đổi raster. Kiểm tra ban đầu trên ranh giới bị làm tròn từng xuất hiện chênh lệch nhỏ; sai khác biến mất khi khôi phục tọa độ đầy đủ.

### 2.3. Dữ liệu đầu vào đã dùng

CSV chính:
- `dien_khanh_NTL_2020_500m.csv`;
- `CHN_beijing_yanqing_2020_500m_lisa_cells.csv`;
- `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv`.

GeoTIFF đối chứng:
- `yanqing_viirs_2020_reference.tif`, `yanqing_valid_months_2020.tif`;
- `yanqing_viirs_2020_annual_mean.tif`, `yanqing_viirs_2020_masked_median.tif`;
- `yanqing_viirs_2014_reference.tif`, `yanqing_valid_months_2014.tif`, `yanqing_viirs_2014_masked_median.tif`.

CSV xuất `ntl_mean` với bốn chữ số thập phân. Do đó, khi so trung bình raster chưa làm tròn với CSV, dung sai tuyệt đối phù hợp là **5×10⁻⁵ nW/cm²/sr**.

<a id="s3"></a>
## 3. Kiểm chứng ranh giới GADM

### 3.1. Thiết kế kiểm tra

Tập dữ liệu Trung Quốc đã biên tập chứa **2.420 file GeoJSON**. Từng đối tượng được so với GeoPackage GADM 4.1 Trung Quốc đủ độ phân giải. Các tiêu chí bao gồm mã hành chính, hình học, tính hợp lệ, mã trùng lặp, trùng khớp topology và diện tích chồng lấn lớn hơn ngưỡng phát hiện **1 m²**.

### 3.2. Kết quả

- Hình học và mã định danh của **2.420/2.420** đối tượng khớp nguồn tham chiếu trong dung sai kiểm tra.
- Không phát hiện đa giác không hợp lệ, mã GID trùng hoặc phần chồng lấn vượt ngưỡng.
- **2.419/2.420** tên khớp nguồn; trường hợp còn lại đã được đối chiếu và điều chỉnh.
- Tại `GID_2 = CHN.14.10.2_1`, tên trong bản biên tập từng là `Yiyang`, còn nguồn ghi `Nan`. **PR #10** sửa metadata, không thay hình học hay định danh file.
- Một bản ghi nguồn GADM có tên `NA` không nằm trong tập đã biên tập. Do đó, tập curated có hình học khớp nguồn **không mặc nhiên là danh mục một-một của toàn bộ bản ghi nguồn**.

### 3.3. Lựa chọn đơn vị hành chính phù hợp tài nguyên

Các đô thị trực thuộc trung ương hoặc địa bàn rất lớn được phân chia thành các district để bảo đảm ứng dụng hoạt động trong giới hạn RAM của Streamlit Community Cloud. Đây là biện pháp bảo vệ có chủ đích, **không phải lỗi thiếu tính năng phân tích toàn đô thị**. Khi cần số liệu cấp thành phố, nghiên cứu phải định nghĩa riêng cách tổng hợp từ các quận.

### 3.4. Kết luận

**ĐẠT về tính nhất quán hình học và mã định danh trong tập GADM Trung Quốc đã kiểm tra.** Khả năng chuẩn hóa giữa các quốc gia và tính tương đương kinh tế-xã hội của cấp hành chính nằm ngoài phạm vi kiểm tra này.

<a id="s4"></a>
## 4. Kiểm chứng thuật toán Local Moran và suy luận thống kê

### 4.1. Tập ô và cấu trúc láng giềng

Phương pháp baseline chuẩn hóa giá trị NTL của các ô sáng, sử dụng tập tham chiếu là các ô không bị loại bởi ngưỡng biên. Queen adjacency công nhận hai ô là láng giềng nếu chung cạnh **hoặc** chung đỉnh. Chỉ các ô hợp lệ được phép tham gia ma trận láng giềng và tập hoán vị.

Với tập láng giềng hợp lệ \(N_i\), độ trễ không gian là

\[
(Wz)_i=\frac{1}{|N_i|}\sum_{j\in N_i}z_j.
\]

Thống kê Local Moran theo quy ước chuẩn hóa ESDA:

\[
I_i=\frac{z_i(Wz)_i}{\sum_{j\in M}z_j^2/(|M|-1)},
\]

trong đó \(M\) là tập ô hợp lệ chung của phép kiểm định.

### 4.2. Suy luận Monte Carlo có điều kiện

Thuật toán đã sửa giữ giá trị z-score của ô trung tâm cố định. Trong mỗi lượt hoán vị, các ô láng giềng giả lập được lấy từ những ô hợp lệ **không kể ô trung tâm và không hoàn lại**. Cách này khắc phục lỗi lấy mẫu hoàn lại trước PR #10.

Ứng dụng tính pseudo-p **hai phía** bằng cách đếm thống kê mô phỏng ở ít nhất mức cực đoan tương ứng với thống kê quan sát, áp dụng hiệu chỉnh cộng 1, nhân đôi phía nhỏ hơn và giới hạn tối đa bằng 1. Khi dùng 999 hoán vị:

\[
p_{\min}=\frac{2}{999+1}=0{,}002.
\]

Quy tắc xử lý giá trị bằng nhau và p hai phía này **không nhất thiết trùng** với `esda.Moran_Local.p_sim` mặc định. Mọi benchmark phải căn chỉnh định nghĩa p trước.

Benjamini–Hochberg FDR được áp dụng trên những ô đủ điều kiện với \(\alpha=0{,}05\). Nhóm HH/LL/HL/LH được xác định bởi dấu z-score và độ trễ láng giềng; kết luận cụm cuối cùng cần vượt ngưỡng ý nghĩa.

### 4.3. Kiểm tra xác định

| Nội dung kiểm tra | Kết quả |
|---|---:|
| Tổng số ô | **8.333** |
| Ô bị loại ở biên | **600** |
| Ô được kiểm định | **7.733** |
| Số láng giềng Queen theo từng ô | **8.333/8.333 khớp** |
| Góc phần tư HH/LL/HL/LH chưa xét ý nghĩa | **7.733/7.733 khớp** |
| Sai khác tuyệt đối Local Moran I lớn nhất | Khoảng **0,00016805**, dùng CSV đã làm tròn |
| Quyết định BH-FDR tính lại từ `lisa_p_sim` | **Khớp 100%** |
| HH có ý nghĩa | **370** |
| LL có ý nghĩa | **2.510** |
| Không có ý nghĩa | **4.853** |
| Ô loại biên | **600** |

Sai khác nhỏ của Local Moran I không được xem là sai thuật toán, do `ntl_mean` và `lisa_I` trong CSV đã làm tròn.

### 4.4. Hoán vị với seed độc lập và tái lập chính xác

Lần kiểm chứng 999 lượt với seed **20261111** thu được tương quan Pearson của pseudo-p khoảng **0,9967** so với dữ liệu xuất. Kết quả seed độc lập: **2.879** ô có ý nghĩa thay vì **2.880**; HH **375** thay vì **370** (Jaccard **~0,935**); LL **2.504** thay vì **2.510** (Jaccard **~0,940**).

Những khác biệt gần ngưỡng FDR có thể do Monte Carlo. Muốn yêu cầu trùng hoàn toàn từng p-value phải dùng cùng thuật toán lấy mẫu, thứ tự hoán vị và seed. Các lượt kiểm chứng sau dùng seed 42 và cùng implementation đã tái lập **toàn bộ** nhãn/p-value baseline.

### 4.5. Kết luận

**ĐẠT trong cấu hình tham chiếu** về adjacency, Local Moran, hoán vị và BH-FDR. Điều đó **không** bảo đảm bản đồ hotspot bất biến khi đổi cách biến đổi NTL, trọng số không gian hoặc kích thước lưới.

<a id="s5"></a>
## 5. Kiểm chứng độc lập trích xuất VIIRS năm 2020

### 5.1. Ảnh tham chiếu Earth Engine

Ảnh năm 2020 được tạo độc lập từ các composite tháng trong khoảng `2020-01-01` đến `2021-01-01`, loại pixel `avg_rad` có `cf_cvg <= 0`, lấy median và sử dụng cùng quy tắc điền 0 với ứng dụng. GeoTIFF được xuất theo bounding box Diên Khánh đã dùng trong lần kiểm chứng.

### 5.2. Dựng đa giác lưới và phép đối chiếu

Ranh giới GADM đầy đủ tọa độ được chuyển sang EPSG:32650, dựng lưới 500 m và cắt theo đường ranh. Kết quả thu được đúng **8.333 đa giác**, với tổng diện tích khớp CSV trong dung sai tọa độ và làm tròn. Trung bình NTL theo ô được tính lại từ phần diện tích giao với pixel nguồn.

Kiểm chứng trung gian ban đầu xác nhận **7.703 ô vuông nguyên vẹn**, khoảng **30 ô cắt nhẹ**, còn **600 ô biên** cần hình học chính xác. Một ngoại lệ gần `grid_id=349` biến mất khi sử dụng tọa độ GADM đầy đủ. **Kết quả cuối cùng thay thế kết luận tạm thời.**

### 5.3. Kết quả cuối cùng

| Chỉ tiêu | Kết quả |
|---|---:|
| Ô được đối chiếu | **8.333** |
| Ô khớp trong dung sai CSV | **8.333/8.333** |
| Dung sai tuyệt đối | **0,00005 nW/cm²/sr** |
| Sai số tuyệt đối trung bình | Khoảng **0,000025 nW/cm²/sr** |
| Sai số tuyệt đối lớn nhất | Khoảng **0,000050 nW/cm²/sr** |
| Tương quan Pearson | Khoảng **0,99999999997** |
| Ô biên cũng được đối chiếu chính xác | **600/600** |
| Kích thước GeoTIFF | **217 × 142 = 30.814 pixel** |

Raster số tháng quan sát cho thấy **12 tháng có `cf_cvg > 0` tại mọi pixel trong vùng xuất**. Đây là số composite tháng đủ điều kiện, **không phải tổng số lần vệ tinh quan sát**. Ảnh median giữ mask không có pixel NoData trong bounding box này.

### 5.4. Kết luận

**ĐẠT:** toàn bộ quy trình raster VIIRS 2020 → trung bình theo đa giác ô lưới được tái lập độc lập đến độ chính xác CSV, kể cả ô ranh giới. Không suy diễn kết quả này cho nơi hoặc năm khác.

<a id="s6"></a>
## 6. Kiểm chứng độc lập trích xuất VIIRS năm 2014

### 6.1. Ảnh tham chiếu và chất lượng dữ liệu

Annual median năm 2014 được tạo độc lập với cùng collection Earth Engine, mặt nạ `cf_cvg > 0`, phạm vi địa lý, scale, phương pháp tổng hợp và trích xuất theo ô lưới.

Ba ảnh tham chiếu (baseline, median giữ mask, số tháng hợp lệ) đều có **217 × 142 pixel**, căn chỉnh với raster 2020. Toàn bộ **30.814 pixel** ghi nhận 12 composite tháng hợp lệ, không có NoData trong ảnh median.

**Một pixel có radiance âm nhẹ** ở năm 2014 giao với **hai ô phân tích**. Ứng dụng đưa giá trị âm hợp lệ về 0 trước `exactextract`; tái hiện đúng bước này đã xử lý chênh lệch ở hai ô.

### 6.2. Kết quả

| Chỉ tiêu | Kết quả |
|---|---:|
| Ô được so sánh | **8.333** |
| Ô khớp trong dung sai làm tròn | **8.333/8.333** |
| Sai số tuyệt đối trung bình | Khoảng **0,00002505 nW/cm²/sr** |
| Sai số tuyệt đối lớn nhất | Khoảng **0,00004999 nW/cm²/sr** |
| Pearson | Khoảng **0,9999999998** |
| Ô biên đạt | **600/600** |
| Pixel VIIRS có bức xạ âm | **1** |
| Ô lưới chịu ảnh hưởng | **2** |

### 6.3. Diễn giải chênh lệch hai năm

NTL trung bình không trọng số trên cùng lưới tăng từ **~0,4452 (2014)** lên **~1,4137 (2020)**, bằng khoảng **3,18 lần** mức năm 2014. Trong 8.333 ô, **8.221 ô tăng** và **112 ô giảm** radiance tuyệt đối.

**ĐẠT** đối với trích xuất raster 2014 và so sánh radiance của hai mốc. Tăng ánh sáng không tự động tương đương tăng GDP hay hoạt động kinh tế.

<a id="s7"></a>
## 7. Độ nhạy của phép tổng hợp ảnh theo năm và dữ liệu thiếu

### 7.1. Thiết kế

Baseline là median của các composite tháng hợp lệ. Hai biến thể được tính từ Earth Engine: (a) **mean không trọng số của các composite tháng** và (b) **median nhưng giữ missing dưới dạng NoData** thay vì điền 0. Giữ nguyên lưới đa giác, quy tắc trích xuất và các tham số LISA.

Annual mean ở đây **không** phải mean có trọng số theo tổng số quan sát vệ tinh `cf_cvg`; nó là mean của các composite tháng.

### 7.2. Kết quả

| Chỉ số | Median (baseline) | Mean năm | Median giữ NoData |
|---|---:|---:|---:|
| NTL trung bình mỗi ô | **1,4137** | **1,4754** | **1,4137** |
| Gini NTL | **0,6809** | **0,6861** | **0,6809** |
| Global Moran I (binary Queen, cùng 8.333 ô) | **0,91413** | **0,91456** | **0,91413** |
| HH có ý nghĩa | **370** | **385** | **370** |
| LL có ý nghĩa | **2.510** | **2.499** | **2.510** |
| Tỷ trọng diện tích HH | **4,617%** | **4,804%** | **4,617%** |

Mean tăng NTL trung bình khoảng **4,37%** so với median. Tuy nhiên, hai tập cụm HH và LL gần nhau: Jaccard HH **~0,961**, LL **~0,962**.

Median giữ mask và median điền 0 trùng hoàn toàn tại địa bàn này, bởi ảnh tham chiếu không có pixel missing. Thử nghiệm này **chưa kiểm tra tác động thực sự của việc điền 0 trong một dữ liệu có khoảng trống quan sát**.

### 7.3. Kết luận

Lựa chọn tổng hợp năm ảnh hưởng vừa phải tới cường độ và phân phối NTL; phần lớn cấu trúc cụm không gian vẫn ổn định trong pilot. **Annual median được giữ làm baseline**; annual mean là cấu hình kiểm tra độ nhạy.

<a id="s8"></a>
## 8. Độ nhạy theo phép biến đổi raw, P99 và log

### 8.1. Cấu hình

Sử dụng annual median 2020, lưới 500 m, Queen, 999 hoán vị, seed 42 và FDR 5%. P99 giới hạn giá trị NTL dương tại **phân vị 99 của ô sáng**, trước khi chuẩn hóa. Log ở LISA lấy **logarit tự nhiên của NTL dương**; khác với phép `log1p(NTL)` dùng trong module động học hai năm.

### 8.2. Kết quả

| Chỉ tiêu | Raw | P99 | Log tự nhiên |
|---|---:|---:|---:|
| HH có ý nghĩa | **370** | **457** | **1.050** |
| LL có ý nghĩa | **2.510** | **2.510** | **2.441** |
| Tổng ô có ý nghĩa | **2.880** | **2.967** | **3.491** |
| Tỷ trọng diện tích HH | **~4,62%** | **~5,70%** | **~13,10%** |
| Số ô quadrant HH trước FDR | **1.072** | **1.135** | **2.517** |

**Jaccard HH:** raw–P99 **0,810**, raw–log **0,352**, P99–log **0,435**.

Cả **370 HH raw** vẫn là HH dưới log, trong khi log bổ sung **680 ô HH**. NTL trung vị chưa biến đổi của 370 HH ban đầu khoảng **13,259**, của 680 HH bổ sung khoảng **2,731**. Khoảng **20,38%** ô kiểm định đổi quadrant khi chuyển raw sang log.

### 8.3. Giải thích thống kê

Phân phối NTL lệch phải rõ rệt. Các ô cực sáng tác động mạnh lên trung bình và độ lệch chuẩn raw. Log nén phần đuôi trên, làm thay đổi dấu z-score của một số ô cũng như dấu trung bình z-score láng giềng. Vì vậy, Jaccard raw–log thấp biểu thị **sự khác biệt có ý nghĩa về định nghĩa thống kê**, không đơn thuần là nhiễu hoán vị hoặc lỗi lập trình.

### 8.4. Quyết định phương pháp

Giữ **raw NTL** làm baseline khi nghiên cứu tập trung bức xạ tuyệt đối; dùng **P99** để kiểm tra phụ thuộc vào ô cực sáng và **log** để phân tích mức độ sáng tương đối. Không nên chọn cấu hình chỉ vì nó tạo nhiều hay ít cụm HH hơn. Khi kết luận nghiên cứu thay đổi mạnh theo phép biến đổi, cần báo cáo điều đó.

<a id="s9"></a>
## 9. Độ vững không gian: Queen/Rook và 500 m/1.000 m

### 9.1. Thiết kế

Queen xét ô chung cạnh hoặc chung đỉnh; Rook chỉ xét ô chung cạnh. Lưới 1.000 m được dựng lại từ ranh giới GADM và **raster VIIRS nguồn**, không tính bằng cách lấy trung bình đơn giản các ô 500 m trong CSV. Các biến thể đều dùng raw annual median, 999 hoán vị, seed 42, FDR 5%.

### 9.2. Bảng so sánh

| Cấu hình | Ô kiểm định | HH | LL | Tỷ trọng diện tích HH |
|---|---:|---:|---:|---:|
| Queen 500 m (baseline) | **7.733** | **370** | **2.510** | **4,62%** |
| Rook 500 m | **7.733** | **187** | **906** | **2,33%** |
| Queen 1.000 m | **1.865** | **92** | **562** | **4,59%** |
| Rook 1.000 m | **1.865** | **46** | **210** | **2,30%** |

Toàn bộ lưới 1.000 m có **2.162 đa giác**; con số **1.865** là số ô hợp lệ sau khi loại biên.

Ở 500 m, **187 HH của Rook** đều thuộc tập HH Queen. Thay đổi định nghĩa láng giềng khiến diện tích HH giảm xấp xỉ một nửa.

Khi đổi từ 500 sang 1.000 m, diện tích HH Queen từ **92,5 km² → 92,0 km²**; Rook từ **46,75 km² → 46,0 km²**. Tổng diện tích gần nhau không đồng nghĩa vị trí giống hệt. Kết quả chồng đa giác: **Jaccard không gian 0,655** cho Queen (giao HH ~**73,0 km²**) và **0,686** cho Rook (giao ~**37,75 km²**).

### 9.3. Kết luận

**ĐÃ ĐÁNH GIÁ ĐỘ NHẠY.** Tổng diện tích HH khá ổn định khi đổi kích thước ô, nhưng đường biên cụm thay đổi đáng kể; kết quả nhạy hơn với lựa chọn Queen hay Rook. Không có hệ trọng số nào tự động đúng trong mọi nghiên cứu. Cần chọn theo lý thuyết về quan hệ không gian và báo cáo độ vững tương ứng.

<a id="s10"></a>
## 10. Kiểm chứng động học không–thời gian và Spatial Markov

### 10.1. Chuẩn hóa theo từng năm và vector thay đổi

Module tính:

\[
v_{it}=\log(1+\max(\mathrm{NTL}_{it},0))
\]

và chuẩn hóa **riêng ở từng năm** trên tập ô hợp lệ, không thuộc biên:

\[
z_{it}=\frac{v_{it}-\bar{v}_t}{s_{v,t}}.
\]

Độ trễ Queen và các thay đổi:

\[
\Delta z_i=z_{i,2020}-z_{i,2014}, \qquad
\Delta Wz_i=(Wz)_{i,2020}-(Wz)_{i,2014},
\]

\[
m_i=\sqrt{(\Delta z_i)^2+(\Delta Wz_i)^2}.
\]

Ô chỉ được gán nhóm chuyển động khi đủ điều kiện và **\(m_i\ge 0{,}05\)**. Đây là **ngưỡng mô tả hướng thay đổi**, **không phải** p-value hoặc ngưỡng FDR.

### 10.2. Định nghĩa nhóm

| Mã CSV được giữ tương thích | Ý nghĩa hiển thị | Dấu thay đổi |
|---|---|---|
| `1_Synergistic_Growth` | Ô và láng giềng cùng tăng vị thế tương đối | Δz ≥ 0, ΔWz ≥ 0 |
| `2_Agglomeration_Shadow` | Ô giảm, láng giềng tăng vị thế tương đối | Δz < 0, ΔWz ≥ 0 |
| `3_Emergent_Pioneer` | Ô tăng, láng giềng giảm vị thế tương đối | Δz ≥ 0, ΔWz < 0 |
| `4_Synchronized_Decline` | **Ô và láng giềng cùng giảm vị thế tương đối** | Δz < 0, ΔWz < 0 |
| `Excluded_or_Static` | Không hợp lệ hoặc độ thay đổi dưới ngưỡng | Không hợp lệ hoặc m < 0,05 |

### 10.3. Kết quả quan sát

| Nhóm | Số ô | NTL tăng tuyệt đối | NTL giảm tuyệt đối |
|---|---:|---:|---:|
| Cùng tăng vị thế tương đối | **1.456** | 1.456 | 0 |
| Ô giảm / láng giềng tăng vị thế | **75** | 75 | 0 |
| Ô tăng / láng giềng giảm vị thế | **194** | 194 | 0 |
| **Cùng giảm vị thế tương đối** | **4.711** | **4.624** | **87** |
| Loại khỏi phân tích / thay đổi nhỏ | **1.897** | 1.872 | 25 |
| **Tổng** | **8.333** | **8.221** | **112** |

**4.624/4.711 ô (~98,15%)** mang mã `4_Synchronized_Decline` vẫn có **radiance tăng tuyệt đối**. Không có mâu thuẫn số học: vị thế của các ô và láng giềng trong phân phối NTL được chuẩn hóa **riêng mỗi năm** đã giảm tương đối.

### 10.4. Độ nhạy của ngưỡng mô tả

| Ngưỡng \(m_i\) | Số ô cùng giảm vị thế tương đối |
|---|---:|
| 0,025 | **5.242** |
| 0,050 | **4.711** |
| 0,100 | **2.949** |
| 0,200 | **1.111** |

Phân loại nhạy rõ với ngưỡng. Không được mô tả nhãn nhóm là “có ý nghĩa thống kê” chỉ vì ô được gán nhóm.

### 10.5. Spatial Markov

Module xếp hạng `log1p(NTL)` thành bốn quartile ở từng năm và tính ma trận chuyển dịch, gồm các phân nhóm theo độ sáng láng giềng ban đầu cao/thấp so với trung vị. Khoảng **74,90%** ô vẫn thuộc cùng quartile từ 2014 đến 2020. Điều này phản ánh **mức độ duy trì thứ hạng tương đối**, không phải độ sáng tuyệt đối không đổi.

### 10.6. Tái lập và ảnh hưởng làm tròn

Các công thức, nhãn hướng thay đổi và bảng chuyển dịch đã được tái tính từ CSV xuất. Có một ô `grid_id=3922` rất gần ngưỡng **0,05**; khi tính trực tiếp từ NTL lưu bốn chữ số thập phân, nhãn ô này có thể thay đổi. Dựa trên thông tin vector do ứng dụng xuất, kết quả tái lập **8.333/8.333** nhãn. Đây là hạn chế độ chính xác khi xuất số, chưa phải bằng chứng lỗi mới.

### 10.7. Điều chỉnh cách diễn giải

Nhãn cũ “Synchronized Decline” dễ gây hiểu nhầm thành suy giảm kinh tế hoặc ánh sáng tuyệt đối. **PR #11 đã merge** và sửa nhãn hiển thị theo hướng **giảm vị thế tương đối**, giải thích ngưỡng 0,05, trong khi giữ nguyên mã CSV và toàn bộ công thức số.

### 10.8. Giới hạn thời gian còn lại

Kiểm chứng raster độc lập hiện bao phủ **hai năm đầu–cuối (2014 và 2020)**, chưa phải chuỗi thời gian hằng năm đầy đủ. Vấn đề độ phủ từng năm, hiệu chỉnh cảm biến, ánh sáng nền và chính sách tổng hợp ảnh liên thời gian vẫn chưa hoàn tất.

<a id="s11"></a>
## 11. Kiểm chứng hội tụ với GHSL

### 11.1. Kết quả báo cáo từ ứng dụng

Bảng kiểm tra chất lượng của ứng dụng đối chiếu NTL với hai biến GHSL tại Diên Khánh năm 2020:

| Dữ liệu đối chứng | Spearman ρ | Khoảng tin cậy 95% theo block bootstrap | AUC cho nhóm 25% cao nhất |
|---|---:|---|---:|
| Bề mặt xây dựng GHSL | **0,629** | **~0,59–0,68** | **0,867** |
| Dân số GHSL | **0,616** | **~0,58–0,66** | **0,851** |

Khoảng **63%** giá trị GHSL ở cấp ô được hiển thị bằng 0, tùy sản phẩm và cách đo. Tương quan dương là bằng chứng hội tụ sơ bộ có giá trị tham khảo.

### 11.2. Trạng thái

**MỘT PHẦN.** Chưa tái lập độc lập toàn bộ nguồn raster GHSL, cách căn chỉnh lưới, xử lý zero, Spearman, AUC và block bootstrap. Các kết quả ở trên **do ứng dụng báo cáo**, chưa phải benchmark độc lập ngang cấp với kiểm chứng VIIRS. Bề mặt xây dựng và dân số GHSL không thể thay thế dữ liệu GDP hoặc hoạt động kinh tế thực địa.

### 11.3. Phép kiểm cần hoàn thành

Dùng cùng đa giác lưới, đúng phiên bản/sản phẩm GHSL, năm tham chiếu, hệ tọa độ nguồn và phép thống kê trích xuất. Công bố số ô zero, tái tính tương quan hạng, AUC với nhãn dương được định nghĩa rõ, block bootstrap cùng quy tắc chia cụm và khoảng tin cậy; đồng thời đánh giá độ lệch độ phân giải.

<a id="s12"></a>
## 12. Kiểm thử hồi quy và thay đổi mã nguồn

### 12.1. Phát hiện audit

Audit mã nguồn ban đầu phát hiện: (i) Local Moran lấy mẫu hoán vị có hoàn lại, trái với phương pháp mẫu có điều kiện không hoàn lại; (ii) nguy cơ mất mask cho NoData sentinel hữu hạn trong bước chuyển đổi raster; và (iii) trường hợp sai tên GADM nêu ở Mục 3.

**[PR #10](https://github.com/hoanfg/spatial-app/pull/10)** sửa lấy mẫu không hoàn lại, chuẩn hóa Local Moran theo quy ước ESDA, bảo toàn raster mask, sửa metadata và bổ sung kiểm thử hồi quy.

### 12.2. Kết quả CI

Sau khi PR #10 merge, hai nhóm GitHub Actions ghi nhận **32** và **22** kiểm thử đạt, tổng cộng **54** lượt kiểm thử trong các job liên quan. Đây là bằng chứng hồi quy mã nguồn theo fixture, không phải benchmark Earth Engine thực.

**[PR #11](https://github.com/hoanfg/spatial-app/pull/11)** cập nhật cách diễn giải chế độ Space-Time, ngưỡng 0,05 và giữ tương thích CSV. GitHub Actions của PR này hoàn thành thành công. Thay đổi chỉ liên quan giao diện/tài liệu, không sửa kết quả số.

### 12.3. Giới hạn tái lập

Fixture tĩnh không khẳng định hiệu năng trên mọi đầu vào. Hai cài đặt thống kê có thể dùng chung giả định phương pháp, nên sự phù hợp của chúng không loại bỏ toàn bộ thiên lệch thiết kế. Đối chiếu độc lập raster–đa giác trên dữ liệu vệ tinh thật là tầng bằng chứng bổ sung, được lưu cùng kết quả CI.

<a id="s13"></a>
## 13. Trạng thái toàn chương trình và công việc còn lại

| Mã | Hạng mục | Trạng thái | Nội dung chưa hoàn thành |
|---|---|---|---|
| V01 | Hình học/GID GADM Trung Quốc | **ĐẠT trong tập được audit** | Mở rộng khi thêm quốc gia |
| V02 | Kiểm thử tự động và sửa hồi quy | **ĐẠT theo CI đã xem** | Kiểm thử liên tục ở commit mới |
| V03 | LISA và BH-FDR độc lập | **ĐẠT: Diên Khánh 2020** | Thử thêm địa lý, seed |
| V04 | VIIRS raster 2020 → ô | **ĐẠT: 8.333/8.333** | Khả năng khái quát |
| V05 | VIIRS raster 2014 → ô | **ĐẠT: 8.333/8.333** | Nhiều năm, độ phủ thay đổi |
| V06 | Mean/median, missing | **ĐÃ ĐÁNH GIÁ ĐỘ NHẠY** | Địa bàn/năm có missing thực |
| V07 | Raw/P99/log | **ĐÃ ĐÁNH GIÁ ĐỘ NHẠY** | Kết quả ở vùng khác |
| V08 | Queen/Rook, kích thước ô | **ĐÃ ĐÁNH GIÁ ĐỘ NHẠY** | Địa hình, cấu trúc khác |
| V09 | Space-Time và Markov | **ĐẠT phép tính; ĐÃ SỬA diễn giải** | Kiểm chứng động học rộng hơn |
| V10 | GHSL | **MỘT PHẦN** | Tái tính độc lập từ raster GHSL |
| V11 | Kiểm chứng nhiều địa phương | **CHƯA THỰC HIỆN** | Ít nhất 2–3 địa bàn đối lập |
| V12 | Chuỗi nhiều năm liên tục | **MỘT PHẦN** | Raster và cờ chất lượng từng năm |
| V13 | Giá trị đại diện kinh tế | **CHƯA THỰC HIỆN** | Chỉ báo kinh tế độc lập phù hợp |
| V14 | Streamlit Cloud | **CHƯA THỰC HIỆN** | RAM, thời gian, xử lý lỗi, xuất dữ liệu |

### 13.1. Thứ tự ưu tiên

1. **Nhiều địa phương:** chọn lõi đô thị sáng mạnh, khu công nghiệp/ven đô và vùng nông thôn ánh sáng thấp; nêu lý do lựa chọn và tôn trọng cơ chế bảo vệ RAM.
2. **GHSL độc lập:** ghép đúng raster GHSL vào ô đã kiểm chứng và tái lập các chỉ số của bảng chất lượng.
3. **Chuỗi năm liên tục:** cùng ranh giới và lưới, đánh giá missing, bất thường và tính nhất quán composite từng năm.
4. **Vận hành:** ghi peak RAM, thời gian chạy, lỗi Earth Engine/retry và khả năng xuất dữ liệu trên Streamlit Community Cloud.
5. **Đại diện kinh tế:** đối chiếu với chỉ báo kinh tế có nguồn đáng tin và phạm vi địa lý tương ứng, không tự khẳng định nhân quả.

Một chương trình validation có giá trị khoa học không yêu cầu tất cả tương quan phải cao. Điều cần có là phép tính đúng, phương pháp rõ, phạm vi kiểm chứng xác định, đánh giá bất định và công bố minh bạch các kết quả phụ thuộc giả định.

<a id="s14"></a>
## 14. Danh mục và bảo quản bằng chứng

### 14.1. Báo cáo và sản phẩm liên quan

| Nhóm | Báo cáo Markdown gốc | Bằng chứng bổ sung |
|---|---|---|
| Audit repository | `verification-report.md`; `Báo cáo kiểm chứng NTL spatial econometrics.md` | `spatial-app-audit-evidence.zip` |
| LISA/FDR | `yanqing_validation_report.md` | `yanqing_validation_evidence.zip`; `yanqing_lisa_independent_cell_comparison.csv` |
| VIIRS 2020 tạm thời | `yanqing_viirs_validation_report.md` | `yanqing_viirs_validation_evidence.zip`; `yanqing_viirs_reference_interior_comparison.csv` |
| VIIRS 2020 cuối cùng | `yanqing_viirs_all_cells_validation_report.md` | `yanqing_viirs_all_cells_validation_evidence.zip`; `yanqing_viirs_all_8333_polygon_comparison.csv` |
| VIIRS 2014 | `yanqing_2014_temporal_raster_validation_report.md` | `yanqing_2014_temporal_raster_validation_evidence.zip`; `yanqing_2014_viirs_cell_validation.csv` |
| Độ nhạy tổng hợp ảnh | `yanqing_2020_measurement_sensitivity_report.md` | `yanqing_2020_measurement_sensitivity_evidence.zip`; `yanqing_2020_measurement_sensitivity_cells.csv` |
| Độ nhạy phép biến đổi | `yanqing_2020_transformation_sensitivity_report.md` | `yanqing_2020_transformation_sensitivity_evidence.zip`; `yanqing_2020_transformation_sensitivity_cells.csv` |
| Độ vững không gian | `yanqing_spatial_robustness_validation_report.md` | `yanqing_spatial_robustness_evidence.zip`; `yanqing_spatial_robustness_500m_cells.csv`; `yanqing_spatial_robustness_1000m_cells.csv` |
| Động học thời gian | `yanqing_temporal_validation_report.md` | `yanqing_temporal_validation_evidence.zip`; `yanqing_temporal_validation_by_cell.csv`; `yanqing_temporal_regime_summary.csv`; `yanqing_temporal_markov_counts.csv` |

### 14.2. Phạm vi lưu trữ

Repository hiện có **một phần bộ bằng chứng thực**, truy cập tại [validation/evidence/yanqing](../validation/evidence/yanqing/README.md), gồm các CSV gốc đủ 8.333 ô, bảng kiểm tra độc lập LISA và VIIRS 2020 theo ô, ZIP mã tái lập LISA, và GeoTIFF tham chiếu VIIRS 2014. Bảng chỉ mục ghi mã định danh Git và SHA-256 cho dữ liệu nhị phân đã công bố. Tuy nhiên, **chưa đăng đầy đủ** raster 2020, hình học lưới, toàn bộ script và kết quả các đợt độ nhạy. Gói ZIP tổng hợp 73 file đã được tạo và có checksum nhưng **chưa lưu trong GitHub**; không được khẳng định người ngoài có thể tái lập mọi kết quả chỉ từ repository.

Trước khi công bố học thuật, cần lưu gói bằng chứng đầy đủ vào kho bền vững và cập nhật đường dẫn cùng checksum tại đây.

### 14.3. Kết quả trung gian được thay thế

Kiểm chứng VIIRS 2020 ban đầu chỉ đối chiếu chính xác các ô nguyên vẹn và xấp xỉ phần biên. Kết quả đó đã được **thay thế** bằng kiểm chứng đa giác GADM đủ precision trên **8.333/8.333** ô. Tương tự, kết quả pseudo-p với seed khác là biến thiên ngẫu nhiên Monte Carlo, không mâu thuẫn với việc tái lập chính xác khi dùng cùng seed.

Không xóa các bản gốc khỏi lịch sử nghiên cứu; chỉ xác định rõ kết luận cuối cùng được ưu tiên.

<a id="s15"></a>
## 15. Quy trình cập nhật đặc tả

### 15.1. Thông tin bắt buộc cho đợt mới

Mỗi chiến dịch phải ghi rõ:

1. Ngày, commit/PR, mã validation và câu hỏi nghiên cứu.
2. Địa bàn/GID, năm, sản phẩm vệ tinh, band, scale, CRS.
3. Mặt nạ missing, quy tắc zero/âm, baseline và biến thể.
4. Lưới, ô biên, trọng số láng giềng, seed, số hoán vị, quy tắc p/FDR.
5. Tiêu chí chấp nhận, số ô, sai số, độ chồng lấp, ngoại lệ và độ bất định.
6. Script tái lập, danh mục đầu vào, hash và nơi lưu bằng chứng.
7. Kết luận có giới hạn phạm vi, trạng thái và hành động tiếp theo.

Cập nhật bảng trạng thái ở Mục 13, bổ sung kết quả chi tiết vào mục thích hợp (hoặc thêm mục đánh số mới), đồng thời ghi một dòng vào lịch sử. Không xóa hoặc âm thầm thay thế kết quả mâu thuẫn; phải nêu rõ vì sao kết luận được điều chỉnh.

### 15.2. Mẫu cập nhật

```markdown
### YYYY-MM-DD - Vxx: Tên đợt kiểm chứng
- Commit / Pull Request:
- Địa bàn (GID), năm, sản phẩm vệ tinh:
- Raster nguồn, mặt nạ, lưới, hệ tọa độ:
- Cấu hình baseline và cấu hình đối chứng:
- Script tái lập, hash dữ liệu, nơi lưu bằng chứng:
- Seed, số hoán vị, quy tắc ý nghĩa thống kê:
- Tiêu chí chấp nhận:
- Kết quả chi tiết và ngoại lệ:
- Diễn giải và giới hạn chưa giải quyết:
- Trạng thái mới và bước kế tiếp:
```

### 15.3. Lịch sử chỉnh sửa

| Ngày | Nội dung | Tham chiếu |
|---|---|---|
| 11/11/2026 | Audit GADM Trung Quốc; sửa Local Moran/NoData | [PR #10](https://github.com/hoanfg/spatial-app/pull/10) |
| 11/11/2026 | Kiểm chứng VIIRS 2014/2020 và các phép thử thống kê, không gian, thời gian | Danh mục bằng chứng ở Mục 14 |
| 11/11/2026 | Làm rõ chế độ Space-Time tương đối và ngưỡng mô tả | [PR #11](https://github.com/hoanfg/spatial-app/pull/11) |
| 11/11/2026 | Thiết lập sổ cái validation thống nhất | [PR #12](https://github.com/hoanfg/spatial-app/pull/12) |
| 11/11/2026 | Mở rộng tài liệu thành bản kỹ thuật tổng hợp | [PR #13](https://github.com/hoanfg/spatial-app/pull/13) |
| 11/11/2026 | Tách đặc tả validation thành phiên bản tiếng Việt và tiếng Anh | Lần cập nhật tài liệu hiện tại |

---

**Kết luận chung:** Việc trích xuất VIIRS, suy luận Local Moran và công thức động học hai thời điểm đã có bằng chứng độc lập mạnh **trong trường hợp Diên Khánh được thử**. Những độ nhạy quan trọng theo phép biến đổi, trọng số không gian và ngưỡng thời gian đã được định lượng. Khả năng áp dụng trên nhiều địa phương, pipeline GHSL độc lập, chuỗi nhiều năm liên tục, giá trị đại diện kinh tế và độ tin cậy trên Streamlit Cloud **vẫn chưa được kiểm chứng đầy đủ**.

[Về đầu trang](#top)


## Audit evidence update — 2026-11-15

See [consolidated evidence](../validation/CONSOLIDATED_FIELD_EVIDENCE_2026-11.md) for the latest evidence inventory. Historical PENDING statements above describe the earlier stage: V11 now has repository aggregate results, while source pairs and per-cell outputs for all three locations remain unavailable in this revision. The retrievable Bao'an CSV and profiler are published with hashes; this does not establish full V11/GHSL or post-PR-27 acceptance.

<!-- END ORIGINAL -->

---

## Source: docs/audit-fixes-2026-11-11.md

<!-- BEGIN ORIGINAL -->
# Audit corrections and migration (11 November 2026)

Primary evidence: `verification-report.md` and `spatial-app-audit-evidence.zip`,
auditing commit `81a53c96eb1405c56665146325383c6e02350dc9`. Current main was
inspected and still matched that commit before these changes.

## Local Moran

The conditional null now fixes the focal observation and samples k **distinct**
values uniformly from the other m−1 active members, without replacement within
each replicate. Replicates are independent and may repeat. Sequential rejection
sampling retains bounded O(number of focal cells × maximum grid degree) working
memory, without constructing an m×m matrix. Queen/Rook weights, active sample,
edge handling, minimum sample/neighbor requirements and grid guards are unchanged.

Observed and simulated Local I now use
`(m−1) * z_i * mean(neighbor z) / sum(active z²)`, matching ESDA's normalization.
Consequently new I equals old I × (m−1)/m for the same sample. Signs, spatial lag
and raw quadrants are unchanged by normalization. The regional `moran_I_lit`
is a mean of these Local I values, not the app's binary-weight Global Moran I;
Global Moran's implementation has not changed.

The app retains inclusive upper/lower tails with absolute tie tolerance 1e-12,
the +1 Monte Carlo correction, doubled smaller-tail p capped at one, and the
existing Benjamini–Hochberg FDR family and thresholds. Its p floor remains
2/(permutations+1). ESDA's one-tail `p_sim` and tie handling differ, so raw p-values
are not promised to match, and matching seeds do not match random streams.

Recompute prior p-values, FDR decisions, hotspot areas, cluster membership,
spillover treatment/control assignments and downstream panel results. Old and new
results must not be pooled silently. Region exports include
`lisa_method_version=conditional-wor-esda-v2`; the LISA session-cache key also
changes. Restart active app sessions and regenerate stored exports/panels.

## Raster masks

Both main-app raster rewrites and `zonal_stat` now preserve explicit NoData and
GDAL masks and exclude NaN/infinite pixels before clipping valid negatives.
The rewritten raster declares NaN as NoData. Thus [10, −9999 NoData] has mean 10,
not 5 (clipped) or −4994.5 (unclipped). Valid zeros remain observations.

`fill_missing=None` preserves missing zonal means; the default final cell fill
remains zero. The app also retains its explicit final cell-level zero fill and
reports missing-result counts. Entirely missing/outside sums remain zero under
exactextract's sum convention. These final fills do not add invalid pixels to
partially observed pixel means. Earth Engine's existing upstream unmask-to-zero
convention is unchanged: an upstream zero cannot subsequently be distinguished
from an observed zero. No real satellite data agreement is claimed.

## Nan / Yiyang metadata

The audit's official full-resolution GADM 4.1 GeoPackage (SHA-256
`e8f9e5ead4526e30e0ccd83365b06c10ce25bbef8831f7881bdbc05a026f00bc`)
identifies source GID_3 `CHN.14.10.2_1` as NAME_3 `Nan`, under Yiyang.
The curated schema maps GID_3→GID_2 and NAME_3→NAME_2. Only NAME_2 is corrected
from Yiyang to Nan. The legacy filename `CHN_Hunan_Yiyang_Yiyang_District.geojson`
is deliberately retained for path compatibility; it is not an authoritative name.
Geometry, GID, type and processing folder are preserved. Joins should use GIDs;
name-based joins and saved display labels may need updating. This restores the
GADM source label and makes no claim about current legal administrative status.

## Validation

Use Python 3.12+ for the ESDA 2.10.0 benchmark dependencies (the application
runtime requirements are unchanged). `python -m pip install -r requirements-test.txt`
then `python -m pytest -q`.
Independent regression tests compare observed I with ESDA 2.10.0 on Queen/Rook
grids of 9, 100 and 400 cells, and conditional p with exhaustive corner-neighbor
combinations on 9- and 30-cell fixtures, distinguishing replacement nulls.
Complete-neighborhood ties, mask/sentinel/nonfinite raster means and sums,
ordering, outside coverage and both app rewrite sites are also covered.

No grid splitting/resolution, resource guard, Earth Engine authentication or
deployment policy was changed. Live Earth Engine acquisition and validation
remain conditional on legitimate authorization and were not performed here.

<!-- END ORIGINAL -->

---

## Source: docs/spacetime-relative-regime-interpretation.md

<!-- BEGIN ORIGINAL -->
# Space-Time LISA regime interpretation (display-only clarification)

## What the four regimes measure

The Space-Time module computes `log1p(max(NTL, 0))` at each of two selected years and standardizes the transformed values **separately within each year**, over the valid, non-edge analysis cells. It computes the mean neighboring z-score using the active Queen grid.

- `delta_z = z_t1 - z_t0`
- `delta_lag_z = lag(z)_t1 - lag(z)_t0`
- `movement_magnitude = sqrt(delta_z**2 + delta_lag_z**2)`

A regime is assigned only if the cell has valid neighbors and `movement_magnitude >= 0.05`. Cells below the threshold are `Excluded_or_Static`. This **0.05 cutoff is descriptive**, not a p-value, FDR cutoff, or other statistical significance test. In particular, Space-Time regime labels are not significance-tested Local Moran classifications.

The signs of `delta_z` and `delta_lag_z` identify changes in **relative NTL position**, not changes in the underlying radiance itself. A cell can increase in absolute NTL yet receive a relative-decline label if its within-year standardized position worsens.

| CSV identifier (unchanged) | English user-facing interpretation |
|---|---|
| `1_Synergistic_Growth` | Synergistic Relative Growth (focal and neighboring relative positions increase) |
| `2_Agglomeration_Shadow` | Cell Relative Decline / Neighbor Relative Growth |
| `3_Emergent_Pioneer` | Cell Relative Growth / Neighbor Relative Decline |
| `4_Synchronized_Decline` | Synchronized Relative Decline (both relative positions decrease) |

## Compatibility and scope

This change **only** updates bilingual explanatory text and the display table. It deliberately leaves the `spacetime_regime` CSV codes, `regime_summary` raw result, Space-Time equations, `movement_magnitude` threshold, Spatial Markov calculations, and export column names untouched. Existing scripts filtering `4_Synchronized_Decline` will continue to work.

The Yanqing, Beijing 2014–2020 validation found that 4,624 of the 4,711 cells classified with raw identifier `4_Synchronized_Decline` increased in **absolute** NTL. This illustrates the distinction; it does not imply a calculation error or verify the interpretation for every location/year.

## Remaining scientific limitations

Because z-scores are normalized separately by year, the regimes show changes in relative spatial standing. They do not directly measure economic growth or decline, and they do not establish causality. The proportion of cells in each regime is sensitive to the descriptive movement threshold; report this choice and consider sensitivity analyses when publishing results.

<!-- END ORIGINAL -->

---

## Source: validation/A02_POST_OPTIMIZATION_FIELD_2026-11-15.md

<!-- BEGIN ORIGINAL -->
# Bao'an A02: first field measurement after PR #27

Scope: Bao'an, 2020, 500 m, 7,148 cells. The recorder JSON was created at `2026-11-15T15:54:29+00:00`. PR #27 had merged earlier, but the JSON does not record its deployed commit, so the running build cannot be confirmed from this artifact alone.

## Directly inspectable files

- [New performance JSON](evidence/a02_post_pr27/spatial_app_performance.json): 2,185 bytes, SHA-256 `4d79fa4c056cce98bfe924e85d599102c21c0e16d0d5e8e81e289fefa4b5d68e`.
- [New LISA CSV](evidence/a02_post_pr27/CHN_guangdong_shenzhen_bao_an_2020_500m_lisa_cells.csv): 7,148 rows, 2,718,846 bytes, SHA-256 `c0e8bec2a5326ddb63b5c1a4992a876cbbd6150b4d052a4877ddb39b6a92519c`.
- The newly supplied main NTL CSV has SHA-256 `40b76f2f0f1fec0834be16f88e4b97084986886f5edc84d8718e28bf263eaece`, identical byte-for-byte to [the already published baseline CSV](evidence/audit-2026-11-15/baoan_ntl_2020_500m.csv). It is not duplicated in this PR. Its download timestamp alone cannot establish a fresh raster extraction.

All 7,148 `grid_id` values and their order match in the baseline NTL, newly supplied NTL, and new LISA exports. Every column shared between the two NTL files matches exactly, including all five A02 quality values, NTL indicators and grid metadata. Every column shared by the new main NTL and LISA exports matches exactly. The LISA CSV adds 20 fields; the file reports 1,007 High-High, 1,774 Low-Low, 3,405 Not Significant and 962 Edge-Masked cells. These are CSV comparisons, not independent raster or LISA computations. There is no prior LISA file body here to compare LISA-only values before and after.

## Measured performance

| Measure | Baseline | New | Difference |
| --- | ---: | ---: | ---: |
| A02 cell quality | 25.0028 s | 26.4623 s | **+1.4595 s (+5.84%)** |
| Main pipeline | 46.6687 s | 37.6479 s | -9.0208 s (-19.33%) |
| Grid build | 9.7399 s | 5.0124 s | -4.7275 s (-48.54%) |
| NTL zonal mean | 9.6193 s | 4.4589 s | -5.1604 s (-53.65%) |
| Sampled server-process RSS peak | 728.531 MiB | 688.941 MiB | -39.590 MiB (-5.43%) |

Both recorded pipelines succeeded. The new recorder stops after LISA; the historical one also includes subsequent GHSL stages. Its pipeline time ends before those later stages, while RSS is shared across the server process and can reflect other work. One run per version cannot isolate the effect of the A02 change, and the new A02 stage is slower in this run. **A02 numerical values are preserved at exported precision; an A02 runtime speedup is not demonstrated.**

## Diagnostic follow-up

This PR adds optional A02 substep timings and a `source_commit` field to the performance JSON. The detailed timing keys are `schema_validation_s`, `raster_read_normalize_s`, `memory_geotiff_write_s`, `polygon_extract_s`, `join_s` and `quality_status_s`, plus schema status and grid-cell count. The existing `a02.cell_quality` total remains the authoritative stage wall time; substep sums may differ due to uninstrumented overhead. No quality values, statistical estimators or export columns are changed.

After deployment, run several comparable Bao'an 2020/500 m analyses with the same settings, save each profiler alongside its CSV, verify `source_commit`, and compare A02 substep distributions. A separate field case with actual missing observations is still needed to test missingness semantics. No fresh Earth Engine or independent raster-overlay result is claimed here.

<!-- END ORIGINAL -->

---

## Source: validation/A02_PR_PROPOSAL.md

<!-- BEGIN ORIGINAL -->
# Preserve observational semantics alongside legacy NTL results (A02)

Missing observations, observed zero radiance and clipped negative annual medians can share `ntl_mean=0` under the current pipeline. Add per-cell observational fractions and monthly support metadata without changing legacy analysis values or statistical algorithms.

The change adds quality bands to annual raster downloads, retains their metadata in main/LISA exports, and includes both years in Space-Time CSVs. Regression tests cover mixed raster semantics and Space-Time UI/cache exports. CI discovers new test files automatically, preserving the A01 coverage fix from merged PR #19.

Validation: **66 local tests passed, no failures or skips** on Python 3.11 / Windows. JUnit results and reproducible synthetic sensitivity are recorded in `validation/evidence/a02/` and explained in `validation/DATA_SEMANTICS_A02.md`. Remote CI has not been run for this proposal. Synthetic missingness changes the measured indicators and classifications; it does not demonstrate an error in Yanqing's historical results.

Review as a draft until live Earth Engine multiband export, a real missingness case, and large-region resource checks are recorded. Additional CSV columns require review by consumers with strict schemas. Existing zero-fill policy remains in effect and is explicitly labeled in metadata.

Prepared with Codex assistance. Existing field rasters, independent comparison archives and historical validation results are attributed to their prior evidence records; this proposal does not claim their creation or independent authorship.

Review status: draft. Live Earth Engine and real-missingness acceptance remain pending; no automatic merge is authorized.

<!-- END ORIGINAL -->

---

## Source: validation/ADVANCED_STATISTICAL_VALIDATION_A03B.md

<!-- BEGIN ORIGINAL -->
# A03-B — Advanced statistical validation (incremental)

**Current lifecycle update (12 November 2026):** PR [#22](https://github.com/hoanfg/spatial-app/pull/22) was merged; its [GitHub Actions run #116](https://github.com/hoanfg/spatial-app/actions/runs/43249266533) completed successfully. This confirms that the covered CI jobs succeeded, **not** that independent field validation was completed. PR-time instructions below are retained as historical context.

## Scope and reproducibility

This is a **test-only** extension of A03 (PR #21), built on the existing `main` implementation. The source implementation, default scientific parameters, Earth Engine workflows and CSV schemas have not been modified.

To run from the repository root:

```sh
python -m pytest -q tests/test_advanced_statistics_a03b.py
python -m pytest -q tests
```

Do not infer results from the commands alone. Remote CI completion and the corresponding commit are the required execution evidence; a successful test run is not proof of correctness for all empirical data.

## Independent checks

1. **Conditional LISA permutations:** for four units with focal value 3 and non-focal values 1, -1, -3, each singleton non-focal subset is equiprobable. For an observed neighbor equal to 1, the inclusive upper/lower tail proportions are respectively 1/3 and 1. Under the repository's doubled-smaller-tail convention, the limiting one-sided and two-sided pseudo p-values are 1/3 and 2/3. The test enumerates all subsets independently using `itertools.combinations` and compares simulated p-values at 9,999 draws with stated Monte Carlo tolerances. These are **not ESDA's one-tail p_sim**.
2. **Tie semantics:** with four identical positive z inputs, every simulated statistic ties the observed value; inclusive comparison gives both tail proportions of 1. The two-sided p-value is capped at 1; Local I is 3/4 under the repository's sample denominator.
3. **Benjamini–Hochberg:** a four-test boundary case establishes step-up behavior and inclusive threshold comparisons. This is a statistical oracle, not a Monte Carlo assertion.
4. **Space-Time:** two identical observed years yield zero numerical movement and no directional regime. Replacing the central cell in the second year by NaN must not create an extensive exit, nor should the missing value be presented as a measured zero.

## Existing complementary coverage

`tests/test_zonal.py` already exercises clipped and unclipped zonal means, sums, raster masks, nodata and nonfinite inputs, and zero-filling versus preserving missing results. `tests/test_data_semantics.py` tests A02 quality bands. `tests/test_numerical_validation_a03.py` covers Gini, local I, binary global Moran reference, Queen neighbors, FDR and fixed-seed repeatability.

No large raster or GeoJSON fixtures are duplicated in this increment.

## Known limits / unresolved work

- Monte Carlo p-value tolerances characterize the **distribution**, not a specific RNG stream or numerical equivalence to PySAL/ESDA.
- No independent end-to-end comparison of all Space-Time transition matrices has been completed.
- Local Moran assumes valid non-isolated eligible focal units; behavior for empty neighbor sets, incorrect neighbor membership and insufficient population remains outside these tests.
- No live Earth Engine, large-region memory or real-world missingness evaluation is claimed.
- Verify new tests in CI before marking this increment ready to merge. If any test fails, investigate the source and oracle independently before changing production formulas.

## Evidence provenance

Only the small explicit synthetic observations printed in the test file are used as new reference evidence. The test design and this report were prepared with coding assistance, with no assertion of independently collected field data or completed external statistical replication.

<!-- END ORIGINAL -->

---

## Source: validation/DATA_SEMANTICS_A02.md

<!-- BEGIN ORIGINAL -->
# A02: data semantics validation

Date: 12 November 2026. Base: `719ccf1953373326fac8451e7e0571e09961acf9`, the merge of audit PR #19. New validation documentation, evidence labels and PR proposal use English. Existing localized UI strings retain the application's language switch.

## Acceptance and evidence

| Requirement | Implementation / evidence | Status |
|---|---|---|
| A01: existing and new tests enter CI | Core job retains its two files; UI job discovers `tests/`, excluding exactly those two core files | Implemented; local suite executed; remote CI not executed for this change |
| A02: distinguish zero, no observation and clipped negatives per cell | Annual-median mask, negative/zero indicators, monthly support, cell extraction and CSV fields | Synthetic raster and UI contracts verified |
| A02: quantify effects before changing policy | `run_a02_semantics.py`, `evidence/a02/synthetic_sensitivity.json` | Synthetic sensitivity characterized |
| Preserve existing scientific calculations | Band 1 remains median → unmask(0); negative clipping and cell filling remain as before | Regression suite and explicit expected raster values |
| Evidence from missing observations in real products | No new Earth Engine export or missingness field study performed | Pending; not a claim of full field validation |

The audit's A02 is a methodological risk, not proof that missingness corrupted the published Yanqing results. This change adds observability; it does not select an observed-only analysis policy or retroactively validate existing exports.

## Data contract

`fetch_ntl_raster` exports six float bands on the same raster grid:

1. `avg_rad`: historical annual median of monthly `avg_rad` masked by `cf_cvg > 0`, then unmasked to zero.
2. `dq_observed_fraction`: annual median mask (1 observed, 0 no valid monthly radiance).
3. `dq_negative_fraction`: annual median below zero, before clipping; missing contributes zero.
4. `dq_zero_fraction`: annual median exactly zero; missing contributes zero.
5. `dq_mean_valid_months`: number of valid monthly radiances, missing contributes zero.
6. `dq_low_month_fraction`: monthly count below 3, including count zero.

Raster band identifiers become cell CSV column names. Binary bands are reduced using exact fractional pixel coverage, so the resulting values are area fractions. Monthly counts become area-weighted means; the low-month field is a fraction, not an inference based on the mean count. Fractions refer to raster-covered polygon area; the main pipeline pads its bounding box around the grid. These are annual-median indicators, not fractions of all monthly measurements. `cf_cvg` is cloud-free observational support, not a comprehensive atmospheric or radiometric quality assessment.

`dq_status` is `observed`, `partial_observation`, `no_observation`, or `unknown`. An observed zero has positive observed fraction and positive zero fraction. A clipped negative has positive negative fraction. Missing radiance has zero observed fraction even when `ntl_mean` is zero. Partial coverage does not get relabeled as a measured zero. A legacy single-band file, an unsupported band schema or a cell outside the raster produces unknown metadata; its zero values cannot establish observation.

`dq_stat_missing` separately records a missing zonal result or missing join before cell-level zero filling. It is distinct from the observation mask. `dq_ntl_policy=legacy_zero_fill` explicitly identifies the calculation policy. Metadata is additive: original NTL and classification columns retain their names and values. Consumers that require an exact column list must allow the new `dq_` columns.

Main cell and LISA downloads inherit these fields. Space-Time CSVs additionally carry quality fields suffixed with each year, so t0 support is not inferred from t1. The callback accepts a DataFrame with `ntl_mean` plus quality columns; legacy array callbacks remain supported. Cache versions change to avoid reusing pre-A02 raster/dynamics entries. Existing results held in old sessions require a fresh analysis to obtain metadata.

## Reproducible synthetic evidence

From the repository root, in an environment with `requirements-test.txt` installed:

```sh
python -m pytest -q tests
python validation/run_a02_semantics.py
```

The raster tests cover measured zero, no observation, valid negative median, low monthly support, mixed coverage within a polygon, cell reordering, unknown legacy coverage, outside-raster cells and CSV roundtrip. An AppTest triggers the actual Space-Time UI with a quality-bearing callback, checks both years, and checks cached reruns for duplicate columns. Earth Engine behavior is represented by a masked-array double, explicitly not a live-service benchmark.

Local acceptance run: **66 passed, zero failures, zero skips, 96.05 seconds**, Python 3.11 on Windows. Command: `python -m pytest -q tests --junitxml=validation/evidence/a02/pytest.xml`. The raw JUnit report is committed with the proposed files. This is local execution evidence, not a GitHub Actions or Python 3.13 result.

The sensitivity experiment uses a 6×6 synthetic 500 m grid, a genuine zero and six deliberately removed positive observations. It records input values, affected indices, seed 42, 99 Local Moran permutations and package versions. It compares complete data, missing-as-zero and an observed-only sensitivity scenario. Global Moran is binary Queen I without a p-value; Local Moran retains its own documented eligibility and weights. The observed-only scenario changes the sample and neighbor graph and is not a recommended replacement estimator.

| Metric | Complete synthetic data | Six cells filled with zero |
|---|---:|---:|
| Mean NTL | 10.9444 | 9.1944 |
| Zero-cell share | 0.0278 | 0.1944 |
| Gini | 0.305415 | 0.428919 |
| Binary Queen Global Moran I | 0.731877 | 0.620963 |
| Changed LISA labels | Reference | 6 / 36 |
| Changed Space-Time regimes | No-change two-year reference | 33 / 36 |

The Space-Time contrast holds the underlying radiance constant and inserts missingness only in t1. Resulting regimes demonstrate possible artificial movement under the legacy policy; their descriptive vector threshold does not establish statistical significance.

## Real-data provenance and limits

The existing repository raster `validation/evidence/yanqing/rasters/yanqing_viirs_2014_reference.tif` has SHA-256 `637661ab304986ef19befa4c7ca62d1e9cface500862803f02ad76a4b6637c31`, matching its published evidence index. This run counted 30,814 finite pixels, zero exact-zero pixels and one negative pixel. It has one band and no monthly observation counts. Finite pixels do not prove cloud-free monthly support. The raster was deposited by prior work; it was not collected or independently generated in this task. Prior validation reports and archives retain their original provenance and limitations.

The current code, tests, synthetic experiment and this report were prepared with Codex assistance in this task. Synthetic results are new implementation checks, not new independent field validation or a reproduction of the entire earlier evidence campaign. No human-only or independent-contributor authorship is asserted.

Live Earth Engine multiband GeoTIFF band descriptions, downloads with large regions, Cloud RAM/time, and real missingness cases remain unverified here. Six bands increase download and in-memory raster size relative to the original one-band request and may reach service limits sooner. Five quality reductions add extraction work. Before production acceptance, export a region with known zero-support and low-support pixels, confirm the six band identifiers, compare band 1 with the prior extraction at identical projection/scale, and verify per-cell flags through both year downloads. Record source collection, dates, bounds, projection, checksums and outputs. Do not mark field A02 complete until that evidence is deposited.

No new policy is applied to Gini, Moran, LISA, Space-Time, GHSL or robustness. Automatic exclusion of missing cells would require a separate scientific decision with real-data sensitivity evidence.

<!-- END ORIGINAL -->

---

## Source: validation/INTEGRATION_AUDIT_2026-11-11-vi.md

<!-- BEGIN ORIGINAL -->
# Kiểm toán tích hợp và hồi quy — spatial-app

**Ngày:** 11/11/2026  
**Commit được đánh giá:** `44f2347cffca1e761350bb948df8fa7ce4f22f9f` (`main` tại thời điểm bắt đầu)  
**Phạm vi:** `app.py`, `ntl/`, `tests/`, `.github/workflows/`, khai báo dependencies và ranh giới tích hợp các chức năng. **Không** kiểm định lại 19.987 GeoJSON.  
**Phương pháp:** đọc mã nguồn, xác định hợp đồng dữ liệu giữa các module, đối chiếu CI run thực tế và thêm kiểm thử hồi quy tổng hợp. Không thay đổi thuật toán trong PR này.

> **Mức độ bằng chứng:** Đọc được toàn bộ 23 file Python của repo qua GitHub, kiểm tra workflow và log GitHub Actions thực tế trên main. Đợt kiểm toán mới **không** tự tải dữ liệu Earth Engine hoặc chạy end-to-end trên Streamlit Cloud; các kết quả này phải được phân biệt với regression tests dùng dữ liệu tổng hợp.

## 1. Kết quả xác minh bằng CI

- Trên main tại commit nêu trên, GitHub Actions run [#43053877659](https://github.com/hoanfg/spatial-app/actions/runs/43053877659) **SUCCESS**, gồm **32** test ở job `core` và **22** test ở job `ui-smoke`, tổng **54 passed**.
- CI trước thay đổi chạy năm file: `test_lisa_reliability.py`, `test_robustness.py`, `test_zonal.py`, `test_ui_smoke.py`, `test_audit_regressions.py`.
- File `tests/test_spacetime_labels.py` có trong `tests/`, nhưng **không nằm trong lệnh pytest của workflow**. Đây là phát hiện A01 xác nhận được: CI xanh không chứng minh file đó được thực thi.
- Branch audit bổ sung test này vào job giao diện, cộng `tests/test_pipeline_integration.py` mới. Trạng thái final của CI trên branch/PR phải được ghi bằng chính run tương ứng; **không dùng trạng thái main để tuyên bố PR mới PASS**.

## 2. Phát hiện và phân loại

| Mã | Phát hiện | Phân loại | Mức độ | Hành động |
|---|---|---|---|---|
| A01 | CI bỏ qua `test_spacetime_labels.py` | **Lỗi xác nhận** | P0 | Bổ sung vào workflow; kiểm tra log job |
| A02 | `.unmask(0)` và `.fillna(0)` khiến missing/no-observation và zero quan sát có thể cùng xuất thành 0 | **Chính sách dữ liệu hiện hành, rủi ro diễn giải** | P1 | Giữ thông tin coverage/quality flags; benchmark dữ liệu có missing trước khi đổi |
| A03 | Global Moran dùng toàn lưới/binary Queen; Local Moran dùng tập ô hợp lệ và row-standardized Queen | **Khác biệt estimand có chủ ý, nguy cơ bị diễn giải như cùng một mẫu** | P1 | Cập nhật tài liệu thuật ngữ, kiểm tra xuất metadata |
| A04 | Hai hàm Gini khác nhau về xử lý NaN/âm (`app.py` vs `ntl/lisa_core.py`) | **Trùng logic, hành vi khác nhau với dữ liệu lỗi** | P2 | Thêm test hợp đồng và thống nhất quy tắc sau review |
| A05 | `requirements.txt` phần lớn chưa pin phiên bản; CI core dùng Python 3.11, smoke dùng 3.13 | **Rủi ro tái lập môi trường** | P1 | Lock/tested matrix, ghi phiên bản tại export |
| A06 | `app.py` ~2.688 dòng kiêm tải raster, grid, Moran, UI, export | **Coupling/maintainability** | P1 | Refactor từ từ sau khi có E2E tests, không viết lại toàn bộ |
| A07 | MAUP trong `ntl/robustness.py` sử dụng block aggregation từ ô mịn, không đồng nhất bắt buộc với dựng trực tiếp lưới thô từ raster | **Khác biệt phương pháp** | P1 | Đặt tên đúng, so sánh 2 cách trên dữ liệu thật |
| A08 | GHSL `nearest_epoch()` và `unmask(0)` | **Giới hạn temporal/missingness** | P1 | Kiểm tra năm sản phẩm và mask, tái lập GHSL độc lập |
| A09 | Ngưỡng `rho = 0.40/0.60` mang tính thực hành | **Giới hạn suy luận đã nêu trong code** | P2 | Giữ là tham khảo, không coi là kiểm định thống kê |
| A10 | Cache theo phiên, theo kết quả và cấu hình; chưa stress-test nhiều phiên | **Chưa kiểm chứng performance** | P2 | Đo RAM/TTL/invalidation sau khi có benchmark |
| A11 | `test_ui_smoke.py` gọi `render_lisa_tab` với dữ liệu tổng hợp; không kích hoạt toàn pipeline Earth Engine | **Khoảng trống E2E** | P1 | Test hợp đồng raster→LISA→CSV, sau đó Cloud/Earth Engine thật |
| A12 | README, specification, validation song ngữ chứa mô tả phương pháp trùng lặp | **Nguy cơ drift tài liệu** | P2 | Tách nguồn chân lý và kiểm tra version/config ở các tài liệu |

### 2.1. Chi tiết A02: zero khác với thiếu quan sát

- `app.py:1406–1443` tính `median` ảnh tháng hợp lệ rồi `unmask(0.0)`.
- `app.py:1911–1927` chuyển thống kê zonal `NaN` và kết quả không ghép được thành `0.0`.
- `ntl/zonal.py` giữ masked/NaN của raster hợp lệ trước lúc trích xuất, nhưng mặc định `fill_missing=0.0` nếu caller không đổi.
- `ntl/data_quality.py` có metadata và cảnh báo phù hợp; `quality_ui.py` có phép đếm tháng hợp lệ theo yêu cầu.
- **Không có bằng chứng từ Yanqing 2014/2020 cho thấy lỗi missing xảy ra**: raster pilot có 12 composite tháng hợp lệ trên toàn bounding-box được thử. Không nên coi một tình huống khác là bug đã tác động đến kết quả Yanqing.

### 2.2. Chi tiết A07: đừng nhập hai phép MAUP làm một

`robustness.aggregate_blocks` nhóm chỉ số lưới mịn thành factor×factor và lấy bình quân theo diện tích ô trước khi chạy lại LISA. Điều này là phép thử block aggregation, **không nhất thiết tái lập** raster→polygon của lưới 1.000 m được dựng trực tiếp từ ranh giới. Sự khác biệt phải ghi trong cả phần diễn giải và bảng phương pháp, không tự kết luận sai số hay thay kết quả trước đó.

## 3. Thử nghiệm tích hợp mới

File `tests/test_pipeline_integration.py` dùng GeoTIFF tổng hợp lưu trong bộ nhớ và đa giác UTM 500 m, gồm bốn phép kiểm:

1. **Raster → zonal mean → Local Moran → CSV**: kiểm tra thứ tự và định danh 16 ô, dữ liệu NTL, nhãn cụm, xuất/đọc CSV.
2. **Missing vs measured zero**: pixel 0 quan sát, NoData sentinel và negative radiance hợp lệ phải phân biệt được trước khi `fill_missing=0`; ghi rõ rằng chính sách fill làm các giá trị cuối có thể giống nhau.
3. **Space-Time label compatibility**: hàm hiển thị không được biến đổi `regime_summary` hoặc mã CSV gốc.
4. **Space-Time CSV contract**: kiểm tra trường số, mã regime và sự ổn định sau CSV roundtrip.

Đây là kiểm tra liên module trên dữ liệu nhân tạo; **không** thay thế thực nghiệm ảnh từ Earth Engine, GHSL hoặc Streamlit Cloud. Trạng thái chạy CI của branch/PR được xem là bằng chứng riêng, không suy diễn từ main.

## 4. Những điều chưa thể xác nhận

- Chưa thu thập bằng chứng của 3 địa phương Cross-location V11; vẫn **PENDING**.
- Chưa chạy export/download VIIRS, GHSL, hoặc hoàn thiện E2E trên Streamlit Community Cloud trong đợt này.
- Chưa kiểm tra đầy đủ mọi hành vi interactive của Streamlit (nhiều phiên, tải lại, reset cache, errors).
- Chưa xác minh toàn bộ so sánh văn bản README, tài liệu kỹ thuật và UI theo từng câu.
- Chưa pin production dependency hay thay đổi công thức phân tích.

## 5. Tiêu chí chấp nhận và thứ tự ưu tiên

- **Ngay:** CI phải chạy đủ 6 file có sẵn + file integration mới; test mới phải PASS và không che giấu fail bằng skip không chủ đích.
- **Sau đó:** tạo bộ dữ liệu cố ý có NoData, low coverage, negative pixel để đo ảnh hưởng đến LISA và CSV; chỉ thay policy khi có kết quả thực nghiệm.
- **Tiếp:** đối chiếu MAUP coarsening từ block với exact raster-on-coarse-grid; độc lập kiểm tra GHSL.
- **Cuối:** benchmark tài nguyên và multiple sessions trên Streamlit Cloud; thiết lập lockfile/compatibility matrix; refactor từng phần có regression test.

**Quy tắc thay đổi:** không gộp việc sửa thuật toán, đổi kết quả CSV hoặc chính sách missing vào PR chỉ bổ sung tests. Mọi thay đổi khoa học cần test hồi quy và bằng chứng đối chiếu riêng.

## 6. Nhật ký bằng chứng

| Bằng chứng | Nơi kiểm tra |
|---|---|
| Commit gốc được audit | `44f2347cffca1e761350bb948df8fa7ce4f22f9f` |
| Main CI run (54 PASS) | https://github.com/hoanfg/spatial-app/actions/runs/43053877659 |
| Workflow CI | `.github/workflows/tests.yml` |
| Regression source | `tests/test_spacetime_labels.py` |
| New contract tests | `tests/test_pipeline_integration.py` |
| Main pipeline, export | `app.py:1382–1504, 1845–1960, 2639–2675` |
| Spatial inference and dynamics | `ntl/lisa_core.py:41–190, 385–729` |
| Robustness | `ntl/robustness.py:18–192` |
| Data quality and GHSL | `ntl/data_quality.py`, `ntl/quality_ui.py`, `ntl/ee_extra.py` |
| Raster extraction contract | `ntl/zonal.py` |


<!-- END ORIGINAL -->

---

## Source: validation/MAJOR_REVIEW_COVERAGE_EVIDENCE_2026-11.md

<!-- BEGIN ORIGINAL -->
# Major validation review — coverage and evidence reconciliation

**Review date:** 12 November 2026  
**Source:** `hoanfg/spatial-app`, `main` following merged PRs #19–#22.  
**Purpose:** reconcile test coverage, evidence availability and outstanding external validation without duplicating synthetic test suites. This review does **not** amend statistical estimators, missing-data policy, VIIRS/GHSL processing or production exports.

## Evidence levels

- **CI verified:** the checked-in code paths were exercised by a successful GitHub Actions run. This is neither field validation nor an external benchmark.
- **Numerical / synthetic verified:** a specified formula or synthetic case is reproduced, with an explicit oracle and tolerance.
- **Archival numeric cross-check:** values already stored in the original evidence archive are checked for internal consistency. This does not recreate all source measurements.
- **Historical field reference:** a previously deposited independently prepared raster/geometry comparison with provenance, scripts and outputs. Its accuracy is only established within the recorded location, year and precision.
- **Pending / not covered:** no sufficient independent evidence of the stated claim.

Do not infer a broad scientific PASS from only CI or synthetic evidence. The historical README reports are snapshots and are not proof that current production outputs were field-validated following later implementation changes.

## Coverage matrix (avoid duplicate test suites)

| Concern | Existing tests / evidence | Scope currently supported | Outstanding check |
|---|---|---|---|
| CI discovery and integration | `.github/workflows/tests.yml`; `tests/test_pipeline_integration.py`; PR #19 | Regression paths, synthetic raster→LISA→CSV; CI discovers later tests | Full live Earth Engine→Streamlit→export run |
| A02 observational semantics | `tests/test_data_semantics.py`; `validation/DATA_SEMANTICS_A02.md`; `validation/evidence/a02/`; PR #20 | Quality-band contract, zero vs missing in synthetic cases; no change to legacy zero-fill values | Real six-band Earth Engine export and genuine missing/low-support cases |
| NTL zonal mean/sum | `tests/test_zonal.py`, `test_pipeline_integration.py`; Yanqing archival comparisons | Nodata/mask/negative handling for synthetic rasters; Yanqing 2014/2020 matches recorded independent reference values at 4 decimal places | Real cross-location raster/cell comparison, new six-band behavior |
| Gini | `tests/test_numerical_validation_a03.py`; PR #21 | Pairwise definition, known-value cases | Reconcile divergent invalid-input conventions in `app.py` vs `ntl.lisa_core` (A04); do not silently change |
| Queen/Rook and Global Moran | `tests/test_numerical_validation_a03.py`; `test_robustness.py` | Synthetic graph and binary global-I reference, Queen/Rook alternative specifications | Matched geographic sample and weights in each scientific comparison |
| Local Moran observed I | `tests/test_audit_regressions.py` (ESDA comparison), `test_numerical_validation_a03.py`; historical Yanqing LISA archive | Deterministic ESDA-scale observed statistic, row-normalized local lag and quadrants | Other locations and real-data numerical perturbation |
| Conditional permutations | `tests/test_audit_regressions.py` (exhaustive null), `tests/test_advanced_statistics_a03b.py` (small exact case); PR #22 | Without-replacement distribution and inclusive-tail convention tested at two scales | Quantified Monte Carlo stability in new morphologies; avoid new overlapping tests |
| BH-FDR | `tests/test_audit_regressions.py`, `test_numerical_validation_a03.py`, `test_advanced_statistics_a03b.py`; Yanqing archived CSV | Step-up threshold, ties, boundaries; exported p-values reproduce 2,880 significant cells | Explain different-seed sensitivity; no need to repeat an identical small synthetic FDR case |
| Space-Time and Markov | `test_spacetime_labels.py`, `test_lisa_reliability.py`, `test_advanced_statistics_a03b.py`, historical Yanqing archive | Label compatibility, missing-year contract, Markov invariants, historical 2014→2020 comparisons | Full annual series, additional locations, source raster coverage |
| Cross-location V11 | `validation/cross_location/` | Three locations selected, boundaries and comparator scripts documented; Yanqing pilot comparator | Shanghai, Bao'an, Qimen VIIRS references, app exports and independent per-cell comparisons — **PENDING** |
| GHSL | `ntl/ee_extra.py`, quality UI and historical validation master | Application-reported diagnostics and synthetic integration | Independently derived source raster grid metrics and sensitivity — **PARTIAL** |
| Cloud reliability | `test_ui_smoke.py` and diagnostics fallback tests | Synthetic Streamlit smoke-level regression | Cloud execution, multiple sessions, actual RAM/runtime/failure modes — **PENDING** |
| Economic construct validity | Validation master discussion | Methodology and limitations documented | Externally published independently aligned economic outcome — **PENDING** |

### Overlap decision

`test_exhaustive_conditional_null` predates A03-B and already benchmarks conditional permutations. A03-B adds a smaller explicit oracle and tie/FDR/temporal edge cases. Both may remain until a measured maintenance cost or redundant assertion justifies removal; **no new permutation/FDR tests are warranted from this review alone**. Avoid confusing necessary **re-execution of regressions** with unnecessary **duplication of test code**.

## Reconciled Yanqing archive status

A historical consolidated package was located in the user's private file Library:
`spatial_app_2026_11_11_validation_evidence_complete.zip`.

- Recorded archive size: **5,554,282 bytes**.
- Observed SHA-256: `95b3874d4253eec2269f2477b648a067fb14d1c94be54bc0ed38f8795599260c`.
- **73 file entries plus `EVIDENCE_MANIFEST.json`**; ZIP CRC and every manifest size/SHA-256 matched.
- The archive has **not** been uploaded into this public GitHub repository. Do not imply public availability, append it to a commit or redistribute without authorization.

The independent, read-only check `validation/audit_evidence_archive.py` was executed locally using the private archive. Its computed results:

| Audit calculation | Measured result | Interpretation |
|---|---:|---|
| Manifest size and SHA-256 | 73/73 matched | Archive integrity against its manifest; not origin authenticity |
| 2014: app CSV vs archived raster-derived reference | 8,333/8,333 within 0.00005 | Comparison of **stored** independent reference columns, not a fresh pixel-overlay run |
| 2020: app CSV vs archived raster-derived reference | 8,333/8,333 within 0.00005 | Same qualification as 2014 |
| Recomputed BH step-up from exported p-values | 2,880 significant; 0 disagreements | New independent Python calculation from archived p-values |
| Between-seed BH disagreements in archived columns | 179 | Monte Carlo sensitivity, not proof of a calculation defect |
| Cross-file 2014→2020 `delta_ntl` and regime labels | max delta error 0; 0 regime disagreements | Consistency of archived derived tables, not a fresh classification from raw imagery |

The check was also run against a deliberately modified ZIP member with the old manifest; it exited non-zero and reported a size/SHA-256 mismatch. This demonstrates an integrity check failure path, not a malicious-file security assessment.

Run on a locally available archival package (no new dataset is downloaded):

```sh
python validation/audit_evidence_archive.py /path/to/spatial_app_2026_11_11_validation_evidence_complete.zip --output /tmp/major_review_evidence.json
```

No package contents or private data are embedded in code or evidence committed by this review. A GitHub CI job should **not** skip/pretend to verify these field measurements when the archive is unavailable.

## Concrete documentation and data gaps

1. **Stale A03/A03-B snapshots:** their original text refers to draft/pending CI, even though PR #21 and #22 subsequently merged. Preserve historical claim timing and append status update with independently checked CI links.
2. **Public archive gap:** the Yanqing evidence index correctly states that the full 73-file package is not in the repo. Do not change that claim merely because the archive was found privately.
3. **V11 remains PENDING:** `compare_raster_cells.py` currently independently checks *radiance band 1* raster zonal means. A02 added five observational quality bands; field-level six-band quality validation cannot be inferred from that comparator.
4. **A04 remains a contract question:** Gini functions differ for nonfinite/negative input handling; decide a common rule based on intended data semantics before changing output.
5. **Reference scope:** older Yanqing single-band historical exports do not establish the new A02 multiband Earth Engine behavior. A full independent field audit of GHSL, Space-Time time series, three contrasting locations and Streamlit Cloud has not occurred in this review.

## Merge gate for one major review

- [x] Inventory tests and identify overlapping coverage.
- [x] Identify existing evidence and keep private archival data separate.
- [x] Run archive integrity, BH-FDR and cross-file checks from stored references; verify tamper detection.
- [ ] Review CI for this branch and verify documentation changes.
- [ ] Complete independent real six-band / cross-location validation (requires source exports not yet present).
- [ ] Complete GHSL and Cloud operational field checks (requires service/runtime data).

The final three pending items are **explicit future evidence dependencies**, not an implied obligation to fabricate data or delay every independent documentation fix. This document is an honest consolidation of scope, not a declaration that V11, GHSL or Cloud validation passed.

<!-- END ORIGINAL -->

---

## Source: validation/NUMERICAL_VALIDATION_A03.md

<!-- BEGIN ORIGINAL -->
# A03 — Numerical and statistical reference validation

**Current lifecycle update (12 November 2026):** PR [#21](https://github.com/hoanfg/spatial-app/pull/21) was merged; its [GitHub Actions run #111](https://github.com/hoanfg/spatial-app/actions/runs/43219550320) completed successfully. **Coverage remains partial:** numerical unit tests are not a general field-validation result. The original PR-time discussion below is retained as historical context.

Historical PR-time status: **partial, draft-only**. This change adds a small, deterministic core of independent reference tests. It does **not** certify all Spatial App statistical results or replace the remaining A03 audit tasks.

## Reference definitions

- **Gini:** compare the production sorted-rank formula against the independent pairwise absolute-difference definition, `sum_i sum_j |x_i-x_j| / (2 n sum_i x_i)`. All-zero and empty samples follow the existing implementation's zero convention.
- **Binary global Moran's I (manual oracle):** four connected units in a chain with values 1, 2, 3, 4 have centered values -1.5, -0.5, 0.5, 1.5, six directed links, directed cross-product 2.5, and squared sum 5. Hence `(4/6) * (2.5/5) = 1/3`. This is an independently computed reference, **not** a call to the application's global statistic.
- **Local Moran:** the same four units with row-standardized neighbors yield lags `[-0.5,-0.5,0.5,0.5]`; the current ESDA-style sample denominator is `5/3`; expected local I is `[0.45,0.15,0.15,0.45]`. Classification quadrants are LL, LL, HH, HH. This only verifies the deterministic observed statistic, not calibration of permutation p-values.
- **FDR:** for p-values `[.2,.01,.04,.001]`, Benjamini–Hochberg at 5% rejects the second and fourth entries only.
- **Queen neighbors:** all four cells of a 2-by-2 grid are mutual Queen neighbors. Explicit integer grid indices isolate adjacency from coordinate rounding.
- **Seed:** same seed and same input produce the same simulated p-values; this does not imply agreement with other RNGs or permutation conventions.

## Running the tests

```sh
python -m pytest -q tests/test_numerical_validation_a03.py
python -m pytest -q tests
```

These are executable acceptance commands, **not evidence of a completed local run**. Record GitHub Actions results and any local JUnit output before moving the PR out of draft.

## Coverage boundaries and follow-ups

The test suite does not yet provide a live Earth Engine result, a complete independent reference for LISA conditional permutation distributions, spatial weight normalization against a second implementation, end-to-end NoData invariants over both years, or broad-region resource testing. ExactExtract NTL mean/sum edge cases remain in the existing `tests/test_zonal.py`, and A02's observation-support contracts remain in `tests/test_data_semantics.py`; those tests should remain in CI.

A previous A02 fixture and report already exist under `validation/evidence/a02/`. Avoid copying those files or depositing new large GeoJSON into this PR. No production statistical formulas or scientific interpretation are changed by this test-only increment.

<!-- END ORIGINAL -->

