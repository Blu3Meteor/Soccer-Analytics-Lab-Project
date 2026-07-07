from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DATA_ROOT = BASE_DIR.parent / "Exam Data" / "open-data" / "data"
ITERATION_ID = 743
FREIBURG_NAME = "SC Freiburg"
BERLIN_TZ = ZoneInfo("Europe/Berlin")

KPI_RED_CARD = 47
KPI_SUCCESSFUL_PASSES = 90
KPI_UNSUCCESSFUL_PASSES = 91
KPI_SHOTS = 100
KPI_NEUTRAL_PASSES = 1431
KPI_SHOTS_ON_TARGET = 1515
KPI_YELLOW_CARD = 1637
KPI_SECOND_YELLOW_CARD = 1638


st.set_page_config(
    page_title="SC Freiburg Match Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
    :root {
        --freiburg-red: #c7152a;
        --ink: #15171a;
        --soft-border: #d8dde3;
        --muted: #667085;
        --panel: #ffffff;
        --wash: #f5f7f9;
    }

    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2.5rem;
    }

    [data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e3e7ed;
    }

    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding: 1.15rem 0.85rem;
    }

    .sidebar-shell {
        display: grid;
        gap: 0.85rem;
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding: 0.2rem 0.1rem 0.85rem;
        border-bottom: 1px solid #e3e7ed;
    }

    .sidebar-badge {
        display: grid;
        place-items: center;
        width: 42px;
        height: 42px;
        border-radius: 8px;
        background: var(--freiburg-red);
        color: #ffffff;
        font-size: 0.8rem;
        font-weight: 950;
    }

    .sidebar-brand-title {
        color: var(--ink);
        font-size: 1rem;
        font-weight: 900;
        line-height: 1.1;
    }

    .sidebar-brand-subtitle {
        color: var(--muted);
        font-size: 0.73rem;
        font-weight: 750;
        margin-top: 0.12rem;
    }

    .sidebar-nav {
        display: grid;
        gap: 0.55rem;
    }

    .sidebar-link {
        display: grid;
        gap: 0.12rem;
        padding: 0.72rem 0.78rem;
        border: 1px solid #e1e7ef;
        border-radius: 8px;
        background: #ffffff;
        color: var(--ink) !important;
        text-decoration: none !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    .sidebar-link:hover {
        border-color: var(--freiburg-red);
        background: #fff7f8;
    }

    .sidebar-link-active {
        border-color: var(--freiburg-red);
        background: #fff3f5;
        box-shadow: inset 3px 0 0 var(--freiburg-red);
    }

    .sidebar-link-title {
        color: var(--ink);
        font-size: 0.95rem;
        font-weight: 880;
        line-height: 1.15;
    }

    .sidebar-link-meta {
        color: var(--muted);
        font-size: 0.74rem;
        font-weight: 720;
    }

    .sidebar-footnote {
        border-top: 1px solid #e3e7ed;
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 700;
        padding: 0.75rem 0.12rem 0;
    }

    h1, h2, h3 {
        letter-spacing: 0;
    }

    .app-kicker {
        color: var(--freiburg-red);
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }

    .headline-row {
        border-bottom: 1px solid var(--soft-border);
        padding-bottom: 1rem;
        margin-bottom: 1rem;
    }

    .summary-card {
        border: 1px solid var(--soft-border);
        border-radius: 8px;
        padding: 0.85rem 1rem;
        background: var(--panel);
        min-height: 104px;
    }

    .summary-heading {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: 0.75rem;
    }

    .summary-label {
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .summary-value {
        color: var(--ink);
        font-size: 1.45rem;
        font-weight: 800;
        white-space: nowrap;
    }

    .record-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.42rem;
        margin-top: 0.65rem;
    }

    .record-item {
        border: 1px solid #edf0f3;
        border-radius: 6px;
        padding: 0.42rem 0.35rem;
        text-align: center;
        background: #fafbfc;
    }

    .record-number {
        color: var(--ink);
        font-size: 1.08rem;
        font-weight: 900;
        line-height: 1;
    }

    .record-label {
        color: var(--muted);
        font-size: 0.66rem;
        font-weight: 800;
        margin-top: 0.15rem;
        text-transform: uppercase;
    }

    div.stButton > button {
        border: 1px solid var(--soft-border);
        border-radius: 8px;
        min-height: 96px;
        white-space: pre-line;
        text-align: left;
        padding: 0.65rem 0.7rem;
        color: var(--ink);
        background: #ffffff;
        box-shadow: none;
    }

    div.stButton > button:hover {
        border-color: var(--freiburg-red);
        color: var(--ink);
    }

    div.stButton > button[kind="primary"] {
        background: var(--freiburg-red);
        color: white;
        border-color: var(--freiburg-red);
    }

    .match-strip {
        display: flex;
        gap: 0.8rem;
        overflow-x: auto;
        overscroll-behavior-x: contain;
        scroll-snap-type: x proximity;
        padding: 0.15rem 0 0.9rem;
        margin: 0.1rem 0 0.65rem;
    }

    .match-strip::-webkit-scrollbar {
        height: 10px;
    }

    .match-strip::-webkit-scrollbar-track {
        background: #edf0f3;
        border-radius: 999px;
    }

    .match-strip::-webkit-scrollbar-thumb {
        background: #aeb7c2;
        border-radius: 999px;
    }

    .match-card {
        flex: 0 0 236px;
        scroll-snap-align: start;
        display: grid;
        grid-template-rows: auto 1fr auto;
        gap: 0.45rem;
        min-height: 124px;
        border: 1px solid var(--soft-border);
        border-radius: 8px;
        padding: 0.7rem;
        background: #ffffff;
        color: var(--ink);
        text-decoration: none;
    }

    .match-card:hover {
        border-color: var(--freiburg-red);
        box-shadow: 0 10px 24px rgba(21, 23, 26, 0.08);
    }

    .match-card-active {
        border-color: var(--freiburg-red);
        box-shadow: inset 0 0 0 2px var(--freiburg-red);
    }

    .match-card-meta {
        display: flex;
        justify-content: space-between;
        color: var(--muted);
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
    }

    .match-card-meta .result-pill {
        margin-top: 0;
        padding: 0.12rem 0.45rem;
        font-size: 0.68rem;
    }

    .match-card-score {
        display: grid;
        grid-template-columns: minmax(54px, 1fr) auto minmax(54px, 1fr);
        align-items: center;
        gap: 0.45rem;
    }

    .match-card-team {
        display: grid;
        justify-items: center;
        gap: 0.25rem;
        min-width: 0;
    }

    .match-card-team img {
        width: 34px;
        height: 34px;
        object-fit: contain;
    }

    .match-card-code {
        font-size: 0.84rem;
        font-weight: 900;
        overflow-wrap: anywhere;
    }

    .match-card-scoreline {
        min-width: 62px;
        text-align: center;
        font-size: 1.3rem;
        font-weight: 950;
        line-height: 1;
    }

    .match-card-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 800;
    }

    .scoreboard {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
        align-items: center;
        gap: 1rem;
        border: 1px solid var(--soft-border);
        border-radius: 8px;
        padding: 1.1rem;
        background: var(--panel);
    }

    .team-name {
        font-size: clamp(1.05rem, 2vw, 1.45rem);
        font-weight: 800;
        overflow-wrap: anywhere;
    }

    .scoreboard-team {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        min-width: 0;
    }

    .scoreboard-team-away {
        justify-content: flex-end;
    }

    .scoreboard-team-away .scoreboard-team-text {
        text-align: right;
    }

    .scoreboard-logo {
        width: 58px;
        height: 58px;
        object-fit: contain;
        flex: 0 0 58px;
    }

    .scoreboard-center {
        display: grid;
        justify-items: center;
        text-align: center;
    }

    .team-meta {
        color: var(--muted);
        font-size: 0.85rem;
        margin-top: 0.15rem;
    }

    .scoreline {
        min-width: 132px;
        text-align: center;
        color: var(--ink);
        font-size: clamp(2rem, 5vw, 3.2rem);
        font-weight: 900;
        line-height: 1;
    }

    .result-pill {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.25rem 0.55rem;
        margin-top: 0.45rem;
        background: var(--wash);
        color: var(--ink);
        font-size: 0.78rem;
        font-weight: 800;
    }

    .result-W {
        background: #e7f6ee;
        color: #087443;
    }

    .result-D {
        background: #fff4dc;
        color: #9a5b00;
    }

    .result-L {
        background: #ffe8e8;
        color: #b42318;
    }

    .stat-row {
        display: grid;
        grid-template-columns: minmax(72px, 0.35fr) minmax(110px, 0.3fr) minmax(72px, 0.35fr);
        gap: 0.75rem;
        align-items: center;
        border-bottom: 1px solid #edf0f3;
        padding: 0.65rem 0;
    }

    .stat-row:last-child {
        border-bottom: 0;
    }

    .stat-value {
        font-size: 1.02rem;
        font-weight: 850;
    }

    .stat-name {
        color: var(--muted);
        font-size: 0.86rem;
        font-weight: 750;
        text-align: center;
    }

    .align-right {
        text-align: right;
    }

    .event-chip {
        display: inline-block;
        border: 1px solid var(--soft-border);
        border-radius: 999px;
        padding: 0.14rem 0.5rem;
        margin-right: 0.25rem;
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 700;
    }

    .league-table-wrap {
        border: 1px solid var(--soft-border);
        border-radius: 8px;
        overflow: hidden;
        background: #ffffff;
    }

    .league-table {
        width: 100%;
        border-collapse: collapse;
    }

    .league-table th {
        background: #f5f7f9;
        color: var(--muted);
        font-size: 0.74rem;
        font-weight: 850;
        padding: 0.62rem 0.65rem;
        text-align: right;
        text-transform: uppercase;
    }

    .league-table th:nth-child(2) {
        text-align: left;
    }

    .league-table td {
        border-top: 1px solid #edf0f3;
        color: var(--ink);
        font-size: 0.88rem;
        font-weight: 700;
        padding: 0.62rem 0.65rem;
        text-align: right;
    }

    .league-table td:nth-child(2) {
        text-align: left;
    }

    .league-table-club {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        min-width: 0;
    }

    .league-table-logo {
        width: 26px;
        height: 26px;
        object-fit: contain;
        flex: 0 0 26px;
    }

    .league-table-freiburg td {
        background: #fff3f5;
        color: #8f1020;
    }

    .league-table-points {
        font-weight: 950;
    }

    .lineup-pitch {
        position: relative;
        width: 100%;
        max-width: 560px;
        aspect-ratio: 72 / 100;
        min-height: 520px;
        margin: 0.4rem auto 1rem;
        overflow: hidden;
        border: 2px solid rgba(255, 255, 255, 0.9);
        border-radius: 8px;
        background:
            linear-gradient(rgba(255,255,255,0.16) 2px, transparent 2px) 0 50% / 100% 2px no-repeat,
            linear-gradient(90deg, rgba(255,255,255,0.12), rgba(255,255,255,0.12)) 0 0 / 100% 100%,
            repeating-linear-gradient(
                90deg,
                #2f8f53 0,
                #2f8f53 13%,
                #2b844d 13%,
                #2b844d 26%
            );
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
    }

    .lineup-pitch::before,
    .lineup-pitch::after {
        content: "";
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        border: 2px solid rgba(255, 255, 255, 0.72);
        pointer-events: none;
    }

    .lineup-pitch::before {
        top: -2px;
        width: 58%;
        height: 15%;
        border-top: 0;
    }

    .lineup-pitch::after {
        bottom: -2px;
        width: 58%;
        height: 15%;
        border-bottom: 0;
    }

    .pitch-center-circle {
        position: absolute;
        left: 50%;
        top: 50%;
        width: 26%;
        aspect-ratio: 1;
        transform: translate(-50%, -50%);
        border: 2px solid rgba(255, 255, 255, 0.72);
        border-radius: 50%;
    }

    .player-marker {
        position: absolute;
        display: grid;
        justify-items: center;
        gap: 0.18rem;
        width: 76px;
        transform: translate(-50%, -50%);
        color: #ffffff;
        text-align: center;
    }

    .player-shirt {
        display: grid;
        place-items: center;
        width: 34px;
        height: 34px;
        border: 2px solid rgba(255, 255, 255, 0.95);
        border-radius: 50%;
        background: var(--freiburg-red);
        color: #ffffff;
        font-size: 0.86rem;
        font-weight: 900;
        box-shadow: 0 3px 9px rgba(0, 0, 0, 0.28);
    }

    .player-name {
        max-width: 76px;
        padding: 0.08rem 0.28rem;
        border-radius: 4px;
        background: rgba(21, 23, 26, 0.68);
        font-size: 0.68rem;
        font-weight: 800;
        line-height: 1.1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .lineup-note {
        color: var(--muted);
        font-size: 0.78rem;
        margin: -0.25rem 0 0.6rem;
        text-align: center;
    }

    @media (max-width: 700px) {
        .scoreboard {
            grid-template-columns: 1fr;
            text-align: center;
        }

        .scoreline {
            min-width: 0;
        }

        .scoreboard-team,
        .scoreboard-team-away {
            justify-content: center;
        }

        .scoreboard-team-away .scoreboard-team-text {
            text-align: center;
        }

        .stat-row {
            grid-template-columns: 1fr;
            text-align: center;
            gap: 0.15rem;
        }

        .align-right {
            text-align: center;
        }

        .lineup-pitch {
            min-height: 460px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_json(relative_path: str) -> Any:
    path = DATA_ROOT / relative_path
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_reference_data() -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]], list[dict[str, Any]]]:
    squads = load_json(f"squads/squads_{ITERATION_ID}.json")
    players = load_json(f"players/players_{ITERATION_ID}.json")
    matches = load_json(f"matches/matches_{ITERATION_ID}.json")
    return (
        {int(squad["id"]): squad for squad in squads},
        {int(player["id"]): player for player in players},
        matches,
    )


