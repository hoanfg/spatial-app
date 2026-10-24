# TECHNICAL SPECIFICATION: GADM v4.1 DATA EXTRACTION ARCHITECTURE & COUNTRY CLASSIFICATION FOR SPATIAL ECONOMETRICS

**Project:** Nighttime lights (NTL) data extractor & Spatial econometrics engine  

**Document version:** 1.0  

**Objective:** Standardize global administrative boundaries from the GADM v4.1 database (`.gpkg`) into a consistent 3-level structure (`Country -> Level 1 Folder -> Level 2 GeoJSON File`) for VIIRS nighttime radiance extraction and LISA/Moran's I testing - [[Read the technical manual here]](README-vi.md).

---

## 1. DIAGNOSING THE ROOT CAUSES OF GARBAGE DATA IN GADM v4.1

When automatically processing GeoPackage files (`gadm41_XXX.gpkg`), there are 5 technical pitfalls that cause conventional extraction scripts to generate garbage data or distort spatial regression results:

1. **The `"NA"` string trap (literal string `"NA"` vs. SQL `NULL`):**
   The GADM v4.1 database was exported from an R environment (`terra` / `sf`), in which many missing values in the `NAME_1`, `NAME_2`, `NAME_3`, `TYPE_2`, and `ENGTYPE_2` columns are stored as the **text string `"NA"`** (or `"?"`, `"Unknown"`) rather than as a `NULL` (`NaN`) value. As a result, Pandas' `.dropna()` function completely misses these rows, leading to:
   * The creation of a garbage folder named `NA` (when `NAME_1 == "NA"`).
   * The merging of dozens of unrelated urban districts (sharing `NAME_2 == "NA"`) into a giant multipolygon weighing tens of MB.

2. **The inland water polygon trap (`Water body` / `Lake` polygons):**
   In GADM v4.1, many large lakes, bays, or inland waters are cut into separate polygons in the `ADM_2` and `ADM_3` layers, with the `ENGTYPE_2` / `ENGTYPE_3` columns containing values such as `"Water body"`, `"Lake"`, and `"Inland water"`. If these rows are not filtered out before exporting the files, the econometric model will include entire lakes in the analysis sample with a nighttime light radiance value of $\mathrm{NTL} = 0$, causing severe bias in the light Gini coefficient and economic density.

3. **The administrative-unit name collision trap (name collision when `GID_x` is not used):**
   If the extraction loop uses only `.unique()` on the `NAME_2` or `NAME_3` column, different administrative units that share the same Latin-transliterated name within the same state/province will be merged into a single `.geojson` file:
   * **United States (`USA`):** Independent cities in Virginia, Maryland, and Missouri share names with the counties surrounding them (e.g., *Fairfax City* and *Fairfax County*; *Baltimore City* and *Baltimore County*; *St. Louis City* and *St. Louis County*). They have the same `NAME_2` and are distinguished only by `GID_2` and `ENGTYPE_2`.
   * **China (`CHN`) and Vietnam (`VNM`):** When diacritics are removed or Pinyin transliteration is used in GADM, many districts/counties with different Chinese characters or administrative types (`Shi` vs `Xian`) can have the same string in `NAME_3` / `NAME_2`.
   * **Mandatory rule:** Always group (`groupby`) by the unique identifier key `GID_x` (such as `GID_2`, `GID_3`) instead of `NAME_x`. If two different `GID_x` values in the same folder have the same `NAME_x`, automatically append a suffix using `ENGTYPE_x` or the `GID_x` code.

4. **The micro-fragmentation trap:**
   The native resolution of monthly VIIRS DNB satellite imagery is $$\approx 463.83 \text{ m}$$ (pixel area $\approx 0.215 \text{ km}^2$), and the LISA/Moran's I testing algorithm in the system requires at least $N \ge 30$ grid cells to make statistically meaningful inferences. With standard grids of $$500 \text{ km}^2$$ - $$1000 \text{ km}^2$$, the ideal analysis unit should have a minimum area ranging from $$10 \text{ km}^2$$ to $$5,000 \text{ km}^2$$ (equivalent to the district/county/city level). If the script automatically reads the deepest layer (`ADM_3` or `ADM_4`) for every country, countries such as Vietnam, France, Thailand, and Indonesia will be pushed down to the commune/ward level ($$0.2 - 5 \text{ km}^2$$, crippling LISA testing).

