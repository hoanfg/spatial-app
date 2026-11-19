"""Consolidated science-audit regression tests (bounded, no new field claims)."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from ntl.scientific_validity import observation_support_screen, utm_applicability_screen
from ntl.lisa_diagnostics import resid_moran
from ntl import ee_extra


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "g10_g18_field_audit", ROOT / "validation" / "g10_g18_field_audit.py"
)
field = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(field)


def test_observation_screen_no_metadata_is_unverified():
    out = observation_support_screen(pd.DataFrame({"ntl_mean": [0.0, 1.0]}))
    assert out["status"] == "metadata_unavailable"
    assert out["n_unknown"] == 2 and out["n_support_issues"] == 2
    assert out["requires_field_validation"]


def test_observation_screen_distinguishes_unknown_partial_and_low_months():
    df = pd.DataFrame({
        "dq_status": ["observed", "no_observation", "partial_observation", "unknown", "observed"],
        "dq_observed_fraction": [1.0, 0.0, 0.5, np.nan, 1.0],
        "dq_mean_valid_months": [12, 0, 5, np.nan, 1],
    })
    out = observation_support_screen(df)
    assert out["status"] == "unverified_metadata"
    assert (out["n_unknown"], out["n_no_observation"], out["n_partial"], out["n_low_months"]) == (1, 1, 1, 1)
    assert out["n_support_issues"] == 4
    df = df.iloc[[0]].copy()
    ok = observation_support_screen(df)
    assert ok["status"] == "screened_no_flag_not_field_validated"
    assert ok["requires_field_validation"]


def test_observation_screen_rejects_incoherent_metadata_and_rules():
    df = pd.DataFrame({
        "dq_status": ["observed", "no_observation"],
        "dq_observed_fraction": [0.3, 0.5],
        "dq_mean_valid_months": [12, 0],
    })
    out = observation_support_screen(df)
    assert out["status"] == "unverified_metadata" and out["n_unknown"] == 2
    with pytest.raises(ValueError):
        observation_support_screen(df, min_months=0)


def test_g12_large_grid_moran_does_not_fabricate_inference():
    yy, xx = np.mgrid[:16, :16]
    cx = (xx.ravel() + 0.5) * 500
    cy = (yy.ravel() + 0.5) * 500
    rng = np.random.default_rng(20)
    d = np.hypot(cx - cx.mean(), cy - cy.mean()) / 1000
    ntl = np.clip(20.0 + 9.0 * np.sin(cx / 2000.0) + rng.normal(0, 0.1, cx.size), 0.1, None)
    result = resid_moran(
        cx, cy, ntl, np.full(cx.size, 0.25), d,
        np.zeros(cx.size, bool), 500.0, max_n_perm=30,
    )
    assert np.isfinite(result["I"]) and result["I"] > 0.3
    assert not result["perm_done"] and np.isnan(result["p"])
    assert result["descriptive_high_I"]
    assert not result["flag"]


def _field_csv(tmp_path, *, incomplete=True):
    yy, xx = np.mgrid[:6, :6]
    n = xx.size
    ntl = 5.0 + xx.ravel() + 2.0 * yy.ravel()
    stat = np.array(["observed"] * n, dtype=object)
    frac = np.ones(n, dtype=float)
    months = np.full(n, 10.0)
    ntl[:3] = 0.0  # observed post-clipping zero
    if incomplete:
        ntl[7:10] = 0.0
        stat[7:10] = "no_observation"
        frac[7:10] = 0.0
        months[7:10] = 0.0
    df = pd.DataFrame({
        "grid_id": np.arange(n), "cell_size_m": 500,
        "area_km2": 0.25,
        "centroid_x_epsg32650": xx.ravel() * 500.0 + 250,
        "centroid_y_epsg32650": yy.ravel() * 500.0 + 250,
        "ntl_mean": ntl, "dq_status": stat, "dq_observed_fraction": frac,
        "dq_mean_valid_months": months,
        "dq_negative_fraction": np.zeros(n),
    })
    csv = tmp_path / "test_support.csv"
    df.to_csv(csv, index=False)
    return csv, df


def test_g10_g18_field_runner_rejects_all_observed_and_unknown(tmp_path):
    csv, df = _field_csv(tmp_path, incomplete=False)
    with pytest.raises(ValueError, match="all-observed"):
        field.load_candidate(csv)
    df.loc[4, "dq_status"] = "unknown"
    df.to_csv(csv, index=False)
    with pytest.raises(ValueError, match="Unknown/invalid"):
        field.load_candidate(csv)


def test_g10_g18_field_runner_preserves_observed_zero_vs_missing(tmp_path):
    csv, df = _field_csv(tmp_path)
    source = field.load_candidate(csv)
    assert source["support"]["n_no_observation"] == 3
    assert source["support"]["n_supported_zero_after_clipping"] == 3
    report, cells = field.run_field_audit(source, perms=19, alpha=0.05)
    assert report["status"].endswith("not_independently_certified")
    assert report["source_support"]["n_no_observation"] == 3
    assert report["runs"]["legacy_positive"]["n_no_observation_tested"] == 0
    assert report["runs"]["supported_with_zeros"]["n_no_observation_tested"] == 0
    assert report["runs"]["naive_all_zeros"]["n_no_observation_tested"] == 3
    assert len(cells) == 36
    assert "supported_with_zeros_class" in cells
    assert len(report["comparisons"]) == 3
    reference = pd.DataFrame({
        "grid_id": df.grid_id,
        "ref_observed_fraction": df.dq_observed_fraction,
        "ref_mean_valid_months": df.dq_mean_valid_months,
    })
    ref_csv = tmp_path / "reference.csv"
    reference.to_csv(ref_csv, index=False)
    good = field._independent_support_check(source["df"], ref_csv)
    assert good["within_tolerance_1e_3"]
    reference.loc[0, "ref_mean_valid_months"] = 2
    reference.to_csv(ref_csv, index=False)
    assert not field._independent_support_check(source["df"], ref_csv)["within_tolerance_1e_3"]


def test_g10_source_cf_cvg_count_is_not_months():
    ee = MagicMock()
    ee.ImageCollection.return_value.filterDate.return_value.filterBounds.return_value.size.return_value.getInfo.return_value = 12
    with patch("ntl.ee_extra.download_tiled_geotiff", return_value=b"mock") as dl:
        out = ee_extra.fetch_cf_cvg_total_raster(
            ee, "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG", (100, 10, 100.01, 10.01),
            2020, 463.83
        )
    assert out == b"mock" and dl.call_count == 1
    image = ee.ImageCollection.return_value.filterDate.return_value.filterBounds.return_value
    assert image.map.called
    # The count source is cf_cvg, not a monthly 0/1 count.
    monthly = MagicMock()
    image.map.call_args.args[0](monthly)
    monthly.select.assert_called_with("cf_cvg")


def test_single_register_has_all_and_only_original_g01_g18():
    import json

    register = json.loads(
        (ROOT / "validation" / "scientific_closure_register.json").read_text(encoding="utf-8")
    )
    codes = [item["id"] for item in register["disposition"]]
    assert codes == [f"G{i:02}" for i in range(1, 19)]
    allowed = set(register["statuses"])
    assert all(item["status"] in allowed for item in register["disposition"])
    assert all(item["claim_ceiling"] and item["evidence_needed"] for item in register["disposition"])
    assert "V11" in " ".join(register["no_repetition"])


def test_g16_evidence_link_matches_actual_application_source():
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    assert 'GEE_DATASET = "NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG"' in app
    for name in ("README.md", "README-vi.md"):
        evidence = (ROOT / "validation" / "evidence" / name).read_text(encoding="utf-8")
        assert "NOAA_VIIRS_DNB_MONTHLY_V1_VCMSLCFG" in evidence


def test_g11_utm_scope_is_explicit_and_conservative():
    local = utm_applicability_screen((113.9, 22.4, 114.4, 23.1))
    assert not local["unsupported"]
    assert not local["requires_geodesic_validation"]
    wide = utm_applicability_screen((100.0, 20.0, 111.0, 30.0))
    assert wide["status"] == "broad_extent_needs_geodesic_error_check"
    assert wide["requires_geodesic_validation"] and not wide["unsupported"]
    polar = utm_applicability_screen((30.0, 84.2, 31.0, 85.1))
    assert polar["unsupported"]
    dateline_bbox = utm_applicability_screen((-179.0, -20.0, 179.0, -19.0))
    assert dateline_bbox["unsupported"]
    with pytest.raises(ValueError):
        utm_applicability_screen((20.0, 30.0, 10.0, 40.0))


def test_g06_uncalibrated_hill_cannot_receive_success_status():
    from ntl.lisa_core import run_lisa
    from ntl.lisa_diagnostics import auto_diagnostics
    yy, xx = np.mgrid[:12, :12]
    cx, cy = (xx.ravel() + 0.5) * 500.0, (yy.ravel() + 0.5) * 500.0
    ntl = np.maximum(0.1, 12.0 + 3.0 * np.sin(cx / 1000.0) + cy / 2000.0)
    area = np.full(len(ntl), 0.25)
    res = run_lisa(cx, cy, ntl, area, 500.0, perms=19, fdr=False)
    diag = auto_diagnostics(
        cx, cy, ntl, area, 500.0, res.cell_df,
        res.region_metrics, 19, 0.05, False,
    )
    hill = next(item for item in diag["items"] if item["key"] == "hill")
    assert hill["level"] != "ok"


def test_g10_independent_source_raster_reference_respects_native_geometry():
    import geopandas as gpd
    import rasterio
    import shapely.geometry
    from rasterio.io import MemoryFile
    from rasterio.transform import from_origin

    spec = importlib.util.spec_from_file_location(
        "g10_reference_zonal", ROOT / "validation" / "g10_reference_zonal.py"
    )
    ref_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref_mod)

    origin_x, origin_y = 500000.0, 2000000.0
    transform = from_origin(origin_x, origin_y, 500.0, 500.0)
    observed = np.ones((4, 4), dtype=np.float32)
    months = np.full((4, 4), 8.0, dtype=np.float32)
    counts = np.full((4, 4), 60.0, dtype=np.float32)
    observed[0, 0] = months[0, 0] = counts[0, 0] = 0.0
    with MemoryFile() as mem:
        with mem.open(driver="GTiff", width=4, height=4, count=3,
                      dtype="float32", crs="EPSG:32650",
                      transform=transform, nodata=np.nan) as writer:
            writer.write(np.stack([observed, months, counts]))
            for i, name in enumerate(ref_mod.BANDS, start=1):
                writer.set_band_description(i, name)
        raw = mem.read()
    geometries = [
        shapely.geometry.box(origin_x + ix * 500, origin_y - (iy + 1) * 500,
                             origin_x + (ix + 1) * 500, origin_y - iy * 500)
        for iy in range(4) for ix in range(4)
    ]
    polygons = gpd.GeoDataFrame(
        {"grid_id": np.arange(16)}, geometry=geometries, crs="EPSG:32650"
    )
    ref = ref_mod.make_reference(raw, polygons)
    assert len(ref) == 16
    assert ref.loc[0, "ref_cf_cvg_total"] == pytest.approx(0.0)
    assert ref.loc[1, "ref_cf_cvg_total"] == pytest.approx(60.0)
    assert ref.loc[1, "ref_mean_valid_months"] == pytest.approx(8.0)
    assert ref.loc[1, "ref_observed_fraction"] == pytest.approx(1.0)
