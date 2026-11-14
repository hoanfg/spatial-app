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

    Band 1 retains the historical unmask(0) composite. Other bands describe
    the annual median before clipping and its monthly observational support.
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


def _check_unlabeled_quality_values(src):
    """Validate unlabeled producer-generated bands before trusting their order.

    Never infer semantic meaning from six arbitrary bands. This validates the
    five annual VIIRS quality bands with the producer's exact pixel contracts.
    The fallback is only available to *the app's own six-band download path*.
    """
    for band_no in (2, 3, 4, 6):
        # Pixel indicators 0/1, masked outside the downloaded ROI.
        a = src.read(band_no, masked=True)
        vals = np.asarray(a.compressed(), dtype=float)
        if vals.size and (not np.isfinite(vals).all()
                          or np.any((vals < -1e-5) | (vals > 1 + 1e-5))
                          or np.any(np.abs(vals - np.rint(vals)) > 1e-5)):
            return False, f"band_{band_no}_not_binary"
    count = src.read(5, masked=True)
    vals = np.asarray(count.compressed(), dtype=float)
    if vals.size and (not np.isfinite(vals).all() or np.any((vals < -1e-5) | (vals > 12 + 1e-5))
                      or np.any(np.abs(vals - np.rint(vals)) > 1e-5)):
        return False, "monthly_count_outside_0_12_or_fractional"
    # Pixel-level logical coherence of missingness, negative, measured zero,
    # and monthly support. Compare only on the common valid pixel footprint.
    observed = src.read(2, masked=True)
    negative = src.read(3, masked=True)
    zero = src.read(4, masked=True)
    low_month = src.read(6, masked=True)
    common = ~(np.ma.getmaskarray(observed) | np.ma.getmaskarray(negative)
               | np.ma.getmaskarray(zero) | np.ma.getmaskarray(count)
               | np.ma.getmaskarray(low_month))
    if np.any(common):
        o = observed.data[common]
        neg = negative.data[common]
        z = zero.data[common]
        m = count.data[common]
        low = low_month.data[common]
        if (np.any(np.abs(o - (m > 0)) > 1e-5)
                or np.any(np.abs(low - (m < 3)) > 1e-5)
                or np.any((neg > 0.5) & (z > 0.5))
                or np.any((o < 0.5) & ((neg > 0.5) | (z > 0.5)))):
            return False, "observed_monthly_zero_negative_inconsistent"
    return True, "logical_and_value_constraints_pass"


def quality_raster_schema(tif_bytes: bytes, *, trusted_producer: bool = False) -> dict:
    """Recognize band semantics without silently treating unknown data as verified.

    Only the live app producer (annual_image_with_quality -> fetch_ntl_raster)
    may set trusted_producer=True. Other or user-supplied TIFFs remain strict.
    """
    from rasterio.io import MemoryFile

    with MemoryFile(tif_bytes) as mf, mf.open() as src:
        descriptions = tuple(d if d is None else str(d) for d in src.descriptions)
        details = {"band_count": src.count, "descriptions": descriptions,
                   "status": "unsupported", "supported": False}
        if src.count != 6:
            details["status"] = "wrong_band_count"
            return details
        if descriptions[1:] == QUALITY_BANDS:
            details.update(status="named", supported=True)
            return details
        if not all(d is None or d == "" for d in descriptions[1:]):
            details["status"] = "conflicting_band_descriptions"
            return details
        if not trusted_producer:
            details["status"] = "unlabeled_untrusted"
            return details
        ok, reason = _check_unlabeled_quality_values(src)
        details.update(status="validated_producer_order" if ok else "invalid_unlabeled_values",
                       supported=ok, validation=reason)
        return details


def cell_quality(tif_bytes, grid, *, trusted_producer: bool = False):
    """Area-weighted quality flags in grid order; absent evidence stays unknown.

    Raw quality bands are accepted by name. If the trusted app download strips
    *all* five quality descriptions, validate the value/logic contracts before
    relying on the known order. Misnamed bands never fall back to positional use.
    """
    from ntl.zonal import zonal_stat

    info = quality_raster_schema(tif_bytes, trusted_producer=trusted_producer)
    out = pd.DataFrame(index=range(len(grid)))
    for band, name in enumerate(QUALITY_BANDS, start=2):
        out[name] = (zonal_stat(tif_bytes, grid, band=band, clip_negative=False,
                                fill_missing=None).to_numpy() if info["supported"] else np.nan)
    observed = out.dq_observed_fraction
    out["dq_status"] = np.select(
        [observed.isna(), observed <= 0, observed < 1 - 1e-6],
        ["unknown", "no_observation", "partial_observation"], default="observed",
    )
    out["dq_ntl_policy"] = "legacy_zero_fill"
    out.attrs["quality_raster_schema"] = info
    return out


def year_quality(frame, year):
    """Year-qualified metadata for Space-Time CSVs without duplicate names."""
    return frame.filter(regex=r"^dq_").add_suffix(f"_{int(year)}")
