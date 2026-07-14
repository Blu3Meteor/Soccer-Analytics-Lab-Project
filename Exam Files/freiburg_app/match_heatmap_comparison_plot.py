# PROVENANCE: AI-ASSISTED — DATA VISUALISATION / SVG PLOT
# This plot was generated with LLM assistance and is not human-authored.

from __future__ import annotations

from html import escape
from typing import Any

from .match_heatmap_comparison import comparison_summary
from .season_heatmap_data import GRID_COLUMNS, GRID_ROWS, PITCH_LENGTH, PITCH_WIDTH


def _format_value(value: float, metric: str, signed: bool = False) -> str:
    sign = "+" if signed and value > 0 else ""
    if metric in {"Shots", "Positive PxT actions"}:
        return f"{sign}{value:.2f}"
    return f"{sign}{value:.3f}"


def _difference_color(value: float, maximum: float) -> str:
    """Map negative differences to blue and positive differences to red."""
    if maximum <= 0 or abs(value) < 1e-12:
        return "rgba(255,255,255,0.035)"
    intensity = min(1.0, abs(value) / maximum)
    alpha = 0.12 + intensity * 0.80
    if value > 0:
        return f"rgba(239,68,68,{alpha:.3f})"
    return f"rgba(56,139,253,{alpha:.3f})"


def _tooltip_svg(row: dict[str, Any], metric: str) -> str:
    selected = float(row["Selected match"])
    normal = float(row["Other-match average"])
    difference = float(row["Difference"])
    return (
        '<g class="heatmap-tooltip" aria-hidden="true">'
        '<rect x="15" y="2" width="75" height="17.5" rx="2" '
        'fill="rgba(15,23,42,0.97)" stroke="rgba(255,255,255,0.72)" stroke-width="0.35"/>'
        f'<text x="52.5" y="6.0" text-anchor="middle" fill="#ffffff" font-size="2.55" font-weight="700">'
        f'{escape(str(row["Block"]))} · {escape(metric)}</text>'
        f'<text x="52.5" y="9.6" text-anchor="middle" fill="#f8fafc" font-size="2.15">'
        f'Match: {_format_value(selected, metric)} · Normal: {_format_value(normal, metric)}</text>'
        f'<text x="52.5" y="13.0" text-anchor="middle" fill="#f8fafc" font-size="2.15">'
        f'Difference: {_format_value(difference, metric, signed=True)}</text>'
        f'<text x="52.5" y="16.4" text-anchor="middle" fill="#cbd5e1" font-size="2.0">'
        f'x {float(row["X start (m)"]):.1f}-{float(row["X end (m)"]):.1f}m · '
        f'y {float(row["Y start (m)"]):.1f}-{float(row["Y end (m)"]):.1f}m</text>'
        '</g>'
    )


def render_match_comparison_svg(
    comparison_rows: list[dict[str, Any]],
    metric: str,
    title: str,
) -> str:
    """Render raw block differences on a left-to-right football pitch."""
    maximum = max((abs(float(row["Difference"])) for row in comparison_rows), default=0.0)
    cell_width = PITCH_LENGTH / GRID_COLUMNS
    cell_height = PITCH_WIDTH / GRID_ROWS
    cells: list[str] = []
    hover_targets: list[str] = []

    for row in comparison_rows:
        x = int(row["Column"]) * cell_width
        y = int(row["Row"]) * cell_height
        difference = float(row["Difference"])
        aria = (
            f'{row["Block"]}, {metric}; selected {_format_value(float(row["Selected match"]), metric)}; '
            f'normal {_format_value(float(row["Other-match average"]), metric)}; '
            f'difference {_format_value(difference, metric, signed=True)}'
        )
        cells.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_width:.2f}" height="{cell_height:.2f}" '
            f'fill="{_difference_color(difference, maximum)}" '
            'stroke="rgba(255,255,255,0.06)" stroke-width="0.12"/>'
        )
        hover_targets.append(
            '<g class="heatmap-hover-target">'
            f'<rect class="heatmap-zone" x="{x:.2f}" y="{y:.2f}" width="{cell_width:.2f}" '
            f'height="{cell_height:.2f}" fill="transparent" pointer-events="all" tabindex="0" '
            f'role="graphics-symbol" aria-label="{escape(aria)}"><title>{escape(aria)}</title></rect>'
            f'{_tooltip_svg(row, metric)}'
            '</g>'
        )

    summary = comparison_summary(comparison_rows)
    summary_text = (
        f'Match {_format_value(summary["selected_total"], metric)} · '
        f'Other-match average {_format_value(summary["normal_total"], metric)} · '
        f'Difference {_format_value(summary["difference"], metric, signed=True)}'
    )
    return (
        '<div class="season-heatmap">'
        f'<div class="season-heatmap-title">{escape(title)}<br>{escape(summary_text)}</div>'
        '<svg viewBox="0 0 105 68" role="img" aria-label="Match versus normal heatmap">'
        '<rect x="0" y="0" width="105" height="68" rx="1.6" fill="#142820"/>'
        f'{"".join(cells)}'
        '<rect x="0.8" y="0.8" width="103.4" height="66.4" fill="none" stroke="rgba(255,255,255,0.72)" stroke-width="0.55"/>'
        '<line x1="52.5" y1="0.8" x2="52.5" y2="67.2" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<circle cx="52.5" cy="34" r="9.15" fill="none" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<rect x="0.8" y="13.84" width="16.5" height="40.32" fill="none" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<rect x="87.7" y="13.84" width="16.5" height="40.32" fill="none" stroke="rgba(255,255,255,0.52)" stroke-width="0.38"/>'
        '<path d="M43 63 L61 63" stroke="rgba(255,255,255,0.82)" stroke-width="0.65" marker-end="url(#match-comparison-arrow)"/>'
        '<defs><marker id="match-comparison-arrow" markerWidth="4" markerHeight="4" refX="3.6" refY="2" orient="auto">'
        '<path d="M0,0 L4,2 L0,4 Z" fill="rgba(255,255,255,0.82)"/></marker></defs>'
        f'{"".join(hover_targets)}'
        '</svg>'
        '<div class="comparison-legend">'
        '<span>Below normal</span><i class="comparison-negative"></i><i class="comparison-neutral"></i>'
        '<i class="comparison-positive"></i><span>Above normal</span>'
        '</div>'
        '</div>'
    )
