# PROVENANCE: AI-ASSISTED — STREAMLIT WEBSITE ENTRY POINT

from __future__ import annotations

import streamlit as st

from freiburg_app.app import main


st.set_page_config(
    page_title="SC Freiburg Match Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

main()
