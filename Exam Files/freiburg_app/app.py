from __future__ import annotations

import streamlit as st

from .components import render_sidebar_menu, selected_match_id_from_query, selected_page_from_query
from .config import DATA_ROOT
from .data import load_reference_data
from .home import render_home_page
from .league import render_league_table_page
from .match_details import render_match_details_page
from .matches import load_freiburg_match_summaries
from .player_rankings import render_player_rankings_page
from .styles import apply_styles
from .threat import render_threat_page


def main() -> None:
    apply_styles()

    if not DATA_ROOT.exists():
        st.error(f"Could not find Exam Data at {DATA_ROOT}")
        st.stop()

    squads_by_id, players_by_id, matches = load_reference_data()
    summaries, freiburg_id = load_freiburg_match_summaries()

    if not summaries:
        st.error("No SC Freiburg matches were found in the Exam Data.")
        st.stop()

    if "selected_match_index" not in st.session_state:
        st.session_state.selected_match_index = 0

    query_match_id = selected_match_id_from_query()
    if query_match_id is not None:
        for index, match in enumerate(summaries):
            if int(match["id"]) == query_match_id:
                st.session_state.selected_match_index = index
                break

    selected_index = min(max(int(st.session_state.selected_match_index), 0), len(summaries) - 1)
    page = render_sidebar_menu(selected_page_from_query(), int(summaries[selected_index]["id"]))

    if page == "League Table":
        render_league_table_page(squads_by_id)
        st.stop()

    if page == "Attacking Threat":
        render_threat_page(summaries, freiburg_id, players_by_id, squads_by_id, matches)
        st.stop()

    if page == "Player Rankings":
        render_player_rankings_page(freiburg_id, squads_by_id, players_by_id, matches)
        st.stop()

    if page == "Match Details":
        render_match_details_page(summaries, selected_index, freiburg_id, squads_by_id, players_by_id)
        st.stop()

    render_home_page(summaries, selected_index, freiburg_id, squads_by_id, players_by_id)
