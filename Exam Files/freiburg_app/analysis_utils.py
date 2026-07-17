# PROVENANCE: AI-ASSISTED DRAFT — SHARED MATHEMATICAL TRANSFORMATIONS

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def per_90(value: float, minutes: float) -> float:
    return value / minutes * 90 if minutes else 0.0


def percentile_rank(value: float, values: Sequence[float]) -> float:
    """Return the existing strict-lower rank on a 0..100 scale."""
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return 0.0
    if array.size == 1:
        return 100.0
    below = np.count_nonzero(array < value)
    return float(np.round(below / (array.size - 1) * 100))


def minmax_score(value: float, values: Sequence[float]) -> float:
    """Scale a value to 0..100 within its comparison group."""
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return 0.0
    minimum = float(array.min())
    spread = float(np.ptp(array))
    if spread == 0:
        return 100.0
    return float(np.round((value - minimum) / spread * 100))
