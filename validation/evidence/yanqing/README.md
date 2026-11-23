# Yanqing validation evidence

[English](README.md) · [Tiếng Việt](README-vi.md) · [Evidence inventory](../README.md)

This folder contains the public inputs and independent comparison outputs for Yanqing District, Beijing. Results apply to the stated files, years and tolerances.

## Questions and reasons

| Check | Why it is needed |
| --- | --- |
| VIIRS raster to grid | Confirms that projection, polygon coverage and CSV rounding produce the expected NTL value for each cell. |
| Local Moran and FDR | Confirms that neighbor construction, Local I, permutation significance and multiple-testing labels can be recalculated outside the application. |
| 2014 to 2020 Space-Time output | Confirms that the exported two-date fields and regime codes are internally consistent. |
| File integrity | Prevents a later file replacement from being mistaken for the input used by the reported check. |

| File | Contents | Use |
| --- | ---: | --- |
| [2020 LISA export](CHN_beijing_yanqing_2020_500m_lisa_cells.csv) | 8,333 cells | Application output for neighbor, Local Moran and FDR checks |
| [2014 to 2020 Space-Time export](CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv) | 8,333 cells | Application output for direction and regime checks |
| [2020 NTL export](dien_khanh_NTL_2020_500m.csv) | 8,333 cells | Application output for the raster comparison |
| [Independent LISA comparison](yanqing_lisa_independent_cell_comparison.csv) | 8,333 cells | Recalculated neighbors, statistics and significance |
| [Independent VIIRS comparison](yanqing_viirs_all_8333_polygon_comparison.csv) | 8,333 cells | Source radiance compared with polygon extraction |
| [Independent LISA bundle](archives/yanqing_validation_evidence.zip) | ZIP | Python checker, result table, summary and execution log |
| [2014 VIIRS reference](rasters/yanqing_viirs_2014_reference.tif) | GeoTIFF, 217 × 142 | Earth Engine reference raster |

## How the comparisons work

The VIIRS table compares the application `ntl_mean` with an independently calculated polygon mean `ntl_ref_polygon` for the same `grid_id`. The strict tolerance is 0.00005, matching four-decimal CSV rounding. Border cells are retained rather than removed.

The LISA table reconstructs Queen neighbors, recalculates Local I from the rounded exported NTL values, runs an independent permutation sequence and applies BH-FDR. It compares intermediate values as well as the final class. Because the input is rounded and the permutation seed is independent, the table is expected to report any label differences rather than force equality.

The Space-Time CSV is checked by row count and by the exported regime codes for all 8,333 cells.

## Quantitative methods and interpretation rules

**1. Polygon-level raster error.** Calculate VIIRS area-overlap means on each cell polygon, join on `grid_id`, and compare with exported app `ntl_mean` using `e_i = |NTL_ref_i - NTL_app_i|`. **Why:** local errors, particularly at boundaries, can be hidden by an excellent regional correlation. The `0.00005` tolerance follows four-decimal CSV rounding and **is not a satellite accuracy specification**.

**2. Local Moran and randomization.** Build Queen neighbors on the 500 m lattice, standardize NTL on the eligible population and compute `I_i = z_i × mean(z_neighbor) / [sum(z²)/(m-1)]`. Hold each focal cell fixed, sample distinct nonfocal members without replacement, count ties in two-sided permutation tails, use `(count+1)/(B+1)` correction and apply BH-FDR within the actual test family. **Why:** normalization, adjacency, p calculation and multiple-testing decisions are different error sources even if NTL is correct. The independent comparison uses **rounded CSV NTL** and a separate RNG sequence; 179 differing labels must not automatically be treated as algorithm bugs.

**3. Two-year change.** Compare `NTL_2020 - NTL_2014` in raw radiance separately from changes in year-standardized `log1p(NTL)` and its neighbor lag. **Why:** absolute brightness may increase even while **relative standardized position** decreases. The `4_Synchronized_Decline` label does not mean every such cell lost physical light or economic output.

