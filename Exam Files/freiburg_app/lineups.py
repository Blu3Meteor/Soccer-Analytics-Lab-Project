from collections import defaultdict
from html import escape
from typing import Any

import streamlit as st

from .config import FREIBURG_NAME
from .data import format_position, minute_label, player_name, short_player_name


PlayerRankLookup = dict[tuple[int, int], dict[str, Any]]


# UI Assistance
def _player_rank(
    lineup: dict[str, Any],
    player_id: int,
    player_ranks: PlayerRankLookup | None,
) -> dict[str, Any] | None:
    if not player_ranks:
        return None
    return player_ranks.get((int(lineup.get("id", -1)), int(player_id)))


def _rank_label(rank_data: dict[str, Any] | None, detailed: bool = False) -> str:
    if not rank_data or rank_data.get("rank") is None:
        return "NR"
    if detailed:
        return f'{int(rank_data["rank"])} / {int(rank_data["total"])}'
    return f'#{int(rank_data["rank"])}'


def _rank_tooltip(rank_data: dict[str, Any] | None) -> str:
    if not rank_data:
        return "No season ranking data"
    position = str(rank_data["position_group"])
    minutes = float(rank_data["minutes"])
    if rank_data.get("rank") is None:
        return (
            f"Not ranked · {minutes:.0f} minutes · "
            f"{int(rank_data['minimum_minutes'])}-minute minimum"
        )
    return (
        f'{position} rank {int(rank_data["rank"])} of {int(rank_data["total"])} · '
        f'{float(rank_data["mean_percentile"]):.1f} mean percentile · {minutes:.0f} minutes'
    )


def _metric_value_label(metric: dict[str, Any]) -> str:
    value = float(metric["value"])
    if metric.get("is_rate"):
        return f"{value:.1f}%"
    return f"{value:.2f} /90"


def _percentile_label(value: float) -> str:
    percentile = int(round(value))
    if 10 <= percentile % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(percentile % 10, "th")
    return f"{percentile}{suffix} pct"


def _player_tooltip_html(
    full_name: str,
    position: str,
    rank_data: dict[str, Any] | None,
) -> str:
    if not rank_data:
        return (
            '<div class="player-tooltip" role="tooltip">'
            f'<strong>{escape(full_name)}</strong>'
            f'<span>{escape(position)}</span>'
            '<div class="player-tooltip-empty">Season ranking data unavailable</div>'
            "</div>"
        )

    minutes = float(rank_data["minutes"])
    matches = int(rank_data.get("matches", 0))
    if rank_data.get("rank") is None:
        ranking = (
            '<span class="player-tooltip-rank">Not ranked</span>'
            f'<span>{minutes:.0f} min · {matches} apps</span>'
            '<div class="player-tooltip-empty">'
            f'{int(rank_data["minimum_minutes"])} minutes required for a ranking'
            "</div>"
        )
    else:
        ranking = (
            '<span class="player-tooltip-rank">'
            f'{escape(str(rank_data["position_group"]))} #{int(rank_data["rank"])} '
            f'of {int(rank_data["total"])}'
            "</span>"
            f'<span>{float(rank_data["mean_percentile"]):.1f} overall percentile · '
            f"{minutes:.0f} min · {matches} apps</span>"
        )

    metric_rows = []
    for metric in rank_data.get("top_metrics", []):
        metric_rows.append(
            '<div class="player-tooltip-stat">'
            f'<span>{escape(str(metric["label"]))}</span>'
            f'<strong>{escape(_metric_value_label(metric))}</strong>'
            f'<em>{_percentile_label(float(metric["percentile"]))}</em>'
            "</div>"
        )
    metrics = ""
    if metric_rows:
        metrics = (
            '<div class="player-tooltip-subhead">Top attributes</div>'
            f'<div class="player-tooltip-stats">{"".join(metric_rows)}</div>'
        )

    return (
        '<div class="player-tooltip" role="tooltip">'
        f'<strong>{escape(full_name)}</strong>'
        f'<span>{escape(position)}</span>'
        f"{ranking}{metrics}"
        "</div>"
    )


# Data Processing Assistance
def lineup_for_team(lineups: dict[str, Any], team_id: int) -> dict[str, Any]:
    for key in ("squadHome", "squadAway"):
        squad = lineups.get(key, {})
        if int(squad.get("id", -1)) == int(team_id):
            return squad
    return {}


