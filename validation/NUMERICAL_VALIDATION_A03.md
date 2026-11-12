# A03 — Numerical and statistical reference validation

Status: **partial, draft-only**. This change adds a small, deterministic core of independent reference tests. It does **not** certify all Spatial App statistical results or replace the remaining A03 audit tasks.

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
