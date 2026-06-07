from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from warehouse.models import DoraReport

from components.dora_gauge import RATING_CONFIG, render_team_gauge


def render_overview(reports: dict[str, DoraReport]) -> None:
    st.title("🚀 DevEx Intelligence — Engineering Overview")
    st.caption(
        f"Last 30 days · {len(reports)} teams · Powered by devex-platform"
    )

    st.divider()

    total_deploys = sum(
        r.deployment_frequency.total_deployments for r in reports.values()
    )
    elite_teams = sum(
        1 for r in reports.values() if r.overall_rating == "elite"
    )
    avg_lead_time = sum(r.lead_time.median_hours for r in reports.values()) / len(
        reports
    )
    avg_cfr = sum(
        r.change_failure_rate.failure_rate_pct for r in reports.values()
    ) / len(reports)

    cols = st.columns(4)
    with cols[0]:
        st.metric(
            "Total Deployments",
            total_deploys,
            help="Across all teams, last 30 days",
        )
    with cols[1]:
        st.metric(
            "Elite Teams",
            f"{elite_teams}/{len(reports)}",
            help="Teams meeting all 4 DORA elite thresholds",
        )
    with cols[2]:
        st.metric(
            "Avg Lead Time",
            f"{avg_lead_time:.0f}h",
            help="Median across teams",
        )
    with cols[3]:
        st.metric(
            "Avg Failure Rate",
            f"{avg_cfr:.1f}%",
            help="Change failure rate across teams",
        )

    st.divider()
    st.subheader("Team Performance")

    cols = st.columns(len(reports))
    for i, (_team, report) in enumerate(reports.items()):
        with cols[i]:
            render_team_gauge(report)

    st.divider()
    st.subheader("DORA Metrics by Team")

    df = pd.DataFrame(
        [
            {
                "Team": name,
                "Deploy/week": report.deployment_frequency.deployments_per_week,
                "Lead Time (h)": report.lead_time.median_hours,
                "Failure Rate (%)": report.change_failure_rate.failure_rate_pct,
                "MTTR (h)": report.mttr.median_hours,
                "Rating": report.overall_rating.upper(),
            }
            for name, report in reports.items()
        ]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Lead Time by Team")
    fig = go.Figure(
        go.Bar(
            x=df["Team"],
            y=df["Lead Time (h)"],
            marker_color=[
                RATING_CONFIG.get(r.overall_rating, RATING_CONFIG["low"])["color"]
                for r in reports.values()
            ],
            text=df["Lead Time (h)"].apply(lambda x: f"{x:.0f}h"),
            textposition="outside",
        )
    )
    fig.add_hline(
        y=24,
        line_dash="dash",
        line_color="green",
        annotation_text="Elite threshold (24h)",
    )
    fig.update_layout(
        height=300,
        yaxis_title="Median Lead Time (hours)",
        showlegend=False,
        margin=dict(t=20),
    )
    st.plotly_chart(fig, use_container_width=True)
