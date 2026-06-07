from __future__ import annotations

import streamlit as st

from data.mock_data import MOCK_ANALYST_RESULTS, MOCK_REPORTS
from views.adoption import render_adoption
from views.overview import render_overview
from views.team_detail import render_team_detail

st.set_page_config(
    page_title="DevEx Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.title("🚀 DevEx Intelligence")
    st.caption("Engineering Performance Platform")
    st.divider()

    page = st.selectbox(
        "Navigation",
        ["Overview", "Team Detail", "Golden Path Adoption"],
        label_visibility="collapsed",
    )

    team = list(MOCK_REPORTS.keys())[0]
    if page == "Team Detail":
        team = st.selectbox("Select team", list(MOCK_REPORTS.keys()))

    st.divider()
    st.caption("Data source: Mock (demo mode)")
    st.caption("devex-platform v0.1.0")

if page == "Overview":
    render_overview(MOCK_REPORTS)
elif page == "Team Detail":
    render_team_detail(
        team,
        MOCK_REPORTS[team],
        MOCK_ANALYST_RESULTS.get(team),
    )
elif page == "Golden Path Adoption":
    render_adoption(MOCK_REPORTS)
