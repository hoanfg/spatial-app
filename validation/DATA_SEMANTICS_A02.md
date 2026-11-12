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
