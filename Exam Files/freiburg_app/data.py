# PROVENANCE: AI-ASSISTED — IMPECT DATA EXTRACTION / DISPLAY FORMATTING
# This module loads and labels source data; it does not interpret performance.

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import streamlit as st

from .config import BERLIN_TZ, DATA_ROOT, ITERATION_ID


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


@st.cache_data(show_spinner=False)
def load_match_events_kpis(match_id: int) -> list[dict[str, Any]]:
    return load_json(f"events_kpis/events_kpis_{match_id}.json")


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
