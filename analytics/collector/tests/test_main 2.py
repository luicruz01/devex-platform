import boto3
import pytest
from fastapi.testclient import TestClient

from collector.main import app
from tests.conftest import TABLE_NAME, valid_event_payload


@pytest.fixture
def client(mock_table):
    yield TestClient(app)


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_collect_valid_event(client):
    payload = valid_event_payload()
    response = client.post("/events", json=payload)
    assert response.status_code == 202
    body = response.json()
    assert body["accepted"] is True
    assert body["event_id"] == payload["event_id"]
    assert body["work_id"] == payload["work_id"]
    assert body["stage"] == payload["stage"]


def test_collect_missing_required_field(client):
    payload = valid_event_payload()
    del payload["work_id"]
    response = client.post("/events", json=payload)
    assert response.status_code == 422


def test_collect_invalid_status(client):
    payload = valid_event_payload(status="unknown")
    response = client.post("/events", json=payload)
    assert response.status_code == 422


def test_event_persisted_to_dynamodb(client, mock_table):
    payload = valid_event_payload(event_id="evt-persist-001")
    response = client.post("/events", json=payload)
    assert response.status_code == 202

    table = boto3.resource("dynamodb", region_name="us-east-1").Table(TABLE_NAME)
    item = table.get_item(
        Key={
            "PK": f"TEAM#{payload['team']}",
            "SK": f"EVENT#{payload['timestamp']}#{payload['event_id']}",
        },
    )
    assert "Item" in item
    assert item["Item"]["work_id"] == payload["work_id"]
    assert item["Item"]["event_id"] == payload["event_id"]