@st.cache_data(show_spinner=False)
def load_match_events(match_id: int) -> list[dict[str, Any]]:
    return load_json(f"events/events_{match_id}.json")


@st.cache_data(show_spinner=False)
def load_match_lineups(match_id: int) -> dict[str, Any]:
    return load_json(f"lineups/lineups_{match_id}.json")


@st.cache_data(show_spinner=False)
def load_match_player_kpis(match_id: int) -> dict[str, Any]:
    return load_json(f"player_kpis/player_kpis_{match_id}.json")


def team_name(team_id: int, squads: dict[int, dict[str, Any]]) -> str:
    return squads.get(int(team_id), {}).get("name", f"Team {team_id}")


def short_team_name(name: str) -> str:
    replacements = {
        "Bayer 04 Leverkusen": "Leverkusen",
        "FC Bayern München": "Bayern",
        "Borussia Dortmund": "Dortmund",
        "Borussia Mönchengladbach": "Gladbach",
        "Eintracht Frankfurt": "Frankfurt",
        "TSG 1899 Hoffenheim": "Hoffenheim",
        "1. FC Heidenheim 1846": "Heidenheim",
        "SV Werder Bremen": "Bremen",
        "VfL Wolfsburg": "Wolfsburg",
        "1. FSV Mainz 05": "Mainz",
        "1. FC Köln": "Köln",
        "FC Augsburg": "Augsburg",
        "VfB Stuttgart": "Stuttgart",
        "VfL Bochum 1848": "Bochum",
        "SV Darmstadt 98": "Darmstadt",
        "RB Leipzig": "Leipzig",
        "SC Freiburg": "Freiburg",
        "1. FC Union Berlin": "Union",
    }
    return replacements.get(name, name)


