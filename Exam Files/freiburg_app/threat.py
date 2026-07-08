from __future__ import annotations

from collections import defaultdict
from typing import Any

import streamlit as st

from .config import (
    KPI_DEF_PXT_ATTACK,
    KPI_DEF_PXT_DEFEND,
    KPI_OPP_PXT_BALL_LOSS,
    KPI_OPP_PXT_BLOCK,
    KPI_OPP_PXT_BALL_WIN,
    KPI_OPP_PXT_DRIBBLE,
    KPI_OPP_PXT_FOUL,
    KPI_OPP_PXT_NO_VIDEO,
    KPI_OPP_PXT_PASS,
    KPI_OPP_PXT_SETPIECE,
    KPI_OPP_PXT_SHOT,
    KPI_PXT_ATTACK,
    KPI_PXT_BALL_WIN,
    KPI_PXT_BLOCK,
    KPI_PXT_DEFEND,
    KPI_PXT_DRIBBLE,
    KPI_PXT_FOUL,
    KPI_PXT_NO_VIDEO,
    KPI_PXT_PASS,
    KPI_PXT_REC,
    KPI_PXT_SETPIECE,
    KPI_PXT_SHOT,
)
from .data import load_match_player_kpis, player_name, team_name


ATTACK_SOURCE_KPIS = {
    "Pass": KPI_PXT_PASS,
    "Dribble": KPI_PXT_DRIBBLE,
    "Set Piece": KPI_PXT_SETPIECE,
    "Block": KPI_PXT_BLOCK,
    "Shot": KPI_PXT_SHOT,
    "Ball Win": KPI_PXT_BALL_WIN,
    "Foul": KPI_PXT_FOUL,
}

OPP_THREAT_KPIS = {
    "Opp Pass": KPI_OPP_PXT_PASS,
    "Opp Dribble": KPI_OPP_PXT_DRIBBLE,
    "Opp Set Piece": KPI_OPP_PXT_SETPIECE,
    "Opp Block": KPI_OPP_PXT_BLOCK,
    "Opp Shot": KPI_OPP_PXT_SHOT,
    "Opp Ball Win": KPI_OPP_PXT_BALL_WIN,
    "Opp Foul": KPI_OPP_PXT_FOUL,
    "Opp Ball Loss": KPI_OPP_PXT_BALL_LOSS,
}


def _player_kpi_map(player: dict[str, Any]) -> dict[int, float]:
    totals: dict[int, float] = defaultdict(float)
    for kpi in player.get("kpis", []):
        totals[int(kpi["kpiId"])] += float(kpi.get("value") or 0)
    return totals


def _position_group(position: str | None) -> str:
    value = position or ""
    if "GOALKEEPER" in value:
        return "GK"
    if "FORWARD" in value or "WINGER" in value:
        return "Attack"
    if "MIDFIELD" in value:
        return "Midfield"
    if "DEFENDER" in value or "WINGBACK" in value:
        return "Defense"
    return "Unknown"


def _empty_player_row(
    player_id: int,
    team_id: int,
    position: str | None,
    players_by_id: dict[int, dict[str, Any]],
    squads_by_id: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "Player": player_name(player_id, players_by_id),
        "Player ID": player_id,
        "Team": team_name(team_id, squads_by_id),
        "Team ID": team_id,
        "Position": position or "",
        "Position Group": _position_group(position),
        "_Match IDs": set(),
        "_Position Minutes": defaultdict(float),
        "_Raw Position Minutes": defaultdict(float),
        "Matches": 0,
        "Minutes": 0.0,
        "PXT Attack": 0.0,
        "PXT Defend": 0.0,
        "Opponent Threat While Attacking": 0.0,
        "Opponent Threat While Defending": 0.0,
        "Net Threat": 0.0,
        "Receiving PXT": 0.0,
        "No Video PXT": 0.0,
        "Opponent No Video PXT": 0.0,
    }


