"""Realistic mock data for demo mode when AWS credentials are unavailable."""

from __future__ import annotations

from datetime import UTC, datetime

from warehouse.models import (
    ChangeFailureStats,
    DeploymentFrequency,
    DoraReport,
    LeadTimeStats,
    MTTRStats,
)

from data.types import AnalystResult

MOCK_TEAMS = ["payments", "platform", "identity", "notifications"]

_GENERATED_AT = datetime.now(UTC).isoformat()
_WINDOW_DAYS = 30


def _deployment(
    team: str,
    total: int,
    elite: bool,
) -> DeploymentFrequency:
    per_day = total / _WINDOW_DAYS
    return DeploymentFrequency(
        team=team,
        window_days=_WINDOW_DAYS,
        total_deployments=total,
        deployments_per_day=per_day,
        deployments_per_week=per_day * 7,
        elite=elite,
    )


def _lead_time(
    team: str,
    median: float,
    p95: float,
    elite: bool,
    sample_size: int = 48,
) -> LeadTimeStats:
    return LeadTimeStats(
        team=team,
        window_days=_WINDOW_DAYS,
        median_hours=median,
        p95_hours=p95,
        sample_size=sample_size,
        elite=elite,
    )


def _change_failure(
    team: str,
    total: int,
    rate_pct: float,
    elite: bool,
) -> ChangeFailureStats:
    failed = max(1, round(total * rate_pct / 100)) if rate_pct > 0 else 0
    if failed == 0 and rate_pct > 0:
        failed = 1
        total = max(total, round(100 / rate_pct))
    return ChangeFailureStats(
        team=team,
        window_days=_WINDOW_DAYS,
        total_deployments=total,
        failed_deployments=failed,
        failure_rate_pct=rate_pct,
        elite=elite,
    )


def _mttr(
    team: str,
    median: float,
    p95: float,
    elite: bool,
    sample_size: int = 8,
) -> MTTRStats:
    return MTTRStats(
        team=team,
        window_days=_WINDOW_DAYS,
        median_hours=median,
        p95_hours=p95,
        sample_size=sample_size,
        elite=elite,
    )


def _report(
    team: str,
    total_deploys: int,
    df_elite: bool,
    lead_median: float,
    lead_p95: float,
    lead_elite: bool,
    cfr_pct: float,
    cfr_elite: bool,
    mttr_median: float,
    mttr_p95: float,
    mttr_elite: bool,
    overall_rating: str,
    lead_sample: int = 48,
    mttr_sample: int = 8,
) -> DoraReport:
    return DoraReport(
        team=team,
        generated_at=_GENERATED_AT,
        window_days=_WINDOW_DAYS,
        deployment_frequency=_deployment(team, total_deploys, df_elite),
        lead_time=_lead_time(team, lead_median, lead_p95, lead_elite, lead_sample),
        change_failure_rate=_change_failure(team, total_deploys, cfr_pct, cfr_elite),
        mttr=_mttr(team, mttr_median, mttr_p95, mttr_elite, mttr_sample),
        overall_rating=overall_rating,
    )


MOCK_REPORTS: dict[str, DoraReport] = {
    "payments": _report(
        team="payments",
        total_deploys=28,
        df_elite=True,
        lead_median=18,
        lead_p95=36,
        lead_elite=True,
        cfr_pct=4.2,
        cfr_elite=True,
        mttr_median=0.8,
        mttr_p95=2.1,
        mttr_elite=True,
        overall_rating="elite",
        lead_sample=62,
        mttr_sample=5,
    ),
    "platform": _report(
        team="platform",
        total_deploys=15,
        df_elite=False,
        lead_median=42,
        lead_p95=96,
        lead_elite=False,
        cfr_pct=3.1,
        cfr_elite=True,
        mttr_median=0.5,
        mttr_p95=1.4,
        mttr_elite=True,
        overall_rating="high",
        lead_sample=34,
        mttr_sample=3,
    ),
    "identity": _report(
        team="identity",
        total_deploys=4,
        df_elite=False,
        lead_median=120,
        lead_p95=240,
        lead_elite=False,
        cfr_pct=18.5,
        cfr_elite=False,
        mttr_median=6.2,
        mttr_p95=18.0,
        mttr_elite=False,
        overall_rating="low",
        lead_sample=19,
        mttr_sample=11,
    ),
    "notifications": _report(
        team="notifications",
        total_deploys=12,
        df_elite=False,
        lead_median=28,
        lead_p95=72,
        lead_elite=False,
        cfr_pct=7.3,
        cfr_elite=False,
        mttr_median=1.2,
        mttr_p95=3.8,
        mttr_elite=False,
        overall_rating="medium",
        lead_sample=41,
        mttr_sample=6,
    ),
}

