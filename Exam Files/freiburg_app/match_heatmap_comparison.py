# PROVENANCE: AI-ASSISTED DRAFT — MATHEMATICAL / DATA ANALYSIS
# This comparison was generated with LLM assistance and is not human-authored.
# Method: each selected-match block is compared with the arithmetic mean of the
# same block across Freiburg's other matches (a leave-one-out baseline).

from __future__ import annotations

from collections import defaultdict
from typing import Any


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

    match_ids = {int(row["Match ID"]) for row in source_rows}
    selected_match_id = int(selected_match_id)
    if selected_match_id not in match_ids:
        raise ValueError("Selected match is not present in the heatmap source rows.")
    reference_match_ids = match_ids - {selected_match_id}
    if not reference_match_ids:
        raise ValueError("At least one other match is required for comparison.")

    selected_by_block: dict[str, dict[str, Any]] = {}
    reference_values: dict[str, list[float]] = defaultdict(list)
    for row in source_rows:
        block = str(row["Block"])
        if int(row["Match ID"]) == selected_match_id:
            selected_by_block[block] = row
        else:
            reference_values[block].append(float(row[metric]))

    comparisons: list[dict[str, Any]] = []
    for block, selected_row in selected_by_block.items():
        values = reference_values[block]
        normal_value = sum(values) / len(values) if values else 0.0
        selected_value = float(selected_row[metric])
        comparisons.append(
            {
                "Block": block,
                "Row": int(selected_row["Row"]),
                "Column": int(selected_row["Column"]),
                "X start (m)": float(selected_row["X start (m)"]),
                "X end (m)": float(selected_row["X end (m)"]),
                "Y start (m)": float(selected_row["Y start (m)"]),
                "Y end (m)": float(selected_row["Y end (m)"]),
                "Metric": metric,
                "Selected match": selected_value,
                "Other-match average": normal_value,
                "Difference": selected_value - normal_value,
                "Reference matches": len(reference_match_ids),
            }
        )

    comparisons.sort(key=lambda row: (int(row["Row"]), int(row["Column"])))
    return comparisons


def comparison_summary(comparison_rows: list[dict[str, Any]]) -> dict[str, float]:
    """Summarise block differences; block averages sum to the mean match total."""
    selected_total = sum(float(row["Selected match"]) for row in comparison_rows)
    normal_total = sum(float(row["Other-match average"]) for row in comparison_rows)
    return {
        "selected_total": selected_total,
        "normal_total": normal_total,
        "difference": selected_total - normal_total,
    }
