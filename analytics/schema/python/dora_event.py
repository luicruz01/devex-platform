from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

DoraStatus = Literal["success", "failure"]
DoraEnvironment = Literal["sandbox", "staging", "production", "local"]
DoraStage = Literal[
    "init",
    "branch-create",
    "check",
    "pr-pipeline",
    "deploy-sandbox",
    "deploy-staging",
    "deploy-production",
    "integration-pipeline",
    "collect",
    "analyze",
]


class DoraEventV1(BaseModel):
    version: Literal["1.0"] = "1.0"
    work_id: str
    team: str
    stack: str
    stage: DoraStage
    environment: DoraEnvironment = "local"
    status: DoraStatus
    duration_ms: int = 0
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )

    model_config = ConfigDict(extra="forbid")


class DoraEventV2(DoraEventV1):
    version: Literal["2.0"] = "2.0"
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    correlation_id: Optional[str] = None
    repo: Optional[str] = None
    service: Optional[str] = None
    commit_sha: Optional[str] = None
    pr_number: Optional[int] = None
    workflow_run_id: Optional[str] = None
    actor: Optional[str] = None
    failure_reason: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


DoraEvent = Union[DoraEventV1, DoraEventV2]


def parse_event(data: dict) -> DoraEvent:
    """Parse a dict into the correct DoraEvent version."""
    version = data.get("version", "1.0")
    if version == "2.0":
        return DoraEventV2(**data)
    return DoraEventV1(**data)


def emit_event(event: DoraEvent) -> None:
    """Emit event as single-line JSON to stdout."""
    print(event.model_dump_json())