MOCK_ANALYST_RESULTS: dict[str, AnalystResult] = {
    "payments": AnalystResult(
        team="payments",
        window_days=_WINDOW_DAYS,
        overall_rating="elite",
        generated_at=_GENERATED_AT,
        raw_analysis="",
        summary=(
            "Payments is operating at elite DORA performance across all four metrics, "
            "deploying nearly daily with a median lead time of 18 hours. "
            "Change failure rate (4.2%) and MTTR (0.8h) both sit comfortably within elite thresholds."
        ),
        top_insight=(
            "The team's consistent trunk-based deployment cadence — 28 deploys in 30 days — "
            "correlates with sub-24h lead times. Failed changes are recovered in under an hour, "
            "suggesting strong observability and rollback automation on the golden path."
        ),
        recommendation=(
            "Document the payments deployment playbook as a reference implementation for other teams. "
            "Focus next on reducing p95 lead time (36h) by profiling the slowest PRs in the pipeline."
        ),
        has_risk_flag=False,
    ),
    "platform": AnalystResult(
        team="platform",
        window_days=_WINDOW_DAYS,
        overall_rating="high",
        generated_at=_GENERATED_AT,
        raw_analysis="",
        summary=(
            "Platform delivers reliably with elite change failure rate (3.1%) and MTTR (0.5h), "
            "but median lead time of 42 hours prevents an overall elite rating. "
            "Deployment frequency at 3.5/week is steady but below the daily-deploy elite bar."
        ),
        top_insight=(
            "Lead time p95 spikes to 96 hours — roughly 4x the median — indicating a long tail "
            "of changes waiting on cross-team approvals or manual infra steps. "
            "Infrastructure changes account for most of the delay based on stage-level event data."
        ),
        recommendation=(
            "Introduce a platform-internal fast lane for low-risk changes (docs, config) "
            "with automated approval. Target reducing median lead time below 24h within one sprint "
            "by parallelizing CDK synth and integration tests."
        ),
        has_risk_flag=False,
    ),
    "identity": AnalystResult(
        team="identity",
        window_days=_WINDOW_DAYS,
        overall_rating="low",
        generated_at=_GENERATED_AT,
        raw_analysis="",
        summary=(
            "Identity is the lowest-performing team with only 4 deployments in 30 days "
            "and a change failure rate of 18.5% — nearly 4x the elite threshold. "
            "Median lead time of 120 hours and MTTR of 6.2 hours indicate systemic delivery friction."
        ),
        top_insight=(
            "Nearly one in five deployments fails, and recovery takes over 6 hours on median. "
            "Failure events cluster around auth-service deploys to staging, suggesting "
            "insufficient pre-production validation and missing contract tests against downstream consumers."
        ),
        recommendation=(
            "Pause feature work for one sprint to stabilize the deploy pipeline: add smoke tests "
            "before staging promotion, enable automatic rollback on health-check failure, "
            "and pair with the platform team to adopt the golden-path CI template."
        ),
        has_risk_flag=True,
    ),
    "notifications": AnalystResult(
        team="notifications",
        window_days=_WINDOW_DAYS,
        overall_rating="medium",
        generated_at=_GENERATED_AT,
        raw_analysis="",
        summary=(
            "Notifications is on an improvement trajectory — 12 deploys in 30 days (up from 8 "
            "the prior period) with lead time trending down to 28 hours. "
            "Change failure rate (7.3%) and MTTR (1.2h) remain above elite but are moving in the right direction."
        ),
        top_insight=(
            "The team adopted devex init and branch commands 6 weeks ago, and deployment frequency "
            "has increased 50% since. Remaining friction is in the test stage — "
            "3 of 4 recent failures occurred during integration test timeouts."
        ),
        recommendation=(
            "Split the integration test suite into parallel shards to cut pipeline duration below 15 minutes. "
            "This should unlock daily deploys and pull change failure rate below 5% within two sprints."
        ),
        has_risk_flag=False,
    ),
}
