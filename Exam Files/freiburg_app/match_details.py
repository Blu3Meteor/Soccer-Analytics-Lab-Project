from __future__ import annotations

from collections import defaultdict
from html import escape
from typing import Any

import streamlit as st

from .components import render_scoreboard
from .config import (
    KPI_PXT_BALL_WIN,
    KPI_PXT_BLOCK,
    KPI_PXT_DRIBBLE,
    KPI_PXT_FOUL,
    KPI_PXT_PASS,
    KPI_PXT_SETPIECE,
    KPI_PXT_SHOT,
)
from .data import (
    compact_matchday,
    format_position,
    load_match_events,
    load_match_events_kpis,
    load_match_lineups,
    load_match_player_kpis,
    minute_label,
    player_name,
    short_team_name,
    team_name,
)
from .events import card_events, scoring_events, shot_events
from .lineups import lineup_for_team, render_lineup_panel
from .metrics import compute_stats, opposition_team, shot_xg_by_event, stat_rows


PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
PXT_ACTION_KPIS = {
    KPI_PXT_PASS: "Pass",
    KPI_PXT_DRIBBLE: "Dribble",
    KPI_PXT_SETPIECE: "Set Piece",
    KPI_PXT_BLOCK: "Block",
    KPI_PXT_SHOT: "Shot",
    KPI_PXT_BALL_WIN: "Ball Win",
    KPI_PXT_FOUL: "Foul",
}


def _clock_seconds(value: dict[str, Any] | str | None) -> float:
    if isinstance(value, dict):
        raw = value.get("gameTime", "")
    else:
        raw = value or ""
    if not raw:
        return 0.0
    main = raw.split()[0].split(".", 1)[0]
    added_seconds = 0.0
    if "+" in main:
        main, added = main.split("+", 1)
        try:
            added_seconds = float(added.split(":", 1)[0]) * 60
        except ValueError:
            added_seconds = 0.0
    parts = main.split(":")
    try:
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1]) + added_seconds
        return float(parts[0]) + added_seconds
    except ValueError:
        return 0.0


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


def _player_short_name(player_id: int, players: dict[int, dict[str, Any]]) -> str:
    name = player_name(player_id, players)
    if len(name) <= 13:
        return name
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name[:12]


def _pitch_background() -> str:
    return (
        '<rect x="0" y="0" width="105" height="68" rx="1.8" fill="#2f8f53"/>'
        '<rect x="0.8" y="0.8" width="103.4" height="66.4" fill="none" stroke="rgba(255,255,255,0.78)" stroke-width="0.6"/>'
        '<line x1="52.5" y1="0.8" x2="52.5" y2="67.2" stroke="rgba(255,255,255,0.65)" stroke-width="0.45"/>'
        '<circle cx="52.5" cy="34" r="9.15" fill="none" stroke="rgba(255,255,255,0.65)" stroke-width="0.45"/>'
        '<circle cx="52.5" cy="34" r="0.65" fill="rgba(255,255,255,0.75)"/>'
        '<rect x="0.8" y="13.84" width="16.5" height="40.32" fill="none" stroke="rgba(255,255,255,0.65)" stroke-width="0.45"/>'
        '<rect x="87.7" y="13.84" width="16.5" height="40.32" fill="none" stroke="rgba(255,255,255,0.65)" stroke-width="0.45"/>'
        '<rect x="0.8" y="24.84" width="5.5" height="18.32" fill="none" stroke="rgba(255,255,255,0.65)" stroke-width="0.45"/>'
        '<rect x="98.7" y="24.84" width="5.5" height="18.32" fill="none" stroke="rgba(255,255,255,0.65)" stroke-width="0.45"/>'
        '<text x="52.5" y="66" text-anchor="middle" fill="rgba(255,255,255,0.8)" font-size="2.6">Attacking direction</text>'
        '<path d="M43 63 L61 63" stroke="rgba(255,255,255,0.8)" stroke-width="0.6" marker-end="url(#arrow-soft)"/>'
    )


