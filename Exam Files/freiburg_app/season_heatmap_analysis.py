# PROVENANCE: AI-ASSISTED DRAFT — MATHEMATICAL ANALYSIS
# MANUAL REVIEW REQUIRED: Do not describe this module as manually authored.
# A student should be able to derive, justify, test, and if necessary rewrite
# each operation below before using it in assessed analytical work.

from __future__ import annotations

from .season_heatmap_data import GRID_COLUMNS, GRID_ROWS, empty_grid


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
    kernel = ((1.0, 2.0, 1.0), (2.0, 4.0, 2.0), (1.0, 2.0, 1.0))
    smoothed = empty_grid()

    for source_row, row in enumerate(grid):
        for source_column, value in enumerate(row):
            if value <= 0:
                continue

            valid_neighbours: list[tuple[int, int, float]] = []
            for row_offset in range(-1, 2):
                for column_offset in range(-1, 2):
                    target_row = source_row + row_offset
                    target_column = source_column + column_offset
                    if 0 <= target_row < GRID_ROWS and 0 <= target_column < GRID_COLUMNS:
                        weight = kernel[row_offset + 1][column_offset + 1]
                        valid_neighbours.append((target_row, target_column, weight))

            # The local denominator changes at an edge, which is why this is
            # calculated per source block rather than fixed at 16 everywhere.
            local_weight_total = sum(weight for _row, _column, weight in valid_neighbours)
            for target_row, target_column, weight in valid_neighbours:
                smoothed[target_row][target_column] += value * weight / local_weight_total

    return smoothed


def display_scale_maximum(grid: list[list[float]]) -> float:
    """Use the indexed 90% point of positive blocks as the colour-scale cap.

    Values above this cap receive the maximum colour. This prevents a single
    extreme block from making all other blocks appear nearly empty. It changes
    only the colour mapping; raw values and displayed totals are untouched.

    Note that this is an indexed empirical quantile, not an interpolated
    statistical percentile. For ``n`` positive values, the selected zero-based
    index is ``min(n - 1, floor(0.9 * n))``.
    """
    non_zero = sorted(value for row in grid for value in row if value > 0)
    if not non_zero:
        return 0.0
    percentile_index = min(len(non_zero) - 1, int(len(non_zero) * 0.9))
    return non_zero[percentile_index]


def attacking_third_share(grid: list[list[float]]) -> float:
    """Calculate the fraction of grid value in the rightmost pitch third.

    With 12 equal-width columns and left-to-right attacking direction, columns
    8 to 11 represent x from 70m to 105m. The denominator is the complete grid
    total. An empty grid returns 0 instead of dividing by zero.
    """
    total = sum(value for row in grid for value in row)
    attacking_total = sum(row[column] for row in grid for column in range(8, GRID_COLUMNS))
    return attacking_total / total if total else 0.0