def lineup_rows(
    lineup: dict[str, Any],
    players: dict[int, dict[str, Any]],
    player_ranks: PlayerRankLookup | None = None,
) -> list[dict[str, Any]]:
    shirts = {int(player["id"]): player.get("shirtNumber") for player in lineup.get("players", [])}
    rows = []
    for position in lineup.get("startingPositions", []):
        player_id = int(position["playerId"])
        rows.append(
            {
                "#": shirts.get(player_id, ""),
                "Player": player_name(player_id, players),
                "Position rank": _rank_label(_player_rank(lineup, player_id, player_ranks), detailed=True),
                "Position": format_position(position.get("position")),
                "Side": format_position(position.get("positionSide")),
            }
        )
    return rows


def shirt_numbers(lineup: dict[str, Any]) -> dict[int, Any]:
    return {int(player["id"]): player.get("shirtNumber") for player in lineup.get("players", [])}


# UI Assistance
def position_depth(position: str | None) -> float:
    position = position or ""
    if position == "GOALKEEPER":
        return 90
    if "WINGBACK_DEFENDER" in position:
        return 66
    if "DEFENDER" in position or "FULLBACK" in position:
        return 74
    if position == "DEFENSE_MIDFIELD":
        return 58
    if "MIDFIELD" in position:
        return 45
    if "WINGER" in position:
        return 30
    if "FORWARD" in position or "STRIKER" in position:
        return 17
    return 50


def position_width(position_side: str | None) -> float:
    position_side = position_side or ""
    side_map = {
        "LEFT": 18,
        "CENTRE_LEFT": 38,
        "CENTER_LEFT": 38,
        "CENTRE": 50,
        "CENTER": 50,
        "CENTRE_RIGHT": 62,
        "CENTER_RIGHT": 62,
        "RIGHT": 82,
    }
    return side_map.get(position_side, 50)


def marker_color(title: str) -> str:
    return "#c7152a" if title == FREIBURG_NAME else "#1f4d78"


def lineup_marker_positions(lineup: dict[str, Any]) -> list[dict[str, Any]]:
    base_markers = []
    for position in lineup.get("startingPositions", []):
        base_markers.append(
            {
                "player_id": int(position["playerId"]),
                "x": position_width(position.get("positionSide")),
                "y": position_depth(position.get("position")),
                "position": position.get("position"),
                "side": position.get("positionSide"),
            }
        )

    grouped: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for marker in base_markers:
        grouped[(round(marker["x"]), round(marker["y"]))].append(marker)

    for group in grouped.values():
        if len(group) == 1:
            continue
        total = len(group)
        for index, marker in enumerate(group):
            offset = index - (total - 1) / 2
            marker["x"] = min(92, max(8, marker["x"] + offset * 8))

    return base_markers


def render_lineup_pitch(
    title: str,
    lineup: dict[str, Any],
    players: dict[int, dict[str, Any]],
    player_ranks: PlayerRankLookup | None = None,
) -> None:
    shirts = shirt_numbers(lineup)
    markers = []
    color = marker_color(title)
    for marker in lineup_marker_positions(lineup):
        player_id = marker["player_id"]
        shirt = shirts.get(player_id, "")
        full_name = player_name(player_id, players)
        short_name = short_player_name(player_id, players)
        rank_data = _player_rank(lineup, player_id, player_ranks)
        rank_label = _rank_label(rank_data)
        position = format_position(marker["position"])
        tooltip = _player_tooltip_html(full_name, position, rank_data)
        tooltip_vertical = " tooltip-below" if marker["y"] < 35 else ""
        if marker["x"] < 30:
            tooltip_horizontal = " tooltip-align-left"
        elif marker["x"] > 70:
            tooltip_horizontal = " tooltip-align-right"
        else:
            tooltip_horizontal = ""
        markers.append(
            f'<div class="player-marker{tooltip_vertical}{tooltip_horizontal}" '
            f'style="left: {marker["x"]:.1f}%; top: {marker["y"]:.1f}%;" '
            f'tabindex="0" aria-label="{escape(_rank_tooltip(rank_data))}">'
            f'<div class="player-shirt" style="background: {color};">{escape(str(shirt))}</div>'
            '<div class="player-label-row">'
            f'<div class="player-name">{escape(short_name)}</div>'
            f'<span class="player-rank">{escape(rank_label)}</span>'
            '</div>'
            f"{tooltip}"
            '</div>'
        )

    st.markdown(
        '<div class="lineup-pitch">'
        '<div class="pitch-center-circle"></div>'
        f'{"".join(markers)}'
        '</div>',
        unsafe_allow_html=True,
    )


