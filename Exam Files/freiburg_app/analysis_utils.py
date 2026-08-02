from collections.abc import Sequence

from scipy.stats import percentileofscore


# Data Processing Assistance
# Mathematical reference: Soccermatics radar plots
# https://soccermatics.readthedocs.io/en/latest/gallery/lesson3/plot_RadarPlot.html
def per_90(value: float, minutes: float) -> float:
    return value / minutes * 90 if minutes else 0.0


def percentile_rank(value: float, values: Sequence[float]) -> float:
    """Return the Soccermatics/Scipy percentile rank on a 0..100 scale."""
    if len(values) == 0:
        return 0.0
    return float(percentileofscore(values, value))


# Extra mathematical method: not part of the referenced Soccermatics lessons.
def minmax_score(value: float, values: Sequence[float]) -> float:
    """Scale a value to 0..100 within its comparison group."""
    if len(values) == 0:
        return 0.0
    minimum = min(values)
    spread = max(values) - minimum
    if spread == 0:
        return 100.0
    return float(round((value - minimum) / spread * 100))
