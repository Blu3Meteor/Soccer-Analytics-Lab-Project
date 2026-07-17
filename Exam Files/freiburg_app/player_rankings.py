# PROVENANCE: MIXED MODULE — SEE CODE_PROVENANCE.md
# AI-assisted extraction and radar/UI code are mixed with ranking calculations.
# Do not claim the mathematical sections as manual until authorship is verified.

from __future__ import annotations

import math
from collections import defaultdict
from html import escape
from typing import Any

import streamlit as st

from .analysis_utils import per_90, percentile_rank
from .config import (
    KPI_DEF_PXT_ACTIVE,
    KPI_DEF_PXT_BALL_WIN,
    KPI_DEF_PXT_BLOCK,
    KPI_DEF_PXT_DRIBBLE,
    KPI_DEF_PXT_PASS,
    KPI_PXT_ATTACK,
    KPI_PXT_BALL_WIN,
    KPI_PXT_DRIBBLE,
    KPI_PXT_PASS,
    KPI_PXT_REC,
    KPI_SHOT_XG,
)
from .data import load_match_events, load_match_events_kpis, load_match_player_kpis, player_name, team_name
from .event_utils import attacking_event_shares, event_coordinate_x, event_kpi_values, event_player_id


KPI_ASSISTS = 77
KPI_SUCCESSFUL_PASSES = 90
KPI_UNSUCCESSFUL_PASSES = 91
KPI_WON_GROUND_DUELS = 94
KPI_LOST_GROUND_DUELS = 95
KPI_WON_AERIAL_DUELS = 96
KPI_LOST_AERIAL_DUELS = 97
KPI_BALL_LOSS_NUMBER = 22
KPI_BALL_LOSS_ADDED_OPPONENTS = 20
KPI_BALL_WIN_ADDED_TEAMMATES = 23
KPI_BALL_WIN_REMOVED_OPPONENTS = 24
KPI_BALL_WIN_ADDED_TEAMMATES_DEFENDERS = 36
KPI_BYPASSED_OPPONENTS = 0
KPI_BYPASSED_DEFENDERS = 2
KPI_BYPASSED_OPPONENTS_RECEIVING = 7
KPI_NUMBER_OF_PRESSES = 1536
KPI_SHOT_CREATING_ACTIONS = 1694
KPI_EXPECTED_SHOT_ASSISTS = 1781
KPI_EXPECTED_GOAL_ASSISTS = 1782
KPI_EXPECTED_PASSES = 1783

KPI_MAP_KEYS = {
    "PXT": KPI_PXT_ATTACK,
    "Pass PXT": KPI_PXT_PASS,
    "Dribble PXT": KPI_PXT_DRIBBLE,
    "Ball Win PXT": KPI_PXT_BALL_WIN,
    "Receiving PXT": KPI_PXT_REC,
    "Assists": KPI_ASSISTS,
    "Aerial Wins": KPI_WON_AERIAL_DUELS,
    "Aerial Losses": KPI_LOST_AERIAL_DUELS,
    "Ground Wins": KPI_WON_GROUND_DUELS,
    "Ground Losses": KPI_LOST_GROUND_DUELS,
    "Bypassed Opponents": KPI_BYPASSED_OPPONENTS,
    "Bypassed Defenders": KPI_BYPASSED_DEFENDERS,
    "Bypassed Receiving": KPI_BYPASSED_OPPONENTS_RECEIVING,
    "Ball Losses": KPI_BALL_LOSS_NUMBER,
    "Dangerous Ball Losses": KPI_BALL_LOSS_ADDED_OPPONENTS,
    "Ball Win Added Teammates": KPI_BALL_WIN_ADDED_TEAMMATES,
    "Ball Win Removed Opponents": KPI_BALL_WIN_REMOVED_OPPONENTS,
    "Ball Win Added Defenders": KPI_BALL_WIN_ADDED_TEAMMATES_DEFENDERS,
    "Def PXT Active": KPI_DEF_PXT_ACTIVE,
    "Def PXT Pass": KPI_DEF_PXT_PASS,
    "Def PXT Dribble": KPI_DEF_PXT_DRIBBLE,
    "Def PXT Block": KPI_DEF_PXT_BLOCK,
    "Def PXT Ball Win": KPI_DEF_PXT_BALL_WIN,
    "Presses": KPI_NUMBER_OF_PRESSES,
    "Shot Creating Actions": KPI_SHOT_CREATING_ACTIONS,
    "Expected Shot Assists": KPI_EXPECTED_SHOT_ASSISTS,
    "Expected Goal Assists": KPI_EXPECTED_GOAL_ASSISTS,
    "Expected Passes": KPI_EXPECTED_PASSES,
    "Successful Passes": KPI_SUCCESSFUL_PASSES,
    "Unsuccessful Passes": KPI_UNSUCCESSFUL_PASSES,
    "Shot xG": KPI_SHOT_XG,
}


