from collections import defaultdict
from typing import Any

import streamlit as st

from .analysis_utils import minmax_score, per_90, percentile_rank
from .config import (
    KPI_DEF_PXT_ATTACK,
    KPI_DEF_PXT_DEFEND,
    KPI_OPP_PXT_BALL_LOSS,
    KPI_OPP_PXT_BLOCK,
    KPI_OPP_PXT_BALL_WIN,
    KPI_OPP_PXT_DRIBBLE,
    KPI_OPP_PXT_FOUL,
    KPI_OPP_PXT_PASS,
    KPI_OPP_PXT_SETPIECE,
    KPI_OPP_PXT_SHOT,
    KPI_PXT_ATTACK,
    KPI_PXT_DEFEND,
    KPI_PXT_REC,
    PLAYER_ATTRIBUTABLE_PXT_KPIS,
)
from .data import load_match_player_kpis, player_name, team_name
from .event_utils import player_kpi_values


ATTACK_SOURCE_KPIS = {label: kpi_id for kpi_id, label in PLAYER_ATTRIBUTABLE_PXT_KPIS.items()}

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

PERCENTILE_SCALE_VERSION = 4


# Data Processing Assistance
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
    }


def _add_player_segment(row: dict[str, Any], player: dict[str, Any], match_id: int) -> None:
    duration = float(player.get("playDuration") or 0) / 60
    position = player.get("position") or ""
    if duration > 0:
        row["_Match IDs"].add(match_id)
        row["_Position Minutes"][_position_group(position)] += duration
        row["_Raw Position Minutes"][position] += duration
    row["Minutes"] += duration

    kpis = player_kpi_values(player)
    row["PXT Attack"] += kpis[KPI_PXT_ATTACK]
    row["PXT Defend"] += kpis[KPI_PXT_DEFEND]
    row["Opponent Threat While Attacking"] += kpis[KPI_DEF_PXT_ATTACK]
    row["Opponent Threat While Defending"] += kpis[KPI_DEF_PXT_DEFEND]
    row["Receiving PXT"] += kpis[KPI_PXT_REC]

    for label, kpi_id in ATTACK_SOURCE_KPIS.items():
        row[label] = row.get(label, 0.0) + kpis[kpi_id]
    for label, kpi_id in OPP_THREAT_KPIS.items():
        row[label] = row.get(label, 0.0) + kpis[kpi_id]


# Extra mathematical methods: project-specific net-threat and interpretation
# rules are listed in README.md and are not Soccermatics formulas.
def _finalize_player_row(row: dict[str, Any]) -> dict[str, Any]:
    # REVIEW NOTE: Net Threat is defined here as Freiburg attacking PxT minus
    # opponent threat generated while Freiburg are attacking. It is a project
    # definition and should not be confused with Impect's raw PXT Attack KPI.
    row["Matches"] = len(row.pop("_Match IDs"))
    position_minutes = row.pop("_Position Minutes")
    raw_position_minutes = row.pop("_Raw Position Minutes")
    if position_minutes:
        row["Position Group"] = max(position_minutes.items(), key=lambda item: item[1])[0]
    if raw_position_minutes:
        row["Position"] = max(raw_position_minutes.items(), key=lambda item: item[1])[0]
    row["Net Threat"] = row["PXT Attack"] - row["Opponent Threat While Attacking"]
    for output, source in {
        "Attack PxT / 90": "PXT Attack",
        "Net / 90": "Net Threat",
        "Receiving PXT / 90": "Receiving PXT",
        "Shot / 90": "Shot",
        "Pass / 90": "Pass",
        "Dribble / 90": "Dribble",
    }.items():
        row[output] = per_90(float(row.get(source, 0.0)), float(row["Minutes"]))
    for key, value in list(row.items()):
        if isinstance(value, float) and key != "Minutes":
            row[key] = round(value, 4)
    return row


def _semantic_band(percentile: float) -> str:
    # REVIEW NOTE: These labels are editorial thresholds, not thresholds supplied
    # by Impect or estimated statistically. They require manual justification.
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


# UI Assistance
def _rank_label(rank: int, total: int) -> str:
    return f"{rank} / {total}"


