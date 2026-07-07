from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from .data import compact_matchday, format_date, squad_logo_url, team_code, team_name


def result_word(code: str) -> str:
    return {"W": "Win", "D": "Draw", "L": "Loss"}.get(code, code)


def query_param_value(name: str) -> str | None:
    if hasattr(st, "query_params"):
        raw_value = st.query_params.get(name)
    else:
        raw_value = st.experimental_get_query_params().get(name)
    if isinstance(raw_value, list):
        raw_value = raw_value[0] if raw_value else None
    return str(raw_value) if raw_value is not None else None


def selected_match_id_from_query() -> int | None:
    raw_value = query_param_value("match_id")
    try:
        return int(raw_value) if raw_value is not None else None
    except (TypeError, ValueError):
        return None


def selected_page_from_query() -> str:
    raw_value = query_param_value("page")
    if raw_value in {"league", "league_table", "table"}:
        return "League Table"
    if raw_value in {"threat", "attacking_threat", "pxt"}:
        return "Attacking Threat"
    return "Home Page"


def render_team_logo(team_id: int, code: str, squads: dict[int, dict[str, Any]]) -> str:
    logo_url = squad_logo_url(team_id, squads)
    if logo_url:
        return f'<img src="{escape(logo_url)}" alt="{escape(code)} logo">'
    return f'<div class="match-card-code">{escape(code)}</div>'


def render_scoreboard_logo(team_id: int, name: str, squads: dict[int, dict[str, Any]]) -> str:
    logo_url = squad_logo_url(team_id, squads)
    if not logo_url:
        return ""
    return f'<img class="scoreboard-logo" src="{escape(logo_url)}" alt="{escape(name)} logo">'


def render_sidebar_menu(current_page: str, selected_match_id: int) -> str:
    home_active = " sidebar-link-active" if current_page == "Home Page" else ""
    table_active = " sidebar-link-active" if current_page == "League Table" else ""
    threat_active = " sidebar-link-active" if current_page == "Attacking Threat" else ""
    home_href = f"./?page=home&match_id={int(selected_match_id)}"

    st.sidebar.markdown(
        '<div class="sidebar-shell">'
        '<div class="sidebar-brand">'
        '<div class="sidebar-badge">SCF</div>'
        '<div>'
        '<div class="sidebar-brand-title">Freiburg Lab</div>'
        '<div class="sidebar-brand-subtitle">Bundesliga match analysis</div>'
        '</div>'
        '</div>'
        '<div class="sidebar-nav">'
        f'<a class="sidebar-link{home_active}" href="{home_href}" target="_self">'
        '<span class="sidebar-link-title">Home Page</span>'
        '<span class="sidebar-link-meta">Matches, lineups, stats</span>'
        '</a>'
        f'<a class="sidebar-link{table_active}" href="./?page=league_table" target="_self">'
        '<span class="sidebar-link-title">League Table</span>'
        '<span class="sidebar-link-meta">Bundesliga standings</span>'
        '</a>'
        f'<a class="sidebar-link{threat_active}" href="./?page=threat" target="_self">'
        '<span class="sidebar-link-title">Attacking Threat</span>'
        '<span class="sidebar-link-meta">Season player pxT ranks</span>'
        '</a>'
        '</div>'
        '<div class="sidebar-footnote">Data: ImpectAPI/open-data</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    return current_page


def render_season_record_card(record: dict[str, int]) -> str:
    return (
        '<div class="summary-card">'
        '<div class="summary-heading">'
        '<div class="summary-label">Season Record</div>'
        f'<div class="summary-value">{record["points"]} pts</div>'
        '</div>'
        '<div class="record-grid">'
        f'<div class="record-item"><div class="record-number">{record["wins"]}</div><div class="record-label">Wins</div></div>'
        f'<div class="record-item"><div class="record-number">{record["draws"]}</div><div class="record-label">Draws</div></div>'
        f'<div class="record-item"><div class="record-number">{record["losses"]}</div><div class="record-label">Losses</div></div>'
        '</div>'
        '</div>'
    )


def render_stat_comparison(rows: list[dict[str, Any]], home_label: str, away_label: str) -> None:
    html = []
    for row in rows:
        html.append(
            f"""
            <div class="stat-row">
                <div class="stat-value">{row[home_label]}</div>
                <div class="stat-name">{row["Stat"]}</div>
                <div class="stat-value align-right">{row[away_label]}</div>
            </div>
            """
        )
    st.markdown("".join(html), unsafe_allow_html=True)


def render_match_strip(
    summaries: list[dict[str, Any]],
    selected_index: int,
    squads: dict[int, dict[str, Any]],
) -> None:
    cards = []
    for index, match in enumerate(summaries):
        home_id = int(match["homeSquadId"])
        away_id = int(match["awaySquadId"])
        home_code = team_code(match["homeName"])
        away_code = team_code(match["awayName"])
        active_class = " match-card-active" if index == selected_index else ""
        result_code = match["freiburgResult"]
        scoreline = f"{match['homeScore']} - {match['awayScore']}"
        href = f"./?page=home&match_id={int(match['id'])}"
        label = (
            f"{team_name(home_id, squads)} {scoreline} {team_name(away_id, squads)}, "
            f"{result_word(result_code)} for Freiburg"
        )
        cards.append(
            f'<a class="match-card{active_class}" href="{href}" target="_self" aria-label="{escape(label)}">'
            '<div class="match-card-meta">'
            f'<span>{escape(compact_matchday(match))}</span>'
            f'<span class="result-pill result-{escape(result_code)}">{escape(result_code)}</span>'
            '</div>'
            '<div class="match-card-score">'
            '<div class="match-card-team">'
            f'{render_team_logo(home_id, home_code, squads)}'
            f'<div class="match-card-code">{escape(home_code)}</div>'
            '</div>'
            f'<div class="match-card-scoreline">{escape(scoreline)}</div>'
            '<div class="match-card-team">'
            f'{render_team_logo(away_id, away_code, squads)}'
            f'<div class="match-card-code">{escape(away_code)}</div>'
            '</div>'
            '</div>'
            '<div class="match-card-footer">'
            f'<span>{escape(format_date(match["scheduledDate"]).split(",", 1)[0])}</span>'
            f'<span>{escape(team_code(match["opponentName"]))}</span>'
            '</div>'
            '</a>'
        )
    st.markdown(f'<div class="match-strip">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_scoreboard(
    selected_match: dict[str, Any],
    home_id: int,
    away_id: int,
    home_name: str,
    away_name: str,
    result_code: str,
    squads: dict[int, dict[str, Any]],
) -> None:
    st.markdown(
        f"""
        <div class="scoreboard">
            <div class="scoreboard-team">
                {render_scoreboard_logo(home_id, home_name, squads)}
                <div class="scoreboard-team-text">
                    <div class="team-name">{home_name}</div>
                    <div class="team-meta">Home · {compact_matchday(selected_match)}</div>
                </div>
            </div>
            <div class="scoreboard-center">
                <div class="scoreline">{selected_match["homeScore"]}-{selected_match["awayScore"]}</div>
                <div class="result-pill result-{result_code}">{result_word(result_code)} for Freiburg</div>
            </div>
            <div class="scoreboard-team scoreboard-team-away">
                <div class="scoreboard-team-text">
                    <div class="team-name">{away_name}</div>
                    <div class="team-meta">Away · {format_date(selected_match["scheduledDate"])}</div>
                </div>
                {render_scoreboard_logo(away_id, away_name, squads)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