def _add_player_segment(row: dict[str, Any], player: dict[str, Any], match_id: int) -> None:
    duration = float(player.get("playDuration") or 0) / 60
    position = player.get("position") or ""
    if duration > 0:
        row["_Match IDs"].add(match_id)
        row["_Position Minutes"][_position_group(position)] += duration
        row["_Raw Position Minutes"][position] += duration
    row["Minutes"] += duration

    kpis = _player_kpi_map(player)
    row["PXT Attack"] += kpis[KPI_PXT_ATTACK]
    row["PXT Defend"] += kpis[KPI_PXT_DEFEND]
    row["Opponent Threat While Attacking"] += kpis[KPI_DEF_PXT_ATTACK]
    row["Opponent Threat While Defending"] += kpis[KPI_DEF_PXT_DEFEND]
    row["Receiving PXT"] += kpis[KPI_PXT_REC]
    row["No Video PXT"] += kpis[KPI_PXT_NO_VIDEO]
    row["Opponent No Video PXT"] += kpis[KPI_OPP_PXT_NO_VIDEO]

    for label, kpi_id in ATTACK_SOURCE_KPIS.items():
        row[label] = row.get(label, 0.0) + kpis[kpi_id]
    for label, kpi_id in OPP_THREAT_KPIS.items():
        row[label] = row.get(label, 0.0) + kpis[kpi_id]


def _finalize_player_row(row: dict[str, Any]) -> dict[str, Any]:
    row["Matches"] = len(row.pop("_Match IDs"))
    position_minutes = row.pop("_Position Minutes")
    raw_position_minutes = row.pop("_Raw Position Minutes")
    if position_minutes:
        row["Position Group"] = max(position_minutes.items(), key=lambda item: item[1])[0]
    if raw_position_minutes:
        row["Position"] = max(raw_position_minutes.items(), key=lambda item: item[1])[0]
    row["Net Threat"] = row["PXT Attack"] - row["Opponent Threat While Attacking"]
    row["PXT / 90"] = (row["PXT Attack"] / row["Minutes"] * 90) if row["Minutes"] else 0.0
    row["Net / 90"] = (row["Net Threat"] / row["Minutes"] * 90) if row["Minutes"] else 0.0
    row["Receiving PXT / 90"] = (row["Receiving PXT"] / row["Minutes"] * 90) if row["Minutes"] else 0.0
    row["Shot / 90"] = (row.get("Shot", 0.0) / row["Minutes"] * 90) if row["Minutes"] else 0.0
    row["Pass / 90"] = (row.get("Pass", 0.0) / row["Minutes"] * 90) if row["Minutes"] else 0.0
    row["Dribble / 90"] = (row.get("Dribble", 0.0) / row["Minutes"] * 90) if row["Minutes"] else 0.0
    row["Minutes"] = round(row["Minutes"], 0)
    for key, value in list(row.items()):
        if isinstance(value, float) and key != "Minutes":
            row[key] = round(value, 4)
    return row


def _percentile(value: float, values: list[float]) -> float:
    if not values:
        return 0.0
    below = sum(1 for item in values if item < value)
    equal = sum(1 for item in values if item == value)
    return round(((below + (0.5 * equal)) / len(values)) * 100, 0)


def _semantic_band(percentile: float) -> str:
    if percentile >= 80:
        return "elite"
    if percentile >= 65:
        return "strong"
    if percentile >= 55:
        return "above average"
    if percentile >= 45:
        return "around average"
    if percentile >= 30:
        return "below average"
    return "weak"


def _rank_label(rank: int, total: int) -> str:
    return f"{rank} / {total}"


