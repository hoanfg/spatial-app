from __future__ import annotations

import math


def fmt_p(p: float, perms: int | None, prefix: bool = False, digits: int = 3) -> str:
    """Format a permutation pseudo p-value without overstating its precision.

    With ``R`` permutations, the smallest measurable value is ``1/(R+1)``.
    Values at that floor are displayed as an upper bound.
    """
    if p is None or not math.isfinite(p):
        return "N/A"
    lead = "p " if prefix else ""
    if perms and perms > 0:
        floor = 1.0 / (perms + 1)
        if p <= floor * (1 + 1e-9):
            return f"{lead}≤ {floor:.{digits}f}"
    return f"{lead}{'= ' if prefix else ''}{p:.{digits}f}"