# Data Processing Assistance
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
    percentile_scale_version: int = PERCENTILE_SCALE_VERSION,
) -> list[dict[str, Any]]:
    _ = percentile_scale_version
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
                kpis = player_kpi_values(player)
                row["PXT Attack"] += kpis[KPI_PXT_ATTACK]
                row["Opponent Threat While Attacking"] += kpis[KPI_DEF_PXT_ATTACK]
                for label in ("Shot", "Pass", "Dribble", "Set Piece"):
                    row[label] += kpis[ATTACK_SOURCE_KPIS[label]]

    rows = []
    for row in team_totals.values():
        matches = len(row.pop("_Match IDs"))
        row["Matches"] = matches
        row["Net Threat"] = row["PXT Attack"] - row["Opponent Threat While Attacking"]
        row["Attack PxT / Match"] = row["PXT Attack"] / matches if matches else 0.0
        row["Net / Match"] = row["Net Threat"] / matches if matches else 0.0
        row["Shot / Match"] = row["Shot"] / matches if matches else 0.0
        row["Pass / Match"] = row["Pass"] / matches if matches else 0.0
        row["Dribble / Match"] = row["Dribble"] / matches if matches else 0.0
        row["Set Piece / Match"] = row["Set Piece"] / matches if matches else 0.0
        for key, value in list(row.items()):
            if isinstance(value, float):
                row[key] = round(value, 4)
        rows.append(row)

    rows.sort(key=lambda item: (-float(item["Attack PxT / Match"]), -float(item["Net / Match"]), item["Team"]))
    for rank, row in enumerate(rows, start=1):
        row["Attack PxT Rank"] = rank
    metric_specs = [
        ("Attack PxT / Match", "Team Attack PxT"),
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
            row[f"{label} Percentile Rank"] = percentile_rank(float(row[metric]), values)
            row[f"{label} Value Score"] = minmax_score(float(row[metric]), values)
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
        pxt_groups[group].append(float(row["Attack PxT / 90"]))
        net_groups[group].append(float(row["Net / 90"]))

    enriched = []
    for row in freiburg_rows:
        copy = dict(row)
        group = copy["Position Group"]
        copy["Attack PxT / 90 Percentile Rank"] = percentile_rank(
            float(copy["Attack PxT / 90"]), pxt_groups[group]
        )
        copy["Attack PxT / 90 Value Score"] = minmax_score(
            float(copy["Attack PxT / 90"]), pxt_groups[group]
        )
        copy["Net / 90 Percentile Rank"] = percentile_rank(float(copy["Net / 90"]), net_groups[group])
        copy["Net / 90 Value Score"] = minmax_score(float(copy["Net / 90"]), net_groups[group])
        copy["Attack PxT / 90 Meaning"] = _semantic_band(
            float(copy["Attack PxT / 90 Percentile Rank"])
        )
        enriched.append(copy)
    return enriched


# UI Assistance
def _render_metric_guide() -> None:
    st.markdown("**How to read attack-phase PxT**")
    st.markdown(
        "Impect's `PXT Attack` KPI measures influence on a team's goal threat while that team is attacking. "
        "Positive attack-phase PxT is good because it increased attacking threat; negative values reduced it. "
        "Per-90 values are usually more "
        "meaningful than raw totals because players have different minutes and positions. Percentile Rank shows "
        "peer standing; Value Score shows distance between the lowest and highest actual PxT values."
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
                "Category": "Receiving PxT",
                "Meaning": "Threat gained by receiving the ball; shown separately to avoid double-counting passer credit.",
                "Positive Means": "The player got into valuable receiving locations.",
            },
            {
                "Category": "Fouled / passive PxT",
                "Meaning": "Attributable threat from being fouled or from responsibility-based off-ball influence.",
                "Positive Means": "The player increased own-team threat without a tagged on-ball action.",
            },
            {
                "Category": "Net Threat",
                "Meaning": "Attack-phase PxT minus opponent threat while Freiburg were attacking.",
                "Positive Means": "Freiburg created threat without giving much transition threat back.",
            },
        ],
        hide_index=True,
        width="stretch",
    )


