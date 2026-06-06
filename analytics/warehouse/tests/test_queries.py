from __future__ import annotations

from datetime import datetime, timedelta

import boto3
import pytest
from freezegun import freeze_time
from moto import mock_aws

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
    """Insert a DoraEvent-shaped item matching collector EventStore layout."""
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


@pytest.fixture
def query_service():
    with mock_aws(), freeze_time(FROZEN_NOW):
        dynamodb = boto3.resource("dynamodb", region_name=REGION)
        table = create_events_table(dynamodb)
        service = EventQueryService(TABLE_NAME, REGION)
        yield service, table


def test_get_team_events_filters_by_team(query_service):
    service, table = query_service

    put_event(table, team="payments", event_id="evt-pay-1")
    put_event(table, team="payments", event_id="evt-pay-2")
    put_event(table, team="platform", event_id="evt-plat-1")

    events = service.get_team_events_in_window("payments", days=30)
    assert len(events) == 2
    assert all(e["team"] == "payments" for e in events)
    event_ids = {e["event_id"] for e in events}
    assert event_ids == {"evt-pay-1", "evt-pay-2"}


def test_get_team_events_respects_window(query_service):
    service, table = query_service

    now = datetime.fromisoformat(FROZEN_NOW.replace("Z", "+00:00"))
    old_ts = (now - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent_ts = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    put_event(table, event_id="evt-old", timestamp=old_ts)
    put_event(table, event_id="evt-recent", timestamp=recent_ts)

    events = service.get_team_events_in_window("payments", days=30)
    assert len(events) == 1
    assert events[0]["event_id"] == "evt-recent"


def test_get_production_deploys_filters_stage(query_service):
    service, table = query_service

    put_event(
        table,
        event_id="evt-prod",
        stage="deploy-production",
        timestamp="2026-06-05T10:00:00Z",
    )
    put_event(
        table,
        event_id="evt-sandbox",
        stage="deploy-sandbox",
        environment="sandbox",
        timestamp="2026-06-05T11:00:00Z",
    )

    deploys = service.get_production_deploys("payments", days=30)
    assert len(deploys) == 1
    assert deploys[0]["event_id"] == "evt-prod"
    assert deploys[0]["stage"] == "deploy-production"


def test_get_events_by_work_id(query_service):
    service, table = query_service

    put_event(
        table,
        event_id="evt-w1-branch",
        work_id="feat-abc",
        stage="branch-create",
        environment="local",
        timestamp="2026-06-01T10:00:00Z",
    )
    put_event(
        table,
        event_id="evt-w1-deploy",
        work_id="feat-abc",
        stage="deploy-production",
        timestamp="2026-06-03T10:00:00Z",
    )
    put_event(
        table,
        event_id="evt-w2",
        work_id="feat-xyz",
        timestamp="2026-06-04T10:00:00Z",
    )

    events = service.get_events_by_work_id("payments", "feat-abc")
    assert len(events) == 2
    assert all(
        e.get("work_id") == "feat-abc" or e.get("correlation_id") == "feat-abc"
        for e in events
    )
    event_ids = {e["event_id"] for e in events}
    assert event_ids == {"evt-w1-branch", "evt-w1-deploy"}
