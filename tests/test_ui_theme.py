from __future__ import annotations

import re

import numpy as np

from ntl.ui_theme import light_signature


def test_small_regular_light_signature_does_not_scatter_cells():
    x, y = np.meshgrid(np.arange(7) * 500.0, np.arange(5) * 500.0)
    values = np.arange(1, 36, dtype=float)

    html = light_signature(x.ravel(), y.ravel(), values)

    assert 'style="--c:7"' in html
    assert len(re.findall(r"<i\b", html)) == 35
    assert 'class="e"' not in html


def test_light_signature_keeps_empty_cells_inside_irregular_boundary():
    x = np.array([0.0, 500.0, 0.0])
    y = np.array([500.0, 500.0, 0.0])
    values = np.array([1.0, 2.0, 3.0])

    html = light_signature(x, y, values)

    assert 'style="--c:2"' in html
    assert len(re.findall(r"<i\b", html)) == 4
    assert html.count('class="e"') == 1