@st.cache_data(show_spinner=False)
def season_player_threat_rows(
    match_ids: tuple[int, ...],
    players_by_id: dict[int, dict[str, Any]],
    squads_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    player_totals: dict[tuple[int, int], dict[str, Any]] = {}

    for match_id in match_ids:
        player_kpis = load_match_player_kpis(match_id)
        for side_key in ("squadHome", "squadAway"):
            side = player_kpis.get(side_key, {})
            team_id = int(side.get("id", -1))
            if team_id < 0:
                continue
            for player in side.get("players", []):
                player_id = int(player["id"])
                key = (team_id, player_id)
                row = player_totals.setdefault(
                    key,
                    _empty_player_row(player_id, team_id, player.get("position"), players_by_id, squads_by_id),
                )
                _add_player_segment(row, player, match_id)

    rows = [_finalize_player_row(row) for row in player_totals.values()]
    rows.sort(key=lambda item: (-float(item["PXT Attack"]), -float(item["Net Threat"]), item["Player"]))
    for rank, row in enumerate(rows, start=1):
        row["Rank"] = rank
    return rows


@st.cache_data(show_spinner=False)
def season_team_threat_rows(
    match_ids: tuple[int, ...],
    squads_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    team_totals: dict[int, dict[str, Any]] = {}

    for match_id in match_ids:
        player_kpis = load_match_player_kpis(match_id)
        for side_key in ("squadHome", "squadAway"):
            side = player_kpis.get(side_key, {})
            team_id = int(side.get("id", -1))
            if team_id < 0:
                continue
            row = team_totals.setdefault(
                team_id,
                {
                    "Team": team_name(team_id, squads_by_id),
                    "Team ID": team_id,
                    "_Match IDs": set(),
                    "PXT Attack": 0.0,
                    "Opponent Threat While Attacking": 0.0,
                    "Net Threat": 0.0,
                    "Shot": 0.0,
                    "Pass": 0.0,
                    "Dribble": 0.0,
                    "Set Piece": 0.0,
                },
            )
            row["_Match IDs"].add(match_id)
            for player in side.get("players", []):
                kpis = _player_kpi_map(player)
                row["PXT Attack"] += kpis[KPI_PXT_ATTACK]
                row["Opponent Threat While Attacking"] += kpis[KPI_DEF_PXT_ATTACK]
                row["Shot"] += kpis[KPI_PXT_SHOT]
                row["Pass"] += kpis[KPI_PXT_PASS]
                row["Dribble"] += kpis[KPI_PXT_DRIBBLE]
                row["Set Piece"] += kpis[KPI_PXT_SETPIECE]

    rows = []
    for row in team_totals.values():
        matches = len(row.pop("_Match IDs"))
        row["Matches"] = matches
        row["Net Threat"] = row["PXT Attack"] - row["Opponent Threat While Attacking"]
        row["PXT / Match"] = row["PXT Attack"] / matches if matches else 0.0
        row["Net / Match"] = row["Net Threat"] / matches if matches else 0.0
        row["Shot / Match"] = row["Shot"] / matches if matches else 0.0
        row["Pass / Match"] = row["Pass"] / matches if matches else 0.0
        row["Dribble / Match"] = row["Dribble"] / matches if matches else 0.0
        row["Set Piece / Match"] = row["Set Piece"] / matches if matches else 0.0
        for key, value in list(row.items()):
            if isinstance(value, float):
                row[key] = round(value, 4)
        rows.append(row)

    rows.sort(key=lambda item: (-float(item["PXT / Match"]), -float(item["Net / Match"]), item["Team"]))
    for rank, row in enumerate(rows, start=1):
        row["PXT Rank"] = rank
    metric_specs = [
        ("PXT / Match", "Team PXT"),
        ("Net / Match", "Team Net"),
        ("Shot / Match", "Shot PXT"),
        ("Pass / Match", "Pass PXT"),
        ("Dribble / Match", "Dribble PXT"),
        ("Set Piece / Match", "Set Piece PXT"),
    ]
    for metric, label in metric_specs:
        values = [float(row[metric]) for row in rows]
        ranked = sorted(rows, key=lambda item: (-float(item[metric]), item["Team"]))
        for rank, row in enumerate(ranked, start=1):
            row[f"{label} Rank"] = rank
            row[f"{label} Percentile"] = _percentile(float(row[metric]), values)
    return rows


def _summary_totals(rows: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "PXT Attack": sum(float(row["PXT Attack"]) for row in rows),
        "Net Threat": sum(float(row["Net Threat"]) for row in rows),
        "Shot": sum(float(row.get("Shot", 0)) for row in rows),
        "Pass": sum(float(row.get("Pass", 0)) for row in rows),
    }


def _add_position_percentiles(
    freiburg_rows: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    minimum_minutes: int,
) -> list[dict[str, Any]]:
    eligible = [row for row in all_rows if float(row["Minutes"]) >= minimum_minutes]
    pxt_groups: dict[str, list[float]] = defaultdict(list)
    net_groups: dict[str, list[float]] = defaultdict(list)
    for row in eligible:
        group = row["Position Group"]
        pxt_groups[group].append(float(row["PXT / 90"]))
        net_groups[group].append(float(row["Net / 90"]))

    enriched = []
    for row in freiburg_rows:
        copy = dict(row)
        group = copy["Position Group"]
        copy["PXT / 90 Percentile"] = _percentile(float(copy["PXT / 90"]), pxt_groups[group])
        copy["Net / 90 Percentile"] = _percentile(float(copy["Net / 90"]), net_groups[group])
        copy["PXT / 90 Meaning"] = _semantic_band(float(copy["PXT / 90 Percentile"]))
        enriched.append(copy)
    return enriched


def _render_metric_guide() -> None:
    st.markdown("**How To Read PXT**")
    st.markdown(
        "PXT estimates how much an action changes the chance that the team will eventually score. "
        "Positive own-team PXT is good because the action moved the team into a more threatening state. "
        "Negative own-team PXT is bad because the action reduced attacking threat. Per-90 and percentile views "
        "are usually more meaningful than raw totals because players have different minutes and positions."
    )
    st.dataframe(
        [
            {
                "Category": "Pass",
                "Meaning": "Threat created or lost through passes.",
                "Positive Means": "Passes moved Freiburg into more dangerous possessions.",
            },
            {
                "Category": "Dribble",
                "Meaning": "Threat created or lost through carries and dribbles.",
                "Positive Means": "Ball carrying advanced or protected attacking threat.",
            },
            {
                "Category": "Shot",
                "Meaning": "Threat change from shots, including post-shot value where available.",
                "Positive Means": "Shot quality/outcome improved the expected scoring state.",
            },
            {
                "Category": "Set Piece",
                "Meaning": "Threat created or lost from corners, free kicks, throw-ins, goal kicks, and kick-offs.",
                "Positive Means": "Set-piece situations increased attacking threat.",
            },
            {
                "Category": "Receiving PXT",
                "Meaning": "Threat gained by receiving the ball; shown separately to avoid double-counting passer credit.",
                "Positive Means": "The player got into valuable receiving locations.",
            },
            {
                "Category": "Net Threat",
                "Meaning": "Own PXT minus opponent threat while Freiburg were attacking.",
                "Positive Means": "Freiburg created threat without giving much transition threat back.",
            },
        ],
        hide_index=True,
        width="stretch",
    )


def _freiburg_category_context(freiburg_team: dict[str, Any], team_count: int) -> list[dict[str, Any]]:
    specs = [
        ("Overall PXT", "PXT / Match", "Team PXT"),
        ("Net Threat", "Net / Match", "Team Net"),
        ("Shot PXT", "Shot / Match", "Shot PXT"),
        ("Pass PXT", "Pass / Match", "Pass PXT"),
        ("Dribble PXT", "Dribble / Match", "Dribble PXT"),
        ("Set Piece PXT", "Set Piece / Match", "Set Piece PXT"),
    ]
    rows = []
    for label, metric, rank_prefix in specs:
        percentile = float(freiburg_team[f"{rank_prefix} Percentile"])
        rows.append(
            {
                "Metric": label,
                "Freiburg / Match": round(float(freiburg_team[metric]), 3),
                "League Rank": _rank_label(int(freiburg_team[f"{rank_prefix} Rank"]), team_count),
                "Percentile": int(percentile),
                "Interpretation": _semantic_band(percentile),
            }
        )
    return rows


def _render_inferences(
    freiburg_team: dict[str, Any],
    team_rows: list[dict[str, Any]],
    ranked_rows: list[dict[str, Any]],
) -> None:
    team_count = len(team_rows)
    category_rows = _freiburg_category_context(freiburg_team, team_count)
    strongest = max(category_rows, key=lambda row: row["Percentile"])
    weakest = min(category_rows, key=lambda row: row["Percentile"])
    top_player = ranked_rows[0] if ranked_rows else None
    bullets = [
        (
            f"Freiburg's overall attacking PXT is {freiburg_team['PXT / Match']:.2f} per match, "
            f"ranking {_rank_label(int(freiburg_team['Team PXT Rank']), team_count)} in the league "
            f"({int(freiburg_team['Team PXT Percentile'])}th percentile, "
            f"{_semantic_band(float(freiburg_team['Team PXT Percentile']))})."
        ),
        (
            f"The strongest source relative to the league is {strongest['Metric']} "
            f"({strongest['Percentile']}th percentile)."
        ),
        (
            f"The weakest source relative to the league is {weakest['Metric']} "
            f"({weakest['Percentile']}th percentile)."
        ),
    ]
    if top_player:
        bullets.append(
            f"Among Freiburg players meeting the minutes filter, {top_player['Player']} grades highest by "
            f"PXT / 90 percentile within his position group "
            f"({int(top_player['PXT / 90 Percentile'])}th percentile, {top_player['PXT / 90 Meaning']})."
        )
    st.markdown("**What This Suggests**")
    st.markdown("\n".join(f"- {item}" for item in bullets))


def render_threat_page(
    summaries: list[dict[str, Any]],
    freiburg_id: int,
    players_by_id: dict[int, dict[str, Any]],
    squads_by_id: dict[int, dict[str, Any]],
    matches: list[dict[str, Any]],
) -> None:
    all_match_ids = tuple(int(match["id"]) for match in matches)
    all_player_rows = season_player_threat_rows(all_match_ids, players_by_id, squads_by_id)
    team_rows = season_team_threat_rows(all_match_ids, squads_by_id)
    freiburg_rows = [row for row in all_player_rows if int(row["Team ID"]) == int(freiburg_id)]
    totals = _summary_totals(freiburg_rows)
    freiburg_team = next(row for row in team_rows if int(row["Team ID"]) == int(freiburg_id))

    st.markdown('<div class="headline-row">', unsafe_allow_html=True)
    st.markdown('<div class="app-kicker">Bundesliga 2023/24 · SC Freiburg</div>', unsafe_allow_html=True)
    st.title("Attacking Threat")
    st.markdown("</div>", unsafe_allow_html=True)

    _render_metric_guide()
    st.divider()

    metric_cols = st.columns(4)
    metric_cols[0].metric("Team PXT / Match", f"{freiburg_team['PXT / Match']:.2f}")
    metric_cols[1].metric("League Rank", _rank_label(int(freiburg_team["Team PXT Rank"]), len(team_rows)))
    metric_cols[2].metric("Team Percentile", f"{freiburg_team['Team PXT Percentile']:.0f}")
    metric_cols[3].metric("Net / Match", f"{freiburg_team['Net / Match']:.2f}")

    st.markdown("**Freiburg vs League By Threat Source**")
    st.dataframe(_freiburg_category_context(freiburg_team, len(team_rows)), hide_index=True, width="stretch")

    with st.expander("Freiburg total sources", expanded=False):
        source_cols = st.columns(4)
        source_cols[0].metric("Total PXT Attack", f"{totals['PXT Attack']:.2f}")
        source_cols[1].metric("Net Threat", f"{totals['Net Threat']:.2f}")
        source_cols[2].metric("Shot PXT", f"{totals['Shot']:.2f}")
        source_cols[3].metric("Pass PXT", f"{totals['Pass']:.2f}")

    st.divider()
    ranking_metric = st.selectbox(
        "Rank players by",
        [
            "PXT / 90 Percentile",
            "PXT / 90",
            "Net / 90 Percentile",
            "Net / 90",
            "Receiving PXT / 90",
            "Shot / 90",
            "Pass / 90",
            "Dribble / 90",
            "PXT Attack",
            "Net Threat",
            "Receiving PXT",
            "Shot",
            "Pass",
            "Dribble",
        ],
        index=0,
    )
    minimum_minutes = st.slider("Minimum minutes", 0, 2500, 450, 90)

    ranked_rows = [
        row
        for row in _add_position_percentiles(freiburg_rows, all_player_rows, minimum_minutes)
        if float(row["Minutes"]) >= minimum_minutes
    ]
    ranked_rows.sort(key=lambda item: (-float(item[ranking_metric]), item["Player"]))
    for rank, row in enumerate(ranked_rows, start=1):
        row["Rank"] = rank

    top_chart_rows = [{"Player": row["Player"], ranking_metric: row[ranking_metric]} for row in ranked_rows[:12]]
    if top_chart_rows:
        st.bar_chart(top_chart_rows, x="Player", y=ranking_metric)

    _render_inferences(freiburg_team, team_rows, ranked_rows)

    display_columns = [
        "Rank",
        "Player",
        "Position Group",
        "PXT / 90 Percentile",
        "PXT / 90 Meaning",
        "Position",
        "Matches",
        "Minutes",
        "PXT Attack",
        "Net Threat",
        "PXT / 90",
        "Net / 90",
        "Net / 90 Percentile",
        "Receiving PXT / 90",
        "Shot / 90",
        "Pass / 90",
        "Dribble / 90",
        "Pass",
        "Dribble",
        "Shot",
        "Set Piece",
        "Ball Win",
        "Receiving PXT",
        "Opponent Threat While Attacking",
    ]
    st.dataframe(
        [{column: row.get(column, "") for column in display_columns} for row in ranked_rows],
        hide_index=True,
        width="stretch",
    )

    with st.expander("League team PXT context", expanded=False):
        team_display_columns = [
            "PXT Rank",
            "Team",
            "Matches",
            "PXT Attack",
            "PXT / Match",
            "Team PXT Percentile",
            "Net Threat",
            "Net / Match",
            "Team Net Percentile",
            "Shot",
            "Shot / Match",
            "Shot PXT Percentile",
            "Pass",
            "Pass / Match",
            "Pass PXT Percentile",
            "Dribble",
            "Dribble / Match",
            "Dribble PXT Percentile",
            "Set Piece",
            "Set Piece / Match",
            "Set Piece PXT Percentile",
        ]
        st.dataframe(
            [{column: row.get(column, "") for column in team_display_columns} for row in team_rows],
            hide_index=True,
            width="stretch",
        )

    with st.expander("Metric notes", expanded=False):
        st.markdown(
            "`PXT Attack` is Impect's own attacking-phase goal-threat change KPI. "
            "`Net Threat` subtracts opponent goal-threat change while Freiburg are attacking. "
            "`Team Percentile` compares Freiburg's team PXT per match against the other Bundesliga teams. "
            "`PXT / 90 Percentile` compares each Freiburg player to all league players in the same position group "
            "who meet the selected minimum-minutes filter. "
            "The player table is sorted by PXT / 90 percentile by default, so the ranking answers how strong a player "
            "is against comparable league players rather than only how large the raw number is. "
            "`Receiving PXT` is shown separately because adding it to pass/set-piece PXT can double-count credit."
        )
