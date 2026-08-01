from collections import Counter, defaultdict
from collections.abc import Iterable
from typing import Any


PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0
IGNORED_ATTACKING_SHARE_EVENTS = {"FINAL_WHISTLE", "NO_VIDEO"}


# Data Processing Assistance
def clamp(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))


def event_player_id(event: dict[str, Any]) -> int | None:
    value = (event.get("player") or {}).get("id")
    return int(value) if value is not None else None


def event_team_id(event: dict[str, Any]) -> int | None:
    value = event.get("squadId")
    return int(value) if value is not None else None


def event_coordinate_x(event: dict[str, Any], point_key: str) -> float | None:
    point = event.get(point_key) or {}
    coordinates = point.get("adjCoordinates")
    return float(coordinates.get("x", 0.0)) if coordinates else None


def event_xy(event: dict[str, Any], point_key: str) -> tuple[float, float] | None:
    """Convert centre-origin Impect coordinates to physical pitch coordinates."""
    point = event.get(point_key) or {}
    coordinates = point.get("adjCoordinates")
    if not coordinates:
        return None
    x = float(coordinates.get("x", 0.0)) + PITCH_LENGTH / 2
    y = PITCH_WIDTH / 2 - float(coordinates.get("y", 0.0))
    return clamp(x, 0.0, PITCH_LENGTH), clamp(y, 0.0, PITCH_WIDTH)


def event_kpi_values(events_kpis: list[dict[str, Any]], kpi_id: int) -> dict[int, float]:
    """Sum one KPI by event ID."""
    values: dict[int, float] = defaultdict(float)
    for item in events_kpis:
        if int(item.get("kpiId", -1)) == int(kpi_id):
            values[int(item["eventId"])] += float(item.get("value") or 0.0)
    return dict(values)


def player_kpi_values(player: dict[str, Any]) -> defaultdict[int, float]:
    """Sum a player's KPI list by KPI ID."""
    values: defaultdict[int, float] = defaultdict(float)
    for item in player.get("kpis", []):
        values[int(item["kpiId"])] += float(item.get("value") or 0.0)
    return values


# Extra mathematical method: this is an event-count share, not a time measure.
def attacking_event_shares(
    events: list[dict[str, Any]],
    team_ids: Iterable[int],
) -> dict[int, float]:
    """Return each team's share of recorded attacking events."""
    ids = tuple(int(team_id) for team_id in team_ids)
    counts: Counter[int] = Counter()
    for event in events:
        team_id = event.get("currentAttackingSquadId")
        if team_id in ids and event.get("actionType") not in IGNORED_ATTACKING_SHARE_EVENTS:
            counts[int(team_id)] += 1
    total = sum(counts.values())
    if not total:
        return {team_id: 1 / len(ids) for team_id in ids}
    return {team_id: counts[team_id] / total for team_id in ids}
