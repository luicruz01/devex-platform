from __future__ import annotations

from typing import Any

from devex_schema import DoraEventV2, emit_event
from warehouse.metrics import DoraMetricsEngine
from warehouse.queries import EventQueryService

from agent.analyst import DoraAnalyst
from agent.config import Settings


def handler(event: dict, context: Any) -> dict:
    """
    EventBridge scheduled handler.

    Event format:
    {
      "team": "payments",           # required
      "window_days": 30,            # optional, default 30
      "dry_run": false              # optional, skips LLM call
    }
    """
    team = event.get("team")
    if not team:
        return {"error": "team is required", "statusCode": 400}

    window_days = event.get("window_days", 30)
    dry_run = event.get("dry_run", False)

    settings = Settings()

    query_service = EventQueryService(settings.table_name, settings.aws_region)
    engine = DoraMetricsEngine(query_service)
    report = engine.generate_report(team, window_days)

    emit_event(
        DoraEventV2(
            work_id=f"ANALYST-{team}",
            team="platform",
            stack="python-lambda-cdk",
            stage="analyze",
            environment="production",
            status="success",
            service="dora-analyst",
        )
    )

    if dry_run:
        return {
            "statusCode": 200,
            "team": team,
            "report": report.model_dump(),
            "dry_run": True,
        }

    analyst = DoraAnalyst(settings)
    result = analyst.analyze(report, query_service)

    return {
        "statusCode": 200,
        "team": team,
        "overall_rating": result.overall_rating,
        "has_risk_flag": result.has_risk_flag,
        "summary": result.summary,
        "recommendation": result.recommendation,
        "generated_at": result.generated_at,
    }
