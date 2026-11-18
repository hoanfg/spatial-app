"""Scientific-claim guardrails, separate from established numerical validation.

These tests protect interpretation and chronological direction. They do not
re-run the archived field comparisons for VIIRS, GHSL, Gini or A03.
"""
from pathlib import Path

import numpy as np
import pytest

from ntl.lisa_core import (
    compute_spillover_rings_and_rdd,
    run_lisa,
    run_spacetime_lisa,
)


@pytest.mark.parametrize("year_t0,year_t1", [(2020, 2020), (2021, 2020)])
def test_spacetime_requires_forward_chronology(year_t0, year_t1):
    with pytest.raises(ValueError, match="year_t0 < year_t1"):
        run_spacetime_lisa(
            np.array([250.0]), np.array([250.0]),
            np.array([1.0]), np.array([2.0]),
            np.array([0.25]), 500.0, year_t0=year_t0, year_t1=year_t1,
        )


def test_signed_hh_distance_is_between_cell_centers_not_boundaries():
    cx = np.array([250.0, 750.0, 1250.0])
    cy = np.zeros(3)
    hh = np.array([True, False, False])
    core = np.ones(3, dtype=bool)
    edge = np.zeros(3, dtype=bool)
    distance, signed, groups = compute_spillover_rings_and_rdd(
        cx, cy, hh, core, edge,
    )
    assert np.allclose(distance, [0.0, 0.5, 1.0])
    assert np.allclose(signed, [-0.5, 0.5, 1.0])
    assert groups[0] == "0_Treated_HH"  # Historical export identifier only.


def test_legacy_spatial_ar1_key_is_cross_sectional_lag_correlation():
    xy = np.arange(5, dtype=float) * 500 + 250
    cx, cy = [a.ravel() for a in np.meshgrid(xy, xy)]
    ntl = np.arange(1.0, 26.0) ** 1.5
    result = run_lisa(
        cx, cy, ntl, np.full(ntl.size, 0.25), 500.0,
        perms=199, fdr=False,
    )
    cells = result.cell_df
    ok = cells["lisa_p_sim"].notna()
    z = cells.loc[ok, "ntl_z_lit"].to_numpy(float)
    lag = cells.loc[ok, "lisa_lag_z"].to_numpy(float)
    r = float(np.corrcoef(z, lag)[0, 1])
    assert result.region_metrics["spatial_ar1_persistence"] == pytest.approx(r, abs=0.003)


def test_scientific_descriptions_do_not_assert_unidentified_effects():
    root = Path(__file__).resolve().parents[1]
    ui = (root / "ntl" / "lisa_ui.py").read_text(encoding="utf-8")
    app = (root / "app.py").read_text(encoding="utf-8")
    for unsupported in (
        "Causal spillover rings",
        "Spatial AR(1) Persistence",
        "Độ bền AR(1) không gian",
        "Vành đai lan tỏa nhân quả",
        "resource siphoning effect",
    ):
        assert unsupported not in ui
    assert "other_years = sorted({int(y) for y in available_years if int(y) < yr})" in ui
    assert "Global economic class 1-5" not in app
    assert "Nhóm kinh tế toàn cầu 1-5" not in app
