from __future__ import annotations

import math
from typing import Any

import streamlit as st

from .config import FREIBURG_NAME
from .data import load_match_events, load_reference_data
from .metrics import compute_score


MAX_GOALS = 10


def _fit_poisson_glm(
    goal_rows: list[dict[str, Any]],
    teams: list[str],
    max_iterations: int = 80,
    tolerance: float = 1e-8,
    ridge: float = 1e-5,
) -> dict[str, Any]:
    baseline_team = FREIBURG_NAME if FREIBURG_NAME in teams else teams[0]
    ordered_teams = [baseline_team] + [team for team in teams if team != baseline_team]
    parameter_names = ["Intercept", "home"]
    parameter_names.extend(f"team:{team}" for team in ordered_teams[1:])
    parameter_names.extend(f"opponent:{team}" for team in ordered_teams[1:])

    parameter_index = {name: index for index, name in enumerate(parameter_names)}
    beta = [0.0 for _ in parameter_names]
    mean_goals = sum(float(row["goals"]) for row in goal_rows) / max(1, len(goal_rows))
    beta[0] = math.log(max(mean_goals, 0.05))

    design_rows = []
    goals = []
    for row in goal_rows:
        indices = [parameter_index["Intercept"]]
        if int(row["home"]) == 1:
            indices.append(parameter_index["home"])
        if row["team"] != baseline_team:
            indices.append(parameter_index[f"team:{row['team']}"])
        if row["opponent"] != baseline_team:
            indices.append(parameter_index[f"opponent:{row['opponent']}"])
        design_rows.append(indices)
        goals.append(float(row["goals"]))

    converged = False
    iterations = 0
    for iterations in range(1, max_iterations + 1):
        gradient = [0.0 for _ in beta]
        hessian = [[0.0 for _ in beta] for _ in beta]

        for indices, goals_for_row in zip(design_rows, goals):
            eta = sum(beta[index] for index in indices)
            mu = math.exp(min(20.0, max(-20.0, eta)))
            residual = goals_for_row - mu
            for i in indices:
                gradient[i] += residual
                for j in indices:
                    hessian[i][j] += mu

        for i in range(len(beta)):
            hessian[i][i] += ridge

        step = _solve_linear_system(hessian, gradient)
        max_step = max(abs(value) for value in step)
        if max_step > 1.5:
            scale = 1.5 / max_step
            step = [value * scale for value in step]

        beta = [current + update for current, update in zip(beta, step)]
        if max(abs(value) for value in step) < tolerance:
            converged = True
            break

    coefficients = dict(zip(parameter_names, beta))
    attack = {baseline_team: 0.0}
    concede = {baseline_team: 0.0}
    for team in ordered_teams[1:]:
        attack[team] = coefficients[f"team:{team}"]
        concede[team] = coefficients[f"opponent:{team}"]

    log_likelihood = 0.0
    for indices, goals_for_row in zip(design_rows, goals):
        eta = sum(beta[index] for index in indices)
        mu = math.exp(min(20.0, max(-20.0, eta)))
        log_likelihood += goals_for_row * eta - mu - math.lgamma(goals_for_row + 1)

    return {
        "baseline_team": baseline_team,
        "coefficients": coefficients,
        "attack": attack,
        "concede": concede,
        "home_advantage": coefficients["home"],
        "intercept": coefficients["Intercept"],
        "iterations": iterations,
        "converged": converged,
        "log_likelihood": log_likelihood,
    }


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]

    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            augmented[pivot][column] = 1e-12
        if pivot != column:
            augmented[column], augmented[pivot] = augmented[pivot], augmented[column]

        pivot_value = augmented[column][column]
        for item in range(column, size + 1):
            augmented[column][item] /= pivot_value

        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0:
                continue
            for item in range(column, size + 1):
                augmented[row][item] -= factor * augmented[column][item]

    return [augmented[row][size] for row in range(size)]