# Data Processing Assistance
def bench_rows(
    lineup: dict[str, Any],
    players: dict[int, dict[str, Any]],
    player_ranks: PlayerRankLookup | None = None,
) -> list[dict[str, Any]]:
    starter_ids = {int(position["playerId"]) for position in lineup.get("startingPositions", [])}
    rows = []
    for player in lineup.get("players", []):
        player_id = int(player["id"])
        if player_id in starter_ids:
            continue
        rows.append(
            {
                "#": player.get("shirtNumber", ""),
                "Player": player_name(player_id, players),
                "Position rank": _rank_label(_player_rank(lineup, player_id, player_ranks), detailed=True),
            }
        )
    return rows


# Data Processing Assistance
def formation_rows(lineup: dict[str, Any]) -> list[dict[str, str]]:
    history = sorted(
        lineup.get("formations", []),
        key=lambda change: float(change.get("gameTimeInSec") or 0.0),
    )
    return [
        {
            "Time": minute_label(change.get("gameTime")),
            "Formation": str(change.get("formation") or "Unknown"),
        }
        for change in history
    ]


def lineup_change_rows(
    lineup: dict[str, Any],
    players: dict[int, dict[str, Any]],
    player_ranks: PlayerRankLookup | None = None,
) -> list[dict[str, Any]]:
    rows = []
    for change in lineup.get("substitutions", []):
        from_position = change.get("fromPosition")
        to_position = change.get("toPosition")
        if from_position == "BANK":
            movement = "↑ In"
            movement_class = "sub-in"
        elif to_position == "BANK":
            movement = "↓ Out"
            movement_class = "sub-out"
        else:
            movement = "↔ Moved"
            movement_class = "sub-moved"
        rows.append(
            {
                "Time": minute_label(change.get("gameTime")),
                "Player": player_name(int(change["playerId"]), players),
                "Position rank": _rank_label(
                    _player_rank(lineup, int(change["playerId"]), player_ranks),
                    detailed=True,
                ),
                "Move": movement,
                "_class": movement_class,
                "From position": format_position(from_position),
                "From side": format_position(change.get("fromPositionSide")),
                "To position": format_position(to_position),
                "To side": format_position(change.get("positionSide")),
            }
        )
    return rows


# UI Assistance
def render_lineup_change_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        movement_class = row.get("_class", "sub-moved")
        body.append(
            "<tr>"
            f"<td>{escape(str(row.get('Time', '')))}</td>"
            f"<td>{escape(str(row.get('Player', '')))}</td>"
            f"<td>{escape(str(row.get('Position rank', '')))}</td>"
            f'<td><span class="sub-move {movement_class}">{escape(str(row.get("Move", "")))}</span></td>'
            f"<td>{escape(str(row.get('From position', '')))}</td>"
            f"<td>{escape(str(row.get('From side', '')))}</td>"
            f"<td>{escape(str(row.get('To position', '')))}</td>"
            f"<td>{escape(str(row.get('To side', '')))}</td>"
            "</tr>"
        )
    return (
        '<table class="sub-table">'
        "<thead><tr><th>Time</th><th>Player</th><th>Position rank</th><th>Move</th>"
        "<th>From position</th><th>From side</th><th>To position</th><th>To side</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody>"
        "</table>"
    )


def render_lineup_panel(
    title: str,
    lineup: dict[str, Any],
    players: dict[int, dict[str, Any]],
    player_ranks: PlayerRankLookup | None = None,
) -> None:
    formation = lineup.get("startingFormation", "Unknown")
    st.markdown(f"**{title} · {formation}**")
    render_lineup_pitch(title, lineup, players, player_ranks)
    st.markdown(
        '<div class="lineup-note">Hover or focus a player for season details · '
        'Badge shows league-wide position-group rank · NR means below 450 minutes.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Starting XI", expanded=False):
        st.dataframe(lineup_rows(lineup, players, player_ranks), hide_index=True, width="stretch")
    with st.expander("Bench", expanded=False):
        st.dataframe(bench_rows(lineup, players, player_ranks), hide_index=True, width="stretch")
    with st.expander("Formation changes", expanded=False):
        rows = formation_rows(lineup)
        if rows:
            st.dataframe(rows, hide_index=True, width="stretch")
        else:
            st.caption("No formation history listed.")
    with st.expander("Lineup changes", expanded=False):
        rows = lineup_change_rows(lineup, players, player_ranks)
        if rows:
            st.markdown(render_lineup_change_table(rows), unsafe_allow_html=True)
        else:
            st.caption("No lineup changes listed.")