RADAR_CONFIGS: dict[str, list[dict[str, Any]]] = {
    "Forwards": [
        {"label": "PXT", "key": "PXT", "kind": "attack"},
        {"label": "Aerial Wins", "key": "Aerial Wins", "kind": "neutral"},
        {"label": "npxG", "key": "npxG", "kind": "attack"},
        {"label": "NP Goals", "key": "NP Goals", "kind": "attack"},
        {"label": "Assists", "key": "Assists", "kind": "attack"},
        {"label": "Final 3rd Receive", "key": "Final Third Receptions", "kind": "attack"},
        {"label": "Dribble Success", "key": "Dribble Success %", "kind": "rate"},
    ],
    "Midfield": [
        {"label": "PXT", "key": "PXT", "kind": "attack"},
        {"label": "Pass PXT", "key": "Pass PXT", "kind": "attack"},
        {"label": "Bypassed Opp.", "key": "Bypassed Opponents", "kind": "attack"},
        {"label": "Receiving PXT", "key": "Receiving PXT", "kind": "attack"},
        {"label": "Ball Wins", "key": "Ball Win Removed Opponents", "kind": "defense"},
        {"label": "Def Threat", "key": "Def PXT Active", "kind": "defense"},
        {"label": "xShot Assists", "key": "Expected Shot Assists", "kind": "attack"},
        {"label": "Ball Security", "key": "Ball Security", "kind": "rate"},
    ],
    "Defense": [
        {"label": "Def Threat", "key": "Def PXT Active", "kind": "defense"},
        {"label": "Interceptions", "key": "Interceptions", "kind": "defense"},
        {"label": "Blocks", "key": "Blocks", "kind": "defense"},
        {"label": "Aerial Win %", "key": "Aerial Win %", "kind": "rate"},
        {"label": "Ground Win %", "key": "Ground Win %", "kind": "rate"},
        {"label": "Pass PXT", "key": "Pass PXT", "kind": "attack"},
        {"label": "Restores Shape", "key": "Ball Win Added Defenders", "kind": "defense"},
        {"label": "Ball Security", "key": "Ball Security", "kind": "rate"},
    ],
    "GK": [
        {"label": "Save Actions", "key": "GK Saves", "kind": "defense"},
        {"label": "Claims", "key": "GK Catches", "kind": "defense"},
        {"label": "PSxG Prevented", "key": "PSxG Prevented", "kind": "rate"},
        {"label": "Def Actions", "key": "Keeper Defensive Actions", "kind": "defense"},
        {"label": "Pass PXT", "key": "Pass PXT", "kind": "attack"},
        {"label": "Pass Over Exp.", "key": "Pass Over Expected", "kind": "rate"},
        {"label": "Ball Security", "key": "Ball Security", "kind": "rate"},
    ],
}


