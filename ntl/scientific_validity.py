"""Transparent scientific scope screens; never substitute a screen for validation.

These helpers do not alter historical VIIRS, LISA, GHSL or CSV values.
They prevent missing observational evidence and model assumptions being
reported as if independently verified.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_SUPPORT_FIELDS = (
    "dq_status", "dq_observed_fraction", "dq_mean_valid_months",
)
KNOWN_STATUSES = (
    "observed", "partial_observation", "no_observation", "unknown",
)


def observation_support_screen(frame: pd.DataFrame, *, min_months: int = 3) -> dict:
    """Summarize A02 support for interpretive warnings and audit provenance.

    The min_months threshold is a *descriptive sensitivity flag*, not a
    source-certified cutoff. dq_mean_valid_months counts non-empty monthly
    composites, NOT individual cf_cvg observations or their precision.
    A fully supported-looking scene is still NOT field-validation evidence.
    """
    if min_months < 1:
        raise ValueError("min_months must be >= 1")
    n = len(frame)
    missing = [name for name in REQUIRED_SUPPORT_FIELDS if name not in frame]
    if missing:
        return {
            "status": "metadata_unavailable", "n_cells": n,
            "n_unknown": n, "n_no_observation": 0, "n_partial": 0,
            "n_low_months": 0, "n_support_issues": n,
            "min_months_rule": min_months, "requires_field_validation": True,
            "missing_columns": missing,
        }
    status = frame["dq_status"].astype("string").fillna("unknown").to_numpy(dtype=str)
    unsupported = ~np.isin(status, KNOWN_STATUSES)
    observed = pd.to_numeric(frame["dq_observed_fraction"], errors="coerce").to_numpy(float)
    months = pd.to_numeric(frame["dq_mean_valid_months"], errors="coerce").to_numpy(float)
    invalid = (~np.isfinite(observed) | (observed < -1e-6)
               | (observed > 1 + 1e-6) | ~np.isfinite(months)
               | (months < -1e-6))
    incoherent = (
        (np.isin(status, ["observed", "partial_observation"]) & (observed <= 0))
        | ((status == "no_observation") & (observed > 1e-6))
        | ((status == "observed") & (observed < 1 - 1e-6))
    )
    unknown = (status == "unknown") | unsupported | invalid | incoherent
    no_obs = (status == "no_observation") & ~unknown
    partial = (status == "partial_observation") & ~unknown
    low = (~unknown & ~no_obs & (months < min_months))
    issues = unknown | no_obs | partial | low
    if unknown.any():
        label = "unverified_metadata"
    elif no_obs.any():
        label = "missing_observation_support"
    elif partial.any() or low.any():
        label = "partial_or_low_month_support"
    else:
        label = "screened_no_flag_not_field_validated"
    return {
        "status": label,
        "n_cells": n,
        "n_unknown": int(unknown.sum()),
        "n_no_observation": int(no_obs.sum()),
        "n_partial": int(partial.sum()),
        "n_low_months": int(low.sum()),
        "n_support_issues": int(issues.sum()),
        "min_months_rule": min_months,
        "requires_field_validation": True,
        "missing_columns": [],
    }



def utm_applicability_screen(bounds_wgs84) -> dict:
    """Flag scientific limits of applying a single UTM zone to a study area.

    Limits are conservative applicability checks, not measured projection
    error. They do NOT replace independent geodesic control of areas/distances.
    """
    if len(bounds_wgs84) != 4:
        raise ValueError("WGS84 bounds must be xmin,ymin,xmax,ymax")
    west, south, east, north = [float(x) for x in bounds_wgs84]
    if (not np.isfinite([west, south, east, north]).all()
            or west >= east or south >= north
            or west < -180 or east > 180 or south < -90 or north > 90):
        raise ValueError("Invalid WGS84 bounding box")
    lon_span = east - west
    lat_span = north - south
    if south < -80 or north > 84:
        status = "outside_standard_utm_latitudes"
    elif lon_span >= 180:
        status = "dateline_bbox_cannot_be_modeled_by_one_utm_zone"
    elif lon_span > 6 or lat_span > 8:
        status = "broad_extent_needs_geodesic_error_check"
    else:
        status = "candidate_local_utm_not_independently_validated"
    return {
        "status": status,
        "lon_span_degrees": lon_span,
        "lat_span_degrees": lat_span,
        "unsupported": status in (
            "outside_standard_utm_latitudes",
            "dateline_bbox_cannot_be_modeled_by_one_utm_zone",
        ),
        "requires_geodesic_validation": status != "candidate_local_utm_not_independently_validated",
    }