def _svg_wrapper(inner: str) -> str:
    return (
        '<div class="advanced-pitch">'
        '<svg viewBox="0 0 105 68" role="img" aria-label="Football pitch visualisation">'
        '<defs>'
        '<marker id="arrow-soft" markerWidth="4" markerHeight="4" refX="3.6" refY="2" orient="auto">'
        '<path d="M0,0 L4,2 L0,4 Z" fill="rgba(255,255,255,0.85)"/>'
        '</marker>'
        '<marker id="arrow-red" markerWidth="4" markerHeight="4" refX="3.6" refY="2" orient="auto">'
        '<path d="M0,0 L4,2 L0,4 Z" fill="#c7152a"/>'
        '</marker>'
        '<marker id="arrow-blue" markerWidth="4" markerHeight="4" refX="3.6" refY="2" orient="auto">'
        '<path d="M0,0 L4,2 L0,4 Z" fill="#1f4d78"/>'
        '</marker>'
        '<marker id="arrow-dark" markerWidth="4" markerHeight="4" refX="3.6" refY="2" orient="auto">'
        '<path d="M0,0 L4,2 L0,4 Z" fill="#27313f"/>'
        '</marker>'
        '</defs>'
        f'{_pitch_background()}{inner}'
        '</svg>'
        '</div>'
    )


def _freiburg_substitution_times(lineup: dict[str, Any]) -> list[tuple[float, str]]:
    by_second: dict[float, str] = {}
    for substitution in lineup.get("substitutions", []):
        game_time = substitution.get("gameTime")
        second = _clock_seconds(game_time)
        if second > 0:
            by_second[second] = minute_label(game_time)
    return sorted(by_second.items())


def _match_segments(events: list[dict[str, Any]], lineup: dict[str, Any]) -> list[dict[str, Any]]:
    cutoffs = _freiburg_substitution_times(lineup)
    max_second = max((_clock_seconds(event.get("gameTime")) for event in events), default=0.0)
    boundaries = [(0.0, "0'")] + cutoffs + [(max_second + 1.0, "FT")]
    segments = []
    for index in range(len(boundaries) - 1):
        start_second, start_label = boundaries[index]
        end_second, end_label = boundaries[index + 1]
        segments.append(
            {
                "label": f"{start_label} to {end_label}",
                "start": start_second,
                "end": end_second,
            }
        )
    return segments


def _successful_team_passes(
    events: list[dict[str, Any]],
    team_id: int,
    start_second: float,
    end_second: float,
) -> list[dict[str, Any]]:
    passes = []
    for event in events:
        squad_id = event.get("squadId")
        if squad_id is None or int(squad_id) != int(team_id):
            continue
        if event.get("actionType") != "PASS" or event.get("result") != "SUCCESS":
            continue
        receiver = (event.get("pass") or {}).get("receiver") or {}
        if receiver.get("type") != "TEAMMATE" or receiver.get("playerId") is None:
            continue
        second = _clock_seconds(event.get("gameTime"))
        if start_second <= second < end_second:
            passes.append(event)
    return passes