# AI-ASSISTED DATA EXTRACTION / PLAYER-EVENT PREPARATION
def _position_bucket(position: str | None) -> str:
    value = position or ""
    if "GOALKEEPER" in value:
        return "GK"
    if "FORWARD" in value or "WINGER" in value:
        return "Forwards"
    if "MIDFIELD" in value:
        return "Midfield"
    if "DEFENDER" in value or "WINGBACK" in value:
        return "Defense"
    return "Midfield"


def _kpi_map(player: dict[str, Any]) -> dict[int, float]:
    values: dict[int, float] = defaultdict(float)
    for item in player.get("kpis", []):
        values[int(item["kpiId"])] += float(item.get("value") or 0.0)
    return values


def _empty_row(
    player_id: int,
    team_id: int,
    position: str | None,
    players: dict[int, dict[str, Any]],
    squads: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "Player ID": player_id,
        "Player": player_name(player_id, players),
        "Team ID": team_id,
        "Team": team_name(team_id, squads),
        "_match_ids": set(),
        "_position_minutes": defaultdict(float),
        "_team_possession_seconds": 0.0,
        "_opponent_possession_seconds": 0.0,
        "Minutes": 0.0,
        "Position": position or "",
        "Position Group": _position_bucket(position),
        "npxG": 0.0,
        "NP Goals": 0.0,
        "Final Third Receptions": 0.0,
        "Passes Ending Final Third": 0.0,
        "Dribbles": 0.0,
        "Successful Dribbles": 0.0,
        "Interceptions": 0.0,
        "Blocks": 0.0,
        "GK Saves": 0.0,
        "GK Catches": 0.0,
        "PSxG Faced": 0.0,
        "Goals Conceded": 0.0,
        "Keeper Defensive Actions": 0.0,
    }
    for key in KPI_MAP_KEYS:
        row[key] = 0.0
    return row


def _add_kpis(row: dict[str, Any], player: dict[str, Any]) -> None:
    values = _kpi_map(player)
    for label, kpi_id in KPI_MAP_KEYS.items():
        row[label] += values[kpi_id]


def _add_events(
    player_rows: dict[tuple[int, int], dict[str, Any]],
    events: list[dict[str, Any]],
    events_kpis: list[dict[str, Any]],
    home_id: int,
    away_id: int,
) -> None:
    xg_by_event = event_kpi_values(events_kpis, KPI_SHOT_XG)
    postshot_xg_by_event = event_kpi_values(events_kpis, 1401)
    goalkeepers = {
        (team_id, player_id): row
        for (team_id, player_id), row in player_rows.items()
        if row["Position Group"] == "GK"
    }
    keepers_by_team = defaultdict(list)
    for (team_id, _player_id), row in goalkeepers.items():
        keepers_by_team[team_id].append(row)

    for event in events:
        team_id_raw = event.get("squadId")
        player_id = event_player_id(event)
        action_type = event.get("actionType")
        action = event.get("action")
        if team_id_raw is None or player_id is None:
            continue
        team_id = int(team_id_raw)
        key = (team_id, player_id)
        row = player_rows.get(key)
        if row is not None:
            if action_type == "SHOT" and action != "PENALTY_KICK":
                row["npxG"] += xg_by_event.get(int(event["id"]), 0.0)
            elif action_type == "GOAL" and action != "PENALTY_KICK":
                row["NP Goals"] += 1
            elif action_type == "RECEPTION":
                start_x = event_coordinate_x(event, "start")
                if start_x is not None and start_x >= 17.5:
                    row["Final Third Receptions"] += 1
            elif action_type == "PASS":
                end_x = event_coordinate_x(event, "end")
                if end_x is not None and end_x >= 17.5:
                    row["Passes Ending Final Third"] += 1
            elif action_type == "DRIBBLE":
                row["Dribbles"] += 1
                if event.get("result") == "SUCCESS":
                    row["Successful Dribbles"] += 1
            elif action_type == "INTERCEPTION":
                row["Interceptions"] += 1
            elif action_type == "BLOCK":
                row["Blocks"] += 1
            elif action_type == "GK_SAVE":
                row["GK Saves"] += 1
                row["Keeper Defensive Actions"] += 1
            elif action_type == "GK_CATCH":
                row["GK Catches"] += 1
                row["Keeper Defensive Actions"] += 1
            elif action_type in {"CLEARANCE", "LOOSE_BALL_REGAIN"} and row["Position Group"] == "GK":
                row["Keeper Defensive Actions"] += 1

        if action_type in {"SHOT", "GOAL"}:
            defending_team = away_id if team_id == home_id else home_id
            active_keepers = keepers_by_team.get(defending_team, [])
            if active_keepers:
                keeper = max(active_keepers, key=lambda item: item["Minutes"])
                keeper["PSxG Faced"] += postshot_xg_by_event.get(int(event["id"]), 0.0)
                if action_type == "GOAL":
                    keeper["Goals Conceded"] += 1


