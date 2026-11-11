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
