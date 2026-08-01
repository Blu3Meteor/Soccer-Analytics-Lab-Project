from html import escape
from typing import Any

import streamlit as st

from .config import FREIBURG_NAME
from .data import load_reference_data, squad_logo_url
from .matches import load_scored_matches
from .regression import build_regression_outputs


# Data Processing Assistance
@st.cache_data(show_spinner=False)
def build_league_table() -> list[dict[str, Any]]:
    squads, _, _ = load_reference_data()
    table = {
        squad_id: {
            "team_id": squad_id,
            "team": squad["name"],
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0,
        }
        for squad_id, squad in squads.items()
    }

    for match in load_scored_matches():
        home_id = int(match["homeSquadId"])
        away_id = int(match["awaySquadId"])
        home_goals = int(match["homeScore"])
        away_goals = int(match["awayScore"])

        table[home_id]["played"] += 1
        table[away_id]["played"] += 1
        table[home_id]["goals_for"] += home_goals
        table[home_id]["goals_against"] += away_goals
        table[away_id]["goals_for"] += away_goals
        table[away_id]["goals_against"] += home_goals

        if home_goals > away_goals:
            table[home_id]["wins"] += 1
            table[home_id]["points"] += 3
            table[away_id]["losses"] += 1
        elif home_goals < away_goals:
            table[away_id]["wins"] += 1
            table[away_id]["points"] += 3
            table[home_id]["losses"] += 1
        else:
            table[home_id]["draws"] += 1
            table[away_id]["draws"] += 1
            table[home_id]["points"] += 1
            table[away_id]["points"] += 1

    rows = []
    for row in table.values():
        row["goal_difference"] = row["goals_for"] - row["goals_against"]
        rows.append(row)

    rows.sort(
        key=lambda row: (
            -row["points"],
            -row["goal_difference"],
            -row["goals_for"],
            row["team"],
        )
    )
    for position, row in enumerate(rows, start=1):
        row["position"] = position
    return rows


# UI Assistance
def render_league_table_page(squads: dict[int, dict[str, Any]]) -> None:
    rows = build_league_table()
    regression = build_regression_outputs()
    model_by_team = regression["table"]
    model_rank_by_team = {
        team: index
        for index, (team, _) in enumerate(
            sorted(
                model_by_team.items(),
                key=lambda item: (
                    -item[1]["expected_points"],
                    -item[1]["expected_goal_difference"],
                    -item[1]["expected_goals_for"],
                    item[0],
                ),
            ),
            start=1,
        )
    }
    st.markdown('<div class="headline-row">', unsafe_allow_html=True)
    st.markdown('<div class="app-kicker">Bundesliga 2023/24 · League Table</div>', unsafe_allow_html=True)
    st.title("League Table")
    st.markdown("</div>", unsafe_allow_html=True)

    model = regression["model"]
    st.markdown(
        '<div class="model-summary">'
        '<div><span>Regression model</span><strong>goals ~ home + team + opponent</strong></div>'
        f'<div><span>Home coefficient</span><strong>{model["home_advantage"]:+.3f}</strong></div>'
        f'<div><span>Baseline club</span><strong>{escape(FREIBURG_NAME)} (reference)</strong></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Regression coefficients", expanded=False):
        st.caption(
            "Attack is the club-specific scoring lift relative to the baseline club. "
            "Concede is the club-specific defensive effect relative to the baseline club, so lower values mean a stronger defense. "
            "Because SC Freiburg is the baseline here, Freiburg is 0.00 by construction and every other club is measured against it. "
            "GD is actual goal difference from the results table."
        )
        st.dataframe(regression["coefficients"], hide_index=True, width="stretch")

    html_rows = []
    for row in rows:
        team_id = int(row["team_id"])
        model_row = model_by_team.get(
            row["team"],
            {
                "expected_points": 0.0,
                "attack_coefficient": 0.0,
                "concede_coefficient": 0.0,
            },
        )
        logo_url = squad_logo_url(team_id, squads)
        logo_html = (
            f'<img class="league-table-logo" src="{escape(logo_url)}" alt="{escape(row["team"])} logo">'
            if logo_url
            else ""
        )
        row_class = "league-table-freiburg" if row["team"] == FREIBURG_NAME else ""
        html_rows.append(
            f'<tr class="{row_class}">'
            f'<td>{row["position"]}</td>'
            '<td>'
            '<div class="league-table-club">'
            f'{logo_html}<span>{escape(row["team"])}</span>'
            '</div></td>'
            f'<td>{row["played"]}</td>'
            f'<td>{row["wins"]}</td>'
            f'<td>{row["draws"]}</td>'
            f'<td>{row["losses"]}</td>'
            f'<td>{row["goals_for"]}</td>'
            f'<td>{row["goals_against"]}</td>'
            f'<td>{row["goal_difference"]:+d}</td>'
            f'<td class="league-table-points">{row["points"]}</td>'
            f'<td class="league-table-model">{model_rank_by_team.get(row["team"], "")}</td>'
            f'<td class="league-table-model">{model_row["expected_points"]:.1f}</td>'
            f'<td class="league-table-model">{model_row["attack_coefficient"]:+.2f}</td>'
            f'<td class="league-table-model">{model_row["concede_coefficient"]:+.2f}</td>'
            '</tr>'
        )

    st.markdown(
        '<div class="league-table-wrap">'
        '<table class="league-table">'
        '<thead><tr>'
        '<th>#</th><th>Club</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th>'
        '<th>Model Rank</th><th>Expected Pts</th><th>Attack</th><th>Concede</th>'
        '</tr></thead>'
        f'<tbody>{"".join(html_rows)}</tbody>'
        '</table>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Model Rank = clubs ordered by expected points from the regression model; "
        "Expected Pts = in-sample model-based points for the supplied fixtures; "
        "Attack = scoring strength, where higher is better; Concede = defensive strength, where lower is better."
    )