5. **The urban-rural administrative hierarchy asymmetry trap:**
   Some countries have large metropolitan areas directly under the central government or urban counties with a missing intermediate level (such as `GBR`, where Metropolitan counties and Unitary authorities have `NAME_2 == "NA"`; or `CHN`, where the four centrally administered municipalities of Beijing, Shanghai, Tianjin, and Chongqing appear directly in `NAME_1`).

---

## 2. ARCHITECTURAL TRADE-OFF ANALYSIS

The table below compares 3 architectural approaches for the data pipeline:

| Evaluation criterion | Approach 1: Blind dynamic self-healing (Automatically read the deepest layer + skip columns when encountering `'NA'`) | Approach 2: Simple strict extractor + front-end alias JSON (Hard-coded extraction + name mapping in the UI) | Approach 3 (Recommended): Declarative rule-driven ETL (Extraction controlled by a country rules table) |
| :--- | :--- | :--- | :--- |
| **Geometry quality** | **Low:** Large county-level polygons can easily be mixed with small commune/district-level polygons within the same country when only some rows have `NAME_2 == 'NA'`. | **Low (if the source data is asymmetric):** The JSON file in the front end can only change display labels; it cannot split an incorrectly merged 37MB `NA` polygon already written to disk. | **Absolute:** Fully resolves geometry merging/splitting (`dissolve` by `GID`) during `.geojson` file creation. |
| **Econometric consistency** | **Poor:** Causes *Cross-level mixing* (rows in the panel are not at the same administrative level, violating the assumption of homogeneous observational units). | **Good** for homogeneous countries (`CHN`, `VNM`), but **fails** for hybrid cases (`GBR`, `TWN`). | **Optimal:** Ensures that 100% of `.geojson` files within a country represent economically equivalent units. |
| **Runtime performance on Streamlit Cloud (~1GB RAM)** | **Risk of memory overflow:** Generates tens of thousands of commune/ward-level files for countries with `ADM_3`/`ADM_4`. | **Fast:** The front end is lightweight, but a huge JSON file with tens of thousands of rows must be maintained if each district name needs to be corrected. | **Optimal:** All computationally intensive processing is performed offline once. `app.py` retains the current lightweight folder-reading structure. |
| **Maintainability** | Difficult to control hidden errors when adding new countries. | Both the extraction script and the JSON file in the front end must be modified. | Only one rule declaration (5 attributes) needs to be added to the `COUNTRY_RULES` dictionary in the ETL script. |

**Architectural conclusion:**  
Do not place geometry-fixing logic in the front end, and do not let the extractor blindly guess the deepest layer. Use a **declarative rule-driven extractor**: explicitly specify which layer (`layer`) each country group reads, which column is used for the folder (`folder_expr`), which column is used for the file (`file_expr`), and the unique grouping key (`gid_col`).

---

## 3. GADM v4.1 COUNTRY CLASSIFICATION TABLE

All countries and territories (matching the `COUNTRY_NAMES` list in `app.py`) are classified into the following **4 structural groups**:

### Group 1: `STANDARD_ADM2` (Standard Level 2, covering ~85% of countries)

* **Characteristics:** Level 1 (`NAME_1`) is a state/province/centrally administered city; Level 2 (`NAME_2`) is a district/county/county-equivalent/city within a province, covers 100% of the territory, and has an ideal area scale for the NTL grid ($$500 \text{ km}^2$$ - $$2000 \text{ km}^2$$).

* **Extraction configuration:**
  * `layer`: `ADM_ADM_2`
  * `Folder (State/Province)`: `NAME_1`
  * `File (District/County)`: `NAME_2` (group by `GID_2`; use `ENGTYPE_2` to distinguish duplicate `NAME_2` values)

