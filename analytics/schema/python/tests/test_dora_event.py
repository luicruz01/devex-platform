import json
import sys
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dora_event import DoraEventV1, DoraEventV2, emit_event, parse_event


def test_v1_defaults():
    event = DoraEventV1(
        work_id="FIN-123",
        team="platform",
        stack="python",
        stage="check",
        status="success",
    )
    assert event.version == "1.0"
    assert event.environment == "local"
    assert event.duration_ms == 0
    assert event.timestamp
    assert event.timestamp.endswith("Z")


def test_v2_has_event_id():
    event = DoraEventV2(
        work_id="FIN-123",
        team="platform",
        stack="python",
        stage="check",
        status="success",
    )
    assert event.version == "2.0"
    UUID(event.event_id)


def test_v2_optional_fields():
    event = DoraEventV2(
        work_id="FIN-123",
        team="platform",
        stack="python",
        stage="check",
        status="success",
    )
    dumped = event.model_dump(exclude_none=True)
    assert "correlation_id" not in dumped
    assert "repo" not in dumped
    assert "service" not in dumped
    assert "commit_sha" not in dumped
    assert "pr_number" not in dumped
    assert "workflow_run_id" not in dumped
    assert "actor" not in dumped
    assert "failure_reason" not in dumped


def test_parse_event_v1():
    event = parse_event(
        {
            "version": "1.0",
            "work_id": "FIN-123",
            "team": "platform",
            "stack": "python",
            "stage": "check",
            "status": "success",
        }
    )
    assert isinstance(event, DoraEventV1)
    assert event.version == "1.0"


def test_parse_event_v2():
    event = parse_event(
        {
            "version": "2.0",
            "work_id": "FIN-123",
            "team": "platform",
            "stack": "python",
            "stage": "check",
            "status": "success",
        }
    )
    assert isinstance(event, DoraEventV2)
    assert event.version == "2.0"


def test_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        DoraEventV2(
            work_id="FIN-123",
            team="platform",
            stack="python",
            stage="check",
            status="success",
            unknown_field="x",
        )


def test_emit_event_is_single_line(capsys):
    event = DoraEventV2(
        work_id="FIN-123",
        team="platform",
        stack="python",
        stage="check",
        status="success",
    )
    emit_event(event)
    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["version"] == "2.0"
    assert parsed["work_id"] == "FIN-123"


def test_failure_reason_only_on_failure():
    event = DoraEventV2(
        work_id="FIN-123",
        team="platform",
        stack="python",
        stage="check",
        status="failure",
        failure_reason="timeout",
    )
    dumped = event.model_dump()
    assert dumped["status"] == "failure"
    assert dumped["failure_reason"] == "timeout"
