"""A03-B: independent statistical invariants and small synthetic checks.

The exact conditional permutation distribution is enumerated separately from
the production random sampler. Statistical simulation is compared only within
a stated tolerance; identical random draws are never assumed.
"""
from itertools import combinations

import numpy as np
import pytest

from ntl.lisa_core import bh_reject, local_moran, run_spacetime_lisa


def _single_focal_neighbors(n, neighbors):
    matrix = np.full((n, 8), -1, dtype=np.int64)
    matrix[0, :len(neighbors)] = neighbors
    return matrix


def _exact_conditional_tails(z, observed_neighbors):
    """Enumerate unordered non-focal k-subsets for focal unit zero."""
    candidates = range(1, len(z))
    k = len(observed_neighbors)
    observed = float(np.mean([z[j] for j in observed_neighbors]))
    possibilities = [float(np.mean([z[j] for j in indices]))
                     for indices in combinations(candidates, k)]
    ge = sum(value >= observed - 1e-12 for value in possibilities)
    le = sum(value <= observed + 1e-12 for value in possibilities)
    # As permutations -> infinity, (+1)/(perms+1) converges to these tails.
    one_tail = min(ge, le) / len(possibilities)
    return one_tail, min(1.0, 2.0 * one_tail)


def test_a03b_exact_conditional_distribution_against_monte_carlo():
    # Fixed focal z=3, observed neighbor z=1. The three possible non-focal
    # singleton samples have lag 1, -1, -3, so tails are 1/3 and 3/3.
    z = np.array([3.0, 1.0, -1.0, -3.0])
    expected_one, expected_two = _exact_conditional_tails(z, [1])
    assert expected_one == pytest.approx(1 / 3)
    assert expected_two == pytest.approx(2 / 3)

    eligible = np.array([True, False, False, False])
    members = np.ones(4, dtype=bool)
    nbr = _single_focal_neighbors(4, [1])
    one = local_moran(z, nbr, eligible, members, perms=9999, seed=2026, two_sided=False)
    two = local_moran(z, nbr, eligible, members, perms=9999, seed=2026, two_sided=True)
    assert one[2][0] == pytest.approx(expected_one, abs=0.035)
    assert two[2][0] == pytest.approx(expected_two, abs=0.07)
    assert two[2][0] == pytest.approx(min(1.0, 2 * one[2][0]), abs=1e-12)
    assert np.isnan(one[2][1:]).all()


def test_a03b_inclusive_ties_and_plus_one_correction():
    # Every possible non-focal singleton equals observed. Inclusive tails
    # are both 100%; doubled smaller-tail p is capped at 1.
    z = np.ones(4, dtype=float)
    members = np.ones(4, dtype=bool)
    focal = np.array([True, False, False, False])
    nbr = _single_focal_neighbors(4, [1])
    for two_sided in (False, True):
        i, lag, p, quadrant = local_moran(
            z, nbr, focal, members, perms=19, seed=7, two_sided=two_sided
        )
        assert i[0] == pytest.approx(0.75)
        assert lag[0] == pytest.approx(1.0)
        assert p[0] == pytest.approx(1.0)
        assert quadrant[0] == 0


def test_a03b_fdr_step_up_and_boundary_equality():
    # BH is step-up, not independent threshold checks: p2=.025 equals
    # alpha*(2/4); p1=.015 > alpha/4 yet both are rejected.
    p = np.array([0.08, 0.025, 0.015, 0.20])
    np.testing.assert_array_equal(
        bh_reject(p, alpha=0.05), [False, True, True, False]
    )
    np.testing.assert_array_equal(
        bh_reject(p, alpha=0.01), [False, False, False, False]
    )


def _grid3():
    xx, yy = np.meshgrid(np.arange(3), np.arange(3))
    return (xx.ravel() * 500.0 + 250, yy.ravel() * 500.0 + 250,
            np.full(9, 0.25))


def test_a03b_spacetime_identical_years_are_static():
    x, y, area = _grid3()
    values = np.arange(1.0, 10.0)
    out = run_spacetime_lisa(x, y, values, values.copy(), area, 500.0,
                             year_t0=2018, year_t1=2024)
    df = out.st_cell_df
    assert set(df["spacetime_regime"]) == {"Excluded_or_Static"}
    np.testing.assert_allclose(df["delta_ntl"], 0.0, atol=0)
    np.testing.assert_allclose(df["delta_z"], 0.0, atol=0)
    np.testing.assert_allclose(df["delta_lag_z"], 0.0, atol=0)
    assert out.metrics["mean_delta_ln_ntl"] == pytest.approx(0.0)
    assert (df["margin_type"] == "intensive").all()


def test_a03b_spacetime_missing_year_is_not_zero():
    x, y, area = _grid3()
    t0 = np.arange(1.0, 10.0)
    t1 = t0.copy()
    t1[4] = np.nan
    out = run_spacetime_lisa(x, y, t0, t1, area, 500.0,
                             year_t0=2018, year_t1=2024)
    df = out.st_cell_df
    assert df.loc[4, "ntl_2018"] == pytest.approx(5.0)
    assert np.isnan(df.loc[4, "ntl_2024"])
    assert np.isnan(df.loc[4, "delta_ntl"])
    assert df.loc[4, "margin_type"] == "excluded"
    assert df.loc[4, "spacetime_regime"] == "Excluded_or_Static"
    # There is no valid transition to label as extensive exit.
    assert out.metrics["extensive_exit_pct"] == pytest.approx(0.0)
