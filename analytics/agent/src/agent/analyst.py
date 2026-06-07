from __future__ import annotations

from datetime import UTC, datetime

import anthropic
from pydantic import BaseModel
from warehouse.models import DoraReport
from warehouse.queries import EventQueryService

from agent.config import Settings
from agent.prompts import SYSTEM_PROMPT, build_report_prompt


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


class DoraAnalyst:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def analyze(
        self,
        report: DoraReport,
        query_service: EventQueryService | None = None,
    ) -> AnalystResult:
        """Generate LLM-powered analysis of a DORA report."""
        _ = query_service
        prompt = build_report_prompt(report)

        message = self.client.messages.create(
            model=self.settings.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text

        has_risk = any(
            [
                report.change_failure_rate.failure_rate_pct > 15,
                report.lead_time.median_hours > 168,
                report.mttr.median_hours > 24,
                report.deployment_frequency.deployments_per_week < 1,
            ]
        )

        return AnalystResult(
            team=report.team,
            window_days=report.window_days,
            overall_rating=report.overall_rating,
            generated_at=datetime.now(UTC).isoformat(),
            raw_analysis=raw,
            summary=self._extract_summary(raw),
            top_insight=self._extract_insight(raw),
            recommendation=self._extract_recommendation(raw),
            has_risk_flag=has_risk,
        )

    def _extract_summary(self, text: str) -> str:
        """Extract first 2 sentences from analysis."""
        sentences = text.replace("\n", " ").split(". ")
        return ". ".join(sentences[:2]) + "." if sentences else text[:200]

    def _extract_insight(self, text: str) -> str:
        """Extract the key insight paragraph."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for i, line in enumerate(lines):
            if any(
                word in line.lower()
                for word in ["insight", "notable", "significant", "important"]
            ):
                return lines[i + 1] if i + 1 < len(lines) else line
        return lines[1] if len(lines) > 1 else text[:200]

    def _extract_recommendation(self, text: str) -> str:
        """Extract the recommendation."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for i, line in enumerate(lines):
            if any(
                word in line.lower()
                for word in ["recommend", "suggest", "should", "action"]
            ):
                return (
                    lines[i]
                    if lines[i] != line
                    else (lines[i + 1] if i + 1 < len(lines) else line)
                )
        return lines[-1] if lines else text[-200:]
