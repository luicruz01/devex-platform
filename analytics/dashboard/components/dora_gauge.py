from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from warehouse.models import DoraReport

RATING_CONFIG = {
    "elite": {"color": "#22C55E", "label": "Elite", "score": 4},
    "high": {"color": "#3B82F6", "label": "High", "score": 3},
    "medium": {"color": "#F59E0B", "label": "Medium", "score": 2},
    "low": {"color": "#EF4444", "label": "Low", "score": 1},
}


def render_rating_badge(rating: str) -> None:
    config = RATING_CONFIG.get(rating, RATING_CONFIG["low"])
    st.markdown(
        f'<span style="background:{config["color"]};'
        f'color:white;padding:4px 12px;border-radius:12px;'
        f'font-weight:bold;font-size:14px">'
        f'{config["label"]}</span>',
        unsafe_allow_html=True,
    )


def render_team_gauge(report: DoraReport) -> None:
    """Render a plotly gauge for overall team rating."""
    rating = report.overall_rating
    config = RATING_CONFIG.get(rating, RATING_CONFIG["low"])
    score = config["score"]

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": f"{report.team}<br><sup>{config['label']}</sup>"},
            gauge={
                "axis": {
                    "range": [0, 4],
                    "tickvals": [1, 2, 3, 4],
                    "ticktext": ["Low", "Med", "High", "Elite"],
                },
                "bar": {"color": config["color"]},
                "steps": [
                    {"range": [0, 1], "color": "#FEE2E2"},
                    {"range": [1, 2], "color": "#FEF3C7"},
                    {"range": [2, 3], "color": "#DBEAFE"},
                    {"range": [3, 4], "color": "#DCFCE7"},
                ],
            },
        )
    )
    fig.update_layout(height=200, margin=dict(t=40, b=0, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)
