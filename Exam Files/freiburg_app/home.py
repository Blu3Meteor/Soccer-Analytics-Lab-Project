from __future__ import annotations

from typing import Any

import streamlit as st

from .components import (
    render_match_strip,
    render_scoreboard,
    render_season_record_card,
    render_stat_comparison,
)
from .data import (
    load_match_events,
    load_match_events_kpis,
    load_match_lineups,
    load_match_player_kpis,
    short_team_name,
    team_name,
)
from .events import card_events, scoring_events, shot_events
from .lineups import lineup_for_team, render_lineup_panel
from .metrics import compute_stats, opposition_team, points_progression, season_record, shot_xg_by_event, stat_rows


def render_home_page(
    summaries: list[dict[str, Any]],
    selected_index: int,
    freiburg_id: int,
    squads_by_id: dict[int, dict[str, Any]],
    players_by_id: dict[int, dict[str, Any]],
) -> None:
    record = season_record(summaries)
    points_chart_data = points_progression(summaries)

    st.markdown('<div class="headline-row">', unsafe_allow_html=True)
    left, right = st.columns([0.74, 0.26])
    with left:
        st.markdown('<div class="app-kicker">Bundesliga 2023/24 · Impect Exam Data</div>', unsafe_allow_html=True)
        st.title("SC Freiburg Match Dashboard")
    with right:
        st.markdown(render_season_record_card(record), unsafe_allow_html=True)
        with st.expander("Points progression", expanded=False):
            st.line_chart(points_chart_data, x="Game", y="Points")
    st.markdown("</div>", unsafe_allow_html=True)

    render_match_strip(summaries, selected_index, squads_by_id)

    selected_match = summaries[selected_index]
    events = load_match_events(int(selected_match["id"]))
    events_kpis = load_match_events_kpis(int(selected_match["id"]))
    lineups = load_match_lineups(int(selected_match["id"]))
    player_kpis = load_match_player_kpis(int(selected_match["id"]))

    home_id = int(selected_match["homeSquadId"])
    away_id = int(selected_match["awaySquadId"])
    home_name = selected_match["homeName"]
    away_name = selected_match["awayName"]
    home_short = short_team_name(home_name)
    away_short = short_team_name(away_name)
    result_code = selected_match["freiburgResult"]
    xg_by_event = shot_xg_by_event(events_kpis)
    stats = compute_stats(selected_match, events, player_kpis, events_kpis)
    rows = stat_rows(stats, home_id, away_id, home_name, away_name)
    goals = scoring_events(events, selected_match, players_by_id, squads_by_id)

    st.divider()
    with st.container(border=True):
        render_scoreboard(selected_match, home_id, away_id, home_name, away_name, result_code, squads_by_id)
        st.markdown(
            f'<a class="detail-link" href="./?page=match_details&match_id={int(selected_match["id"])}" target="_self">'
            'Open Advanced Match Details</a>',
            unsafe_allow_html=True,
        )

        overview_tab, lineup_tab, stats_tab, events_tab = st.tabs(["Overview", "Lineups", "Stats", "Events"])

        with overview_tab:
            overview_cols = st.columns(4)
            freiburg_goals = stats[freiburg_id]["shots"]
            opponent_id = opposition_team(selected_match, freiburg_id)
            overview_cols[0].metric("Freiburg Shots", int(freiburg_goals))
            overview_cols[1].metric("Freiburg Pass Accuracy", f"{stats[freiburg_id]['pass_accuracy']:.1f}%")
            overview_cols[2].metric("Freiburg Possession", f"{stats[freiburg_id]['possession']}%")
            overview_cols[3].metric("Opponent", short_team_name(team_name(opponent_id, squads_by_id)))

            st.markdown("**Scoring**")
            if goals:
                st.dataframe(goals, hide_index=True, width="stretch")
            else:
                st.caption("No goals recorded.")

        with lineup_tab:
            lineup_columns = st.columns(2)
            with lineup_columns[0]:
                render_lineup_panel(home_name, lineup_for_team(lineups, home_id), players_by_id)
            with lineup_columns[1]:
                render_lineup_panel(away_name, lineup_for_team(lineups, away_id), players_by_id)

        with stats_tab:
            render_stat_comparison(rows, home_short, away_short)

        with events_tab:
            event_cols = st.columns(2)
            with event_cols[0]:
                st.markdown("**Goals**")
                if goals:
                    st.dataframe(goals, hide_index=True, width="stretch")
                else:
                    st.caption("No goals recorded.")
            with event_cols[1]:
                cards = card_events(events, players_by_id, squads_by_id)
                st.markdown("**Cards**")
                if cards:
                    st.dataframe(cards, hide_index=True, width="stretch")
                else:
                    st.caption("No card events recorded.")

            with st.expander("Shots", expanded=False):
                st.dataframe(shot_events(events, players_by_id, squads_by_id, xg_by_event), hide_index=True, width="stretch")
