from __future__ import annotations

from datetime import UTC, datetime

from warehouse.models import (
    ChangeFailureStats,
    DeploymentFrequency,
    DoraReport,
    LeadTimeStats,
    MTTRStats,
)
from warehouse.queries import EventQueryService


class DoraMetricsEngine:
    def __init__(self, query_service: EventQueryService) -> None:
        self.queries = query_service

    def deployment_frequency(
        self,
        team: str,
        window_days: int = 30,
    ) -> DeploymentFrequency:
        deploys = self.queries.get_production_deploys(team, window_days)
        successful = [d for d in deploys if d.get("status") == "success"]
        total = len(successful)
        per_day = total / window_days if window_days > 0 else 0
        return DeploymentFrequency(
            team=team,
            window_days=window_days,
            total_deployments=total,
            deployments_per_day=round(per_day, 3),
            deployments_per_week=round(per_day * 7, 3),
            elite=per_day >= 1.0,
        )

    def lead_time_for_changes(
        self,
        team: str,
        window_days: int = 30,
    ) -> LeadTimeStats:
        """
        Lead time = time from branch-create to deploy-production.
        Groups events by work_id, finds branch-create and
        deploy-production timestamps, computes difference.
        """
        events = self.queries.get_team_events_in_window(team, window_days)

        by_work_id: dict[str, list[dict]] = {}
        for e in events:
            wid = e.get("work_id", "")
            if wid and wid != "N/A":
                by_work_id.setdefault(wid, []).append(e)

        lead_times_hours: list[float] = []
        for _work_id, work_events in by_work_id.items():
            branch_events = [
                e for e in work_events if e.get("stage") == "branch-create"
            ]
            deploy_events = [
                e
                for e in work_events
                if e.get("stage") == "deploy-production"
                and e.get("status") == "success"
            ]
            if branch_events and deploy_events:
                start = min(e["timestamp"] for e in branch_events)
                end = max(e["timestamp"] for e in deploy_events)
                try:
                    delta = datetime.fromisoformat(
                        end.replace("Z", "+00:00")
                    ) - datetime.fromisoformat(start.replace("Z", "+00:00"))
                    lead_times_hours.append(delta.total_seconds() / 3600)
                except Exception:
                    pass

        if not lead_times_hours:
            return LeadTimeStats(
                team=team,
                window_days=window_days,
                median_hours=0,
                p95_hours=0,
                sample_size=0,
                elite=False,
            )

        sorted_times = sorted(lead_times_hours)
        n = len(sorted_times)
        median = sorted_times[n // 2]
        p95 = sorted_times[int(n * 0.95)]

        return LeadTimeStats(
            team=team,
            window_days=window_days,
            median_hours=round(median, 2),
            p95_hours=round(p95, 2),
            sample_size=n,
            elite=median <= 24.0,
        )

    def change_failure_rate(
        self,
        team: str,
        window_days: int = 30,
    ) -> ChangeFailureStats:
        deploys = self.queries.get_production_deploys(team, window_days)
        total = len(deploys)
        failed = len([d for d in deploys if d.get("status") == "failure"])
        rate = (failed / total * 100) if total > 0 else 0
        return ChangeFailureStats(
            team=team,
            window_days=window_days,
            total_deployments=total,
            failed_deployments=failed,
            failure_rate_pct=round(rate, 2),
            elite=rate <= 5.0,
        )

    def mttr(
        self,
        team: str,
        window_days: int = 30,
    ) -> MTTRStats:
        """
        MTTR = time from deploy-production failure to
        next deploy-production success for same team.
        """
        deploys = self.queries.get_production_deploys(team, window_days)
        deploys_sorted = sorted(deploys, key=lambda e: e.get("timestamp", ""))

        recovery_times: list[float] = []
        i = 0
        while i < len(deploys_sorted):
            event = deploys_sorted[i]
            if event.get("status") == "failure":
                for j in range(i + 1, len(deploys_sorted)):
                    if deploys_sorted[j].get("status") == "success":
                        try:
                            fail_ts = event["timestamp"]
                            recover_ts = deploys_sorted[j]["timestamp"]
                            delta = datetime.fromisoformat(
                                recover_ts.replace("Z", "+00:00")
                            ) - datetime.fromisoformat(
                                fail_ts.replace("Z", "+00:00")
                            )
                            recovery_times.append(delta.total_seconds() / 3600)
                        except Exception:
                            pass
                        break
            i += 1

        if not recovery_times:
            return MTTRStats(
                team=team,
                window_days=window_days,
                median_hours=0,
                p95_hours=0,
                sample_size=0,
                elite=True,
            )

        sorted_rt = sorted(recovery_times)
        n = len(sorted_rt)
        return MTTRStats(
            team=team,
            window_days=window_days,
            median_hours=round(sorted_rt[n // 2], 2),
            p95_hours=round(sorted_rt[int(n * 0.95)], 2),
            sample_size=n,
            elite=sorted_rt[n // 2] <= 1.0,
        )

    def generate_report(
        self,
        team: str,
        window_days: int = 30,
    ) -> DoraReport:
        freq = self.deployment_frequency(team, window_days)
        lt = self.lead_time_for_changes(team, window_days)
        cfr = self.change_failure_rate(team, window_days)
        mttr_stats = self.mttr(team, window_days)

        report = DoraReport(
            team=team,
            generated_at=datetime.now(UTC).isoformat(),
            window_days=window_days,
            deployment_frequency=freq,
            lead_time=lt,
            change_failure_rate=cfr,
            mttr=mttr_stats,
            overall_rating="low",
        )
        report.overall_rating = report.compute_overall_rating()
        return report
