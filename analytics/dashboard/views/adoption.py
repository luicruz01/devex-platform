from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from warehouse.models import DoraReport

from components.dora_gauge import render_rating_badge


def render_adoption(reports: dict[str, DoraReport]) -> None:
    st.title("📈 Golden Path Adoption")
    st.caption("Which teams are following the platform standards")

    st.divider()

    adopted = len(reports)
    elite_or_high = sum(
        1
        for r in reports.values()
        if r.overall_rating in ("elite", "high")
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Teams on Golden Path",
            f"{adopted}",
            help="Teams emitting DORA events",
        )
    with col2:
        st.metric(
            "Elite or High performers",
            f"{elite_or_high}/{adopted}",
        )
    with col3:
        adoption_pct = (adopted / 10) * 100
        st.metric(
            "Platform adoption",
            f"{adoption_pct:.0f}%",
            help="Out of 10 target teams",
        )

    st.divider()
    st.subheader("Adoption by metric")

    metrics = ["Deploy Freq", "Lead Time", "Failure Rate", "MTTR"]
    elite_counts = [
        sum(1 for r in reports.values() if r.deployment_frequency.elite),
        sum(1 for r in reports.values() if r.lead_time.elite),
        sum(1 for r in reports.values() if r.change_failure_rate.elite),
        sum(1 for r in reports.values() if r.mttr.elite),
    ]

    fig = go.Figure(
        go.Bar(
            x=metrics,
            y=elite_counts,
            marker_color=["#22C55E", "#3B82F6", "#F59E0B", "#8B5CF6"],
            text=[f"{c}/{adopted}" for c in elite_counts],
            textposition="outside",
        )
    )
    fig.add_hline(
        y=adopted,
        line_dash="dash",
        line_color="gray",
        annotation_text="All teams",
    )
    fig.update_layout(
        height=300,
        yaxis_title="Teams at elite threshold",
        yaxis_range=[0, adopted + 1],
        showlegend=False,
        margin=dict(t=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Team ratings")

    for team, report in reports.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{team}**")
        with col2:
            render_rating_badge(report.overall_rating)
