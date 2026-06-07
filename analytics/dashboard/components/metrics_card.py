from __future__ import annotations

import streamlit as st
from warehouse.models import DoraReport


def render_metric_card(
    label: str,
    value: str,
    delta: str | None = None,
    is_elite: bool = False,
    help_text: str | None = None,
) -> None:
    """Render a single metric card with elite indicator."""
    icon = "⚡" if is_elite else "📊"
    st.metric(
        label=f"{icon} {label}",
        value=value,
        delta=delta,
        help=help_text,
    )


def render_dora_summary_row(report: DoraReport) -> None:
    """Render 4 metric cards in a row for a team."""
    cols = st.columns(4)
    with cols[0]:
        render_metric_card(
            "Deploy Freq",
            f"{report.deployment_frequency.deployments_per_week:.1f}/week",
            is_elite=report.deployment_frequency.elite,
            help_text="Elite: ≥7/week (1/day)",
        )
    with cols[1]:
        render_metric_card(
            "Lead Time",
            f"{report.lead_time.median_hours:.0f}h",
            is_elite=report.lead_time.elite,
            help_text="Elite: ≤24h median",
        )
    with cols[2]:
        render_metric_card(
            "Change Failure",
            f"{report.change_failure_rate.failure_rate_pct:.1f}%",
            is_elite=report.change_failure_rate.elite,
            help_text="Elite: ≤5%",
        )
    with cols[3]:
        render_metric_card(
            "MTTR",
            f"{report.mttr.median_hours:.1f}h",
            is_elite=report.mttr.elite,
            help_text="Elite: ≤1h",
        )
