import streamlit as st

from freiburg_app.app import main


# UI Assistance
st.set_page_config(
    page_title="SC Freiburg Match Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

main()