**4. Reproduction boundary.** SHA-256 identifies bytes; scientific replay additionally needs the exact polygons, raster, masks, seed and p-tail convention. The raw 2020 reference raster is not retained in this directory, so its 2020 result is based on the **archived per-cell comparison** rather than full source re-extraction. The 2014 raster lacks observation-support bands needed to test the missingness policy.

## Results

| Check | Result | Interpretation |
| --- | --- | --- |
| VIIRS 2020 polygon comparison | 8,332/8,333 cells are within 0.00005. Mean absolute error is 0.0000250270. Maximum absolute error is 0.0000643242 at border cell `grid_id=349`. | The comparison agrees at CSV precision except for one retained border-cell exceedance. |
| LISA final class | 8,154/8,333 classes match; 7,733 cells are active and 600 are edge-masked. | All 179 differences are visible: 80 Not Significant to Low-Low, 74 Low-Low to Not Significant, 15 High-High to Not Significant and 10 Not Significant to High-High. |
| Local I | Maximum absolute difference among populated Local I pairs is 0.0001680453. | The table uses rounded NTL and is not a full-precision identity test. |
| Space-Time regimes | 1,456 Synergistic Growth; 75 Agglomeration Shadow; 194 Emergent Pioneer; 4,711 Synchronized Decline; 1,897 Excluded or Static. | These are descriptive two-date categories, not causal or permutation-significance results. |
| 2014 reference raster metadata | 30,814 finite pixels, one negative pixel and no zero pixels are recorded for the deposited raster. | The legacy raster has no observation-count bands, so monthly support is unknown. |

## Interpreting the two-date change

The deposited Space-Time CSV permits a separate check of absolute radiance change. Mean cell NTL rises from 0.4451583 in 2014 to 1.4137191 in 2020. Across all 8,333 cells, 8,221 increase and 112 decrease; none tie at the exported precision.

The regime code is based on changes in each year's standardized `log1p(NTL)` value and its spatial lag. It therefore measures a change in relative position, not necessarily a change in raw radiance. Of the 4,711 cells labelled `4_Synchronized_Decline`, 4,624 increase in absolute NTL and 87 decrease. The appropriate reading is synchronized decline in relative standing. It is not evidence that 4,711 cells lost light or experienced economic contraction.

The evidence command recalculates these counts directly from the deposited CSV. The comparison still has only two dates, uses rounded exported values and does not establish what happened in the intervening years.

## Integrity

| File | SHA-256 |
| --- | --- |
| `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv` | `56450adc6f46ce06f7fa9b68ebbfdd704b8e3bd1445ec0be32809d3cd98d198c` |
| `CHN_beijing_yanqing_2020_500m_lisa_cells.csv` | `37186205051561607d611597a80cc3ce3cd22ec2cc201d9c9c842e23f3a87ec6` |
| `dien_khanh_NTL_2020_500m.csv` | `0d7f29127621e1964c338bd97e62544e342a4377ac830821bdbef0bee124206b` |
| `yanqing_lisa_independent_cell_comparison.csv` | `83fc8d94cc2badc785ba9fdbbe85be3619462afdf419a35cd47090653bca4bdd` |
| `yanqing_viirs_all_8333_polygon_comparison.csv` | `c5af295ea01f9f927c133d8fb5596ab8fd4848334d9ea33046c63df248174250` |
| `yanqing_validation_evidence.zip` | `51a662cb875ffe4bccfd3c628eeafb136aa9025bb500b5bdaa94d31b24ca5b93` |
| `yanqing_viirs_2014_reference.tif` | `637661ab304986ef19befa4c7ca62d1e9cface500862803f02ad76a4b6637c31` |

These hashes identify the bytes currently deposited in the repository. A rerun must report a different hash if a tool rewrites line endings or serialization, even when the numerical values remain equal.

## Limits

- The raw 2020 reference raster used to build the deposited polygon-comparison table is not included.
- The 2014 raster lacks monthly observation-count bands, so it cannot test A02 support semantics.
- Independent LISA values are based on rounded CSV input and an independent permutation sequence.
- Two dates do not provide a continuous annual trend.
- These files do not reproduce GHSL or establish that NTL is a valid economic outcome.

The application methods are documented in the [data and method guide](../../../docs/README.md). Current acceptance status is maintained in the [validation guide](../../README.md).
