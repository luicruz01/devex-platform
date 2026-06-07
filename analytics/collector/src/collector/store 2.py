from __future__ import annotations

import time

import boto3
from boto3.dynamodb.conditions import Key
from dora_event import DoraEventV2


class EventStore:
    def __init__(self, table_name: str, region: str) -> None:
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def save(self, event: DoraEventV2) -> dict:
        """
        Persist event to DynamoDB.
        Returns the item as stored.
        """
        item = {
            "PK": f"TEAM#{event.team}",
            "SK": f"EVENT#{event.timestamp}#{event.event_id}",
            "GSI1PK": f"REPO#{event.repo or 'unknown'}",
            "GSI1SK": f"EVENT#{event.timestamp}",
            "GSI2PK": f"STAGE#{event.stage}",
            "GSI2SK": f"STATUS#{event.status}#{event.timestamp}",
            **event.model_dump(exclude_none=True),
            "ttl": int(time.time()) + (90 * 24 * 60 * 60),
        }
        self.table.put_item(Item=item)
        return item

    def get_team_events(self, team: str, limit: int = 100) -> list[dict]:
        """Get recent events for a team."""
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"TEAM#{team}"),
            ScanIndexForward=False,
            Limit=limit,
        )
        return response.get("Items", [])

    def get_stage_failures(self, stage: str, limit: int = 50) -> list[dict]:
        """Get recent failures for a specific stage."""
        response = self.table.query(
            IndexName="GSI2",
            KeyConditionExpression=(
                Key("GSI2PK").eq(f"STAGE#{stage}")
                & Key("GSI2SK").begins_with("STATUS#failure")
            ),
            ScanIndexForward=False,
            Limit=limit,
        )
        return response.get("Items", [])
