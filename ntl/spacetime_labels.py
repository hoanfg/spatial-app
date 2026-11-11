"""Presentation-only Space-Time regime labels.

Keep legacy machine-readable regime identifiers unchanged in exports.
These labels describe directional changes in year-standardized ln(1+NTL)
and its spatial lag, not changes in absolute nighttime radiance.
"""
from __future__ import annotations

import pandas as pd

_LABELS = {
    "vi": {
        "1_Synergistic_Growth": "Cùng tăng vị thế tương đối (ô và láng giềng)",
        "2_Agglomeration_Shadow": "Ô giảm, láng giềng tăng vị thế tương đối",
        "3_Emergent_Pioneer": "Ô tăng, láng giềng giảm vị thế tương đối",
        "4_Synchronized_Decline": "Cùng giảm vị thế tương đối",
    },
    "en": {
        "1_Synergistic_Growth": "Synergistic Relative Growth",
        "2_Agglomeration_Shadow": "Cell Relative Decline / Neighbor Relative Growth",
        "3_Emergent_Pioneer": "Cell Relative Growth / Neighbor Relative Decline",
        "4_Synchronized_Decline": "Synchronized Relative Decline",
    },
}


def format_regime_summary(summary: pd.DataFrame, *, lang: str = "vi") -> pd.DataFrame:
    """Return an annotated display copy, preserving source data and column names.

    This function must never be applied to exported machine-readable data.
    """
    if lang not in _LABELS:
        raise ValueError(f"Unsupported language: {lang}")
    display = summary.copy()
    if "regime" in display.columns:
        display["regime"] = display["regime"].map(
            lambda value: _LABELS[lang].get(value, value)
        )
    return display
