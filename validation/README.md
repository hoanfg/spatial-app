<a id="top"></a>

# Validation status

[English](README.md) · [Tiếng Việt](README-vi.md) · [Application manual](../README.md) · [Evidence guide](evidence/README.md)

A result applies only to the stated location, year, input and precision. The table separates results supported by deposited evidence from work that still needs additional data.

## Results

| Topic | Result | Limit |
| --- | --- | --- |
| GADM China | 2,420 curated units matched the full-resolution GADM 4.1 source at the documented precision. | This does not verify current official boundaries or every country. |
| Yanqing VIIRS and LISA | Independent 2014 and 2020 comparisons cover 8,333 cells for each year; the recorded formulas, FDR and two-date calculations were checked. | Two dates do not establish a continuous annual trend. |
| Shanghai, Bao'an and Qimen | V11 reports 15,330/15,330 full cells within the four-decimal CSV bound; 1,846/1,847 clipped cells were within 0.00005 and all were within 0.0000501. | Complete source rasters, cellwise outputs and plots are not deposited. |
| A02 observation metadata | The 7,148-cell Bao'an CSV has observed status and five finite quality fields in every row. The later NTL CSV is byte-identical to the deposited reference. | No real missing or low-support field case has been checked. |
| GHSL Shanghai | The native-grid quantity calculation and independent aggregate comparison reproduce the displayed rho, bootstrap interval and AUC rounding on 715 eligible cells. | There is no deposited live per-cell GHSL export; Bao'an and Qimen charts are not independent cellwise checks. |
| A02 performance | The later Bao'an run records 37.6479 s for the pipeline and 26.4623 s for A02, compared with 46.6687 s and 25.0028 s in the earlier run. | The total run was shorter, but A02 itself was not faster. Repeated comparable runs are needed. |

File locations, hashes and runnable checks are listed in the [evidence guide](evidence/README.md).

## What can be reproduced from this repository

| Check | Command or material | Scope |
| --- | --- | --- |
| Bao'an evidence | `node validation/audit_public_evidence.mjs --check-result` | Checks rows, IDs, A02 fields, stored summary and file inventories. |
| Documentation | `node validation/check_docs.mjs` | Checks the maintained English/Vietnamese guides, links and math delimiters. |
| Application contracts | `python -m pytest -q tests` | Checks numerical, schema, masking and interface behavior with deposited or synthetic inputs. |
| Three-location raster comparison | [Cross-location workflow](cross_location/README.md) | The method and checker are present; a full rerun needs the matching source rasters and app exports. |

## Next steps

1. Test A02 with a real missing or low-observation case without changing the `legacy_zero_fill` policy silently.
2. Deposit or regenerate the matching raster pairs and per-cell outputs for Shanghai, Bao'an and Qimen.
3. Export GHSL values per cell and compare them independently on the same grid.
4. Repeat performance measurements with the same deployed commit, location, year and grid size.
5. Extend the two-date analysis to a continuous annual series before making temporal claims.
6. Compare NTL with an independently sourced and aligned economic outcome before drawing economic conclusions.

## Method boundaries

- NTL per cell is the fractional-coverage mean of valid VIIRS radiance. Negative valid radiance is clipped to zero for the legacy output; observation-support fields remain separate.
- Local Moran uses eligible core or lit cells and row-standardized weights. Global Moran uses all cells and binary Queen weights; the two statistics are not interchangeable.
- GHSL source-pixel quantities are summed by polygon intersection fraction on the native grid, then divided by cell area for density.
- Automated tests, stored numeric comparisons and live service checks answer different questions. Each published result should state its input, revision, location, year, grid and tolerance.