* **Applicable countries:**
  * **Southeast Asia:** `VNM` (Vietnam - 63 provinces, 705 districts), `THA` (Thailand - 77 provinces, 928 Amphoe/Khet), `IDN` (Indonesia - 34 provinces, 514 Kabupaten/Kota), `MYS` (Malaysia - 16 states, 160 Daerah), `PHL` (Philippines - 81 provinces + Metro Manila, 1,634 municipalities), `KHM` (Cambodia - 25 provinces, 197 districts), `LAO` (Laos - 18 provinces, 148 districts), `MMR` (Myanmar - 15 states/regions, 330 townships), `TLS` (Timor-Leste - 13 municipalities, 65 subdistricts).

  * **East Asia & South Asia:** `JPN` (Japan - 47 prefectures, ~1,741 Shi/Ku/Machi/Mura), `KOR` (South Korea - 17 provinces/cities, ~250 Si/Gun/Gu), `PRK` (North Korea), `MNG` (Mongolia - 22 provinces, 339 Sums), `IND` (India - 36 states/UTs, ~676 districts), `BGD` (Bangladesh - 8 Divisions, 64 Districts; or `ADM_3` for 544 Upazilas), `PAK` (Pakistan - 8 Level 1 units, ~36 Divisions in `ADM_2` or ~160 Districts in `ADM_3`), `LKA` (Sri Lanka - 25 Districts in `ADM_1`, 331 DS Divisions in `ADM_2`), `NPL` (Nepal).

  * **The Americas:** `USA` (United States - 50 states + DC, 3,143 Counties/Independent Cities), `CAN` (Canada - 13 provinces/territories, 293 Census Divisions), `MEX` (Mexico - 32 states, 2,469 Municipios), `BRA` (Brazil - 27 states, 5,570 Municípios), `ARG` (Argentina - 24 provinces, 528 Departamentos/Partidos), `CHL` (Chile - 16 regions, 56 provinces in `ADM_2` or 346 Comunas in `ADM_3`), `COL` (Colombia - 33 regions, 1,122 Municipios), `PER` (Peru - 26 regions, 196 Provincias), `VEN`, `CUB`.

  * **Europe:** `DEU` (Germany - 16 states, 401 Kreise/Kreisfreie Städte), `FRA` (France - 13 regions, 96 Départements in `ADM_2`), `ITA` (Italy - 20 regions, 107 provinces/metropolitan cities in `ADM_2`), `ESP` (Spain - 17 autonomous communities, 52 provinces in `ADM_2` or 326 Comarcas in `ADM_3`), `POL` (Poland - 16 provinces, 380 Powiaty), `NLD` (Netherlands - 12 provinces, 342 Gemeenten), `BEL` (Belgium - 3 regions, 11 provinces/Arrondissements), `CHE` (Switzerland - 26 Cantons, 143 Bezirke), `AUT` (Austria - 9 states, 94 Bezirke), `CZE`, `HUN`, `ROU`, `BGR`, `GRC`, `PRT`, `SWE` (Sweden - 21 counties, 290 Kommuner), `NOR` (Norway - 11 counties, 356 Kommuner), `DNK` (Denmark - 5 regions, 99 Kommuner), `FIN`, `RUS` (Russia - ~85 federal subjects, ~2,350 Raions/Cities), `UKR`, `TUR` (Turkey - 81 provinces, 973 Ilçe).

  * **Oceania, the Middle East & Africa:** `AUS` (Australia - 8 states/territories, 562 Local Government Areas), `NZL` (New Zealand - 16 regions, 67 Territorial Authorities), `SAU`, `EGY`, `ZAF`, `NGA` (Nigeria - 37 states, 774 LGAs), `KEN`, `ETH`, `MAR`, `DZA`, `GHA`, `TZA`, `KAZ`, `UZB`, `IRN`, `IRQ`.

---

### Group 2: `SHIFTED_ADM3_PREFECTURE` (Shifted Level 3: Prefecture-level unit as folder, district/county as file)

