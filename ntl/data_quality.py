from __future__ import annotations

import numpy as np


NEG_SHARE_WARN = 0.10
NODATA_SHARE_WARN = 0.0
ZERO_CELL_INFO = 0.50
NO_OBS_WARN = 0.01
LOW_OBS_MONTHS = 3
LOW_OBS_WARN = 0.20

PIPELINE_PROVENANCE = {
    "ntl_composite": "median_of_monthly_cf_cvg_gt0",
    "ntl_negative_handling": "clip_to_0_before_zonal_mean",
    "ntl_nodata_handling": "unmask_to_0",
    "ntl_observation_metadata": "annual_median_mask_and_month_count_v1",
}


def raster_report(arr) -> dict:

    a = np.asarray(arr, dtype=float).ravel()
    n = int(a.size)
    if n == 0:
        return {"n_pixels": 0, "nodata_share": float("nan"), "neg_share": float("nan"),
                "zero_share": float("nan"), "min": float("nan"), "max": float("nan"), "p99": float("nan")}
    finite = np.isfinite(a)
    v = a[finite]
    out = {
        "n_pixels": n,
        "nodata_share": float(1.0 - finite.mean()),
        "neg_share": float((v < 0).mean()) if v.size else float("nan"),
        "zero_share": float((v == 0).mean()) if v.size else float("nan"),
        "min": float(v.min()) if v.size else float("nan"),
        "max": float(v.max()) if v.size else float("nan"),
        "p99": float(np.percentile(v, 99)) if v.size else float("nan"),
    }
    return out


def cell_report(n_cells: int, n_stat_nan: int, n_merge_miss: int, ntl) -> dict:

    v = np.asarray(ntl, dtype=float)
    return {
        "n_cells": int(n_cells),
        "cells_stat_nan": int(n_stat_nan),
        "cells_merge_miss": int(n_merge_miss),
        "cells_missing_stats": int(n_stat_nan) + int(n_merge_miss),
        "zero_cell_share": float((v == 0).mean()) if v.size else float("nan"),
    }


def obs_report(n_obs, min_months: int = LOW_OBS_MONTHS) -> dict:

    a = np.asarray(n_obs, dtype=float).ravel()
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {"no_obs_share": float("nan"), "low_obs_share": float("nan"),
                "median_months": float("nan"), "min_months": int(min_months)}
    return {
        "no_obs_share": float((a <= 0).mean()),
        "low_obs_share": float((a < min_months).mean()),
        "median_months": float(np.median(a)),
        "min_months": int(min_months),
    }


def quality_flags(raster: dict | None, cells: dict | None, obs: dict | None = None) -> list[dict]:

    items = []
    if raster and raster.get("n_pixels"):
        bad_nodata = raster["nodata_share"] > NODATA_SHARE_WARN
        items.append({"key": "nodata", "level": "warn" if bad_nodata else "ok", "vals": raster})
        neg = raster["neg_share"]
        items.append({"key": "neg", "level": "warn" if np.isfinite(neg) and neg > NEG_SHARE_WARN else "ok",
                      "vals": raster})
    if cells:
        items.append({"key": "missing", "level": "warn" if cells["cells_missing_stats"] > 0 else "ok",
                      "vals": cells})
        zs = cells["zero_cell_share"]
        items.append({"key": "zero", "level": "info" if np.isfinite(zs) and zs > ZERO_CELL_INFO else "ok",
                      "vals": cells})
    if obs and np.isfinite(obs["no_obs_share"]):
        warn = obs["no_obs_share"] > NO_OBS_WARN or obs["low_obs_share"] > LOW_OBS_WARN
        items.append({"key": "obs", "level": "warn" if warn else "ok", "vals": obs})
    return items


def quality_export(raster: dict | None, cells: dict | None, obs: dict | None = None) -> dict:
    out = dict(PIPELINE_PROVENANCE)
    if raster and raster.get("n_pixels"):
        out["dq_nodata_pixel_share"] = round(raster["nodata_share"], 6)
        out["dq_neg_pixel_share"] = round(raster["neg_share"], 6) if np.isfinite(raster["neg_share"]) else float("nan")
    if cells:
        out["dq_cells_missing_stats"] = cells["cells_missing_stats"]
        out["dq_zero_cell_share"] = round(cells["zero_cell_share"], 6)
    if obs and np.isfinite(obs["no_obs_share"]):
        out["dq_no_obs_pixel_share"] = round(obs["no_obs_share"], 6)
        out["dq_low_obs_pixel_share"] = round(obs["low_obs_share"], 6)
        out["dq_median_valid_months"] = obs["median_months"]
    return out
