# PROVENANCE: AI-ASSISTED — DATA EXTRACTION / TRANSFORMATION
# This module was generated with LLM assistance. It only reads Impect JSON data,
# selects Freiburg events, converts coordinates, and aggregates them into grids.
# It does not decide what the resulting patterns mean.

from __future__ import annotations

from collections import defaultdict
import csv
from io import StringIO
from typing import Any

import streamlit as st

from .config import (
    KPI_PXT_BALL_WIN,
    KPI_PXT_BLOCK,
    KPI_PXT_DRIBBLE,
    KPI_PXT_FOUL,
    KPI_PXT_PASS,
    KPI_PXT_SETPIECE,
    KPI_PXT_SHOT,
    KPI_SHOT_XG,
)
from .data import load_match_events, load_match_events_kpis


PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
GRID_COLUMNS = 12
GRID_ROWS = 8
PXT_KPIS = {
    KPI_PXT_PASS,
    KPI_PXT_DRIBBLE,
    KPI_PXT_SETPIECE,
    KPI_PXT_BLOCK,
    KPI_PXT_SHOT,
    KPI_PXT_BALL_WIN,
    KPI_PXT_FOUL,
}


def _clip(value: float, lower: float, upper: float) -> float:
    """Keep an adjusted coordinate inside the physical pitch boundary."""
    return min(upper, max(lower, value))


def _event_xy(event: dict[str, Any], key: str) -> tuple[float, float] | None:
    """Convert Impect centre-origin coordinates to a 0..105 by 0..68 pitch."""
    point = event.get(key) or {}
    coords = point.get("adjCoordinates") or point.get("coordinates")
    if not coords:
        return None
    x = _clip(float(coords.get("x", 0.0)) + PITCH_LENGTH / 2, 0.0, PITCH_LENGTH)
    y = _clip(PITCH_WIDTH / 2 - float(coords.get("y", 0.0)), 0.0, PITCH_WIDTH)
    return x, y


def _event_kpi_totals(events_kpis: list[dict[str, Any]]) -> tuple[dict[int, float], dict[int, float]]:
    """Index shot xG and summed attacking PxT by event ID for fast lookup."""
    xg_by_event: dict[int, float] = defaultdict(float)
    pxt_by_event: dict[int, float] = defaultdict(float)
    for item in events_kpis:
        event_id = int(item["eventId"])
        kpi_id = int(item.get("kpiId", -1))
        value = float(item.get("value") or 0.0)
        if kpi_id == KPI_SHOT_XG:
            xg_by_event[event_id] += value
        elif kpi_id in PXT_KPIS:
            pxt_by_event[event_id] += value
    return xg_by_event, pxt_by_event


def empty_grid() -> list[list[float]]:
    """Create the fixed 12-by-8 accumulation grid used by the heatmap."""
    return [[0.0 for _column in range(GRID_COLUMNS)] for _row in range(GRID_ROWS)]


def _add_to_grid(grid: list[list[float]], x: float, y: float, value: float) -> None:
    """Assign one event value to its pitch block using proportional binning."""
    column = min(GRID_COLUMNS - 1, max(0, int((x / PITCH_LENGTH) * GRID_COLUMNS)))
    row = min(GRID_ROWS - 1, max(0, int((y / PITCH_WIDTH) * GRID_ROWS)))
    grid[row][column] += value


@st.cache_data(show_spinner=False)
def season_freiburg_heatmap_data(
    match_ids: tuple[int, ...],
    freiburg_id: int,
) -> dict[str, Any]:
    """Extract season shot/xG and positive-PxT grids from Impect event files."""
    xg_grid = empty_grid()
    shot_grid = empty_grid()
    pxt_grid = empty_grid()
    action_grid = empty_grid()
    shot_count = 0
    action_count = 0
    total_xg = 0.0
    total_pxt = 0.0

    for match_id in match_ids:
        events = load_match_events(match_id)
        events_kpis = load_match_events_kpis(match_id)
        xg_by_event, pxt_by_event = _event_kpi_totals(events_kpis)
        for event in events:
            if int(event.get("squadId") or -1) != int(freiburg_id):
                continue
            event_id = int(event["id"])
            action_type = event.get("actionType")

            # A shot contributes once to the volume grid and contributes its xG
            # value to the quality grid at the event's starting coordinate.
            if action_type in {"SHOT", "GOAL"}:
                xy = _event_xy(event, "start")
                if xy:
                    value = max(0.0, xg_by_event.get(event_id, 0.0))
                    _add_to_grid(xg_grid, xy[0], xy[1], value)
                    _add_to_grid(shot_grid, xy[0], xy[1], 1.0)
                    total_xg += value
                    shot_count += 1

            # The destination is used for positive PxT when present; the start
            # coordinate is a documented fallback for events without an end.
            pxt_value = max(0.0, pxt_by_event.get(event_id, 0.0))
            if pxt_value > 0:
                xy = _event_xy(event, "end") or _event_xy(event, "start")
                if xy:
                    _add_to_grid(pxt_grid, xy[0], xy[1], pxt_value)
                    _add_to_grid(action_grid, xy[0], xy[1], 1.0)
                    total_pxt += pxt_value
                    action_count += 1

    return {
        "xg_grid": xg_grid,
        "shot_grid": shot_grid,
        "pxt_grid": pxt_grid,
        "action_grid": action_grid,
        "matches": len(match_ids),
        "shots": shot_count,
        "actions": action_count,
        "total_xg": round(total_xg, 2),
        "total_pxt": round(total_pxt, 2),
    }


def heatmap_block_rows(match_id: int, data: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten one match's four raw grids into auditable block-level rows.

    This is data preparation only. No season baseline, difference, ratio,
    percentile, label, or football interpretation is calculated here.
    """
    cell_width = PITCH_LENGTH / GRID_COLUMNS
    cell_height = PITCH_WIDTH / GRID_ROWS
    rows: list[dict[str, Any]] = []
    for row_index in range(GRID_ROWS):
        for column_index in range(GRID_COLUMNS):
            rows.append(
                {
                    "Match ID": int(match_id),
                    "Block": f"R{row_index + 1}C{column_index + 1}",
                    "Row": row_index,
                    "Column": column_index,
                    "X start (m)": round(column_index * cell_width, 3),
                    "X end (m)": round((column_index + 1) * cell_width, 3),
                    "Y start (m)": round(row_index * cell_height, 3),
                    "Y end (m)": round((row_index + 1) * cell_height, 3),
                    "Shots": int(round(data["shot_grid"][row_index][column_index])),
                    "xG": round(float(data["xg_grid"][row_index][column_index]), 6),
                    "Positive PxT actions": int(round(data["action_grid"][row_index][column_index])),
                    "Positive PxT": round(float(data["pxt_grid"][row_index][column_index]), 6),
                }
            )
    return rows


@st.cache_data(show_spinner=False)
def match_heatmap_source_rows(
    match_ids: tuple[int, ...],
    freiburg_id: int,
) -> list[dict[str, Any]]:
    """Return raw block rows for each match, ready for student analysis."""
    rows: list[dict[str, Any]] = []
    for match_id in match_ids:
        match_data = season_freiburg_heatmap_data((int(match_id),), int(freiburg_id))
        rows.extend(heatmap_block_rows(int(match_id), match_data))
    return rows


def heatmap_rows_csv(rows: list[dict[str, Any]]) -> str:
    """Serialize extracted block rows so they can be reviewed independently."""
    if not rows:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