def team_code(name: str) -> str:
    replacements = {
        "Bayer 04 Leverkusen": "B04",
        "FC Bayern München": "FCB",
        "Borussia Dortmund": "BVB",
        "Borussia Mönchengladbach": "BMG",
        "Eintracht Frankfurt": "SGE",
        "TSG 1899 Hoffenheim": "TSG",
        "1. FC Heidenheim 1846": "FCH",
        "SV Werder Bremen": "SVW",
        "VfL Wolfsburg": "WOB",
        "1. FSV Mainz 05": "M05",
        "1. FC Köln": "KOE",
        "FC Augsburg": "FCA",
        "VfB Stuttgart": "VFB",
        "VfL Bochum 1848": "BOC",
        "SV Darmstadt 98": "SVD",
        "RB Leipzig": "RBL",
        "SC Freiburg": "SCF",
        "1. FC Union Berlin": "FCU",
    }
    if name in replacements:
        return replacements[name]
    compact = "".join(part[0] for part in name.replace(".", " ").split() if part[:1].isalpha())
    return compact[:3].upper() or name[:3].upper()


def squad_logo_url(team_id: int, squads: dict[int, dict[str, Any]]) -> str:
    return squads.get(int(team_id), {}).get("imageUrl", "")


def player_name(player_id: int | None, players: dict[int, dict[str, Any]]) -> str:
    if player_id is None:
        return "Unknown"
    player = players.get(int(player_id), {})
    return (
        player.get("commonname")
        or " ".join(part for part in [player.get("firstname"), player.get("lastname")] if part)
        or f"Player {player_id}"
    )


