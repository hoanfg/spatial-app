"""Regression checks: Space-Time display must not change numeric or CSV outputs."""
import pandas as pd
import pytest

from ntl.spacetime_labels import format_regime_summary


@pytest.mark.parametrize("lang,expected", [
    ("en", "Synchronized Relative Decline"),
    ("vi", "Cùng giảm vị thế tương đối"),
])
def test_relative_decline_is_display_only(lang, expected):
    original = pd.DataFrame({
        "regime": ["4_Synchronized_Decline", "Excluded_or_Static"],
        "cells": [4711, 1897],
        "area_share_pct": [60.0, 40.0],
        "mean_delta_ln_ntl": [0.2, 0.0],
    })
    snapshot = original.copy(deep=True)

    display = format_regime_summary(original, lang=lang)

    assert display.loc[0, "regime"] == expected
    assert display.loc[1, "regime"] == "Excluded_or_Static"
    pd.testing.assert_frame_equal(original, snapshot)
    pd.testing.assert_frame_equal(display.drop(columns="regime"), original.drop(columns="regime"))
    assert original.loc[0, "regime"] == "4_Synchronized_Decline"


def test_regime_summary_display_rejects_invalid_language():
    with pytest.raises(ValueError):
        format_regime_summary(pd.DataFrame({"regime": []}), lang="unknown")