def _pass_network_rows(
    passes: list[dict[str, Any]],
    players: dict[int, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[tuple[int, int], int], float]:
    nodes: dict[int, dict[str, Any]] = {}
    edge_counts: dict[tuple[int, int], int] = defaultdict(int)

    for event in passes:
        passer_id_raw = (event.get("player") or {}).get("id")
        receiver_id_raw = ((event.get("pass") or {}).get("receiver") or {}).get("playerId")
        if passer_id_raw is None or receiver_id_raw is None:
            continue
        passer_id = int(passer_id_raw)
        receiver_id = int(receiver_id_raw)
        start_xy = _event_xy(event, "start")
        end_xy = _event_xy(event, "end")
        if not start_xy or not end_xy:
            continue

        passer = nodes.setdefault(passer_id, {"x": [], "y": [], "passes": 0, "received": 0})
        receiver = nodes.setdefault(receiver_id, {"x": [], "y": [], "passes": 0, "received": 0})
        passer["x"].append(start_xy[0])
        passer["y"].append(start_xy[1])
        passer["passes"] += 1
        receiver["x"].append(end_xy[0])
        receiver["y"].append(end_xy[1])
        receiver["received"] += 1
        edge_counts[tuple(sorted((passer_id, receiver_id)))] += 1

    rows = []
    for player_id, data in nodes.items():
        involvement = int(data["passes"]) + int(data["received"])
        rows.append(
            {
                "player_id": player_id,
                "Player": player_name(player_id, players),
                "x": sum(data["x"]) / len(data["x"]),
                "y": sum(data["y"]) / len(data["y"]),
                "Passes": int(data["passes"]),
                "Received": int(data["received"]),
                "Involvement": involvement,
            }
        )
    rows.sort(key=lambda row: (-row["Involvement"], row["Player"]))

    total_passes = sum(row["Passes"] for row in rows)
    if len(rows) <= 1 or total_passes == 0:
        centralisation = 0.0
    else:
        max_passes = max(row["Passes"] for row in rows)
        centralisation = sum(max_passes - row["Passes"] for row in rows) / ((len(rows) - 1) * total_passes)

    return rows, edge_counts, centralisation


def _render_pass_network(
    passes: list[dict[str, Any]],
    players: dict[int, dict[str, Any]],
) -> tuple[str, list[dict[str, Any]], float]:
    rows, edge_counts, centralisation = _pass_network_rows(passes, players)
    if not rows:
        return "", [], 0.0

    rows_by_id = {int(row["player_id"]): row for row in rows}
    max_edge = max(edge_counts.values()) if edge_counts else 1
    max_involvement = max(row["Involvement"] for row in rows) or 1

    lines = []
    for (player_a, player_b), count in sorted(edge_counts.items(), key=lambda item: item[1]):
        if player_a not in rows_by_id or player_b not in rows_by_id:
            continue
        a = rows_by_id[player_a]
        b = rows_by_id[player_b]
        width = 0.22 + (count / max_edge) * 1.55
        opacity = 0.24 + (count / max_edge) * 0.42
        lines.append(
            f'<line x1="{a["x"]:.2f}" y1="{a["y"]:.2f}" x2="{b["x"]:.2f}" y2="{b["y"]:.2f}" '
            f'stroke="#ffffff" stroke-width="{width:.2f}" opacity="{opacity:.2f}"/>'
        )

    markers = []
    for row in rows:
        radius = 1.3 + (row["Involvement"] / max_involvement) * 2.05
        markers.append(
            f'<circle cx="{row["x"]:.2f}" cy="{row["y"]:.2f}" r="{radius:.2f}" fill="#c7152a" '
            'stroke="#ffffff" stroke-width="0.34"/>'
            f'<text x="{row["x"]:.2f}" y="{row["y"] - radius - 1.0:.2f}" text-anchor="middle" '
            'fill="#ffffff" font-size="1.85" font-weight="800">'
            f'{escape(_player_short_name(int(row["player_id"]), players))}</text>'
        )

    return _svg_wrapper("".join(lines + markers)), rows, centralisation


def _event_pxt_values(events_kpis: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    values: dict[int, dict[str, Any]] = defaultdict(lambda: {"total": 0.0, "by_type": defaultdict(float)})
    for item in events_kpis:
        kpi_id = int(item.get("kpiId", -1))
        if kpi_id not in PXT_ACTION_KPIS:
            continue
        event_id = int(item["eventId"])
        value = float(item.get("value") or 0.0)
        label = PXT_ACTION_KPIS[kpi_id]
        values[event_id]["total"] += value
        values[event_id]["by_type"][label] += value
    return values


def _event_team_id(event: dict[str, Any]) -> int | None:
    squad_id = event.get("squadId")
    if squad_id is None:
        return None
    return int(squad_id)


def _event_player_id(event: dict[str, Any]) -> int | None:
    player_id = (event.get("player") or {}).get("id")
    if player_id is None:
        return None
    return int(player_id)


def _event_sort_key(event: dict[str, Any]) -> tuple[int, float, int]:
    return (
        int(event.get("periodId") or 0),
        _clock_seconds(event.get("gameTime")),
        int(event.get("index") or 0),
    )


def _event_xt_row(
    event: dict[str, Any],
    value_data: dict[str, Any],
    players: dict[int, dict[str, Any]],
    squads: dict[int, dict[str, Any]],
    include_zero: bool = False,
) -> dict[str, Any] | None:
    event_id = int(event["id"])
    action_type = event.get("actionType") or ""
    value = float(value_data.get("total") or 0.0)
    if not include_zero and abs(value) < 0.000001 and action_type not in {"SHOT", "GOAL", "OWN_GOAL"}:
        return None

    start_xy = _event_xy(event, "start")
    end_xy = _event_xy(event, "end") or start_xy
    if not start_xy or not end_xy:
        return None

    team_id = _event_team_id(event)
    player_id = _event_player_id(event)
    by_type = value_data.get("by_type", {})
    dominant_type = max(by_type.items(), key=lambda item: abs(item[1]))[0] if by_type else format_position(action_type)

    return {
        "event_id": event_id,
        "index": int(event.get("index") or 0),
        "Time": minute_label(event.get("gameTime")),
        "second": _clock_seconds(event.get("gameTime")),
        "team_id": team_id,
        "Team": short_team_name(team_name(team_id, squads)) if team_id is not None else "",
        "player_id": player_id if player_id is not None else -event_id,
        "Player": player_name(player_id, players),
        "Action": format_position(action_type),
        "Detail": format_position(event.get("action")),
        "Result": format_position(event.get("result")),
        "xT": value,
        "Type": dominant_type,
        "start_x": start_xy[0],
        "start_y": start_xy[1],
        "end_x": end_xy[0],
        "end_y": end_xy[1],
    }


def _match_xt_rows(
    events: list[dict[str, Any]],
    events_kpis: list[dict[str, Any]],
    players: dict[int, dict[str, Any]],
    squads: dict[int, dict[str, Any]],
    team_ids: set[int] | None = None,
) -> list[dict[str, Any]]:
    values_by_event = _event_pxt_values(events_kpis)
    rows = []
    for event in events:
        team_id = _event_team_id(event)
        if team_id is None:
            continue
        if team_ids is not None and team_id not in team_ids:
            continue
        event_id = int(event["id"])
        row = _event_xt_row(event, values_by_event.get(event_id, {"total": 0.0, "by_type": {}}), players, squads)
        if row:
            rows.append(row)
    rows.sort(key=lambda row: (-abs(float(row["xT"])), row["second"]))
    return rows


def _player_xt_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: dict[tuple[int | None, int], dict[str, Any]] = {}
    for row in rows:
        player_id = int(row["player_id"])
        player = summary.setdefault(
            (row.get("team_id"), player_id),
            {
                "Team": row["Team"],
                "Player": row["Player"],
                "Actions": 0,
                "Total xT": 0.0,
                "Pass xT": 0.0,
                "Shot xT": 0.0,
                "Dribble xT": 0.0,
                "Shots": 0,
            },
        )
        value = float(row["xT"])
        player["Actions"] += 1
        player["Total xT"] += value
        if row["Action"] in {"Shot", "Goal", "Own Goal"}:
            player["Shots"] += 1
            player["Shot xT"] += value
        elif row["Type"] == "Pass":
            player["Pass xT"] += value
        elif row["Type"] == "Dribble":
            player["Dribble xT"] += value

    output = []
    for player in summary.values():
        output.append(
            {
                "Team": player["Team"],
                "Player": player["Player"],
                "Actions": player["Actions"],
                "Shots": player["Shots"],
                "Total xT": round(player["Total xT"], 4),
                "Pass xT": round(player["Pass xT"], 4),
                "Shot xT": round(player["Shot xT"], 4),
                "Dribble xT": round(player["Dribble xT"], 4),
            }
        )
    output.sort(key=lambda row: (-float(row["Total xT"]), row["Player"]))
    return output


def _shot_goal_options(
    events: list[dict[str, Any]],
    events_kpis: list[dict[str, Any]],
    players: dict[int, dict[str, Any]],
    squads: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    values_by_event = _event_pxt_values(events_kpis)
    rows = []
    for event in events:
        if event.get("actionType") not in {"SHOT", "GOAL", "OWN_GOAL"}:
            continue
        event_id = int(event["id"])
        row = _event_xt_row(
            event,
            values_by_event.get(event_id, {"total": 0.0, "by_type": {}}),
            players,
            squads,
            include_zero=True,
        )
        if not row:
            continue
        result = f" · {row['Result']}" if row["Result"] else ""
        row["Label"] = (
            f"{row['Time']} · {row['Team']} · {row['Player']} · "
            f"{row['Action']}{result} · xT {float(row['xT']):.3f}"
        )
        rows.append(row)
    rows.sort(key=lambda row: (row["second"], row["index"]))
    return rows


def _build_up_rows(
    events: list[dict[str, Any]],
    target_event: dict[str, Any],
    events_kpis: list[dict[str, Any]],
    players: dict[int, dict[str, Any]],
    squads: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    values_by_event = _event_pxt_values(events_kpis)
    target_id = int(target_event["id"])
    target_index = int(target_event.get("index") or 0)
    target_period = target_event.get("periodId")
    target_sequence = target_event.get("sequenceIndex")
    target_attack_id = target_event.get("currentAttackingSquadId") or target_event.get("squadId")

    candidates: list[dict[str, Any]] = []
    if target_sequence is not None:
        candidates = [
            event
            for event in events
            if event.get("sequenceIndex") == target_sequence
            and event.get("periodId") == target_period
            and int(event.get("index") or 0) <= target_index
        ]

    if not candidates:
        candidates = [
            event
            for event in events
            if event.get("periodId") == target_period and int(event.get("index") or 0) <= target_index
        ]

    if target_attack_id is not None:
        target_attack_id = int(target_attack_id)
        same_squad = [
            event
            for event in candidates
            if event.get("squadId") == target_attack_id
        ]
        same_attack = [
            event
            for event in candidates
            if event.get("currentAttackingSquadId") == target_attack_id
        ]
        if same_squad:
            candidates = same_squad
        elif same_attack:
            candidates = same_attack

    candidates = sorted(candidates, key=_event_sort_key)
    if len(candidates) > 18:
        candidates = candidates[-18:]

    rows = []
    for event in candidates:
        event_id = int(event["id"])
        row = _event_xt_row(
            event,
            values_by_event.get(event_id, {"total": 0.0, "by_type": {}}),
            players,
            squads,
            include_zero=True,
        )
        if not row:
            continue
        if event_id != target_id and _event_xy(event, "end") is None and abs(float(row["xT"])) < 0.000001:
            continue
        row["is_target"] = event_id == target_id
        rows.append(row)

    if not any(row["event_id"] == target_id for row in rows):
        target_row = _event_xt_row(
            target_event,
            values_by_event.get(target_id, {"total": 0.0, "by_type": {}}),
            players,
            squads,
            include_zero=True,
        )
        if target_row:
            target_row["is_target"] = True
            rows.append(target_row)

    rows.sort(key=lambda row: (row["second"], row["index"]))
    return rows


def _build_up_table_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "#": index,
            "Time": row["Time"],
            "Team": row["Team"],
            "Player": row["Player"],
            "Action": row["Action"],
            "Detail": row["Detail"],
            "Result": row["Result"],
            "xT": round(float(row["xT"]), 5),
        }
        for index, row in enumerate(rows, start=1)
    ]


def _render_build_up_map(rows: list[dict[str, Any]], players: dict[int, dict[str, Any]]) -> str:
    if not rows:
        return ""

    max_value = max((abs(float(row["xT"])) for row in rows), default=0.01) or 0.01
    arrows = []
    step_markers = []
    player_locations: dict[int, dict[str, Any]] = {}
    for index, row in enumerate(rows, start=1):
        value = float(row["xT"])
        is_target = bool(row.get("is_target"))
        if is_target:
            color = "#c7152a"
            marker = "arrow-red"
        elif value > 0:
            color = "#1f4d78"
            marker = "arrow-blue"
        else:
            color = "#27313f"
            marker = "arrow-dark"
        width = 0.3 + (abs(value) / max_value) * 1.5
        if is_target:
            width = max(width, 1.3)
        opacity = 0.42 + min(0.48, abs(value) / max_value * 0.48)
        start_x = float(row["start_x"])
        start_y = float(row["start_y"])
        end_x = float(row["end_x"])
        end_y = float(row["end_y"])
        if abs(start_x - end_x) < 0.1 and abs(start_y - end_y) < 0.1:
            arrows.append(
                f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="{width + 0.8:.2f}" '
                f'fill="{color}" opacity="{opacity:.2f}"/>'
            )
        else:
            arrows.append(
                f'<line x1="{start_x:.2f}" y1="{start_y:.2f}" '
                f'x2="{end_x:.2f}" y2="{end_y:.2f}" stroke="{color}" '
                f'stroke-width="{width:.2f}" opacity="{opacity:.2f}" marker-end="url(#{marker})"/>'
            )
        step_markers.append(
            f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="1.25" fill="#111827" opacity="0.78"/>'
            f'<text x="{start_x:.2f}" y="{start_y + 0.72:.2f}" text-anchor="middle" '
            'fill="#ffffff" font-size="1.55" font-weight="900">'
            f"{index}</text>"
        )
        player = player_locations.setdefault(
            int(row["player_id"]),
            {"x": [], "y": [], "value": 0.0, "name": row["Player"]},
        )
        player["x"].append(start_x)
        player["y"].append(start_y)
        player["value"] += max(0.001, abs(value))

    max_player_value = max((float(row["value"]) for row in player_locations.values()), default=1.0) or 1.0
    circles = []
    for _player_id, row in player_locations.items():
        x = sum(row["x"]) / len(row["x"])
        y = sum(row["y"]) / len(row["y"])
        radius = 1.15 + (float(row["value"]) / max_player_value) * 1.85
        label = str(row["name"])
        if len(label) > 13:
            parts = label.split()
            label = f"{parts[0][0]}. {parts[-1]}" if len(parts) >= 2 else label[:12]
        circles.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" fill="#111827" '
            'fill-opacity="0.68" stroke="#ffffff" stroke-width="0.28"/>'
            f'<text x="{x:.2f}" y="{y - radius - 1.0:.2f}" text-anchor="middle" '
            'fill="#ffffff" font-size="1.75" font-weight="800">'
            f'{escape(label)}</text>'
        )

    legend = (
        '<rect x="2" y="2" width="42" height="11.5" rx="1.2" fill="rgba(21,23,26,0.72)"/>'
        '<line x1="4" y1="5" x2="10" y2="5" stroke="#1f4d78" stroke-width="1" marker-end="url(#arrow-blue)"/>'
        '<text x="12" y="5.8" fill="#ffffff" font-size="2.1">positive build-up xT</text>'
        '<line x1="4" y1="8.2" x2="10" y2="8.2" stroke="#c7152a" stroke-width="1" marker-end="url(#arrow-red)"/>'
        '<text x="12" y="9" fill="#ffffff" font-size="2.1">selected shot / goal</text>'
        '<line x1="4" y1="11.4" x2="10" y2="11.4" stroke="#27313f" stroke-width="1" marker-end="url(#arrow-dark)"/>'
        '<text x="12" y="12.2" fill="#ffffff" font-size="2.1">neutral or negative</text>'
    )
    return _svg_wrapper("".join(arrows + circles + step_markers) + legend)


def _event_table_rows(events: list[dict[str, Any]], players: dict[int, dict[str, Any]], squads: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for event in events:
        player_id = (event.get("player") or {}).get("id")
        squad_id = event.get("squadId")
        rows.append(
            {
                "Index": event.get("index"),
                "Time": minute_label(event.get("gameTime")),
                "Team": short_team_name(team_name(int(squad_id), squads)) if squad_id is not None else "",
                "Player": player_name(player_id, players),
                "Action Type": format_position(event.get("actionType")),
                "Action": format_position(event.get("action")),
                "Result": format_position(event.get("result")),
                "Phase": format_position(event.get("phase")),
                "Pressure": event.get("pressure"),
                "Team pxT": (event.get("pxT") or {}).get("team"),
                "Opponent pxT": (event.get("pxT") or {}).get("opponent"),
            }
        )
    return rows


def _detail_section_selector(match_id: int, sections: list[str]) -> str:
    key = f"match_details_section_{match_id}"
    if st.session_state.get(key) not in sections:
        st.session_state[key] = sections[0]

    if hasattr(st, "segmented_control"):
        selected = st.segmented_control(
            "Match detail section",
            sections,
            key=key,
            label_visibility="collapsed",
            width="stretch",
        )
    else:
        selected = st.radio(
            "Match detail section",
            sections,
            key=key,
            horizontal=True,
            label_visibility="collapsed",
        )
    return selected or st.session_state[key]


def _match_option_label(match: dict[str, Any]) -> str:
    return (
        f"{compact_matchday(match)} · "
        f"{short_team_name(match['homeName'])} {match['homeScore']}-{match['awayScore']} "
        f"{short_team_name(match['awayName'])}"
    )


def _selected_match_from_details_selector(
    summaries: list[dict[str, Any]],
    selected_index: int,
) -> dict[str, Any]:
    match_ids = [int(match["id"]) for match in summaries]
    selected_index = min(max(selected_index, 0), len(summaries) - 1)
    selected_id = int(summaries[selected_index]["id"])
    chosen_id = st.selectbox(
        "Select match",
        match_ids,
        index=match_ids.index(selected_id),
        format_func=lambda match_id: _match_option_label(next(match for match in summaries if int(match["id"]) == int(match_id))),
    )
    chosen_index = match_ids.index(int(chosen_id))
    if chosen_index != selected_index:
        st.session_state.selected_match_index = chosen_index
        if hasattr(st, "query_params"):
            st.query_params["page"] = "match_details"
            st.query_params["match_id"] = str(chosen_id)
        else:
            st.experimental_set_query_params(page="match_details", match_id=str(chosen_id))
        st.rerun()
    return summaries[chosen_index]


def render_match_details_page(
    summaries: list[dict[str, Any]],
    selected_index: int,
    freiburg_id: int,
    squads_by_id: dict[int, dict[str, Any]],
    players_by_id: dict[int, dict[str, Any]],
) -> None:
    selected_match = _selected_match_from_details_selector(summaries, selected_index)
    match_id = int(selected_match["id"])
    events = load_match_events(match_id)
    events_kpis = load_match_events_kpis(match_id)
    lineups = load_match_lineups(match_id)
    player_kpis = load_match_player_kpis(match_id)

    home_id = int(selected_match["homeSquadId"])
    away_id = int(selected_match["awaySquadId"])
    home_name = selected_match["homeName"]
    away_name = selected_match["awayName"]
    result_code = selected_match["freiburgResult"]

    st.markdown('<div class="headline-row">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="app-kicker">Match Details · {escape(compact_matchday(selected_match))}</div>',
        unsafe_allow_html=True,
    )
    st.title(f"{short_team_name(home_name)} {selected_match['homeScore']}-{selected_match['awayScore']} {short_team_name(away_name)}")
    st.markdown("</div>", unsafe_allow_html=True)

    render_scoreboard(selected_match, home_id, away_id, home_name, away_name, result_code, squads_by_id)

    xg_by_event = shot_xg_by_event(events_kpis)
    stats = compute_stats(selected_match, events, player_kpis, events_kpis)
    opponent_id = opposition_team(selected_match, freiburg_id)
    goals = scoring_events(events, selected_match, players_by_id, squads_by_id)
    match_xt_rows = _match_xt_rows(events, events_kpis, players_by_id, squads_by_id, {home_id, away_id})
    freiburg_xt_total = sum(float(row["xT"]) for row in match_xt_rows if row.get("team_id") == freiburg_id)
    player_xt_rows = _player_xt_summary(match_xt_rows)
    shot_goal_rows = _shot_goal_options(events, events_kpis, players_by_id, squads_by_id)
    events_by_id = {int(event["id"]): event for event in events}

    section = _detail_section_selector(
        match_id,
        ["Overview", "Passing Networks", "Shot Build-up xT", "Lineups", "Event Data"],
    )

    if section == "Overview":
        metric_cols = st.columns(4)
        metric_cols[0].metric("Freiburg Total xT", f"{freiburg_xt_total:.3f}")
        metric_cols[1].metric("Freiburg Shots", int(stats[freiburg_id]["shots"]))
        metric_cols[2].metric("Pass Accuracy", f"{stats[freiburg_id]['pass_accuracy']:.1f}%")
        metric_cols[3].metric("Opponent", short_team_name(team_name(opponent_id, squads_by_id)))

        st.markdown("**Match Stats**")
        st.dataframe(
            stat_rows(stats, home_id, away_id, home_name, away_name),
            hide_index=True,
            width="stretch",
        )
        st.markdown("**Scoring**")
        if goals:
            st.dataframe(goals, hide_index=True, width="stretch")
        else:
            st.caption("No goals recorded.")

    elif section == "Passing Networks":
        st.markdown("**Segmented Passing Networks**")
        st.caption("Successful teammate passes, split from initial lineup to first substitution, then between each substitution window.")
        network_columns = st.columns(2)
        for column, team_id, team_label in (
            (network_columns[0], home_id, home_name),
            (network_columns[1], away_id, away_name),
        ):
            with column:
                st.markdown(f"**{short_team_name(team_label)}**")
                team_lineup = lineup_for_team(lineups, team_id)
                segments = _match_segments(events, team_lineup)
                segment_labels = [segment["label"] for segment in segments]
                selected_segment_label = st.selectbox(
                    "Segment",
                    segment_labels,
                    key=f"network_segment_{match_id}_{team_id}",
                    label_visibility="collapsed",
                )
                selected_segment = segments[segment_labels.index(selected_segment_label)]
                passes = _successful_team_passes(events, team_id, selected_segment["start"], selected_segment["end"])
                network_html, network_rows, centralisation = _render_pass_network(passes, players_by_id)

                metric_cols = st.columns(2)
                metric_cols[0].metric("Passes", len(passes))
                metric_cols[1].metric("Players", len(network_rows))
                metric_cols = st.columns(2)
                metric_cols[0].metric("Centralisation", f"{centralisation:.2f}")
                metric_cols[1].metric("Top Player", network_rows[0]["Player"] if network_rows else "-")

                if network_html:
                    st.markdown(network_html, unsafe_allow_html=True)
                    with st.expander("Network Table", expanded=False):
                        st.dataframe(
                            [
                                {
                                    "Player": row["Player"],
                                    "Passes": row["Passes"],
                                    "Received": row["Received"],
                                    "Involvement": row["Involvement"],
                                }
                                for row in network_rows
                            ],
                            hide_index=True,
                            width="stretch",
                        )
                else:
                    st.caption("No successful teammate passes in this segment.")

    elif section == "Shot Build-up xT":
        st.markdown("**Shot and Goal Build-up**")
        if shot_goal_rows:
            shot_labels = {int(row["event_id"]): row["Label"] for row in shot_goal_rows}
            selected_event_id = st.selectbox(
                "Shot or goal",
                [int(row["event_id"]) for row in shot_goal_rows],
                format_func=lambda event_id: shot_labels.get(int(event_id), str(event_id)),
            )
            selected_event = events_by_id[int(selected_event_id)]
            selected_shot = next(row for row in shot_goal_rows if int(row["event_id"]) == int(selected_event_id))
            build_up_rows = _build_up_rows(events, selected_event, events_kpis, players_by_id, squads_by_id)

            metric_cols = st.columns(4)
            metric_cols[0].metric("Sequence Actions", len(build_up_rows))
            metric_cols[1].metric("Build-up xT", f"{sum(float(row['xT']) for row in build_up_rows):.3f}")
            metric_cols[2].metric("Selected xT", f"{float(selected_shot['xT']):.3f}")
            metric_cols[3].metric("Player", selected_shot["Player"])

            build_up_map = _render_build_up_map(build_up_rows, players_by_id)
            if build_up_map:
                st.markdown(build_up_map, unsafe_allow_html=True)
                st.dataframe(_build_up_table_rows(build_up_rows), hide_index=True, width="stretch")
            else:
                st.caption("No coordinate data was available for this shot or goal.")
        else:
            st.caption("No shot or goal events with coordinate data were found for this match.")

        st.markdown("**Best xT Players · Both Teams**")
        if player_xt_rows:
            st.dataframe(player_xt_rows[:24], hide_index=True, width="stretch")
        else:
            st.caption("No event-level xT values were found for this match.")

        with st.expander("Top xT Actions · Both Teams", expanded=False):
            st.dataframe(
                [
                    {
                        "Time": row["Time"],
                        "Team": row["Team"],
                        "Player": row["Player"],
                        "Action": row["Action"],
                        "Detail": row["Detail"],
                        "Result": row["Result"],
                        "Type": row["Type"],
                        "xT": round(float(row["xT"]), 5),
                    }
                    for row in match_xt_rows[:120]
                ],
                hide_index=True,
                width="stretch",
            )

    elif section == "Lineups":
        lineup_columns = st.columns(2)
        with lineup_columns[0]:
            render_lineup_panel(home_name, lineup_for_team(lineups, home_id), players_by_id)
        with lineup_columns[1]:
            render_lineup_panel(away_name, lineup_for_team(lineups, away_id), players_by_id)

    elif section == "Event Data":
        st.markdown("**Goals**")
        if goals:
            st.dataframe(goals, hide_index=True, width="stretch")
        else:
            st.caption("No goals recorded.")

        cards = card_events(events, players_by_id, squads_by_id)
        st.markdown("**Cards**")
        if cards:
            st.dataframe(cards, hide_index=True, width="stretch")
        else:
            st.caption("No card events recorded.")

        shots = shot_events(events, players_by_id, squads_by_id, xg_by_event)
        st.markdown("**Shots**")
        if shots:
            st.dataframe(shots, hide_index=True, width="stretch")
        else:
            st.caption("No shots recorded.")

        with st.expander("All Match Events", expanded=False):
            st.dataframe(_event_table_rows(events, players_by_id, squads_by_id), hide_index=True, width="stretch")