# MATHEMATICAL PLAYER SCORING — AUTHORSHIP TO VERIFY
# This section defines derived rates, opportunity adjustments, and ranks.
def _finalize_row(row: dict[str, Any]) -> dict[str, Any]:
    position_minutes = row.pop("_position_minutes")
    if position_minutes:
        row["Position Group"] = max(position_minutes.items(), key=lambda item: item[1])[0]
    row["Matches"] = len(row.pop("_match_ids"))
    minutes = float(row["Minutes"])
    team_possession_minutes = float(row.pop("_team_possession_seconds") or 0.0)
    opponent_possession_minutes = float(row.pop("_opponent_possession_seconds") or 0.0)
    team_pos = team_possession_minutes / minutes if minutes else 0.5
    opp_pos = opponent_possession_minutes / minutes if minutes else 0.5
    row["Team Possession"] = team_pos
    row["Opponent Possession"] = opp_pos
    row["Dribble Success %"] = (
        row["Successful Dribbles"] / row["Dribbles"] * 100 if row["Dribbles"] else 0.0
    )
    aerial_total = row["Aerial Wins"] + row["Aerial Losses"]
    ground_total = row["Ground Wins"] + row["Ground Losses"]
    passes_total = row["Successful Passes"] + row["Unsuccessful Passes"]
    row["Aerial Win %"] = row["Aerial Wins"] / aerial_total * 100 if aerial_total else 0.0
    row["Ground Win %"] = row["Ground Wins"] / ground_total * 100 if ground_total else 0.0
    row["Ball Security"] = 100 - (row["Dangerous Ball Losses"] / max(1.0, minutes / 90) * 10)
    row["Ball Security"] = max(0.0, min(100.0, row["Ball Security"]))
    row["Pass Over Expected"] = row["Successful Passes"] - row["Expected Passes"]
    row["PSxG Prevented"] = row["PSxG Faced"] - row["Goals Conceded"]
    row["Pass Completion %"] = row["Successful Passes"] / passes_total * 100 if passes_total else 0.0
    return row


def _adjusted_value(row: dict[str, Any], metric: dict[str, Any]) -> float:
    """Convert counts to per-90 and rescale opportunity to 50% possession.

    Attacking metrics are multiplied by 0.5/team-possession share; defensive
    metrics by 0.5/opponent-possession share. The 0.05 floor avoids unstable
    division but is a modelling choice that must be justified by the author.
    """
    key = metric["key"]
    kind = metric.get("kind", "neutral")
    value = float(row.get(key, 0.0))
    if kind == "rate":
        return value
    value = per_90(value, float(row["Minutes"]))
    if kind == "attack":
        return value * 0.5 / max(0.05, float(row["Team Possession"]))
    if kind == "defense":
        return value * 0.5 / max(0.05, float(row["Opponent Possession"]))
    return value


