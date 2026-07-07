from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from datetime import datetime
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
        padding: 0.9rem 1rem;
        background: var(--panel);
        min-height: 92px;
    }

    .summary-label {
        color: var(--muted);
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
    }

    .summary-value {
        color: var(--ink);
        font-size: 1.55rem;
        font-weight: 800;
        margin-top: 0.15rem;
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

    @media (max-width: 700px) {
        .scoreboard {
            grid-template-columns: 1fr;
            text-align: center;
        }

        .scoreline {
            min-width: 0;
        }

        .stat-row {
            grid-template-columns: 1fr;
            text-align: center;
            gap: 0.15rem;
        }

        .align-right {
            text-align: center;
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
    st.dataframe(lineup_rows(lineup, players), hide_index=True, use_container_width=True)
    with st.expander("Bench", expanded=False):
        st.dataframe(bench_rows(lineup, players), hide_index=True, use_container_width=True)
    with st.expander("Substitutions", expanded=False):
        rows = substitution_rows(lineup, players)
        if rows:
            st.dataframe(rows, hide_index=True, use_container_width=True)
        else:
            st.caption("No substitutions listed.")


def record_summary(summaries: list[dict[str, Any]]) -> str:
    record = Counter(summary["freiburgResult"] for summary in summaries)
    return f"{record['W']}-{record['D']}-{record['L']}"


def result_word(code: str) -> str:
    return {"W": "Win", "D": "Draw", "L": "Loss"}.get(code, code)


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

selected_index = min(max(int(st.session_state.selected_match_index), 0), len(summaries) - 1)

st.markdown('<div class="headline-row">', unsafe_allow_html=True)
left, right = st.columns([0.74, 0.26])
with left:
    st.markdown('<div class="app-kicker">Bundesliga 2023/24 · Impect Exam Data</div>', unsafe_allow_html=True)
    st.title("SC Freiburg Match Dashboard")
with right:
    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">Season Record</div>
            <div class="summary-value">{record_summary(summaries)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

slider_value = st.slider(
    "SC Freiburg matches",
    min_value=1,
    max_value=len(summaries),
    value=selected_index + 1,
    label_visibility="collapsed",
)
if slider_value - 1 != selected_index:
    st.session_state.selected_match_index = slider_value - 1
    selected_index = slider_value - 1

cards_per_row = 6
for row_start in range(0, len(summaries), cards_per_row):
    columns = st.columns(cards_per_row)
    for offset, column in enumerate(columns):
        index = row_start + offset
        if index >= len(summaries):
            continue
        match = summaries[index]
        home_short = short_team_name(match["homeName"])
        away_short = short_team_name(match["awayName"])
        scoreline = f"{match['homeScore']}-{match['awayScore']}"
        opponent = short_team_name(match["opponentName"])
        label = f"{compact_matchday(match)}\n{home_short} {scoreline} {away_short}\n{match['freiburgResult']} vs {opponent}"
        if column.button(
            label,
            key=f"match_card_{match['id']}",
            use_container_width=True,
            type="primary" if index == selected_index else "secondary",
        ):
            st.session_state.selected_match_index = index
            rerun_app()

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
            <div>
                <div class="team-name">{home_name}</div>
                <div class="team-meta">Home · {compact_matchday(selected_match)}</div>
            </div>
            <div>
                <div class="scoreline">{selected_match["homeScore"]}-{selected_match["awayScore"]}</div>
                <div class="result-pill result-{result_code}">{result_word(result_code)} for Freiburg</div>
            </div>
            <div style="text-align: right;">
                <div class="team-name">{away_name}</div>
                <div class="team-meta">Away · {format_date(selected_match["scheduledDate"])}</div>
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
            st.dataframe(goals, hide_index=True, use_container_width=True)
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
        st.dataframe(rows, hide_index=True, use_container_width=True)

    with events_tab:
        event_cols = st.columns(2)
        with event_cols[0]:
            st.markdown("**Goals**")
            if goals:
                st.dataframe(goals, hide_index=True, use_container_width=True)
            else:
                st.caption("No goals recorded.")
        with event_cols[1]:
            cards = card_events(events, players_by_id, squads_by_id)
            st.markdown("**Cards**")
            if cards:
                st.dataframe(cards, hide_index=True, use_container_width=True)
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
            st.dataframe(shot_rows, hide_index=True, use_container_width=True)