def _freiburg_category_context(freiburg_team: dict[str, Any], team_count: int) -> list[dict[str, Any]]:
    specs = [
        ("Attack-phase PxT", "Attack PxT / Match", "Team Attack PxT"),
        ("Net Threat", "Net / Match", "Team Net"),
        ("Shot PXT", "Shot / Match", "Shot PXT"),
        ("Pass PXT", "Pass / Match", "Pass PXT"),
        ("Dribble PXT", "Dribble / Match", "Dribble PXT"),
        ("Set Piece PXT", "Set Piece / Match", "Set Piece PXT"),
    ]
    rows = []
    for label, metric, rank_prefix in specs:
        percentile_rank = float(freiburg_team[f"{rank_prefix} Percentile Rank"])
        value_score = float(freiburg_team[f"{rank_prefix} Value Score"])
        rows.append(
            {
                "Metric": label,
                "Freiburg / Match": round(float(freiburg_team[metric]), 3),
                "League Rank": _rank_label(int(freiburg_team[f"{rank_prefix} Rank"]), team_count),
                "Percentile Rank": int(percentile_rank),
                "Value Score": int(value_score),
                "Interpretation": _semantic_band(percentile_rank),
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
    strongest = max(category_rows, key=lambda row: row["Percentile Rank"])
    weakest = min(category_rows, key=lambda row: row["Percentile Rank"])
    top_player = ranked_rows[0] if ranked_rows else None
    bullets = [
        (
            f"Freiburg's attack-phase PxT is {freiburg_team['Attack PxT / Match']:.2f} per match, "
            f"ranking {_rank_label(int(freiburg_team['Team Attack PxT Rank']), team_count)} in the league "
            f"({int(freiburg_team['Team Attack PxT Percentile Rank'])}th percentile rank, "
            f"{int(freiburg_team['Team Attack PxT Value Score'])} value score, "
            f"{_semantic_band(float(freiburg_team['Team Attack PxT Percentile Rank']))})."
        ),
        (
            f"The strongest source relative to the league is {strongest['Metric']} "
            f"({strongest['Percentile Rank']}th percentile rank, {strongest['Value Score']} value score)."
        ),
        (
            f"The weakest source relative to the league is {weakest['Metric']} "
            f"({weakest['Percentile Rank']}th percentile rank, {weakest['Value Score']} value score)."
        ),
    ]
    if top_player:
        bullets.append(
            f"Among Freiburg players meeting the minutes filter, {top_player['Player']} grades highest by "
            f"attack-phase PxT / 90 percentile within his position group "
            f"({int(top_player['Attack PxT / 90 Percentile Rank'])}th percentile rank, "
            f"{int(top_player['Attack PxT / 90 Value Score'])} value score, "
            f"{top_player['Attack PxT / 90 Meaning']})."
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
    team_rows = season_team_threat_rows(all_match_ids, squads_by_id, PERCENTILE_SCALE_VERSION)
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
    metric_cols[0].metric("Attack-phase PxT / match", f"{freiburg_team['Attack PxT / Match']:.2f}")
    metric_cols[1].metric(
        "League rank", _rank_label(int(freiburg_team["Team Attack PxT Rank"]), len(team_rows))
    )
    metric_cols[2].metric("Percentile rank", f"{freiburg_team['Team Attack PxT Percentile Rank']:.0f}")
    metric_cols[3].metric("Net / Match", f"{freiburg_team['Net / Match']:.2f}")

    st.markdown("**Freiburg vs league by threat source**")
    st.dataframe(_freiburg_category_context(freiburg_team, len(team_rows)), hide_index=True, width="stretch")

    with st.expander("Freiburg selected sources", expanded=False):
        source_cols = st.columns(4)
        source_cols[0].metric("Attack-phase PxT", f"{totals['PXT Attack']:.2f}")
        source_cols[1].metric("Net Threat", f"{totals['Net Threat']:.2f}")
        source_cols[2].metric("Shot PXT", f"{totals['Shot']:.2f}")
        source_cols[3].metric("Pass PXT", f"{totals['Pass']:.2f}")

    st.divider()
    ranking_metric = st.selectbox(
        "Rank players by",
        [
            "Attack PxT / 90 Percentile Rank",
            "Attack PxT / 90",
            "Attack PxT / 90 Value Score",
            "Net / 90 Percentile Rank",
            "Net / 90",
            "Net / 90 Value Score",
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
        "Attack PxT / 90 Percentile Rank",
        "Attack PxT / 90 Value Score",
        "Attack PxT / 90 Meaning",
        "Position",
        "Matches",
        "Minutes",
        "PXT Attack",
        "Net Threat",
        "Attack PxT / 90",
        "Net / 90",
        "Net / 90 Percentile Rank",
        "Net / 90 Value Score",
        "Receiving PXT / 90",
        "Shot / 90",
        "Pass / 90",
        "Dribble / 90",
        "Pass",
        "Dribble",
        "Shot",
        "Set Piece",
        "Ball Win",
        "Fouled",
        "Passive",
        "Receiving PXT",
        "Opponent Threat While Attacking",
    ]
    st.dataframe(
        [{column: row.get(column, "") for column in display_columns} for row in ranked_rows],
        hide_index=True,
        width="stretch",
        column_config={"Minutes": st.column_config.NumberColumn("Minutes", format="%.0f")},
    )

    with st.expander("League attack-phase PxT context", expanded=False):
        team_display_columns = [
            "Attack PxT Rank",
            "Team",
            "Matches",
            "PXT Attack",
            "Attack PxT / Match",
            "Team Attack PxT Percentile Rank",
            "Team Attack PxT Value Score",
            "Net Threat",
            "Net / Match",
            "Team Net Percentile Rank",
            "Team Net Value Score",
            "Shot",
            "Shot / Match",
            "Shot PXT Percentile Rank",
            "Shot PXT Value Score",
            "Pass",
            "Pass / Match",
            "Pass PXT Percentile Rank",
            "Pass PXT Value Score",
            "Dribble",
            "Dribble / Match",
            "Dribble PXT Percentile Rank",
            "Dribble PXT Value Score",
            "Set Piece",
            "Set Piece / Match",
            "Set Piece PXT Percentile Rank",
            "Set Piece PXT Value Score",
        ]
        st.dataframe(
            [{column: row.get(column, "") for column in team_display_columns} for row in team_rows],
            hide_index=True,
            width="stretch",
        )

    with st.expander("Metric notes", expanded=False):
        st.markdown(
            "`PXT Attack` is Impect's attacking-phase goal-threat change KPI, not total team PxT. "
            "`Net Threat` subtracts opponent goal-threat change while Freiburg are attacking. "
            "`Percentile Rank` shows peer standing: 100 is the best-ranked value in the comparison group and 0 is "
            "the lowest-ranked value. `Value Score` rescales the actual PxT value between the comparison group's "
            "minimum and maximum, so it shows distance from the top producer. "
            "The player table is sorted by attack-phase PxT / 90 percentile rank by default. "
            "`Receiving PxT` is shown separately because adding it to pass/set-piece PxT can double-count credit."
        )
