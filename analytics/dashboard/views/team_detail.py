from __future__ import annotations

import streamlit as st
from warehouse.models import DoraReport

from components.dora_gauge import render_rating_badge
from components.metrics_card import render_dora_summary_row
from data.types import AnalystResult


def render_team_detail(
    team: str,
    report: DoraReport,
    analyst_result: AnalystResult | None = None,
) -> None:
    st.title(f"📊 {team.capitalize()} — Team Detail")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(
            f"Last {report.window_days} days · "
            f"Generated {report.generated_at[:10]}"
        )
    with col2:
        render_rating_badge(report.overall_rating)

    st.divider()
    render_dora_summary_row(report)
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Deployment Frequency")
        st.metric(
            "Total deploys (30d)",
            report.deployment_frequency.total_deployments,
        )
        st.metric(
            "Per week",
            f"{report.deployment_frequency.deployments_per_week:.1f}",
        )
        if report.deployment_frequency.elite:
            st.success("✓ Elite: deploying daily or more")
        else:
            st.warning(
                f"Target: ≥7/week. "
                f"Current: {report.deployment_frequency.deployments_per_week:.1f}/week"
            )

    with col2:
        st.subheader("Change Failure Rate")
        st.metric(
            "Failure rate",
            f"{report.change_failure_rate.failure_rate_pct:.1f}%",
        )
        st.metric(
            "Failed deploys",
            f"{report.change_failure_rate.failed_deployments}"
            f"/{report.change_failure_rate.total_deployments}",
        )
        if report.change_failure_rate.elite:
            st.success("✓ Elite: failure rate ≤5%")
        else:
            st.error("Above elite threshold (5%). Review recent failures.")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Lead Time for Changes")
        st.metric("Median", f"{report.lead_time.median_hours:.0f}h")
        st.metric("P95", f"{report.lead_time.p95_hours:.0f}h")
        st.caption(f"Sample: {report.lead_time.sample_size} changes")

    with col2:
        st.subheader("MTTR")
        st.metric("Median recovery", f"{report.mttr.median_hours:.1f}h")
        st.metric("P95", f"{report.mttr.p95_hours:.1f}h")
        st.caption(f"Sample: {report.mttr.sample_size} incidents")

    if analyst_result:
        st.divider()
        st.subheader("🤖 AI Analysis")

        if analyst_result.has_risk_flag:
            st.error(
                "⚠️ Risk flag: one or more metrics critically below threshold"
            )

        with st.expander("Executive Summary", expanded=True):
            st.write(analyst_result.summary)

        with st.expander("Key Insight"):
            st.write(analyst_result.top_insight)

        with st.expander("Recommendation"):
            st.info(f"💡 {analyst_result.recommendation}")
