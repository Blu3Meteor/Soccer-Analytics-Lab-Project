# PROVENANCE: AI-ASSISTED DRAFT — MATHEMATICAL ANALYSIS
# MANUAL REVIEW REQUIRED: Do not describe this module as manually authored.
# A student should be able to derive, justify, test, and if necessary rewrite
# each operation below before using it in assessed analytical work.

from __future__ import annotations

import numpy as np
from scipy.signal import convolve2d

from .season_heatmap_data import GRID_COLUMNS


def smooth_grid(grid: list[list[float]]) -> list[list[float]]:
    """Return a mass-preserving local smoothing of a 12-by-8 event grid.

    Mathematical definition
    -----------------------
    Each source block distributes its value to the valid blocks in its 3-by-3
    neighbourhood. The unnormalised weights are::

        1  2  1
        2  4  2
        1  2  1

    Interior blocks therefore use a denominator of 16. At pitch edges the
    missing neighbours are removed and the remaining weights are renormalised.
    Renormalising separately for every source block guarantees that the sum of
    the smoothed grid equals the sum of the raw grid. This is a display aid,
    not a statistical density estimate and not evidence of event locations.
    """
    values = np.maximum(np.asarray(grid, dtype=float), 0.0)
    kernel = np.array(((1.0, 2.0, 1.0), (2.0, 4.0, 2.0), (1.0, 2.0, 1.0)))

    # Each source cell has its own edge-aware denominator. Normalise sources
    # first, then let SciPy distribute them through the symmetric kernel.
    local_weight_totals = convolve2d(np.ones_like(values), kernel, mode="same")
    smoothed = convolve2d(values / local_weight_totals, kernel, mode="same")
    return smoothed.tolist()


def display_scale_maximum(grid: list[list[float]]) -> float:
    """Use the indexed 90% point of positive blocks as the colour-scale cap.

    Values above this cap receive the maximum colour. This prevents a single
    extreme block from making all other blocks appear nearly empty. It changes
    only the colour mapping; raw values and displayed totals are untouched.

    Note that this is an indexed empirical quantile, not an interpolated
    statistical percentile. For ``n`` positive values, the selected zero-based
    index is ``min(n - 1, floor(0.9 * n))``.
    """
    positive = np.asarray(grid, dtype=float)
    positive = positive[positive > 0]
    if positive.size == 0:
        return 0.0
    return float(np.quantile(positive, 0.9, method="higher"))


def attacking_third_share(grid: list[list[float]]) -> float:
    """Calculate the fraction of grid value in the rightmost pitch third.

    With 12 equal-width columns and left-to-right attacking direction, columns
    8 to 11 represent x from 70m to 105m. The denominator is the complete grid
    total. An empty grid returns 0 instead of dividing by zero.
    """
    values = np.asarray(grid, dtype=float)
    total = float(values.sum())
    attacking_total = float(values[:, 8:GRID_COLUMNS].sum())
    return attacking_total / total if total else 0.0
