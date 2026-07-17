# PROVENANCE: AI-ASSISTED DRAFT — MATHEMATICAL / DATA ANALYSIS
# This comparison was generated with LLM assistance and is not human-authored.
# Method: each selected-match block is compared with the arithmetic mean of the
# same block across Freiburg's other matches (a leave-one-out baseline).

from __future__ import annotations

from typing import Any

import pandas as pd


SUPPORTED_METRICS = {"Shots", "xG", "Positive PxT actions", "Positive PxT"}


def build_match_vs_normal_comparison(
    selected_match_id: int,
    source_rows: list[dict[str, Any]],
    metric: str,
) -> list[dict[str, Any]]:
    """Compare one match with Freiburg's other-match mean in every pitch block.

    For block b and selected match s, the calculation is::

        normal_b = sum(value[m, b] for m != s) / number_of_other_matches
        difference_b = value[s, b] - normal_b

    The selected match is excluded from its own reference baseline. Positive
    differences mean more of the chosen metric than Freiburg normally records
    in that block; negative differences mean less. No smoothing is applied.
    """
    if metric not in SUPPORTED_METRICS:
        raise ValueError(f"Unsupported heatmap comparison metric: {metric}")

    frame = pd.DataFrame(source_rows)
    if frame.empty:
        raise ValueError("Heatmap source rows are empty.")

    frame["Match ID"] = frame["Match ID"].astype(int)
    match_ids = set(frame["Match ID"].unique())
    selected_match_id = int(selected_match_id)
    if selected_match_id not in match_ids:
        raise ValueError("Selected match is not present in the heatmap source rows.")
    reference_match_ids = match_ids - {selected_match_id}
    if not reference_match_ids:
        raise ValueError("At least one other match is required for comparison.")

    selected = frame.loc[frame["Match ID"] == selected_match_id].copy()
    selected["Selected match"] = selected[metric].astype(float)
    normal = (
        frame.loc[frame["Match ID"] != selected_match_id]
        .groupby("Block", as_index=False)[metric]
        .mean()
        .rename(columns={metric: "Other-match average"})
    )
    comparison = selected.merge(normal, on="Block", validate="one_to_one")
    comparison["Difference"] = comparison["Selected match"] - comparison["Other-match average"]
    comparison["Metric"] = metric
    comparison["Reference matches"] = len(reference_match_ids)
    comparison = comparison.sort_values(["Row", "Column"])

    columns = [
        "Block", "Row", "Column", "X start (m)", "X end (m)", "Y start (m)", "Y end (m)",
        "Metric", "Selected match", "Other-match average", "Difference", "Reference matches",
    ]
    return comparison[columns].to_dict("records")


def comparison_summary(comparison_rows: list[dict[str, Any]]) -> dict[str, float]:
    """Summarise block differences; block averages sum to the mean match total."""
    selected_total = sum(float(row["Selected match"]) for row in comparison_rows)
    normal_total = sum(float(row["Other-match average"]) for row in comparison_rows)
    return {
        "selected_total": selected_total,
        "normal_total": normal_total,
        "difference": selected_total - normal_total,
    }
