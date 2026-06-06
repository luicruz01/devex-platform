from __future__ import annotations

from pydantic import BaseModel


class DeploymentFrequency(BaseModel):
    team: str
    window_days: int
    total_deployments: int
    deployments_per_day: float
    deployments_per_week: float
    elite: bool  # True if >= 1/day (DORA elite threshold)


class LeadTimeStats(BaseModel):
    team: str
    window_days: int
    median_hours: float
    p95_hours: float
    sample_size: int
    elite: bool  # True if median <= 24h (DORA elite)


class ChangeFailureStats(BaseModel):
    team: str
    window_days: int
    total_deployments: int
    failed_deployments: int
    failure_rate_pct: float
    elite: bool  # True if <= 5% (DORA elite)


class MTTRStats(BaseModel):
    team: str
    window_days: int
    median_hours: float
    p95_hours: float
    sample_size: int
    elite: bool  # True if median <= 1h (DORA elite)


class DoraReport(BaseModel):
    team: str
    generated_at: str
    window_days: int
    deployment_frequency: DeploymentFrequency
    lead_time: LeadTimeStats
    change_failure_rate: ChangeFailureStats
    mttr: MTTRStats
    overall_rating: str  # "elite" | "high" | "medium" | "low"

    def compute_overall_rating(self) -> str:
        elite_count = sum(
            [
                self.deployment_frequency.elite,
                self.lead_time.elite,
                self.change_failure_rate.elite,
                self.mttr.elite,
            ]
        )
        if elite_count == 4:
            return "elite"
        if elite_count >= 3:
            return "high"
        if elite_count >= 2:
            return "medium"
        return "low"
