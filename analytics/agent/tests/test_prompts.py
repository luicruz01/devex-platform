from __future__ import annotations

from datetime import UTC, datetime

from agent.prompts import SYSTEM_PROMPT, build_report_prompt
from warehouse.models import (
    ChangeFailureStats,
    DeploymentFrequency,
    DoraReport,
    LeadTimeStats,
    MTTRStats,
)


def _make_report(*, elite: bool) -> DoraReport:
    return DoraReport(
        team="payments",
        generated_at=datetime.now(UTC).isoformat(),
        window_days=30,
        deployment_frequency=DeploymentFrequency(
            team="payments",
            window_days=30,
            total_deployments=25,
            deployments_per_day=1.5 if elite else 0.5,
            deployments_per_week=10.5 if elite else 3.5,
            elite=elite,
        ),
        lead_time=LeadTimeStats(
            team="payments",
            window_days=30,
            median_hours=12.0 if elite else 48.0,
            p95_hours=24.0 if elite else 96.0,
            sample_size=20,
            elite=elite,
        ),
        change_failure_rate=ChangeFailureStats(
            team="payments",
            window_days=30,
            total_deployments=25,
            failed_deployments=1 if elite else 4,
            failure_rate_pct=2.0 if elite else 16.0,
            elite=elite,
        ),
        mttr=MTTRStats(
            team="payments",
            window_days=30,
            median_hours=0.5 if elite else 2.0,
            p95_hours=1.0 if elite else 8.0,
            sample_size=4,
            elite=elite,
        ),
        overall_rating="elite" if elite else "low",
    )


def test_prompt_contains_team_name():
    report = _make_report(elite=False)
    prompt = build_report_prompt(report)

    assert "payments" in prompt


def test_prompt_contains_all_metrics():
    report = _make_report(elite=False)
    prompt = build_report_prompt(report)

    assert "25" in prompt
    assert "48.0h" in prompt
    assert "16.0%" in prompt
    assert "2.0h" in prompt


def test_prompt_marks_elite_metrics():
    report = _make_report(elite=True)
    prompt = build_report_prompt(report)

    assert "ELITE" in prompt


def test_prompt_marks_below_threshold():
    report = _make_report(elite=False)
    prompt = build_report_prompt(report)

    assert "BELOW" in prompt


def test_system_prompt_contains_benchmarks():
    assert "24 hours" in SYSTEM_PROMPT
    assert "5%" in SYSTEM_PROMPT
