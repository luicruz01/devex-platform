from __future__ import annotations

from datetime import datetime, timedelta

import boto3
import pytest
from freezegun import freeze_time
from moto import mock_aws

from warehouse.metrics import DoraMetricsEngine
from warehouse.models import DoraReport
from warehouse.queries import EventQueryService

TABLE_NAME = "devex-events-test"
REGION = "us-east-1"
FROZEN_NOW = "2026-06-06T12:00:00Z"


def create_events_table(dynamodb):
    return dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
            {"AttributeName": "GSI2PK", "AttributeType": "S"},
            {"AttributeName": "GSI2SK", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "GSI2",
                "KeySchema": [
                    {"AttributeName": "GSI2PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI2SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )


def put_event(table, **fields) -> dict:
    event = {
        "version": "2.0",
        "work_id": "feat-default",
        "team": "payments",
        "stack": "python-lambda-cdk",
        "stage": "deploy-production",
        "environment": "production",
        "status": "success",
        "duration_ms": 1500,
        "timestamp": FROZEN_NOW,
        "event_id": "evt-default",
        "repo": "payments-api",
    }
    event.update(fields)

    item = {
        "PK": f"TEAM#{event['team']}",
        "SK": f"EVENT#{event['timestamp']}#{event['event_id']}",
        "GSI1PK": f"REPO#{event.get('repo', 'unknown')}",
        "GSI1SK": f"EVENT#{event['timestamp']}",
        "GSI2PK": f"STAGE#{event['stage']}",
        "GSI2SK": f"STATUS#{event['status']}#{event['timestamp']}",
        **event,
    }
    table.put_item(Item=item)
    return item


def _days_ago(days: int) -> str:
    now = datetime.fromisoformat(FROZEN_NOW.replace("Z", "+00:00"))
    return (now - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def metrics_engine():
    with mock_aws(), freeze_time(FROZEN_NOW):
        dynamodb = boto3.resource("dynamodb", region_name=REGION)
        table = create_events_table(dynamodb)
        queries = EventQueryService(TABLE_NAME, REGION)
        engine = DoraMetricsEngine(queries)
        yield engine, table


def _seed_payments_baseline(table) -> None:
    """10 successes, 2 failures, 10 branch-create events.

    Failures are timestamped before existing successes so MTTR recovery
    is measured against the next chronological success deploy (12 total deploys).
    """
    for i in range(10):
        work_id = f"feat-{i:03d}"
        deploy_day = i + 1
        branch_day = deploy_day + 3

        put_event(
            table,
            event_id=f"evt-branch-{i}",
            work_id=work_id,
            stage="branch-create",
            environment="local",
            status="success",
            timestamp=_days_ago(branch_day),
        )
        put_event(
            table,
            event_id=f"evt-deploy-{i}",
            work_id=work_id,
            stage="deploy-production",
            status="success",
            timestamp=_days_ago(deploy_day),
        )

    for i in range(2):
        put_event(
            table,
            event_id=f"evt-fail-{i}",
            work_id=f"feat-fail-{i}",
            stage="deploy-production",
            status="failure",
            timestamp=_days_ago(15 + i),
        )


def test_deployment_frequency_counts_successes(metrics_engine):
    engine, table = metrics_engine
    _seed_payments_baseline(table)

    result = engine.deployment_frequency("payments", window_days=30)

    assert result.total_deployments == 10
    assert result.deployments_per_day > 0
    assert result.team == "payments"


def test_deployment_frequency_elite_threshold(metrics_engine):
    engine, table = metrics_engine

    for i in range(35):
        put_event(
            table,
            event_id=f"evt-elite-{i}",
            work_id=f"feat-elite-{i}",
            stage="deploy-production",
            status="success",
            timestamp=_days_ago(i % 29 + 1),
        )

    result = engine.deployment_frequency("payments", window_days=30)

    assert result.total_deployments == 35
    assert result.deployments_per_day >= 1.0
    assert result.elite is True


def test_lead_time_computes_correctly(metrics_engine):
    engine, table = metrics_engine

    put_event(
        table,
        event_id="evt-lt-branch",
        work_id="feat-lead-48",
        stage="branch-create",
        environment="local",
        status="success",
        timestamp="2026-06-01T12:00:00Z",
    )
    put_event(
        table,
        event_id="evt-lt-deploy",
        work_id="feat-lead-48",
        stage="deploy-production",
        status="success",
        timestamp="2026-06-03T12:00:00Z",
    )

    result = engine.lead_time_for_changes("payments", window_days=30)

    assert result.sample_size == 1
    assert result.median_hours == pytest.approx(48.0, abs=0.1)
    assert result.elite is False


def test_lead_time_elite_threshold(metrics_engine):
    engine, table = metrics_engine

    put_event(
        table,
        event_id="evt-lt-elite-branch",
        work_id="feat-lead-12",
        stage="branch-create",
        environment="local",
        status="success",
        timestamp="2026-06-05T00:00:00Z",
    )
    put_event(
        table,
        event_id="evt-lt-elite-deploy",
        work_id="feat-lead-12",
        stage="deploy-production",
        status="success",
        timestamp="2026-06-05T12:00:00Z",
    )

    result = engine.lead_time_for_changes("payments", window_days=30)

    assert result.sample_size == 1
    assert result.median_hours == pytest.approx(12.0, abs=0.1)
    assert result.elite is True


def test_change_failure_rate_calculation(metrics_engine):
    engine, table = metrics_engine

    for i in range(10):
        put_event(
            table,
            event_id=f"evt-cfr-ok-{i}",
            stage="deploy-production",
            status="success",
            timestamp=_days_ago(i + 1),
        )
    for i in range(2):
        put_event(
            table,
            event_id=f"evt-cfr-fail-{i}",
            stage="deploy-production",
            status="failure",
            timestamp=_days_ago(i + 15),
        )

    result = engine.change_failure_rate("payments", window_days=30)

    assert result.total_deployments == 12
    assert result.failed_deployments == 2
    assert result.failure_rate_pct == pytest.approx(16.67, abs=0.01)
    assert result.elite is False


def test_change_failure_rate_elite(metrics_engine):
    engine, table = metrics_engine

    for i in range(10):
        put_event(
            table,
            event_id=f"evt-cfr-elite-{i}",
            stage="deploy-production",
            status="success",
            timestamp=_days_ago(i + 1),
        )

    result = engine.change_failure_rate("payments", window_days=30)

    assert result.total_deployments == 10
    assert result.failed_deployments == 0
    assert result.failure_rate_pct == 0.0
    assert result.elite is True


def test_mttr_calculates_recovery_time(metrics_engine):
    engine, table = metrics_engine

    put_event(
        table,
        event_id="evt-mttr-fail",
        stage="deploy-production",
        status="failure",
        timestamp="2026-06-05T10:00:00Z",
    )
    put_event(
        table,
        event_id="evt-mttr-recover",
        stage="deploy-production",
        status="success",
        timestamp="2026-06-05T12:00:00Z",
    )

    result = engine.mttr("payments", window_days=30)

    assert result.sample_size == 1
    assert result.median_hours == pytest.approx(2.0, abs=0.1)


def test_generate_report_returns_dora_report(metrics_engine):
    engine, table = metrics_engine
    _seed_payments_baseline(table)

    report = engine.generate_report("payments", window_days=30)

    assert isinstance(report, DoraReport)
    assert report.team == "payments"
    assert report.window_days == 30
    assert report.deployment_frequency.total_deployments == 10
    assert report.lead_time.sample_size > 0
    assert report.change_failure_rate.total_deployments == 12
    assert report.mttr.sample_size == 2
    assert report.overall_rating in {"elite", "high", "medium", "low"}


def test_overall_rating_elite(metrics_engine):
    engine, table = metrics_engine

    for i in range(35):
        work_id = f"feat-elite-all-{i}"
        deploy_ts = _days_ago(i % 29 + 1)
        branch_ts = (
            datetime.fromisoformat(deploy_ts.replace("Z", "+00:00"))
            - timedelta(hours=12)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        put_event(
            table,
            event_id=f"evt-elite-branch-{i}",
            work_id=work_id,
            stage="branch-create",
            environment="local",
            status="success",
            timestamp=branch_ts,
        )
        put_event(
            table,
            event_id=f"evt-elite-deploy-{i}",
            work_id=work_id,
            stage="deploy-production",
            status="success",
            timestamp=deploy_ts,
        )

    report = engine.generate_report("payments", window_days=30)

    assert report.deployment_frequency.elite is True
    assert report.lead_time.elite is True
    assert report.change_failure_rate.elite is True
    assert report.mttr.elite is True
    assert report.overall_rating == "elite"


def test_team_isolation(metrics_engine):
    engine, table = metrics_engine

    for i in range(10):
        put_event(
            table,
            team="payments",
            event_id=f"evt-pay-{i}",
            stage="deploy-production",
            status="success",
            timestamp=_days_ago(i + 1),
        )

    for i in range(50):
        put_event(
            table,
            team="platform",
            event_id=f"evt-plat-{i}",
            stage="deploy-production",
            status="success",
            timestamp=_days_ago(i % 29 + 1),
        )

    result = engine.deployment_frequency("payments", window_days=30)

    assert result.total_deployments == 10
    assert result.deployments_per_day == pytest.approx(10 / 30, abs=0.001)
    assert result.elite is False