* **Characteristics:** `ADM_1` is too broad (with a population of 50–120 million, comparable to a European country); `ADM_2` consists of prefecture-level cities (such as Shenzhen, Guangzhou, Wuhan, Suzhou) or large subdivisions, while core urban districts and counties (`Qu` / `Xian` / `Xianjishi`) are located at **`ADM_3`**.

* **Most representative case: China (`CHN`):**
  * If exported at `ADM_2`, the entire city of Shenzhen or Guangzhou would be represented by a single file, making it impossible to analyze differences between core districts (Nanshan, Futian, Tianhe) and peripheral areas.
  * **Handling exceptions for the 4 centrally administered municipalities (`Beijing`, `Shanghai`, `Tianjin`, `Chongqing`) and counties directly under provinces (`NAME_2 == "NA"`):**
    In these 4 municipalities, the city name appears directly in `NAME_1`. Therefore, the most accurate folder-naming formula for `CHN` is:
    * If `NAME_1` belongs to `{"Beijing", "Shanghai", "Tianjin", "Chongqing"}` or `NAME_2` is `"NA"` / matches `NAME_1`: Folder = `NAME_1`.
    * For the remaining 27 provinces/autonomous regions: Folder = `NAME_1 + " - " + NAME_2` (e.g., `Guangdong - Shenzhen`, `Guangdong - Guangzhou`, `Jiangsu - Suzhou`). This naming convention allows users to search by province easily in the Streamlit selector while keeping each prefecture-level city separate; the files inside contain all districts/counties in `NAME_3` (grouped by `GID_3`).

* **Other countries that may use Group 2 (or an `ADM_3` configuration):**
  * `PAK` (Pakistan - to analyze at the level of 160 `Districts` in `ADM_3` instead of 36 `Divisions` in `ADM_2`, use Folder = `NAME_1` and File = `NAME_3`).
  * `BGD` (Bangladesh - to analyze at the level of 544 `Upazilas` in `ADM_3` instead of 64 `Districts` in `ADM_2`).
  * `FRA` (France - to analyze at the level of 333 `Arrondissements` in `ADM_3`, with Folder = `NAME_2` Département).

---

### Group 3: `ASYMMETRIC_HYBRID` (Asymmetric / missing intermediate level `NAME_2 = "NA"`)

* **Characteristics:** A hybrid administrative system combining the two-tier shire county model and the single-tier model (Single-tier Unitary Authorities / Metropolitan Boroughs).

* **Case 1: United Kingdom (`GBR`):**
  * **Actual structure in `gadm41_GBR.gpkg`:**
    * Layer `ADM_ADM_1`: Contains the 4 constituent countries (`England`, `Scotland`, `Wales`, `Northern Ireland`).

    * Layer `ADM_ADM_2`: Contains only two-tier rural counties (such as `Kent`, `Essex`, `West Sussex`). All 33 boroughs of Greater London, the 36 districts of the 6 metropolitan counties (Greater Manchester, West Midlands, Merseyside, South Yorkshire, West Yorkshire, Tyne and Wear), all Unitary Authorities in England, and many areas of Scotland/Wales are assigned `NAME_2 = "NA"`.

    * Layer `ADM_ADM_3`: Contains **100% of the standard local government districts/counties (Local Authority Districts / London Boroughs / Metropolitan Districts / Unitary Authorities / Council Areas)** across the United Kingdom. In areas where `NAME_2` is missing (`"NA"`), the district name is in `NAME_3`. In a few small single-tier counties where `NAME_3` is missing (`"NA"`), the name is in `NAME_2`.

  * **Standard extraction solution for `GBR`:**
    * Read layer **`ADM_ADM_3`**.

    * **Folder (State/Region):** Use `NAME_1` (`England`, `Scotland`, `Wales`, `Northern Ireland`), or, if you want to subdivide `England` by county, use `COALESCE(NAME_2, "England_Unitary_and_Metro")`. To remain consistent with the 4 constituent countries in your current interface, set Folder = `NAME_1`.

    * **File (District/Borough):** Use the coalescing function **`COALESCE(NAME_3, NAME_2)`** (take `NAME_3` if valid; if `NAME_3` is `"NA"`, fall back to `NAME_2`) and group by the unique key `COALESCE(GID_3, GID_2)`.

    * **Result:** No London or Manchester districts are lost, no 37MB `NA` polygons are generated, and 100% of the exported files represent local authority districts at the same administrative level.

