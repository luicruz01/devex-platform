from __future__ import annotations

from datetime import UTC, datetime

import pytest

from agent.analyst import AnalystResult, DoraAnalyst
from agent.config import Settings
from warehouse.models import (
    ChangeFailureStats,
    DeploymentFrequency,
    DoraReport,
    LeadTimeStats,
    MTTRStats,
)


@pytest.fixture
def mock_anthropic(mocker):
    mock_client = mocker.MagicMock()
    mock_message = mocker.MagicMock()
    mock_message.content = [
        mocker.MagicMock(
            text="""
        Executive summary: The payments team shows strong
        deployment frequency but elevated lead time.

        Key insight: Lead time of 48h exceeds the 24h elite
        threshold, suggesting review bottlenecks.

        Recommendation: Implement smaller PR sizes to reduce
        review latency. Expected impact: 30-40% lead time reduction.

        Risk flag: Change failure rate at 16% is above the 5%
        elite threshold and requires immediate attention.
      """
        )
    ]
    mock_client.messages.create.return_value = mock_message
    mocker.patch("anthropic.Anthropic", return_value=mock_client)
    return mock_client


@pytest.fixture
def settings():
    return Settings(anthropic_api_key="test-key")


@pytest.fixture
def sample_report():
    return DoraReport(
        team="payments",
        generated_at=datetime.now(UTC).isoformat(),
        window_days=30,
        deployment_frequency=DeploymentFrequency(
            team="payments",
            window_days=30,
            total_deployments=25,
            deployments_per_day=0.83,
            deployments_per_week=5.83,
            elite=False,
        ),
        lead_time=LeadTimeStats(
            team="payments",
            window_days=30,
            median_hours=48.0,
            p95_hours=96.0,
            sample_size=20,
            elite=False,
        ),
        change_failure_rate=ChangeFailureStats(
            team="payments",
            window_days=30,
            total_deployments=25,
            failed_deployments=4,
            failure_rate_pct=16.0,
            elite=False,
        ),
        mttr=MTTRStats(
            team="payments",
            window_days=30,
            median_hours=2.0,
            p95_hours=8.0,
            sample_size=4,
            elite=False,
        ),
        overall_rating="low",
    )


@pytest.fixture
def elite_report():
    return DoraReport(
        team="payments",
        generated_at=datetime.now(UTC).isoformat(),
        window_days=30,
        deployment_frequency=DeploymentFrequency(
            team="payments",
            window_days=30,
            total_deployments=45,
            deployments_per_day=1.5,
            deployments_per_week=10.5,
            elite=True,
        ),
        lead_time=LeadTimeStats(
            team="payments",
            window_days=30,
            median_hours=12.0,
            p95_hours=24.0,
            sample_size=30,
            elite=True,
        ),
        change_failure_rate=ChangeFailureStats(
            team="payments",
            window_days=30,
            total_deployments=45,
            failed_deployments=1,
            failure_rate_pct=2.0,
            elite=True,
        ),
        mttr=MTTRStats(
            team="payments",
            window_days=30,
            median_hours=0.5,
            p95_hours=1.0,
            sample_size=1,
            elite=True,
        ),
        overall_rating="elite",
    )


def test_analyze_calls_claude_api(mock_anthropic, settings, sample_report):
    analyst = DoraAnalyst(settings)
    analyst.analyze(sample_report)

    mock_anthropic.messages.create.assert_called_once()
    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-20250514"


def test_analyze_returns_analyst_result(mock_anthropic, settings, sample_report):
    analyst = DoraAnalyst(settings)
    result = analyst.analyze(sample_report)

    assert isinstance(result, AnalystResult)
    assert result.team == "payments"
    assert result.window_days == 30
    assert result.overall_rating == "low"
    assert result.raw_analysis
    assert result.summary
    assert result.top_insight
    assert result.recommendation
    assert result.generated_at


def test_risk_flag_high_failure_rate(mock_anthropic, settings, sample_report):
    analyst = DoraAnalyst(settings)
    result = analyst.analyze(sample_report)

    assert result.has_risk_flag is True


def test_risk_flag_not_set_for_healthy_team(mock_anthropic, settings, elite_report):
    analyst = DoraAnalyst(settings)
    result = analyst.analyze(elite_report)

    assert result.has_risk_flag is False


def test_extract_summary_returns_two_sentences(settings):
    analyst = DoraAnalyst(settings)
    text = "First sentence here. Second sentence follows. Third is extra."
    summary = analyst._extract_summary(text)

    assert summary.endswith(".")


def test_dry_run_skips_llm(mocker, sample_report):
    mocker.patch(
        "agent.main.Settings",
        return_value=Settings(anthropic_api_key="test-key"),
    )
    mocker.patch("agent.main.EventQueryService")
    mock_engine = mocker.patch("agent.main.DoraMetricsEngine")
    mock_engine.return_value.generate_report.return_value = sample_report
    mock_analyst = mocker.patch("agent.main.DoraAnalyst")
    mocker.patch("agent.main.emit_event")

    from agent.main import handler

    result = handler({"team": "payments", "dry_run": True}, None)

    assert result["statusCode"] == 200
    assert result["dry_run"] is True
    mock_analyst.assert_not_called()