def format_position(value: str | None) -> str:
    if not value:
        return ""
    if value == "BANK":
        return "Bench"
    if value == "UNKNOWN":
        return ""
    return value.replace("_", " ").title()


def format_date(value: str) -> str:
    date = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(BERLIN_TZ)
    return date.strftime("%d %b %Y, %H:%M")


def compact_matchday(match: dict[str, Any]) -> str:
    matchday = match.get("matchDay", {})
    index = matchday.get("index")
    if index is None:
        return matchday.get("name", "")
    return f"MD {int(index) + 1}"


def clock_label(game_time: dict[str, Any] | str | None) -> str:
    if isinstance(game_time, dict):
        raw = game_time.get("gameTime", "")
    else:
        raw = game_time or ""
    if not raw:
        return ""
    return raw.replace(".0000", "").replace("(+", "+").replace(")", "")


def minute_label(game_time: dict[str, Any] | str | None) -> str:
    raw = clock_label(game_time)
    if not raw:
        return ""
    main = raw.split()[0]
    try:
        minute = int(main.split(":")[0])
    except (TypeError, ValueError):
        return raw
    if "+" in raw:
        added = raw.split("+", 1)[1].split(":", 1)[0]
        return f"{minute}+{int(added)}'"
    return f"{minute}'"


