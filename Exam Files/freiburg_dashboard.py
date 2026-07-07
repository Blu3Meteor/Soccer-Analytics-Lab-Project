from __future__ import annotations

import streamlit as st


st.set_page_config(
    page_title="SC Freiburg Match Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)


from freiburg_app.app import main


main()
