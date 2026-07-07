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
from .data import load_match_player_kpis, player_name


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


def _freiburg_side(player_kpis: dict[str, Any], freiburg_id: int) -> dict[str, Any] | None:
    for key in ("squadHome", "squadAway"):
        side = player_kpis.get(key, {})
        if int(side.get("id", -1)) == int(freiburg_id):
            return side
    return None


def _player_kpi_map(player: dict[str, Any]) -> dict[int, float]:
    totals: dict[int, float] = defaultdict(float)
    for kpi in player.get("kpis", []):
        totals[int(kpi["kpiId"])] += float(kpi.get("value") or 0)
    return totals


@st.cache_data(show_spinner=False)
def season_player_threat_rows(
    match_ids: tuple[int, ...],
    freiburg_id: int,
    players_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    player_totals: dict[int, dict[str, Any]] = {}

    for match_id in match_ids:
        side = _freiburg_side(load_match_player_kpis(match_id), freiburg_id)
        if not side:
            continue

        for player in side.get("players", []):
            player_id = int(player["id"])
            row = player_totals.setdefault(
                player_id,
                {
                    "Player": player_name(player_id, players_by_id),
                    "Player ID": player_id,
                    "Position": player.get("position", ""),
                    "_Match IDs": set(),
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
                },
            )

            duration = float(player.get("playDuration") or 0)
            if duration > 0:
                row["_Match IDs"].add(match_id)
            row["Minutes"] += duration / 60

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

    rows = []
    for row in player_totals.values():
        row["Matches"] = len(row.pop("_Match IDs"))
        row["Net Threat"] = row["PXT Attack"] - row["Opponent Threat While Attacking"]
        row["PXT / 90"] = (row["PXT Attack"] / row["Minutes"] * 90) if row["Minutes"] else 0.0
        row["Net / 90"] = (row["Net Threat"] / row["Minutes"] * 90) if row["Minutes"] else 0.0
        row["Minutes"] = round(row["Minutes"], 0)
        for key, value in list(row.items()):
            if isinstance(value, float) and key != "Minutes":
                row[key] = round(value, 4)
        rows.append(row)

    rows.sort(key=lambda item: (-float(item["PXT Attack"]), -float(item["Net Threat"]), item["Player"]))
    for rank, row in enumerate(rows, start=1):
        row["Rank"] = rank
    return rows


def _summary_totals(rows: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "PXT Attack": sum(float(row["PXT Attack"]) for row in rows),
        "Net Threat": sum(float(row["Net Threat"]) for row in rows),
        "Shot": sum(float(row.get("Shot", 0)) for row in rows),
        "Pass": sum(float(row.get("Pass", 0)) for row in rows),
    }


def render_threat_page(
    summaries: list[dict[str, Any]],
    freiburg_id: int,
    players_by_id: dict[int, dict[str, Any]],
) -> None:
    match_ids = tuple(int(match["id"]) for match in summaries)
    rows = season_player_threat_rows(match_ids, freiburg_id, players_by_id)
    totals = _summary_totals(rows)

    st.markdown('<div class="headline-row">', unsafe_allow_html=True)
    st.markdown('<div class="app-kicker">Bundesliga 2023/24 · SC Freiburg</div>', unsafe_allow_html=True)
    st.title("Attacking Threat")
    st.markdown("</div>", unsafe_allow_html=True)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Total PXT Attack", f"{totals['PXT Attack']:.2f}")
    metric_cols[1].metric("Net Threat", f"{totals['Net Threat']:.2f}")
    metric_cols[2].metric("Shot PXT", f"{totals['Shot']:.2f}")
    metric_cols[3].metric("Pass PXT", f"{totals['Pass']:.2f}")

    st.divider()
    ranking_metric = st.selectbox(
        "Rank players by",
        ["PXT / 90", "Net / 90", "Receiving PXT", "PXT Attack", "Net Threat", "Shot", "Pass", "Dribble"],
        index=0,
    )
    minimum_minutes = st.slider("Minimum minutes", 0, 2500, 450, 90)

    ranked_rows = [row for row in rows if float(row["Minutes"]) >= minimum_minutes]
    ranked_rows.sort(key=lambda item: (-float(item[ranking_metric]), item["Player"]))
    for rank, row in enumerate(ranked_rows, start=1):
        row["Rank"] = rank

    top_chart_rows = [
        {"Player": row["Player"], ranking_metric: row[ranking_metric]}
        for row in ranked_rows[:12]
    ]
    if top_chart_rows:
        st.bar_chart(top_chart_rows, x="Player", y=ranking_metric)

    display_columns = [
        "Rank",
        "Player",
        "Position",
        "Matches",
        "Minutes",
        "PXT Attack",
        "Net Threat",
        "PXT / 90",
        "Net / 90",
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

    with st.expander("Metric notes", expanded=False):
        st.markdown(
            "`PXT Attack` is Impect's own attacking-phase goal-threat change KPI. "
            "`Net Threat` subtracts opponent goal-threat change while Freiburg are attacking. "
            "`Receiving PXT` is shown separately because adding it to pass/set-piece PXT can double-count credit."
        )
