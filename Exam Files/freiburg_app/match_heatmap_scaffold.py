# PROVENANCE: AI-ASSISTED — DATA DISPLAY / STREAMLIT WEBSITE
# The imported comparison and plots are also explicitly marked AI-assisted.

from __future__ import annotations

from typing import Any

import streamlit as st

from .match_heatmap_comparison import build_match_vs_normal_comparison
from .match_heatmap_comparison_plot import render_match_comparison_svg
from .season_heatmap_data import (
    heatmap_block_rows,
    heatmap_rows_csv,
    match_heatmap_source_rows,
    season_freiburg_heatmap_data,
)


def render_match_heatmap_scaffold(
    summaries: list[dict[str, Any]],
    selected_match: dict[str, Any],
    freiburg_id: int,
) -> None:
    """Render the AI-assisted match-versus-normal comparison and source data."""
    match_id = int(selected_match["id"])
    match_ids = tuple(int(match["id"]) for match in summaries)
    match_data = season_freiburg_heatmap_data((match_id,), int(freiburg_id))
    selected_rows = heatmap_block_rows(match_id, match_data)
    source_rows = match_heatmap_source_rows(match_ids, int(freiburg_id))

    st.markdown("**Per-match shot and PxT comparison**")
    st.caption(
        "Each block compares the selected match with Freiburg's average in the same block across the other 33 "
        "matches. Positive values are above Freiburg's normal level; negative values are below it."
    )

    with st.container(horizontal=True):
        st.metric("Shots", int(match_data["shots"]), border=True)
        st.metric("Match xG", f'{match_data["total_xg"]:.2f}', border=True)
        st.metric("Positive PxT actions", int(match_data["actions"]), border=True)
        st.metric("Match positive PxT", f'{match_data["total_pxt"]:.2f}', border=True)

    view = st.segmented_control(
        "Comparison measure",
        ["Value", "Volume"],
        default="Value",
        key=f"match_heatmap_measure_{match_id}",
        help="Value compares xG and positive PxT. Volume compares shot and positive-action counts.",
        width="stretch",
    )
    if view == "Volume":
        left_metric, right_metric = "Shots", "Positive PxT actions"
    else:
        left_metric, right_metric = "xG", "Positive PxT"

    left_comparison = build_match_vs_normal_comparison(match_id, source_rows, left_metric)
    right_comparison = build_match_vs_normal_comparison(match_id, source_rows, right_metric)

    plot_columns = st.columns(2)
    with plot_columns[0]:
        with st.container(border=True, height="stretch"):
            st.subheader("Shot comparison")
            st.markdown(
                render_match_comparison_svg(left_comparison, left_metric, f"Selected match vs normal {left_metric}"),
                unsafe_allow_html=True,
            )
    with plot_columns[1]:
        with st.container(border=True, height="stretch"):
            st.subheader("Positive PxT comparison")
            st.markdown(
                render_match_comparison_svg(
                    right_comparison,
                    right_metric,
                    f"Selected match vs normal {right_metric}",
                ),
                unsafe_allow_html=True,
            )

    st.caption(
        "Red blocks are above Freiburg's other-match average; blue blocks are below it. Hover or keyboard-focus a "
        "block for the selected value, normal value, and difference. No smoothing is applied to this comparison."
    )

    with st.expander("Selected-match block inputs", icon=":material/table_chart:"):
        st.caption("Raw 12-by-8 block values before the comparison calculation.")
        st.dataframe(selected_rows, hide_index=True, width="stretch")

    with st.expander("Comparison source dataset", icon=":material/data_object:"):
        st.caption(
            "One raw row per match and pitch block for all Freiburg league matches."
        )
        st.dataframe(source_rows, hide_index=True, width="stretch", height=360)
        st.download_button(
            "Download raw block data",
            data=heatmap_rows_csv(source_rows),
            file_name="freiburg_match_heatmap_source_rows.csv",
            mime="text/csv",
            icon=":material/download:",
            width="stretch",
        )

    st.info(
        "Provenance: the leave-one-out comparison calculation and both pitch plots are AI-assisted, not human-authored.",
        icon=":material/smart_toy:",
    )
