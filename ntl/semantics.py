"""Additive observational metadata; legacy analysis values remain unchanged."""
from __future__ import annotations

import numpy as np
import pandas as pd

QUALITY_BANDS = (
    "dq_observed_fraction", "dq_negative_fraction", "dq_zero_fraction",
    "dq_mean_valid_months", "dq_low_month_fraction",
)


def annual_image_with_quality(monthly, roi):
    """Input is monthly avg_rad masked by cf_cvg > 0. All bands are float.

    Band 1 exactly retains the historical unmask(0) composite. Other bands
    describe the annual median before clipping and its monthly support.
    cf_cvg counts cloud-free observations, not a general VIIRS quality flag.
    """
    median = monthly.median().select("avg_rad")
    count = monthly.count().select("avg_rad").unmask(0.0)
    observed = median.mask().unmask(0.0)
    bands = [
        observed.rename(QUALITY_BANDS[0]),
        median.lt(0).unmask(0.0).rename(QUALITY_BANDS[1]),
        median.eq(0).unmask(0.0).rename(QUALITY_BANDS[2]),
        count.rename(QUALITY_BANDS[3]),
        count.lt(3).rename(QUALITY_BANDS[4]),
    ]
    image = median.unmask(0.0)
    for band in bands:
        image = image.addBands(band)
    return image.toFloat().clip(roi)


def cell_quality(tif_bytes, grid):
    """Area-weighted raster fractions in grid order; unknown stays unknown.

    Fractions refer to raster-covered polygon area (main pipeline pads bbox).
    Negative/zero fractions describe annual medians, not monthly samples.
    Single-band legacy files cannot establish observational coverage.
    """
    from rasterio.io import MemoryFile
    from ntl.zonal import zonal_stat

    out = pd.DataFrame(index=range(len(grid)))
    with MemoryFile(tif_bytes) as mf, mf.open() as src:
        supported = src.count == 6 and tuple(src.descriptions[1:]) == QUALITY_BANDS
    for band, name in enumerate(QUALITY_BANDS, start=2):
        out[name] = (zonal_stat(tif_bytes, grid, band=band, clip_negative=False,
                                fill_missing=None).to_numpy() if supported else np.nan)
    observed = out.dq_observed_fraction
    out["dq_status"] = np.select(
        [observed.isna(), observed <= 0, observed < 1 - 1e-6],
        ["unknown", "no_observation", "partial_observation"], default="observed",
    )
    out["dq_ntl_policy"] = "legacy_zero_fill"
    return out


def year_quality(frame, year):
    """Year-qualified metadata for Space-Time CSVs without duplicate names."""
    return frame.filter(regex=r"^dq_").add_suffix(f"_{int(year)}")
