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
