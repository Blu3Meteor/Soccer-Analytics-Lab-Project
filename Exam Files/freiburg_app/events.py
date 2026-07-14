# PROVENANCE: AI-ASSISTED — EVENT DATA EXTRACTION / TABLE PREPARATION

from __future__ import annotations

from typing import Any

from .data import format_position, minute_label, player_name, short_team_name, team_name


def scoring_events(
    events: list[dict[str, Any]],
    match: dict[str, Any],
    players: dict[int, dict[str, Any]],
    squads: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    home_id = int(match["homeSquadId"])
    away_id = int(match["awaySquadId"])
    rows = []
    for event in events:
        action_type = event.get("actionType")
        if action_type not in {"GOAL", "OWN_GOAL"}:
            continue
        squad_id_raw = event.get("squadId")
        if squad_id_raw is None:
            continue
        squad_id = int(squad_id_raw)
        if action_type == "OWN_GOAL":
            scoring_team = away_id if squad_id == home_id else home_id
            note = f"Own goal by {player_name((event.get('player') or {}).get('id'), players)}"
        else:
            scoring_team = squad_id
            note = player_name((event.get("player") or {}).get("id"), players)
        rows.append(
            {
                "Time": minute_label(event.get("gameTime")),
                "Team": short_team_name(team_name(scoring_team, squads)),
                "Scorer": note,
                "Type": "Own Goal" if action_type == "OWN_GOAL" else "Goal",
            }
        )
    return rows


def card_events(
    events: list[dict[str, Any]],
    players: dict[int, dict[str, Any]],
    squads: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    card_types = {"YELLOW_CARD", "SECOND_YELLOW_CARD", "RED_CARD"}
    for event in events:
        if event.get("actionType") not in card_types:
            continue
        squad_id = event.get("squadId")
        rows.append(
            {
                "Time": minute_label(event.get("gameTime")),
                "Team": short_team_name(team_name(int(squad_id), squads)) if squad_id is not None else "",
                "Player": player_name((event.get("player") or {}).get("id"), players),
                "Card": format_position(event.get("actionType")),
            }
        )
    return rows


def shot_events(
    events: list[dict[str, Any]],
    players: dict[int, dict[str, Any]],
    squads: dict[int, dict[str, Any]],
    xg_by_event: dict[int, float] | None = None,
) -> list[dict[str, Any]]:
    rows = []
    for event in events:
        if event.get("actionType") != "SHOT":
            continue
        player_id = (event.get("player") or {}).get("id")
        squad_id = event.get("squadId")
        event_id = event.get("id")
        xg_value = xg_by_event.get(int(event_id)) if xg_by_event and event_id is not None else None
        shot = event.get("shot") or {}
        rows.append(
            {
                "Time": minute_label(event.get("gameTime")),
                "Team": short_team_name(team_name(int(squad_id), squads)) if squad_id is not None else "",
                "Player": player_name(player_id, players),
                "Action": format_position(event.get("action")),
                "Result": format_position(event.get("result")),
                "xG": round(float(xg_value), 3) if xg_value is not None else "",
                "Distance": f"{shot.get('distance', 0):.1f}m" if shot.get("distance") is not None else "",
            }
        )
    return rows
