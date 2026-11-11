# Yanqing validation evidence — reproducibility package

This directory holds source exports and independent comparison artifacts for the **Yanqing District, Beijing, China** validation of `spatial-app`. It is evidence, not an assertion that every statistical or economic claim has been verified.

## Current repository contents

| File | Record count / type | Verification |
|---|---:|---|
| [2020 LISA export](CHN_beijing_yanqing_2020_500m_lisa_cells.csv) | 8,333 cells | Application output, source for neighbor/Local Moran/FDR checks |
| [2014→2020 Space-Time export](CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv) | 8,333 cells | Application output, source for directional and quartile checks |
| [2020 cell NTL export](dien_khanh_NTL_2020_500m.csv) | 8,333 cells | Application output, source for pixel-to-polygon comparison |
| [Independent LISA per-cell comparison](yanqing_lisa_independent_cell_comparison.csv) | 8,333 cells | Contains recalculated neighbor / statistic / significance comparisons |
| [Independent 2020 pixel-to-polygon results](yanqing_viirs_all_8333_polygon_comparison.csv) | 8,333 cells | Source radiance vs polygon-extraction table |
| [Independent LISA code and results](archives/yanqing_validation_evidence.zip) | ZIP | Original independent LISA validation bundle with Python script, CSV and metrics |
| [2014 VIIRS reference](rasters/yanqing_viirs_2014_reference.tif) | GeoTIFF, 217 × 142 | Unmodified Earth Engine reference raster |

The source CSV exports in this repository were normalized to UTF-8 without a BOM when transferred, with numerical values preserved. Git blob identifiers and file sizes are recorded below for transparent byte-level comparisons. The 2020 comparison CSV was copied as a textual export and may differ at the byte level from the original file; it must not be represented as bit-for-bit identical.

| File | Git blob SHA-1 | Repository bytes |
|---|---|---:|
| `CHN_beijing_yanqing_2020_500m_lisa_cells.csv` | `45823384dbaccd4f5848152897d4c36aee6333ab` | 2,616,153 |
| `CHN_beijing_yanqing_2014_2020_500m_spacetime_cells.csv` | `614433fcd90edfb155c6034467dc2309a9ea255e` | 3,533,025 |
| `dien_khanh_NTL_2020_500m.csv` | `df88c819f435818a79c7f91ea4011a68f9220fce` | 1,556,802 |
| `yanqing_lisa_independent_cell_comparison.csv` | `13e8c0611543c2d0775a353a09f0af075e1f0618` | 813,039 |
| `yanqing_validation_evidence.zip` | `81b9c84095ee3e50960ab6f424e8b4829955ebb5` | 184,943 |
| `yanqing_viirs_2014_reference.tif` | `e52c812adac823d84f6dbd6b116e54e80d271cec` | 140,603 |

## Archive integrity

```text
yanqing_validation_evidence.zip
SHA-256: 51a662cb875ffe4bccfd3c628eeafb136aa9025bb500b5bdaa94d31b24ca5b93

yanqing_viirs_2014_reference.tif
SHA-256: 637661ab304986ef19befa4c7ca62d1e9cface500862803f02ad76a4b6637c31
```

Example integrity check from the repository root:

```bash
python -c "import hashlib,pathlib; p=pathlib.Path('validation/evidence/yanqing/archives/yanqing_validation_evidence.zip'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

The LISA ZIP contains the independent calculation source (`validate_yanqing_lisa.py`), output table, result summary, and execution log. To rerun, extract the archive and place the original LISA application CSV beside the script, or configure the script input path as appropriate.

## Full campaign package and outstanding public deposits

The complete independent evidence campaign also produced a consolidated **73-file / 5,554,282-byte** ZIP, with all required scripts, comparison tables, GADM geometry and source VIIRS GeoTIFFs, plus `EVIDENCE_MANIFEST.json` containing per-member SHA-256 hashes.

```text
spatial_app_2026_11_11_validation_evidence_complete.zip
SHA-256: 95b3874d4253eec2269f2477b648a067fb14d1c94be54bc0ed38f8795599260c
```

**IMPORTANT: This consolidated ZIP is not yet deposited into this GitHub repository.** It is available as a downloadable attachment in the validation conversation. Public third-party reproduction of every raster-to-grid and alternative-specification result remains **incomplete** until a durable copy of the complete ZIP (or a checksum-verified equivalent) is published. Do not mark the whole evidence archive as independently obtainable from GitHub yet.

Pending files include the full-precision reconstructed grid polygons, the 2020 VIIRS reference raster, the complete 2014 per-cell pixel comparison, the measurement/transformation/spatial/temporal rerun scripts and their full outputs. These are inside the complete package named above, but their absence from the public repository must remain explicit.

## Interpretation and evidence status

- **LISA:** source CSV, independent per-cell comparisons and validation code are present here.
- **VIIRS 2014:** source Space-Time CSV and annual reference TIFF are present; independent polygon geometry and per-cell comparison are not fully published here.
- **VIIRS 2020:** source CSV and per-cell comparison are present; the reference TIFF and reconstruction scripts are not yet publicly archived here.
- **Measurement/transformation/spatial/temporal sensitivity:** detailed method and results are in the two specification editions, while complete executable artifacts still require the consolidated package.
- **GHSL:** application-reported quality metrics are preliminary and have not yet been independently reproduced from original GHSL rasters.
- **Economic construct and cloud performance:** not validated to publication-level completeness.

Related methodology: `docs/VALIDATION MASTER.md` (English), `docs/VALIDATION MASTER-vi.md` (Vietnamese). Future evidence uploads should update this index and both documents together.