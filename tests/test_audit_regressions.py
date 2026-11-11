"""Independent ESDA and exhaustive conditional-null benchmarks (audit 2026-11-11)."""
from itertools import combinations, product
import ast
from pathlib import Path

import numpy as np
import pytest

from ntl.lisa_core import build_queen_neighbors, local_moran, zscore_lit_only, bh_reject


def fixture(nx, ny):
    ix, iy = np.meshgrid(np.arange(nx), np.arange(ny))
    x = np.random.default_rng(17).lognormal(size=nx * ny)
    members = np.ones(x.size, bool)
    nbr = build_queen_neighbors(ix.ravel()*500+250, iy.ravel()*500+250, 500, members)
    return x, members, nbr


@pytest.mark.parametrize('shape', [(3, 3), (6, 5)])
def test_exhaustive_conditional_null(shape):
    x, members, nbr = fixture(*shape)
    z = zscore_lit_only(x)
    focal = np.zeros(x.size, bool)
    focal[0] = True
    observed, _, p, _ = local_moran(z, nbr, focal, members, 99999, 42)
    scale = (len(x)-1) / np.sum(z*z)
    def tail(samples):
        sims = np.array([scale*z[0]*np.mean(s) for s in samples])
        return min(1, 2*min(np.mean(sims >= observed[0]-1e-12),
                            np.mean(sims <= observed[0]+1e-12)))
    exact = tail(combinations(z[1:], 3))
    replacement = tail(product(z[1:], repeat=3))
    assert abs(p[0]-exact) < 0.012
    assert abs(p[0]-exact) < abs(p[0]-replacement)
    if len(x) == 30:
        assert exact == pytest.approx(0.5648604269293924)


@pytest.mark.parametrize('shape', [(3, 3), (10, 10), (20, 20)])
@pytest.mark.parametrize('rook', [False, True])
def test_observed_local_i_matches_esda(shape, rook):
    from esda import Moran_Local
    from libpysal.weights import W
    x, members, nbr = fixture(*shape)
    if rook:
        nbr[:, [0, 2, 5, 7]] = -1
    w = W({i: list(row[row >= 0]) for i, row in enumerate(nbr)}, silence_warnings=True)
    ref = Moran_Local(x, w, permutations=0)
    observed, lag, _, q = local_moran(zscore_lit_only(x), nbr, members, members, 0)
    np.testing.assert_allclose(observed, ref.Is, atol=2e-14)
    np.testing.assert_array_equal(q, np.array([0, 3, 1, 2])[ref.q-1])


def test_complete_neighborhood_ties_and_two_tail():
    # Every non-focal member appears: conditional null is a point mass.
    x = np.arange(1., 10.)
    nbr = np.array([[j for j in range(9) if j != i] for i in range(9)])
    members = np.ones(9, bool)
    for two_sided in (False, True):
        _, _, p, _ = local_moran(zscore_lit_only(x), nbr, members, members, 99, two_sided=two_sided)
        np.testing.assert_equal(p, 1.)
        assert not bh_reject(p).any()


def test_app_raster_rewrites_preserve_nodata():
    # Both real extraction paths must use the tested mask reader and carry its
    # NaN nodata through to exactextract, before deliberate cell-level filling.
    tree = ast.parse((Path(__file__).parents[1] / 'app.py').read_text(encoding='utf-8'))
    readers = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Name) and n.func.id == 'read_valid_band']
    assert len(readers) == 2
    writers = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == 'open'
               and any(k.arg == 'driver' and isinstance(k.value, ast.Constant)
                       and k.value.value == 'GTiff' for k in n.keywords)]
    assert len(writers) == 2
    assert all(any(k.arg == 'nodata' for k in n.keywords) for n in writers)