def opposition_team(match: dict[str, Any], team_id: int) -> int:
    if int(match["homeSquadId"]) == int(team_id):
        return int(match["awaySquadId"])
    return int(match["homeSquadId"])


def compute_score(events: list[dict[str, Any]], home_id: int, away_id: int) -> dict[int, int]:
    score = {int(home_id): 0, int(away_id): 0}
    for event in events:
        action_type = event.get("actionType")
        squad_id = event.get("squadId")
        if squad_id not in score:
            continue
        if action_type == "GOAL":
            score[int(squad_id)] += 1
        elif action_type == "OWN_GOAL":
            other_id = int(away_id) if int(squad_id) == int(home_id) else int(home_id)
            score[other_id] += 1
    return score


@st.cache_data(show_spinner=False)
def build_league_table() -> list[dict[str, Any]]:
    squads, _, matches = load_reference_data()
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

    for match in matches:
        home_id = int(match["homeSquadId"])
        away_id = int(match["awaySquadId"])
        events = load_match_events(int(match["id"]))
        score = compute_score(events, home_id, away_id)
        home_goals = score[home_id]
        away_goals = score[away_id]

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


def result_code_for_freiburg(match: dict[str, Any], score: dict[int, int], freiburg_id: int) -> str:
    opponent_id = opposition_team(match, freiburg_id)
    freiburg_goals = score.get(int(freiburg_id), 0)
    opponent_goals = score.get(opponent_id, 0)
    if freiburg_goals > opponent_goals:
        return "W"
    if freiburg_goals < opponent_goals:
        return "L"
    return "D"


def aggregate_kpis_for_team(player_kpis: dict[str, Any], team_id: int) -> dict[int, float]:
    side = None
    for key in ("squadHome", "squadAway"):
        if int(player_kpis.get(key, {}).get("id", -1)) == int(team_id):
            side = player_kpis[key]
            break
    totals: dict[int, float] = defaultdict(float)
    if not side:
        return totals
    for player in side.get("players", []):
        for kpi in player.get("kpis", []):
            totals[int(kpi["kpiId"])] += float(kpi.get("value") or 0)
    return totals


def compute_possession(events: list[dict[str, Any]], team_ids: tuple[int, int]) -> dict[int, int]:
    counts = Counter()
    ignored = {"FINAL_WHISTLE", "NO_VIDEO"}
    for event in events:
        attacking_team = event.get("currentAttackingSquadId")
        if attacking_team in team_ids and event.get("actionType") not in ignored:
            counts[int(attacking_team)] += 1
    total = sum(counts.values())
    if total == 0:
        return {team_ids[0]: 50, team_ids[1]: 50}
    first = int(round((counts[team_ids[0]] / total) * 100))
    return {team_ids[0]: first, team_ids[1]: max(0, 100 - first)}


def compute_stats(
    match: dict[str, Any],
    events: list[dict[str, Any]],
    player_kpis: dict[str, Any],
) -> dict[int, dict[str, Any]]:
    home_id = int(match["homeSquadId"])
    away_id = int(match["awaySquadId"])
    team_ids = (home_id, away_id)
    stats: dict[int, dict[str, Any]] = {team_id: defaultdict(float) for team_id in team_ids}
    possession = compute_possession(events, team_ids)

    for team_id in team_ids:
        kpis = aggregate_kpis_for_team(player_kpis, team_id)
        successful_passes = kpis[KPI_SUCCESSFUL_PASSES]
        unsuccessful_passes = kpis[KPI_UNSUCCESSFUL_PASSES]
        neutral_passes = kpis[KPI_NEUTRAL_PASSES]
        total_passes = successful_passes + unsuccessful_passes + neutral_passes
        stats[team_id]["shots"] = int(round(kpis[KPI_SHOTS]))
        stats[team_id]["shots_on_target"] = int(round(kpis[KPI_SHOTS_ON_TARGET]))
        stats[team_id]["passes"] = int(round(total_passes))
        stats[team_id]["pass_accuracy"] = round((successful_passes / total_passes) * 100, 1) if total_passes else 0
        second_yellow_cards = int(round(kpis[KPI_SECOND_YELLOW_CARD]))
        stats[team_id]["yellow_cards"] = int(round(kpis[KPI_YELLOW_CARD])) + second_yellow_cards
        stats[team_id]["second_yellow_cards"] = int(round(kpis[KPI_SECOND_YELLOW_CARD]))
        stats[team_id]["red_cards"] = int(round(kpis[KPI_RED_CARD])) + second_yellow_cards
        stats[team_id]["possession"] = possession[team_id]

    for event in events:
        squad_id = event.get("squadId")
        if squad_id not in team_ids:
            continue
        action_type = event.get("actionType")
        if action_type == "FOUL":
            stats[int(squad_id)]["fouls"] += 1
        elif action_type == "OFFSIDE":
            stats[int(squad_id)]["offsides"] += 1
        elif action_type == "CORNER":
            stats[int(squad_id)]["corners"] += 1

    return stats


