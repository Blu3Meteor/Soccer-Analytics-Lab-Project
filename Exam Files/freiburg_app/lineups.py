from __future__ import annotations

from collections import defaultdict
from html import escape
from typing import Any

import streamlit as st

from .config import FREIBURG_NAME
from .data import format_position, minute_label, player_name


def lineup_for_team(lineups: dict[str, Any], team_id: int) -> dict[str, Any]:
    for key in ("squadHome", "squadAway"):
        squad = lineups.get(key, {})
        if int(squad.get("id", -1)) == int(team_id):
            return squad
    return {}


def lineup_rows(
    lineup: dict[str, Any],
    players: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    shirts = {int(player["id"]): player.get("shirtNumber") for player in lineup.get("players", [])}
    rows = []
    for position in lineup.get("startingPositions", []):
        player_id = int(position["playerId"])
        rows.append(
            {
                "#": shirts.get(player_id, ""),
                "Player": player_name(player_id, players),
                "Position": format_position(position.get("position")),
                "Side": format_position(position.get("positionSide")),
            }
        )
    return rows


def shirt_numbers(lineup: dict[str, Any]) -> dict[int, Any]:
    return {int(player["id"]): player.get("shirtNumber") for player in lineup.get("players", [])}


def player_display_name(player_id: int, players: dict[int, dict[str, Any]]) -> str:
    name = player_name(player_id, players)
    if len(name) <= 13:
        return name
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name[:12]


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
) -> None:
    shirts = shirt_numbers(lineup)
    markers = []
    color = marker_color(title)
    for marker in lineup_marker_positions(lineup):
        player_id = marker["player_id"]
        shirt = shirts.get(player_id, "")
        full_name = player_name(player_id, players)
        short_name = player_display_name(player_id, players)
        markers.append(
            f'<div class="player-marker" style="left: {marker["x"]:.1f}%; top: {marker["y"]:.1f}%;" '
            f'title="{escape(full_name)} · {escape(format_position(marker["position"]))}">'
            f'<div class="player-shirt" style="background: {color};">{escape(str(shirt))}</div>'
            f'<div class="player-name">{escape(short_name)}</div>'
            '</div>'
        )

    st.markdown(
        '<div class="lineup-pitch">'
        '<div class="pitch-center-circle"></div>'
        f'{"".join(markers)}'
        '</div>',
        unsafe_allow_html=True,
    )


def bench_rows(lineup: dict[str, Any], players: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    starter_ids = {int(position["playerId"]) for position in lineup.get("startingPositions", [])}
    rows = []
    for player in lineup.get("players", []):
        player_id = int(player["id"])
        if player_id in starter_ids:
            continue
        rows.append({"#": player.get("shirtNumber", ""), "Player": player_name(player_id, players)})
    return rows


def substitution_rows(lineup: dict[str, Any], players: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for sub in lineup.get("substitutions", []):
        from_position = sub.get("fromPosition")
        to_position = sub.get("toPosition")
        if from_position == "BANK":
            movement = "On"
        elif to_position == "BANK":
            movement = "Off"
        else:
            movement = "Moved"
        rows.append(
            {
                "Time": minute_label(sub.get("gameTime")),
                "Player": player_name(int(sub["playerId"]), players),
                "Move": movement,
                "From": format_position(from_position),
                "To": format_position(to_position),
            }
        )
    return rows


def render_lineup_panel(
    title: str,
    lineup: dict[str, Any],
    players: dict[int, dict[str, Any]],
) -> None:
    formation = lineup.get("startingFormation", "Unknown")
    st.markdown(f"**{title} · {formation}**")
    render_lineup_pitch(title, lineup, players)
    st.markdown('<div class="lineup-note">Starters shown by shirt number and role.</div>', unsafe_allow_html=True)
    with st.expander("Starting XI", expanded=False):
        st.dataframe(lineup_rows(lineup, players), hide_index=True, width="stretch")
    with st.expander("Bench", expanded=False):
        st.dataframe(bench_rows(lineup, players), hide_index=True, width="stretch")
    with st.expander("Substitutions", expanded=False):
        rows = substitution_rows(lineup, players)
        if rows:
            st.dataframe(rows, hide_index=True, width="stretch")
        else:
            st.caption("No substitutions listed.")
