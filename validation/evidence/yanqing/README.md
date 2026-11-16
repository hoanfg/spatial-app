# Yanqing validation evidence

[English](README.md) · [Tiếng Việt](README-vi.md) · [Evidence inventory](../README.md)

This folder contains the public inputs and independent comparison outputs for Yanqing District, Beijing. Results apply to the stated files, years and tolerances.

| File | Contents | Use |
| --- | ---: | --- |
| [2020 LISA export](CHN_beijing_yanqing_2020_500m_lisa_cells.csv) | 8,333 cells | Application output for neighbor, Local Moran and FDR checks |
| [2014 to 2020 Space-Time export](CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv) | 8,333 cells | Application output for direction and regime checks |
| [2020 NTL export](dien_khanh_NTL_2020_500m.csv) | 8,333 cells | Application output for the raster comparison |
| [Independent LISA comparison](yanqing_lisa_independent_cell_comparison.csv) | 8,333 cells | Recalculated neighbors, statistics and significance |
| [Independent VIIRS comparison](yanqing_viirs_all_8333_polygon_comparison.csv) | 8,333 cells | Source radiance compared with polygon extraction |
| [Independent LISA bundle](archives/yanqing_validation_evidence.zip) | ZIP | Python checker, result table, summary and execution log |
| [2014 VIIRS reference](rasters/yanqing_viirs_2014_reference.tif) | GeoTIFF, 217 × 142 | Earth Engine reference raster |

## Integrity

| File | SHA-256 |
| --- | --- |
| `yanqing_validation_evidence.zip` | `51a662cb875ffe4bccfd3c628eeafb136aa9025bb500b5bdaa94d31b24ca5b93` |
| `yanqing_viirs_2014_reference.tif` | `637661ab304986ef19befa4c7ca62d1e9cface500862803f02ad76a4b6637c31` |

The transferred CSV files preserve their numerical values but may have normalized UTF-8 line encoding. Do not describe them as bit-for-bit copies unless their recorded hash agrees.

## Supported result and limit

The deposited files support the recorded 2014 and 2020 VIIRS comparisons, the 2020 LISA comparison and the two-date Space-Time calculation for Yanqing. They do not provide a continuous annual trend, a complete independent GHSL reproduction or every artifact from the larger 73-file validation campaign. Missing source rasters and detailed rerun products remain absent from this repository.

The application methods are documented in the [data and method guide](../../../docs/README.md). Current acceptance status is maintained in the [validation guide](../../README.md).
