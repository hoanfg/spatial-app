"""A03: hand-checkable numerical reference cases, independent of production oracles.

No Earth Engine service, fixture GeoJSON or fitted parameters are needed.
The observations and expected values are deliberately small and explicit.
"""
import itertools

import numpy as np
import pytest

from ntl.lisa_core import bh_reject, build_queen_neighbors, gini, local_moran


def _pairwise_gini(values):
    """Definition using every pairwise absolute difference (not sorted-rank code)."""
    x = np.asarray(values, dtype=float)
    return sum(abs(float(a) - float(b)) for a, b in itertools.product(x, repeat=2)) / (2 * len(x) * float(x.sum()))


@pytest.mark.parametrize(
    ("observations", "expected"),
    [
        ([5, 5, 5, 5], 0.0),
        ([0, 0, 10, 10], 0.5),
        ([1, 2, 3, 4], 0.25),
        ([0, 0, 0, 0], 0.0),  # documented degenerate convention
        ([], 0.0),
    ],
)
def test_a03_gini_hand_oracle(observations, expected):
    assert gini(observations) == pytest.approx(expected, abs=1e-12)
    if observations and sum(observations):
        assert gini(observations) == pytest.approx(_pairwise_gini(observations), abs=1e-12)


def _chain_neighbors():
    """Four spatial units, binary undirected 1--2--3--4, padded by -1."""
    out = np.full((4, 8), -1, dtype=np.int64)
    out[0, 0] = 1
    out[1, :2] = [0, 2]
    out[2, :2] = [1, 3]
    out[3, 0] = 2
    return out


def test_a03_local_moran_independent_four_unit_oracle():
    # Centered observations x=[1,2,3,4] yield z=[-1.5,-0.5,0.5,1.5].
    # With row-standardized binary neighbors, spatial lag is [-0.5,-0.5,0.5,0.5].
    # ESDA local denominator = sum(z*z)/(n-1) = 5/3.
    z = np.array([-1.5, -0.5, 0.5, 1.5])
    eligible = np.ones(4, dtype=bool)
    actual_i, actual_lag, actual_p, quadrant = local_moran(
        z, _chain_neighbors(), eligible, eligible, perms=99, seed=42
    )
    np.testing.assert_allclose(actual_lag, [-0.5, -0.5, 0.5, 0.5], atol=1e-12)
    np.testing.assert_allclose(actual_i, [0.45, 0.15, 0.15, 0.45], atol=1e-12)
    np.testing.assert_array_equal(quadrant, [1, 1, 0, 0])  # LL, LL, HH, HH
    assert np.all(np.isfinite(actual_p))
    assert np.all((actual_p >= 0) & (actual_p <= 1))


def test_a03_local_moran_seed_reproducibility():
    z = np.array([-1.5, -0.5, 0.5, 1.5])
    eligible = np.ones(4, dtype=bool)
    first = local_moran(z, _chain_neighbors(), eligible, eligible, perms=99, seed=1234)
    second = local_moran(z, _chain_neighbors(), eligible, eligible, perms=99, seed=1234)
    for left, right in zip(first, second):
        np.testing.assert_array_equal(left, right)


def test_a03_bh_fdr_hand_oracle():
    # Sort: 0.001, .010, .040, .200. Thresholds at alpha=.05:
    # .0125, .0250, .0375, .0500 -> reject first two only.
    p = np.array([0.2, 0.01, 0.04, 0.001])
    np.testing.assert_array_equal(bh_reject(p, alpha=0.05), [False, True, False, True])
    np.testing.assert_array_equal(bh_reject([], alpha=0.05), [])


def test_a03_queen_adjacency_on_two_by_two_grid():
    # Exact integer grid indices remove coordinate-rounding ambiguity.
    ix = np.array([0, 1, 0, 1])
    iy = np.array([0, 0, 1, 1])
    nbr = build_queen_neighbors(
        cx=ix * 500.0 + 250.0,
        cy=iy * 500.0 + 250.0,
        cell_size_m=500.0,
        active=np.ones(4, dtype=bool),
        grid_ix=ix,
        grid_iy=iy,
    )
    for node in range(4):
        observed = set(nbr[node][nbr[node] >= 0].tolist())
        assert observed == set(range(4)) - {node}


def test_a03_local_moran_is_not_global_moran():
    # Binary undirected chain and x=[1,2,3,4]:
    # centered z, S0=6, sum(z_i*z_j over directed edges)=2.5,
    # sum(z_i^2)=5, n=4 -> global I=(4/6)*(2.5/5)=1/3.
    # This independently checked GLOBAL result must not be confused
    # with the mean of ESDA-scaled LOCAL I, which uses row-normalized lag.
    z = np.array([-1.5, -0.5, 0.5, 1.5])
    edges = ((0, 1), (1, 2), (2, 3))
    directed_products = 2 * sum(z[i] * z[j] for i, j in edges)
    global_i = len(z) / (2 * len(edges)) * directed_products / np.dot(z, z)
    assert global_i == pytest.approx(1 / 3, abs=1e-12)
    eligible = np.ones(4, dtype=bool)
    local_i = local_moran(z, _chain_neighbors(), eligible, eligible, perms=9, seed=42)[0]
    assert float(local_i.mean()) != pytest.approx(global_i)
