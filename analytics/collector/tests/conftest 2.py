import boto3
import pytest
from moto import mock_aws

from collector.config import get_settings

TABLE_NAME = "devex-events-test"
REGION = "us-east-1"


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


@pytest.fixture
def mock_table(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("DEVEX_EVENTS_TABLE", TABLE_NAME)
    monkeypatch.setenv("AWS_REGION", REGION)
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)
    get_settings.cache_clear()

    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name=REGION)
        table = create_events_table(dynamodb)
        yield table

    get_settings.cache_clear()


def valid_event_payload(**overrides) -> dict:
    payload = {
        "version": "2.0",
        "work_id": "feat-123",
        "team": "payments",
        "stack": "python-lambda-cdk",
        "stage": "deploy-production",
        "environment": "production",
        "status": "success",
        "duration_ms": 1500,
        "timestamp": "2026-06-06T12:00:00Z",
        "event_id": "evt-test-001",
    }
    payload.update(overrides)
    return payload
