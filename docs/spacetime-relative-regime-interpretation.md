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
