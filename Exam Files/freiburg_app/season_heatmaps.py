from __future__ import annotations

from collections import defaultdict
from html import escape
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
    return min(upper, max(lower, value))


def _event_xy(event: dict[str, Any], key: str) -> tuple[float, float] | None:
    point = event.get(key) or {}
    coords = point.get("adjCoordinates") or point.get("coordinates")
    if not coords:
        return None
    x = _clip(float(coords.get("x", 0.0)) + PITCH_LENGTH / 2, 0.0, PITCH_LENGTH)
    y = _clip(PITCH_WIDTH / 2 - float(coords.get("y", 0.0)), 0.0, PITCH_WIDTH)
    return x, y


def _event_kpi_totals(events_kpis: list[dict[str, Any]]) -> tuple[dict[int, float], dict[int, float]]:
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


def _empty_grid() -> list[list[float]]:
    return [[0.0 for _column in range(GRID_COLUMNS)] for _row in range(GRID_ROWS)]


def _add_to_grid(grid: list[list[float]], x: float, y: float, value: float) -> None:
    column = min(GRID_COLUMNS - 1, max(0, int((x / PITCH_LENGTH) * GRID_COLUMNS)))
    row = min(GRID_ROWS - 1, max(0, int((y / PITCH_WIDTH) * GRID_ROWS)))
    grid[row][column] += value


@st.cache_data(show_spinner=False)
def season_freiburg_heatmap_data(
    match_ids: tuple[int, ...],
    freiburg_id: int,
) -> dict[str, Any]:
    xg_grid = _empty_grid()
    pxt_grid = _empty_grid()
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
            if action_type in {"SHOT", "GOAL"}:
                xy = _event_xy(event, "start")
                if xy:
                    value = max(0.0, xg_by_event.get(event_id, 0.0))
                    _add_to_grid(xg_grid, xy[0], xy[1], value)
                    total_xg += value
                    shot_count += 1
            pxt_value = max(0.0, pxt_by_event.get(event_id, 0.0))
            if pxt_value > 0:
                xy = _event_xy(event, "end") or _event_xy(event, "start")
                if xy:
                    _add_to_grid(pxt_grid, xy[0], xy[1], pxt_value)
                    total_pxt += pxt_value
                    action_count += 1

    return {
        "xg_grid": xg_grid,
        "pxt_grid": pxt_grid,
        "shots": shot_count,
        "actions": action_count,
        "total_xg": round(total_xg, 2),
        "total_pxt": round(total_pxt, 2),
    }


def _cell_color(value: float, maximum: float, channel: str) -> str:
    if value <= 0 or maximum <= 0:
        return "rgba(255,255,255,0.03)"
    intensity = min(1.0, value / maximum)
    if channel == "xg":
        alpha = 0.18 + intensity * 0.72
        return f"rgba(199,21,42,{alpha:.2f})"
    alpha = 0.16 + intensity * 0.7
    return f"rgba(31,77,120,{alpha:.2f})"


def _legend(channel: str) -> str:
    label = "xG in zone" if channel == "xg" else "Positive PxT ending zone"
    low = _cell_color(0.25, 1.0, channel)
    mid = _cell_color(0.6, 1.0, channel)
    high = _cell_color(1.0, 1.0, channel)
    return (
        '<div class="heatmap-legend">'
        f'<span>{escape(label)}</span>'
        '<div class="heatmap-scale">'
        f'<i style="background:{low}"></i>'
        f'<i style="background:{mid}"></i>'
        f'<i style="background:{high}"></i>'
        '</div>'
        '<div class="heatmap-scale-labels"><span>Low</span><span>High</span></div>'
        '</div>'
    )


def _render_grid_svg(grid: list[list[float]], title: str, channel: str) -> str:
    maximum = max((value for row in grid for value in row), default=0.0)
    cell_width = PITCH_LENGTH / GRID_COLUMNS
    cell_height = PITCH_WIDTH / GRID_ROWS
    cells = []
    for row_index, row in enumerate(grid):
        for column_index, value in enumerate(row):
            cells.append(
                f'<rect x="{column_index * cell_width:.2f}" y="{row_index * cell_height:.2f}" '
                f'width="{cell_width:.2f}" height="{cell_height:.2f}" '
                f'fill="{_cell_color(float(value), maximum, channel)}" '
                'stroke="rgba(255,255,255,0.16)" stroke-width="0.18"/>'
            )
    return (
        '<div class="season-heatmap">'
        f'<div class="season-heatmap-title">{escape(title)}</div>'
        '<svg viewBox="0 0 105 68" role="img" aria-label="Season heatmap">'
        '<rect x="0" y="0" width="105" height="68" rx="1.6" fill="#2f8f53"/>'
        f'{"".join(cells)}'
        '<rect x="0.8" y="0.8" width="103.4" height="66.4" fill="none" stroke="rgba(255,255,255,0.72)" stroke-width="0.55"/>'
        '<line x1="52.5" y1="0.8" x2="52.5" y2="67.2" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<circle cx="52.5" cy="34" r="9.15" fill="none" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<rect x="0.8" y="13.84" width="16.5" height="40.32" fill="none" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<rect x="87.7" y="13.84" width="16.5" height="40.32" fill="none" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<path d="M43 63 L61 63" stroke="rgba(255,255,255,0.82)" stroke-width="0.65" marker-end="url(#sidebar-arrow)"/>'
        '<defs><marker id="sidebar-arrow" markerWidth="4" markerHeight="4" refX="3.6" refY="2" orient="auto">'
        '<path d="M0,0 L4,2 L0,4 Z" fill="rgba(255,255,255,0.82)"/></marker></defs>'
        '</svg>'
        f'{_legend(channel)}'
        '</div>'
    )


def render_home_season_heatmaps(summaries: list[dict[str, Any]], freiburg_id: int) -> None:
    match_ids = tuple(int(match["id"]) for match in summaries)
    data = season_freiburg_heatmap_data(match_ids, int(freiburg_id))
    st.markdown('<div class="season-heatmap-shell">', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">Season Shot and PxT Heatmaps</div>', unsafe_allow_html=True)
    columns = st.columns(2)
    with columns[0]:
        st.markdown(
            _render_grid_svg(data["xg_grid"], f'xG shots | {data["shots"]} shots | {data["total_xg"]} xG', "xg"),
            unsafe_allow_html=True,
        )
    with columns[1]:
        st.markdown(
            _render_grid_svg(data["pxt_grid"], f'PxT actions | {data["actions"]} actions | {data["total_pxt"]} PxT', "pxt"),
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
