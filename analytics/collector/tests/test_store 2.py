import time

import pytest
from dora_event import DoraEventV2

from collector.store import EventStore
from tests.conftest import TABLE_NAME, REGION, create_events_table


@pytest.fixture
def store():
    import boto3
    from moto import mock_aws

    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name=REGION)
        create_events_table(dynamodb)
        yield EventStore(TABLE_NAME, REGION)


def _event(**overrides) -> DoraEventV2:
    defaults = {
        "work_id": "feat-123",
        "team": "payments",
        "stack": "python-lambda-cdk",
        "stage": "deploy-production",
        "environment": "production",
        "status": "success",
        "duration_ms": 1500,
        "timestamp": "2026-06-06T12:00:00Z",
        "event_id": "evt-store-001",
    }
    defaults.update(overrides)
    return DoraEventV2(**defaults)


def test_save_returns_item(store):
    event = _event()
    item = store.save(event)

    assert item["PK"] == f"TEAM#{event.team}"
    assert item["SK"] == f"EVENT#{event.timestamp}#{event.event_id}"
    assert item["GSI1PK"] == "REPO#unknown"
    assert item["GSI1SK"] == f"EVENT#{event.timestamp}"
    assert item["GSI2PK"] == f"STAGE#{event.stage}"
    assert item["GSI2SK"] == f"STATUS#{event.status}#{event.timestamp}"


def test_save_sets_ttl(store):
    before = int(time.time())
    item = store.save(_event(event_id="evt-ttl-001"))
    after = int(time.time())

    ttl = item["ttl"]
    expected_min = before + (90 * 24 * 60 * 60)
    expected_max = after + (90 * 24 * 60 * 60)
    assert expected_min <= ttl <= expected_max


def test_get_team_events_returns_saved(store):
    for idx in range(3):
        store.save(
            _event(
                event_id=f"evt-team-{idx}",
                timestamp=f"2026-06-06T12:00:0{idx}Z",
            ),
        )

    events = store.get_team_events("payments")
    assert len(events) == 3
    event_ids = {event["event_id"] for event in events}
    assert event_ids == {"evt-team-0", "evt-team-1", "evt-team-2"}


def test_get_stage_failures_filters_correctly(store):
    store.save(
        _event(
            event_id="evt-success",
            status="success",
            timestamp="2026-06-06T12:00:00Z",
        ),
    )
    store.save(
        _event(
            event_id="evt-failure",
            status="failure",
            timestamp="2026-06-06T12:00:01Z",
            failure_reason="deploy timeout",
        ),
    )

    failures = store.get_stage_failures("deploy-production")
    assert len(failures) == 1
    assert failures[0]["event_id"] == "evt-failure"
    assert failures[0]["status"] == "failure"
