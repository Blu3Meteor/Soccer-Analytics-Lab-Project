# PROVENANCE: AI-ASSISTED — WEBSITE DESIGN / VISUALISATION
# This module renders Streamlit controls and SVG heatmaps. The extraction and
# mathematical transformation layers live in separate, explicitly marked files.

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from .season_heatmap_analysis import attacking_third_share, display_scale_maximum, smooth_grid
from .season_heatmap_data import GRID_COLUMNS, GRID_ROWS, PITCH_LENGTH, PITCH_WIDTH, season_freiburg_heatmap_data


def _cell_color(value: float, maximum: float, channel: str) -> str:
    if value <= 0 or maximum <= 0:
        return "rgba(255,255,255,0.015)"
    intensity = min(1.0, (value / maximum) ** 0.62)
    if channel == "xg":
        alpha = 0.12 + intensity * 0.84
        return f"rgba(255,82,82,{alpha:.2f})"
    alpha = 0.12 + intensity * 0.82
    return f"rgba(37,191,255,{alpha:.2f})"


def _legend(channel: str, unit: str) -> str:
    label = f"Smoothed {unit.lower()} intensity"
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


def _zone_name(row: int, column: int) -> str:
    third = ("Defensive third", "Middle third", "Attacking third")[min(2, column // 4)]
    lane = ("Left", "Left half-space", "Centre", "Right half-space", "Right")[min(4, int(row * 5 / GRID_ROWS))]
    return f"{third}, {lane.lower()}"


def _format_zone_value(value: float, unit: str) -> str:
    if unit in {"Shots", "Actions"}:
        return f"{int(round(value))} {unit.lower()}"
    return f"{value:.3f} {unit}"


def _zone_tooltip(
    raw_value: float,
    display_value: float,
    total: float,
    unit: str,
    row: int,
    column: int,
) -> str:
    cell_width = PITCH_LENGTH / GRID_COLUMNS
    cell_height = PITCH_WIDTH / GRID_ROWS
    x_start, x_end = column * cell_width, (column + 1) * cell_width
    y_start, y_end = row * cell_height, (row + 1) * cell_height
    share = raw_value / total if total else 0.0
    lines = [
        _zone_name(row, column),
        f"Block value: {_format_zone_value(raw_value, unit)}",
        f"Share of total: {share:.1%}",
        f"Pitch block: x {x_start:.1f}-{x_end:.1f}m, y {y_start:.1f}-{y_end:.1f}m",
    ]
    if unit in {"Shots", "Actions"}:
        lines.append(f"Smoothed display: {display_value:.1f}")
    else:
        lines.append(f"Smoothed display: {display_value:.3f} {unit}")
    return "\n".join(lines)


def _zone_tooltip_svg(
    raw_value: float,
    display_value: float,
    total: float,
    unit: str,
    row: int,
    column: int,
) -> str:
    cell_width = PITCH_LENGTH / GRID_COLUMNS
    cell_height = PITCH_WIDTH / GRID_ROWS
    x_start, x_end = column * cell_width, (column + 1) * cell_width
    y_start, y_end = row * cell_height, (row + 1) * cell_height
    share = raw_value / total if total else 0.0
    raw_label = _format_zone_value(raw_value, unit)
    display_label = f"{display_value:.1f}" if unit in {"Shots", "Actions"} else f"{display_value:.3f} {unit}"
    return (
        '<g class="heatmap-tooltip" aria-hidden="true">'
        '<rect x="17.5" y="2" width="70" height="17.5" rx="2" '
        'fill="rgba(15,23,42,0.96)" stroke="rgba(255,255,255,0.72)" stroke-width="0.35"/>'
        f'<text x="52.5" y="6.1" text-anchor="middle" fill="#ffffff" font-size="2.65" font-weight="700">'
        f'{escape(_zone_name(row, column))}</text>'
        f'<text x="52.5" y="9.7" text-anchor="middle" fill="#f8fafc" font-size="2.25">'
        f'Block: {escape(raw_label)} · {share:.1%} of total</text>'
        f'<text x="52.5" y="13.1" text-anchor="middle" fill="#cbd5e1" font-size="2.05">'
        f'x {x_start:.1f}-{x_end:.1f}m · y {y_start:.1f}-{y_end:.1f}m</text>'
        f'<text x="52.5" y="16.5" text-anchor="middle" fill="#cbd5e1" font-size="2.05">'
        f'Smoothed display: {escape(display_label)}</text>'
        '</g>'
    )


def _render_grid_svg(grid: list[list[float]], title: str, channel: str, unit: str) -> str:
    display_grid = smooth_grid(grid)
    maximum = display_scale_maximum(display_grid)
    total = sum(value for row in grid for value in row)
    cell_width = PITCH_LENGTH / GRID_COLUMNS
    cell_height = PITCH_WIDTH / GRID_ROWS
    cells = []
    hover_targets = []
    for row_index, row in enumerate(display_grid):
        for column_index, value in enumerate(row):
            raw_value = float(grid[row_index][column_index])
            tooltip = _zone_tooltip(raw_value, float(value), total, unit, row_index, column_index)
            cells.append(
                f'<rect x="{column_index * cell_width:.2f}" y="{row_index * cell_height:.2f}" '
                f'width="{cell_width:.2f}" height="{cell_height:.2f}" '
                f'fill="{_cell_color(float(value), maximum, channel)}" '
                'stroke="rgba(255,255,255,0.045)" stroke-width="0.12"/>'
            )
            hover_targets.append(
                '<g class="heatmap-hover-target">'
                f'<rect class="heatmap-zone" x="{column_index * cell_width:.2f}" y="{row_index * cell_height:.2f}" '
                f'width="{cell_width:.2f}" height="{cell_height:.2f}" fill="transparent" pointer-events="all" '
                f'tabindex="0" role="graphics-symbol" aria-label="{escape(tooltip)}">'
                f'<title>{escape(tooltip)}</title></rect>'
                f'{_zone_tooltip_svg(raw_value, float(value), total, unit, row_index, column_index)}'
                '</g>'
            )
    raw_maximum = max((value for row in grid for value in row), default=0.0)
    hot_row, hot_column = 0, 0
    if raw_maximum > 0:
        hot_row, hot_column = max(
            ((row_index, column_index) for row_index in range(GRID_ROWS) for column_index in range(GRID_COLUMNS)),
            key=lambda position: grid[position[0]][position[1]],
        )
    hot_x = (hot_column + 0.5) * cell_width
    hot_y = (hot_row + 0.5) * cell_height
    return (
        '<div class="season-heatmap">'
        f'<div class="season-heatmap-title">{escape(title)}</div>'
        '<svg viewBox="0 0 105 68" role="img" aria-label="Season heatmap">'
        '<rect x="0" y="0" width="105" height="68" rx="1.6" fill="#142820"/>'
        '<rect x="70" y="0" width="35" height="68" fill="rgba(255,255,255,0.025)"/>'
        f'{"".join(cells)}'
        '<rect x="0.8" y="0.8" width="103.4" height="66.4" fill="none" stroke="rgba(255,255,255,0.72)" stroke-width="0.55"/>'
        '<line x1="52.5" y1="0.8" x2="52.5" y2="67.2" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<circle cx="52.5" cy="34" r="9.15" fill="none" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<rect x="0.8" y="13.84" width="16.5" height="40.32" fill="none" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<rect x="87.7" y="13.84" width="16.5" height="40.32" fill="none" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        f'<circle cx="{hot_x:.2f}" cy="{hot_y:.2f}" r="1.4" fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="0.55">'
        f'<title>Strongest raw zone: {escape(_zone_name(hot_row, hot_column))}</title></circle>'
        '<path d="M43 63 L61 63" stroke="rgba(255,255,255,0.82)" stroke-width="0.65" marker-end="url(#sidebar-arrow)"/>'
        '<defs><marker id="sidebar-arrow" markerWidth="4" markerHeight="4" refX="3.6" refY="2" orient="auto">'
        '<path d="M0,0 L4,2 L0,4 Z" fill="rgba(255,255,255,0.82)"/></marker></defs>'
        f'{"".join(hover_targets)}'
        '</svg>'
        f'{_legend(channel, unit)}'
        '</div>'
    )


def render_season_heatmaps_page(summaries: list[dict[str, Any]], freiburg_id: int) -> None:
    match_ids = tuple(int(match["id"]) for match in summaries)
    data = season_freiburg_heatmap_data(match_ids, int(freiburg_id))
    match_count = max(1, int(data["matches"]))

    st.markdown('<div class="app-kicker">SC Freiburg · Bundesliga 2023/24</div>', unsafe_allow_html=True)
    st.title("Season heatmaps")
    st.caption(
        "Where Freiburg's shots started and where positive possession-threat actions ended. "
        "All matches in the supplied season dataset are shown from left to right."
    )

    with st.container(horizontal=True):
        st.metric("Total xG", f'{data["total_xg"]:.2f}', border=True)
        st.metric("xG per shot", f'{data["total_xg"] / max(1, data["shots"]):.3f}', border=True)
        st.metric("xG per match", f'{data["total_xg"] / match_count:.2f}', border=True)
        st.metric("Positive PxT", f'{data["total_pxt"]:.2f}', border=True)
        st.metric("PxT per match", f'{data["total_pxt"] / match_count:.2f}', border=True)

    view = st.segmented_control(
        "Heatmap measure",
        ["Value", "Volume"],
        default="Value",
        key="season_heatmap_measure",
        help="Value weights zones by xG or PxT. Volume counts shots or positive PxT actions.",
        width="stretch",
    )
    if view == "Volume":
        left_grid, right_grid = data["shot_grid"], data["action_grid"]
        left_title = f'{data["shots"]} shots · {attacking_third_share(left_grid):.0%} in the attacking third'
        right_title = f'{data["actions"]} positive actions · {attacking_third_share(right_grid):.0%} ended in the attacking third'
        left_unit, right_unit = "Shots", "Actions"
    else:
        left_grid, right_grid = data["xg_grid"], data["pxt_grid"]
        left_title = f'{data["total_xg"]:.2f} xG · {attacking_third_share(left_grid):.0%} in the attacking third'
        right_title = f'{data["total_pxt"]:.2f} positive PxT · {attacking_third_share(right_grid):.0%} ended in the attacking third'
        left_unit, right_unit = "xG", "PxT"

    columns = st.columns(2)
    with columns[0]:
        with st.container(border=True):
            st.subheader("Shot locations")
            st.markdown(_render_grid_svg(left_grid, left_title, "xg", left_unit), unsafe_allow_html=True)
    with columns[1]:
        with st.container(border=True):
            st.subheader("Positive PxT destinations")
            st.markdown(_render_grid_svg(right_grid, right_title, "pxt", right_unit), unsafe_allow_html=True)

    st.caption(
        "The outlined dot marks the strongest unsmoothed zone. Hover or keyboard-focus any block for its exact "
        "raw value, total share, pitch coordinates, and smoothed display value."
    )
    with st.expander("How to read these heatmaps", icon=":material/info:"):
        st.markdown(
            "**Value** answers *where did Freiburg generate quality?* by weighting every shot by xG "
            "and every positive threat action by PxT. **Volume** answers *where did actions happen?* "
            "by counting events. A light 3×3 smoothing kernel makes broader spatial patterns easier to see; "
            "the totals above remain calculated from the unsmoothed event values. Only positive PxT is included."
        )