def scoring_events(
    events: list[dict[str, Any]],
    match: dict[str, Any],
    players: dict[int, dict[str, Any]],
    squads: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    home_id = int(match["homeSquadId"])
    away_id = int(match["awaySquadId"])
    rows = []
    for event in events:
        action_type = event.get("actionType")
        if action_type not in {"GOAL", "OWN_GOAL"}:
            continue
        squad_id = int(event.get("squadId"))
        if action_type == "OWN_GOAL":
            scoring_team = away_id if squad_id == home_id else home_id
            note = f"Own goal by {player_name(event.get('player', {}).get('id'), players)}"
        else:
            scoring_team = squad_id
            note = player_name(event.get("player", {}).get("id"), players)
        rows.append(
            {
                "Time": minute_label(event.get("gameTime")),
                "Team": short_team_name(team_name(scoring_team, squads)),
                "Scorer": note,
                "Type": "Own Goal" if action_type == "OWN_GOAL" else "Goal",
            }
        )
    return rows


def card_events(
    events: list[dict[str, Any]],
    players: dict[int, dict[str, Any]],
    squads: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    card_types = {"YELLOW_CARD", "SECOND_YELLOW_CARD", "RED_CARD"}
    for event in events:
        if event.get("actionType") not in card_types:
            continue
        rows.append(
            {
                "Time": minute_label(event.get("gameTime")),
                "Team": short_team_name(team_name(int(event["squadId"]), squads)),
                "Player": player_name(event.get("player", {}).get("id"), players),
                "Card": format_position(event.get("actionType")),
            }
        )
    return rows


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


def lineup_for_team(lineups: dict[str, Any], team_id: int) -> dict[str, Any]:
    for key in ("squadHome", "squadAway"):
        squad = lineups.get(key, {})
        if int(squad.get("id", -1)) == int(team_id):
            return squad
    return {}


def lineup_rows(
    lineup: dict[str, Any],
    players: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    shirts = {int(player["id"]): player.get("shirtNumber") for player in lineup.get("players", [])}
    rows = []
    for position in lineup.get("startingPositions", []):
        player_id = int(position["playerId"])
        rows.append(
            {
                "#": shirts.get(player_id, ""),
                "Player": player_name(player_id, players),
                "Position": format_position(position.get("position")),
                "Side": format_position(position.get("positionSide")),
            }
        )
    return rows


def shirt_numbers(lineup: dict[str, Any]) -> dict[int, Any]:
    return {int(player["id"]): player.get("shirtNumber") for player in lineup.get("players", [])}


def player_display_name(player_id: int, players: dict[int, dict[str, Any]]) -> str:
    name = player_name(player_id, players)
    if len(name) <= 13:
        return name
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name[:12]


def position_depth(position: str | None) -> float:
    position = position or ""
    if position == "GOALKEEPER":
        return 90
    if "WINGBACK_DEFENDER" in position:
        return 66
    if "DEFENDER" in position or "FULLBACK" in position:
        return 74
    if position == "DEFENSE_MIDFIELD":
        return 58
    if "MIDFIELD" in position:
        return 45
    if "WINGER" in position:
        return 30
    if "FORWARD" in position or "STRIKER" in position:
        return 17
    return 50


def position_width(position_side: str | None) -> float:
    position_side = position_side or ""
    side_map = {
        "LEFT": 18,
        "CENTRE_LEFT": 38,
        "CENTER_LEFT": 38,
        "CENTRE": 50,
        "CENTER": 50,
        "CENTRE_RIGHT": 62,
        "CENTER_RIGHT": 62,
        "RIGHT": 82,
    }
    return side_map.get(position_side, 50)


def marker_color(title: str) -> str:
    return "#c7152a" if title == FREIBURG_NAME else "#1f4d78"


def lineup_marker_positions(lineup: dict[str, Any]) -> list[dict[str, Any]]:
    base_markers = []
    for position in lineup.get("startingPositions", []):
        base_markers.append(
            {
                "player_id": int(position["playerId"]),
                "x": position_width(position.get("positionSide")),
                "y": position_depth(position.get("position")),
                "position": position.get("position"),
                "side": position.get("positionSide"),
            }
        )

    grouped: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for marker in base_markers:
        grouped[(round(marker["x"]), round(marker["y"]))].append(marker)

    for group in grouped.values():
        if len(group) == 1:
            continue
        total = len(group)
        for index, marker in enumerate(group):
            offset = index - (total - 1) / 2
            marker["x"] = min(92, max(8, marker["x"] + offset * 8))

    return base_markers


def render_lineup_pitch(
    title: str,
    lineup: dict[str, Any],
    players: dict[int, dict[str, Any]],
) -> None:
    shirts = shirt_numbers(lineup)
    markers = []
    color = marker_color(title)
    for marker in lineup_marker_positions(lineup):
        player_id = marker["player_id"]
        shirt = shirts.get(player_id, "")
        full_name = player_name(player_id, players)
        short_name = player_display_name(player_id, players)
        markers.append(
            f'<div class="player-marker" style="left: {marker["x"]:.1f}%; top: {marker["y"]:.1f}%;" '
            f'title="{escape(full_name)} · {escape(format_position(marker["position"]))}">'
            f'<div class="player-shirt" style="background: {color};">{escape(str(shirt))}</div>'
            f'<div class="player-name">{escape(short_name)}</div>'
            '</div>'
        )

    st.markdown(
        '<div class="lineup-pitch">'
        '<div class="pitch-center-circle"></div>'
        f'{"".join(markers)}'
        '</div>',
        unsafe_allow_html=True,
    )


def bench_rows(lineup: dict[str, Any], players: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    starter_ids = {int(position["playerId"]) for position in lineup.get("startingPositions", [])}
    rows = []
    for player in lineup.get("players", []):
        player_id = int(player["id"])
        if player_id in starter_ids:
            continue
        rows.append({"#": player.get("shirtNumber", ""), "Player": player_name(player_id, players)})
    return rows


def substitution_rows(lineup: dict[str, Any], players: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for sub in lineup.get("substitutions", []):
        from_position = sub.get("fromPosition")
        to_position = sub.get("toPosition")
        if from_position == "BANK":
            movement = "On"
        elif to_position == "BANK":
            movement = "Off"
        else:
            movement = "Moved"
        rows.append(
            {
                "Time": minute_label(sub.get("gameTime")),
                "Player": player_name(int(sub["playerId"]), players),
                "Move": movement,
                "From": format_position(from_position),
                "To": format_position(to_position),
            }
        )
    return rows


def stat_rows(
    stats: dict[int, dict[str, Any]],
    home_id: int,
    away_id: int,
    home_name: str,
    away_name: str,
) -> list[dict[str, Any]]:
    specs = [
        ("Shots", "shots", "number"),
        ("Shots on Target", "shots_on_target", "number"),
        ("Possession", "possession", "percent"),
        ("Passes", "passes", "number"),
        ("Pass Accuracy", "pass_accuracy", "percent_decimal"),
        ("Fouls", "fouls", "number"),
        ("Yellow Cards", "yellow_cards", "number"),
        ("Red Cards", "red_cards", "number"),
        ("Offsides", "offsides", "number"),
        ("Corners", "corners", "number"),
    ]
    rows = []
    for label, key, kind in specs:
        home_value = stats[home_id].get(key, 0)
        away_value = stats[away_id].get(key, 0)
        rows.append(
            {
                "Stat": label,
                short_team_name(home_name): format_stat_value(home_value, kind),
                short_team_name(away_name): format_stat_value(away_value, kind),
            }
        )
    return rows


def format_stat_value(value: float, kind: str) -> str:
    if kind == "percent":
        return f"{int(round(value))}%"
    if kind == "percent_decimal":
        return f"{value:.1f}%"
    return str(int(round(value)))


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


def render_lineup_panel(
    title: str,
    lineup: dict[str, Any],
    players: dict[int, dict[str, Any]],
) -> None:
    formation = lineup.get("startingFormation", "Unknown")
    st.markdown(f"**{title} · {formation}**")
    render_lineup_pitch(title, lineup, players)
    st.markdown('<div class="lineup-note">Starters shown by shirt number and role.</div>', unsafe_allow_html=True)
    with st.expander("Starting XI", expanded=False):
        st.dataframe(lineup_rows(lineup, players), hide_index=True, width="stretch")
    with st.expander("Bench", expanded=False):
        st.dataframe(bench_rows(lineup, players), hide_index=True, width="stretch")
    with st.expander("Substitutions", expanded=False):
        rows = substitution_rows(lineup, players)
        if rows:
            st.dataframe(rows, hide_index=True, width="stretch")
        else:
            st.caption("No substitutions listed.")


def season_record(summaries: list[dict[str, Any]]) -> dict[str, int]:
    record = Counter(summary["freiburgResult"] for summary in summaries)
    wins = record["W"]
    draws = record["D"]
    losses = record["L"]
    return {
        "matches": len(summaries),
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "points": wins * 3 + draws,
    }


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


def points_progression(summaries: list[dict[str, Any]]) -> list[dict[str, int]]:
    points_by_result = {"W": 3, "D": 1, "L": 0}
    total = 0
    rows = [{"Game": 0, "Points": 0}]
    for game_number, summary in enumerate(summaries, start=1):
        total += points_by_result.get(summary["freiburgResult"], 0)
        rows.append({"Game": game_number, "Points": total})
    return rows


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
        '</div>'
        '<div class="sidebar-footnote">Data: ImpectAPI/open-data</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    return current_page


def render_league_table_page(squads: dict[int, dict[str, Any]]) -> None:
    rows = build_league_table()
    st.markdown('<div class="headline-row">', unsafe_allow_html=True)
    st.markdown('<div class="app-kicker">Bundesliga 2023/24 · League Table</div>', unsafe_allow_html=True)
    st.title("League Table")
    st.markdown("</div>", unsafe_allow_html=True)

    html_rows = []
    for row in rows:
        team_id = int(row["team_id"])
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
            '</div>'
            '</td>'
            f'<td>{row["played"]}</td>'
            f'<td>{row["wins"]}</td>'
            f'<td>{row["draws"]}</td>'
            f'<td>{row["losses"]}</td>'
            f'<td>{row["goals_for"]}</td>'
            f'<td>{row["goals_against"]}</td>'
            f'<td>{row["goal_difference"]:+d}</td>'
            f'<td class="league-table-points">{row["points"]}</td>'
            '</tr>'
        )

    st.markdown(
        '<div class="league-table-wrap">'
        '<table class="league-table">'
        '<thead><tr>'
        '<th>#</th><th>Club</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th>'
        '</tr></thead>'
        f'<tbody>{"".join(html_rows)}</tbody>'
        '</table>'
        '</div>',
        unsafe_allow_html=True,
    )


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


def rerun_app() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


if not DATA_ROOT.exists():
    st.error(f"Could not find Exam Data at {DATA_ROOT}")
    st.stop()


squads_by_id, players_by_id, _ = load_reference_data()
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
record = season_record(summaries)
points_chart_data = points_progression(summaries)
page = render_sidebar_menu(selected_page_from_query(), int(summaries[selected_index]["id"]))

if page == "League Table":
    render_league_table_page(squads_by_id)
    st.stop()

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
lineups = load_match_lineups(int(selected_match["id"]))
player_kpis = load_match_player_kpis(int(selected_match["id"]))

home_id = int(selected_match["homeSquadId"])
away_id = int(selected_match["awaySquadId"])
home_name = selected_match["homeName"]
away_name = selected_match["awayName"]
home_short = short_team_name(home_name)
away_short = short_team_name(away_name)
result_code = selected_match["freiburgResult"]
stats = compute_stats(selected_match, events, player_kpis)
rows = stat_rows(stats, home_id, away_id, home_name, away_name)

st.divider()
with st.container(border=True):
    st.markdown(
        f"""
        <div class="scoreboard">
            <div class="scoreboard-team">
                {render_scoreboard_logo(home_id, home_name, squads_by_id)}
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
                {render_scoreboard_logo(away_id, away_name, squads_by_id)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    overview_tab, lineup_tab, stats_tab, events_tab = st.tabs(["Overview", "Line Ups", "Stats", "Events"])

    with overview_tab:
        overview_cols = st.columns(4)
        freiburg_goals = stats[freiburg_id]["shots"]
        opponent_id = opposition_team(selected_match, freiburg_id)
        overview_cols[0].metric("Freiburg Shots", int(freiburg_goals))
        overview_cols[1].metric("Freiburg Pass Accuracy", f"{stats[freiburg_id]['pass_accuracy']:.1f}%")
        overview_cols[2].metric("Freiburg Possession", f"{stats[freiburg_id]['possession']}%")
        overview_cols[3].metric("Opponent", short_team_name(team_name(opponent_id, squads_by_id)))

        goals = scoring_events(events, selected_match, players_by_id, squads_by_id)
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

        shot_rows = []
        for event in events:
            if event.get("actionType") != "SHOT":
                continue
            player_id = event.get("player", {}).get("id")
            shot = event.get("shot") or {}
            shot_rows.append(
                {
                    "Time": minute_label(event.get("gameTime")),
                    "Team": short_team_name(team_name(int(event["squadId"]), squads_by_id)),
                    "Player": player_name(player_id, players_by_id),
                    "Action": format_position(event.get("action")),
                    "Result": format_position(event.get("result")),
                    "Distance": f"{shot.get('distance', 0):.1f}m" if shot.get("distance") is not None else "",
                }
            )
        with st.expander("Shots", expanded=False):
            st.dataframe(shot_rows, hide_index=True, width="stretch")
