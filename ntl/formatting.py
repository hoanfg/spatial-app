from __future__ import annotations

import math


def fmt_p(p: float, perms: int | None, prefix: bool = False, digits: int = 3) -> str:
    """Định dạng p-value giả từ hoán vị.

    Với R hoán vị thì p nhỏ nhất đo được là 1/(R+1). Nếu p chạm mức đó, ta chỉ biết nó "≤ sàn",
    nên hiện '≤ 0.005' chứ không phải '0.005'. prefix=True thêm 'p ' phía trước."""
    if p is None or not math.isfinite(p):
        return "N/A"
    lead = "p " if prefix else ""
    if perms and perms > 0:
        floor = 1.0 / (perms + 1)
        if p <= floor * (1 + 1e-9):
            return f"{lead}≤ {floor:.{digits}f}"
    return f"{lead}{'= ' if prefix else ''}{p:.{digits}f}"
