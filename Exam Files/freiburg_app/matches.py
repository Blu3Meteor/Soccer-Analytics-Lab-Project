from __future__ import annotations

from typing import Any

import streamlit as st

from .config import FREIBURG_NAME
from .data import load_match_events, load_reference_data, team_name
from .metrics import compute_score, opposition_team, result_code_for_freiburg


@st.cache_data(show_spinner=False)
def load_freiburg_match_summaries() -> tuple[list[dict[str, Any]], int]:
    squads, _, matches = load_reference_data()
    freiburg = next(squad for squad in squads.values() if squad.get("name") == FREIBURG_NAME)
    freiburg_id = int(freiburg["id"])
    freiburg_matches = [
        match
        for match in matches
        if int(match["homeSquadId"]) == freiburg_id or int(match["awaySquadId"]) == freiburg_id
    ]
    freiburg_matches.sort(key=lambda match: match["scheduledDate"])

    summaries = []
    for match in freiburg_matches:
        events = load_match_events(int(match["id"]))
        home_id = int(match["homeSquadId"])
        away_id = int(match["awaySquadId"])
        score = compute_score(events, home_id, away_id)
        result_code = result_code_for_freiburg(match, score, freiburg_id)
        opponent_id = opposition_team(match, freiburg_id)
        summaries.append(
            {
                **match,
                "homeName": team_name(home_id, squads),
                "awayName": team_name(away_id, squads),
                "homeScore": score[home_id],
                "awayScore": score[away_id],
                "freiburgResult": result_code,
                "opponentName": team_name(opponent_id, squads),
            }
        )
    return summaries, freiburg_id
