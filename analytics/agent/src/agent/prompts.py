from __future__ import annotations

from warehouse.models import DoraReport

SYSTEM_PROMPT = """
You are a DevEx Intelligence Analyst specialized in
engineering productivity metrics. You analyze DORA metrics
and delivery data to provide actionable insights for
engineering teams.

Your analysis must:
- Be specific and data-driven — reference actual numbers
- Identify the most important trend (positive or negative)
- Give one concrete, actionable recommendation
- Compare against DORA elite benchmarks where relevant
- Never assign blame to individuals
- Be concise — maximum 300 words

DORA Elite benchmarks:
- Deployment Frequency: >= 1 per day
- Lead Time for Changes: <= 24 hours
- Change Failure Rate: <= 5%
- MTTR: <= 1 hour
"""


def build_report_prompt(report: DoraReport) -> str:
    return f"""
Analyze the following DORA metrics report for team
"{report.team}" over the last {report.window_days} days.

## Metrics

### Deployment Frequency
- Total deployments: {report.deployment_frequency.total_deployments}
- Per day: {report.deployment_frequency.deployments_per_day}
- Per week: {report.deployment_frequency.deployments_per_week}
- Elite threshold (>=1/day): {"✓ ELITE" if report.deployment_frequency.elite else "✗ BELOW"}

### Lead Time for Changes
- Median: {report.lead_time.median_hours}h
- P95: {report.lead_time.p95_hours}h
- Sample size: {report.lead_time.sample_size}
- Elite threshold (<=24h): {"✓ ELITE" if report.lead_time.elite else "✗ BELOW"}

### Change Failure Rate
- Total deployments: {report.change_failure_rate.total_deployments}
- Failed: {report.change_failure_rate.failed_deployments}
- Rate: {report.change_failure_rate.failure_rate_pct}%
- Elite threshold (<=5%): {"✓ ELITE" if report.change_failure_rate.elite else "✗ BELOW"}

### MTTR
- Median recovery time: {report.mttr.median_hours}h
- P95: {report.mttr.p95_hours}h
- Sample size: {report.mttr.sample_size}
- Elite threshold (<=1h): {"✓ ELITE" if report.mttr.elite else "✗ BELOW"}

### Overall Rating: {report.overall_rating.upper()}

Provide:
1. A 2-sentence executive summary
2. The single most important insight (positive or negative)
3. One concrete recommendation with expected impact
4. A risk flag if any metric is critically below threshold
"""
