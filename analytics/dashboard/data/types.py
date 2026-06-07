from __future__ import annotations

from pydantic import BaseModel


class AnalystResult(BaseModel):
    team: str
    window_days: int
    overall_rating: str
    generated_at: str
    raw_analysis: str
    summary: str
    top_insight: str
    recommendation: str
    has_risk_flag: bool