# AI-ASSISTED DATASET ASSEMBLY
@st.cache_data(show_spinner=False)
def build_player_ranking_rows(
    match_ids: tuple[int, ...],
    squads: dict[int, dict[str, Any]],
    players: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: dict[tuple[int, int], dict[str, Any]] = {}

    for match_id in match_ids:
        player_kpis = load_match_player_kpis(match_id)
        events = load_match_events(match_id)
        events_kpis = load_match_events_kpis(match_id)
        home_id = int(player_kpis["squadHome"]["id"])
        away_id = int(player_kpis["squadAway"]["id"])
        possession = attacking_event_shares(events, (home_id, away_id))

        for side_key in ("squadHome", "squadAway"):
            side = player_kpis.get(side_key, {})
            team_id = int(side.get("id", -1))
            if team_id < 0:
                continue
            team_possession = possession.get(team_id, 0.5)
            opponent_possession = 1.0 - team_possession
            for player in side.get("players", []):
                player_id = int(player["id"])
                key = (team_id, player_id)
                row = rows.setdefault(
                    key,
                    _empty_row(player_id, team_id, player.get("position"), players, squads),
                )
                minutes = float(player.get("playDuration") or 0) / 60
                if minutes > 0:
                    row["_match_ids"].add(match_id)
                    group = _position_bucket(player.get("position"))
                    row["_position_minutes"][group] += minutes
                    row["_team_possession_seconds"] += team_possession * minutes
                    row["_opponent_possession_seconds"] += opponent_possession * minutes
                row["Minutes"] += minutes
                _add_kpis(row, player)
        _add_events(rows, events, events_kpis, home_id, away_id)

    final_rows = [_finalize_row(row) for row in rows.values()]
    return final_rows


# MATHEMATICAL POSITION COMPARISON — AUTHORSHIP TO VERIFY
def _score_position_rows(rows: list[dict[str, Any]], position: str, minimum_minutes: int) -> list[dict[str, Any]]:
    config = RADAR_CONFIGS[position]
    eligible = [
        row for row in rows if row["Position Group"] == position and float(row["Minutes"]) >= minimum_minutes
    ]
    metric_values = {
        metric["label"]: [_adjusted_value(row, metric) for row in eligible]
        for metric in config
    }
    scored = []
    for row in eligible:
        copy = dict(row)
        radar_values = []
        raw_values = []
        for metric in config:
            value = _adjusted_value(copy, metric)
            score = percentile_rank(value, metric_values[metric["label"]])
            copy[f"{metric['label']} Score"] = score
            copy[f"{metric['label']} Value"] = round(value, 3)
            radar_values.append(score)
            raw_values.append(value)
        copy["Mean Percentile Rank"] = round(sum(radar_values) / len(radar_values), 1) if radar_values else 0.0
        copy["_radar_values"] = radar_values
        copy["_radar_raw_values"] = raw_values
        scored.append(copy)
    scored.sort(key=lambda row: (-float(row["Mean Percentile Rank"]), row["Player"]))
    for rank, row in enumerate(scored, start=1):
        row["Rank"] = rank
    return scored


# AI-ASSISTED RADAR AND STREAMLIT PRESENTATION
def _radar_svg(player: dict[str, Any], position: str) -> str:
    config = RADAR_CONFIGS[position]
    values = [float(player.get(f"{metric['label']} Score", 0.0)) for metric in config]
    labels = [metric["label"] for metric in config]
    cx = cy = 50.0
    radius = 34.0
    rings = []
    for pct in (20, 40, 60, 80, 100):
        r = radius * pct / 100
        points = []
        for idx in range(len(labels)):
            angle = -math.pi / 2 + 2 * math.pi * idx / len(labels)
            points.append(f"{cx + math.cos(angle) * r:.2f},{cy + math.sin(angle) * r:.2f}")
        rings.append(
            f'<polygon points="{" ".join(points)}" fill="none" stroke="#d8dde3" stroke-width="0.45"/>'
        )
    spokes = []
    label_nodes = []
    value_points = []
    for idx, (label, value) in enumerate(zip(labels, values)):
        angle = -math.pi / 2 + 2 * math.pi * idx / len(labels)
        x = cx + math.cos(angle) * radius
        y = cy + math.sin(angle) * radius
        spokes.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="#e6ebf1" stroke-width="0.45"/>')
        lx = cx + math.cos(angle) * (radius + 9)
        ly = cy + math.sin(angle) * (radius + 9)
        anchor = "middle"
        if lx < cx - 6:
            anchor = "end"
        elif lx > cx + 6:
            anchor = "start"
        label_nodes.append(
            f'<text x="{lx:.2f}" y="{ly:.2f}" text-anchor="{anchor}" fill="#263140" font-size="3.2" font-weight="750">{escape(label)}</text>'
        )
        vr = radius * value / 100
        value_points.append(f"{cx + math.cos(angle) * vr:.2f},{cy + math.sin(angle) * vr:.2f}")

    table_rows = []
    for metric in config:
        label = metric["label"]
        table_rows.append(
            f'<tr><td>{escape(label)}</td><td>{float(player.get(f"{label} Value", 0.0)):.3f}</td><td>{float(player.get(f"{label} Score", 0.0)):.0f}</td></tr>'
        )
    return (
        '<div class="radar-wrap">'
        '<svg viewBox="0 0 100 100" role="img" aria-label="Player radar">'
        f'{"".join(rings + spokes)}'
        f'<polygon points="{" ".join(value_points)}" fill="rgba(199,21,42,0.30)" stroke="#c7152a" stroke-width="1.15"/>'
        f'{"".join(label_nodes)}'
        '<text x="50" y="51.2" text-anchor="middle" fill="#15171a" font-size="4.2" font-weight="900">'
        f'{float(player["Mean Percentile Rank"]):.0f}</text>'
        '</svg>'
        '<table class="radar-values"><thead><tr><th>Metric</th><th>Value</th><th>Rank</th></tr></thead>'
        f'<tbody>{"".join(table_rows)}</tbody></table>'
        '</div>'
    )


def _render_position_table(position: str, rows: list[dict[str, Any]], freiburg_id: int) -> None:
    freiburg_rows = [row for row in rows if int(row["Team ID"]) == int(freiburg_id)]
    display_columns = ["Rank", "Player", "Team", "Minutes", "Mean Percentile Rank"] + [
        f"{metric['label']} Score" for metric in RADAR_CONFIGS[position]
    ]
    st.dataframe(
        [{column: row.get(column, "") for column in display_columns} for row in freiburg_rows],
        hide_index=True,
        width="stretch",
    )
    for row in freiburg_rows:
        with st.expander(f"{row['Player']} radar · {float(row['Mean Percentile Rank']):.1f} mean rank"):
            st.markdown(_radar_svg(row, position), unsafe_allow_html=True)


def render_player_rankings_page(
    freiburg_id: int,
    squads_by_id: dict[int, dict[str, Any]],
    players_by_id: dict[int, dict[str, Any]],
    matches: list[dict[str, Any]],
) -> None:
    st.markdown('<div class="headline-row">', unsafe_allow_html=True)
    st.markdown('<div class="app-kicker">Bundesliga 2023/24 · League-wide comparison</div>', unsafe_allow_html=True)
    st.title("Player Rankings")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        "Players are compared league-wide within their broad position group. Counting metrics are per 90 and "
        "possession-adjusted to a 50% possession environment; rates such as duel win percentage and dribble success "
        "are left as rates. The radar uses percentile ranks, so 100 is best in that position group and 0 is lowest."
    )

    minimum_minutes = st.slider("Minimum minutes", 0, 2500, 450, 90)
    all_rows = build_player_ranking_rows(tuple(int(match["id"]) for match in matches), squads_by_id, players_by_id)

    tabs = st.tabs(["Forwards", "Midfield", "Defense", "GK"])
    for tab, position in zip(tabs, ["Forwards", "Midfield", "Defense", "GK"]):
        with tab:
            scored = _score_position_rows(all_rows, position, minimum_minutes)
            st.markdown(f"**{position} · Freiburg Players**")
            _render_position_table(position, scored, freiburg_id)
