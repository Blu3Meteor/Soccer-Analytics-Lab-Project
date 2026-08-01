from collections import defaultdict
from typing import Any

import pandas as pd
import streamlit as st

from .config import KPI_SHOT_XG, TAGGED_ACTION_PXT_KPIS
from .data import load_match_events, load_match_events_kpis
from .event_utils import PITCH_LENGTH, PITCH_WIDTH, event_xy


GRID_COLUMNS = 12
GRID_ROWS = 8
# Data Processing Assistance
def _event_kpi_totals(events_kpis: list[dict[str, Any]]) -> tuple[dict[int, float], dict[int, float]]:
    """Index shot xG and the seven tagged-action PxT sources by event ID."""
    xg_by_event: dict[int, float] = defaultdict(float)
    pxt_by_event: dict[int, float] = defaultdict(float)
    for item in events_kpis:
        event_id = int(item["eventId"])
        kpi_id = int(item.get("kpiId", -1))
        value = float(item.get("value") or 0.0)
        if kpi_id == KPI_SHOT_XG:
            xg_by_event[event_id] += value
        elif kpi_id in TAGGED_ACTION_PXT_KPIS:
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
def team_heatmap_data(
    match_ids: tuple[int, ...],
    team_id: int,
) -> dict[str, Any]:
    """Extract shot/xG and positive tagged-action PxT grids for one team."""
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
            if int(event.get("squadId") or -1) != int(team_id):
                continue
            event_id = int(event["id"])
            action_type = event.get("actionType")

            # A shot contributes once to the volume grid and contributes its xG
            # value to the quality grid at the event's starting coordinate.
            if action_type in {"SHOT", "GOAL"}:
                xy = event_xy(event, "start")
                if xy:
                    value = max(0.0, xg_by_event.get(event_id, 0.0))
                    _add_to_grid(xg_grid, xy[0], xy[1], value)
                    _add_to_grid(shot_grid, xy[0], xy[1], 1.0)
                    total_xg += value
                    shot_count += 1

            # Destination placement is a project visualisation choice. These
            # values cover the seven tagged-player action sources, not total PxT.
            pxt_value = max(0.0, pxt_by_event.get(event_id, 0.0))
            if pxt_value > 0:
                xy = event_xy(event, "end") or event_xy(event, "start")
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


def season_freiburg_heatmap_data(
    match_ids: tuple[int, ...],
    freiburg_id: int,
) -> dict[str, Any]:
    """Backward-compatible Freiburg-specific wrapper used by season views."""
    return team_heatmap_data(match_ids, freiburg_id)


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
                    "Positive action PxT events": int(round(data["action_grid"][row_index][column_index])),
                    "Positive action PxT": round(float(data["pxt_grid"][row_index][column_index]), 6),
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


@st.cache_data(show_spinner=False)
def opponent_match_heatmap_source_rows(
    match_opponent_ids: tuple[tuple[int, int], ...],
) -> list[dict[str, Any]]:
    """Return raw block rows for the opponent Freiburg faced in each match."""
    rows: list[dict[str, Any]] = []
    for match_id, opponent_id in match_opponent_ids:
        match_data = team_heatmap_data((int(match_id),), int(opponent_id))
        rows.extend(heatmap_block_rows(int(match_id), match_data))
    return rows


def heatmap_rows_csv(rows: list[dict[str, Any]]) -> str:
    """Serialize extracted block rows so they can be reviewed independently."""
    return pd.DataFrame(rows).to_csv(index=False) if rows else ""
