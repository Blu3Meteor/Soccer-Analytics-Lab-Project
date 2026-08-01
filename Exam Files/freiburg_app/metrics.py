from collections import Counter, defaultdict
from typing import Any

from .config import (
    KPI_NEUTRAL_PASSES,
    KPI_POSTSHOT_XG,
    KPI_RED_CARD,
    KPI_SECOND_YELLOW_CARD,
    KPI_SHOT_XG,
    KPI_SHOTS,
    KPI_SHOTS_ON_TARGET,
    KPI_SUCCESSFUL_PASSES,
    KPI_UNSUCCESSFUL_PASSES,
    KPI_YELLOW_CARD,
)
from .data import short_team_name
from .event_utils import attacking_event_shares, event_kpi_values, player_kpi_values


PASS_ACCURACY_LABEL = "Pass Accuracy (successful ÷ all attempts)"
PASS_ACCURACY_NOTE = (
    "Pass accuracy = successful ÷ (successful + unsuccessful + neutral) pass attempts. "
    "Neutral passes are included in all attempts; they are not provider-classified failures."
)


# Data Processing Assistance
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
        for kpi_id, value in player_kpi_values(player).items():
            totals[kpi_id] += value
    return totals


def compute_attacking_event_share_percentages(
    events: list[dict[str, Any]],
    team_ids: tuple[int, int],
) -> dict[int, int]:
    """Return each team's percentage share of recorded attacking events.

    If ``n_i`` is the count of eligible events for team i, the percentage is
    ``round(100 * n_i / (n_home + n_away))``. The away percentage is set to
    ``100 - home`` so rounding cannot make the pair sum to 99 or 101.
    """
    shares = attacking_event_shares(events, team_ids)
    first = int(round(shares[team_ids[0]] * 100))
    return {team_ids[0]: first, team_ids[1]: max(0, 100 - first)}


def shot_xg_by_event(events_kpis: list[dict[str, Any]]) -> dict[int, float]:
    return event_kpi_values(events_kpis, KPI_SHOT_XG)


def total_pxt_by_team(
    events: list[dict[str, Any]],
    events_kpis: list[dict[str, Any]],
    team_ids: tuple[int, int],
) -> dict[int, float]:
    """Return full team PxT, which Impect defines as team Post-Shot xG."""
    postshot_xg = event_kpi_values(events_kpis, KPI_POSTSHOT_XG)
    totals = {int(team_id): 0.0 for team_id in team_ids}
    for event in events:
        team_id = event.get("squadId")
        event_id = event.get("id")
        if team_id in totals and event_id is not None:
            totals[int(team_id)] += postshot_xg.get(int(event_id), 0.0)
    return totals


def compute_stats(
    match: dict[str, Any],
    events: list[dict[str, Any]],
    player_kpis: dict[str, Any],
    events_kpis: list[dict[str, Any]] | None = None,
) -> dict[int, dict[str, Any]]:
    """Combine player KPIs and event counts into the match-stat dictionary.

    Pass accuracy uses successful / (successful + unsuccessful + neutral)
    passes. xG is the sum of Impect KPI 82 attached to team events. Fouls,
    offsides, and corners are direct event counts.
    """
    home_id = int(match["homeSquadId"])
    away_id = int(match["awaySquadId"])
    team_ids = (home_id, away_id)
    stats: dict[int, dict[str, Any]] = {team_id: defaultdict(float) for team_id in team_ids}
    attacking_event_share = compute_attacking_event_share_percentages(events, team_ids)
    xg_by_event = shot_xg_by_event(events_kpis or [])

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
        second_yellow_cards = int(round(kpis[KPI_SECOND_YELLOW_CARD])) if KPI_SECOND_YELLOW_CARD in kpis else 0
        stats[team_id]["yellow_cards"] = (
            int(round(kpis[KPI_YELLOW_CARD])) + second_yellow_cards if KPI_YELLOW_CARD in kpis else None
        )
        stats[team_id]["second_yellow_cards"] = (
            second_yellow_cards if KPI_SECOND_YELLOW_CARD in kpis else None
        )
        stats[team_id]["red_cards"] = int(round(kpis[KPI_RED_CARD])) + second_yellow_cards
        stats[team_id]["attacking_event_share"] = attacking_event_share[team_id]
        stats[team_id]["xg"] = 0.0

    for event in events:
        squad_id = event.get("squadId")
        if squad_id not in team_ids:
            continue
        event_id = event.get("id")
        if event_id is not None:
            stats[int(squad_id)]["xg"] += xg_by_event.get(int(event_id), 0.0)
        action_type = event.get("actionType")
        if action_type == "FOUL":
            stats[int(squad_id)]["fouls"] += 1
        elif action_type == "OFFSIDE":
            stats[int(squad_id)]["offsides"] += 1
        elif action_type == "CORNER":
            stats[int(squad_id)]["corners"] += 1

    return stats


def season_record(summaries: list[dict[str, Any]]) -> dict[str, int]:
    """Apply the standard three-points-for-a-win league scoring rule."""
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


def points_progression(summaries: list[dict[str, Any]]) -> list[dict[str, int]]:
    """Return cumulative points after each chronologically ordered match."""
    points_by_result = {"W": 3, "D": 1, "L": 0}
    total = 0
    rows = [{"Game": 0, "Points": 0}]
    for game_number, summary in enumerate(summaries, start=1):
        total += points_by_result.get(summary["freiburgResult"], 0)
        rows.append({"Game": game_number, "Points": total})
    return rows


# UI Assistance
def format_stat_value(value: float | None, kind: str) -> str:
    if value is None:
        return "N/A"
    if kind == "decimal":
        return f"{float(value):.2f}"
    if kind == "percent":
        return f"{int(round(value))}%"
    if kind == "percent_decimal":
        return f"{value:.1f}%"
    return str(int(round(value)))


def stat_rows(
    stats: dict[int, dict[str, Any]],
    home_id: int,
    away_id: int,
    home_name: str,
    away_name: str,
) -> list[dict[str, Any]]:
    specs = [
        ("Shots", "shots", "number"),
        ("xG", "xg", "decimal"),
        ("Shots on Target", "shots_on_target", "number"),
        ("Attacking Event Share", "attacking_event_share", "percent"),
        ("Passes", "passes", "number"),
        (PASS_ACCURACY_LABEL, "pass_accuracy", "percent_decimal"),
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
