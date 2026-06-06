from __future__ import annotations

from datetime import UTC, datetime, timedelta

import boto3
from boto3.dynamodb.conditions import Attr, Key


class EventQueryService:
    def __init__(self, table_name: str, region: str) -> None:
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def get_team_events_in_window(
        self,
        team: str,
        days: int = 30,
    ) -> list[dict]:
        """
        Get all events for a team within the last N days.
        Uses PK = TEAM#{team} and filters by timestamp.
        """
        cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        items: list[dict] = []
        kwargs: dict = {
            "KeyConditionExpression": (
                Key("PK").eq(f"TEAM#{team}") & Key("SK").begins_with("EVENT#")
            ),
            "FilterExpression": Attr("timestamp").gte(cutoff),
            "ScanIndexForward": False,
        }
        while True:
            response = self.table.query(**kwargs)
            items.extend(response.get("Items", []))
            if "LastEvaluatedKey" not in response:
                break
            kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        return items

    def get_production_deploys(
        self,
        team: str,
        days: int = 30,
    ) -> list[dict]:
        """
        Get deploy-production events for a team.
        Filters by stage=deploy-production.
        """
        events = self.get_team_events_in_window(team, days)
        return [e for e in events if e.get("stage") == "deploy-production"]

    def get_events_by_work_id(
        self,
        team: str,
        work_id: str,
    ) -> list[dict]:
        """
        Get all events for a specific work_id.
        Used for lead time calculation.
        """
        events = self.get_team_events_in_window(team, days=90)
        return [
            e
            for e in events
            if e.get("work_id") == work_id or e.get("correlation_id") == work_id
        ]
