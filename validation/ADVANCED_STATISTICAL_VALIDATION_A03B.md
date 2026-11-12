# A03-B — Advanced statistical validation (incremental)

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