* **Case 2: Taiwan (`TWN`):**
  * In GADM v4.1, some counties/cities have a level mismatch between `NAME_1` and `NAME_2` (due to the existence of the two nominal provinces `Fujian` and `Taiwan` in `NAME_1`, alongside centrally administered cities).

  * **Solution for `TWN`:** Read Taiwan's deepest layer (`ADM_ADM_2` or `ADM_ADM_3`, depending on the packaged version), use `COALESCE(NAME_2, NAME_1)` as the Folder (22 counties/cities such as *Taipei, New Taipei, Taichung, Kaohsiung, Hsinchu*) and the next level as the File (368 districts/townships/towns - *Qu/Xiang/Zhen*).

---

### Group 4: `SHALLOW_ADM1_CITY_STATE` (City-states & small countries using Level 1 only)

* **Characteristics:** The country has a small area or is an urban city-state; the `ADM_ADM_2` layer either does not exist in the `.gpkg`, or, if it exists, contains only tiny neighborhood-level units of a few hundred square meters.

* **Extraction configuration:**
  * Read layer **`ADM_ADM_1`** (or automatically fall back to `ADM_ADM_1` when `ADM_ADM_2` is unavailable).
  * **Folder:** Country name (`COUNTRY` / `NAME_0`) or a larger region.
  * **File:** `NAME_1` (group by `GID_1`).

* **Applicable countries:**
  * `SGP` (Singapore - 5 planning areas in `ADM_1`).
  * `HKG` (Hong Kong - 18 administrative districts directly in `ADM_1`).
  * `MAC` (Macau - areas located in `ADM_1`).
  * `BRN` (Brunei - 4 Daerah districts in `ADM_1`, or use `ADM_2` for 38 Mukim).
  * `QAT` (Qatar - 8 Baladiyat municipalities in `ADM_1`).
  * `MDV` (Maldives - 21 Atolls in `ADM_1`).
  * `ISR` (Israel - 6 Districts in `ADM_1`, or 15 Sub-districts in `ADM_2`).
  * `IRL` (Ireland - 26 traditional Counties in `ADM_1`; the `ADM_2` layer contains Municipal Districts).

---

## 4. OUTPUT DATA QUALITY ASSURANCE PROCEDURE

Before being written to disk for use in `app.py`, every `.geojson` file must pass **5 automated validation checks** in the extraction script:

1. **Check 1: Garbage strings**
   Every value in the set `{"NA", "N/A", "NULL", "NONE", "UNKNOWN", "?", "", "NAN"}` (case-insensitive, with surrounding whitespace trimmed) is converted to actual `None` before processing. Every row with `NAME_1 is None` (such as the `NA` state in `gadm41_GBR.gpkg`) is removed or reassigned from a child level if valid.

3. **Check 2: Hydrological filter**
   Completely remove polygons whose `TYPE_x` or `ENGTYPE_x` contains the keywords `Water body`, `Lake`, `Inland water`, `Sea`, or `Estuary`.

5. **Check 3: Geometry merging by identifier**
   Fix self-intersections using `shapely.make_valid()` and merge (`dissolve`) by the correct target `GID` to ensure that one administrative unit corresponds to exactly one `.geojson` file.

7. **Check 4: Prevent overwriting files with duplicate names**
   If two units with different `GID` codes but the same display name exist in the same province/state folder (e.g., *Fairfax County* and *Fairfax City*), the system automatically appends a distinguishing suffix from `ENGTYPE_x` (e.g., `USA_Virginia_Fairfax_County.geojson` and `USA_Virginia_Fairfax_Independent_City.geojson`), compatible with the `list_counties()` and `split_county()` functions in `app.py`.

9. **Check 5: Minimum area check for VIIRS**
   Issue a warning if a polygon has an area of $$< 0.25 \text{ km}^2$$ (smaller than one $$500 \times 500 \text{ m}$$ grid cell).
