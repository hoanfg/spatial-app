"""Định dạng hiển thị dùng chung (chỉ thư viện chuẩn)."""
from __future__ import annotations

import math


def fmt_p(p: float, perms: int | None, prefix: bool = False, digits: int = 3) -> str:
    """Hiển thị p-value giả từ hoán vị.

    Với R hoán vị, p nhỏ nhất đo được là 1/(R+1). Khi p chạm mức sàn đó, giá trị thật chỉ biết là "≤ sàn",
    nên hiện '≤ 0.005' thay vì '0.005' để không bị hiểu là p chính xác. prefix=True thêm 'p ' phía trước."""
    if p is None or not math.isfinite(p):
        return "N/A"
    lead = "p " if prefix else ""
    if perms and perms > 0:
        floor = 1.0 / (perms + 1)
        if p <= floor * (1 + 1e-9):
            return f"{lead}≤ {floor:.{digits}f}"
    return f"{lead}{'= ' if prefix else ''}{p:.{digits}f}"
