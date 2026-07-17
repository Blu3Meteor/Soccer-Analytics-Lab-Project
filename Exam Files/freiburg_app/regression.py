# PROVENANCE: AI-ASSISTED DRAFT — POISSON REGRESSION / MATHEMATICAL ANALYSIS
# This follows the Soccermatics Poisson model. Anyone presenting it must still
# understand the model assumptions and the expected-points calculation below.

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import streamlit as st
from scipy.stats import poisson

from .config import FREIBURG_NAME
from .data import load_reference_data
from .matches import load_scored_matches


MAX_GOALS = 10


def _fit_poisson_glm(goal_rows: list[dict[str, Any]], teams: list[str]) -> dict[str, Any]:
    """Fit the Soccermatics model: ``goals ~ home + team + opponent``."""
    ordered_teams = [FREIBURG_NAME] + [team for team in teams if team != FREIBURG_NAME]
    data = pd.DataFrame(goal_rows)

    # Putting Freiburg first makes it the reference category, with coefficient 0.
    data["team"] = pd.Categorical(data["team"], categories=ordered_teams)
    data["opponent"] = pd.Categorical(data["opponent"], categories=ordered_teams)

    fitted = smf.glm(
        formula="goals ~ home + C(team) + C(opponent)",
        data=data,
        family=sm.families.Poisson(),
    ).fit()

    attack = {FREIBURG_NAME: 0.0}
    concede = {FREIBURG_NAME: 0.0}
    for team in ordered_teams[1:]:
        attack[team] = float(fitted.params[f"C(team)[T.{team}]"])
        concede[team] = float(fitted.params[f"C(opponent)[T.{team}]"])

    return {
        "baseline_team": FREIBURG_NAME,
        "coefficients": {name: float(value) for name, value in fitted.params.items()},
        "attack": attack,
        "concede": concede,
        "home_advantage": float(fitted.params["home"]),
        "intercept": float(fitted.params["Intercept"]),
        "iterations": int(fitted.fit_history.get("iteration", 0)),
        "converged": bool(fitted.converged),
        "log_likelihood": float(fitted.llf),
    }


def _expected_goals(model: dict[str, Any], team: str, opponent: str, home: int) -> float:
    """Convert the fitted coefficients from the log scale to expected goals."""
    log_rate = (
        model["intercept"]
        + model["home_advantage"] * home
        + model["attack"][team]
        + model["concede"][opponent]
    )
    return float(np.exp(log_rate))


def _outcome_probabilities(home_rate: float, away_rate: float) -> dict[str, float]:
    """Calculate home-win, draw and away-win probabilities from a score grid."""
    goals = np.arange(MAX_GOALS + 1)
    score_grid = np.outer(poisson.pmf(goals, home_rate), poisson.pmf(goals, away_rate))

    # Scores above MAX_GOALS are omitted, so normalise the retained grid to 1.
    score_grid /= score_grid.sum()
    return {
        "home_win": float(np.tril(score_grid, -1).sum()),
        "draw": float(np.diag(score_grid).sum()),
        "away_win": float(np.triu(score_grid, 1).sum()),
    }


@st.cache_data(show_spinner=False)
def build_regression_outputs() -> dict[str, Any]:
    """Fit the league model and calculate each club's expected season totals."""
    squads, _, _ = load_reference_data()
    teams = sorted(squad["name"] for squad in squads.values())
    team_names_by_id = {team_id: squad["name"] for team_id, squad in squads.items()}

    fixtures = []
    goal_rows = []
    for match in load_scored_matches():
        home_id = int(match["homeSquadId"])
        away_id = int(match["awaySquadId"])
        home_team = team_names_by_id[home_id]
        away_team = team_names_by_id[away_id]
        fixtures.append((home_team, away_team))
        goal_rows.extend(
            [
                {"team": home_team, "opponent": away_team, "home": 1, "goals": match["homeScore"]},
                {"team": away_team, "opponent": home_team, "home": 0, "goals": match["awayScore"]},
            ]
        )

    model = _fit_poisson_glm(goal_rows, teams)
    table = {
        team: {
            "expected_points": 0.0,
            "expected_goals_for": 0.0,
            "expected_goals_against": 0.0,
            "expected_goal_difference": 0.0,
            "attack_coefficient": model["attack"][team],
            "concede_coefficient": model["concede"][team],
        }
        for team in teams
    }

    for home_team, away_team in fixtures:
        home_rate = _expected_goals(model, home_team, away_team, home=1)
        away_rate = _expected_goals(model, away_team, home_team, home=0)
        outcome = _outcome_probabilities(home_rate, away_rate)

        table[home_team]["expected_points"] += 3 * outcome["home_win"] + outcome["draw"]
        table[away_team]["expected_points"] += 3 * outcome["away_win"] + outcome["draw"]
        table[home_team]["expected_goals_for"] += home_rate
        table[home_team]["expected_goals_against"] += away_rate
        table[away_team]["expected_goals_for"] += away_rate
        table[away_team]["expected_goals_against"] += home_rate

    for row in table.values():
        row["expected_goal_difference"] = row["expected_goals_for"] - row["expected_goals_against"]

    coefficients = [
        {
            "Club": team,
            "Attack Coef": round(model["attack"][team], 3),
            "Concede Coef": round(model["concede"][team], 3),
        }
        for team in teams
    ]
    coefficients.sort(key=lambda row: row["Attack Coef"], reverse=True)

    return {"model": model, "table": table, "coefficients": coefficients}