def _expected_goals(model: dict[str, Any], team: str, opponent: str, home: int) -> float:
    linear_prediction = (
        model["intercept"]
        + model["home_advantage"] * home
        + model["attack"].get(team, 0.0)
        + model["concede"].get(opponent, 0.0)
    )
    return math.exp(min(20.0, max(-20.0, linear_prediction)))


def _poisson_probabilities(rate: float, max_goals: int = MAX_GOALS) -> list[float]:
    first_probability = math.exp(-rate)
    probabilities = [first_probability]
    for goals in range(1, max_goals + 1):
        probabilities.append(probabilities[-1] * rate / goals)
    return probabilities


def _outcome_probabilities(home_rate: float, away_rate: float) -> dict[str, float]:
    home_probs = _poisson_probabilities(home_rate)
    away_probs = _poisson_probabilities(away_rate)
    total_probability = 0.0
    home_win = 0.0
    draw = 0.0
    away_win = 0.0

    for home_goals, home_probability in enumerate(home_probs):
        for away_goals, away_probability in enumerate(away_probs):
            probability = home_probability * away_probability
            total_probability += probability
            if home_goals > away_goals:
                home_win += probability
            elif home_goals == away_goals:
                draw += probability
            else:
                away_win += probability

    if total_probability == 0:
        return {"home_win": 0.0, "draw": 0.0, "away_win": 0.0}
    return {
        "home_win": home_win / total_probability,
        "draw": draw / total_probability,
        "away_win": away_win / total_probability,
    }


def build_regression_outputs() -> dict[str, Any]:
    squads, _, matches = load_reference_data()
    teams = sorted(squad["name"] for squad in squads.values())
    team_names_by_id = {team_id: squad["name"] for team_id, squad in squads.items()}

    scored_matches = []
    goal_rows = []
    for match in matches:
        home_id = int(match["homeSquadId"])
        away_id = int(match["awaySquadId"])
        home_team = team_names_by_id[home_id]
        away_team = team_names_by_id[away_id]
        score = compute_score(load_match_events(int(match["id"])), home_id, away_id)
        home_goals = int(score[home_id])
        away_goals = int(score[away_id])

        scored_matches.append(
            {
                "home_team": home_team,
                "away_team": away_team,
            }
        )
        goal_rows.append({"team": home_team, "opponent": away_team, "home": 1, "goals": home_goals})
        goal_rows.append({"team": away_team, "opponent": home_team, "home": 0, "goals": away_goals})

    model = _fit_poisson_glm(goal_rows, teams)
    table = {
        team: {
            "expected_points": 0.0,
            "expected_goals_for": 0.0,
            "expected_goals_against": 0.0,
            "expected_goal_difference": 0.0,
            "attack_coefficient": model["attack"].get(team, 0.0),
            "concede_coefficient": model["concede"].get(team, 0.0),
        }
        for team in teams
    }

    for match in scored_matches:
        home_team = match["home_team"]
        away_team = match["away_team"]
        home_rate = _expected_goals(model, home_team, away_team, 1)
        away_rate = _expected_goals(model, away_team, home_team, 0)
        probabilities = _outcome_probabilities(home_rate, away_rate)

        table[home_team]["expected_points"] += 3 * probabilities["home_win"] + probabilities["draw"]
        table[away_team]["expected_points"] += 3 * probabilities["away_win"] + probabilities["draw"]
        table[home_team]["expected_goals_for"] += home_rate
        table[home_team]["expected_goals_against"] += away_rate
        table[away_team]["expected_goals_for"] += away_rate
        table[away_team]["expected_goals_against"] += home_rate

    for row in table.values():
        row["expected_goal_difference"] = row["expected_goals_for"] - row["expected_goals_against"]

    coefficient_rows = []
    for team in teams:
        coefficient_rows.append(
            {
                "Club": team,
                "Attack Coef": round(model["attack"].get(team, 0.0), 3),
                "Concede Coef": round(model["concede"].get(team, 0.0), 3),
            }
        )

    coefficient_rows.sort(key=lambda row: row["Attack Coef"], reverse=True)
    return {
        "model": model,
        "table": table,
        "coefficients": coefficient_rows,
    }
