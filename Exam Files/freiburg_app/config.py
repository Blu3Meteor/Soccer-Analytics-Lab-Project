from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_ROOT = BASE_DIR.parent / "Exam Data" / "open-data" / "data"
ITERATION_ID = 743
FREIBURG_NAME = "SC Freiburg"
BERLIN_TZ = ZoneInfo("Europe/Berlin")

KPI_RED_CARD = 47
KPI_SUCCESSFUL_PASSES = 90
KPI_UNSUCCESSFUL_PASSES = 91
KPI_SHOTS = 100
KPI_NEUTRAL_PASSES = 1431
KPI_SHOTS_ON_TARGET = 1515
KPI_YELLOW_CARD = 1637
KPI_SECOND_YELLOW_CARD = 1638
