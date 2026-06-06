import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "../../../../analytics/schema/python"),
)

try:
    from dora_event import DoraEventV2, emit_event as _emit_v2

    USE_V2 = True
except ImportError:
    USE_V2 = False


class DoraEmitter:
    VERSION = "2.0" if USE_V2 else "1.0"

    @staticmethod
    def build_event(
        work_id: str,
        stage: str,
        status: str,
        team: str = "platform",
        stack: str = "unknown",
        environment: str = "local",
        duration_ms: int = 0,
        failure_reason: str | None = None,
    ) -> dict:
        event = {
            "version": DoraEmitter.VERSION,
            "work_id": work_id,
            "team": team,
            "stack": stack,
            "stage": stage,
            "environment": environment,
            "status": status,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        if failure_reason is not None:
            event["failure_reason"] = failure_reason
        return event

    @staticmethod
    def emit(event: dict) -> None:
        if USE_V2:
            try:
                v2 = DoraEventV2(**{k: v for k, v in event.items() if v is not None})
                _emit_v2(v2)
                events_dir = Path.cwd() / ".devex"
                events_dir.mkdir(parents=True, exist_ok=True)
                events_file = events_dir / "dora-events.jsonl"
                with events_file.open("a") as f:
                    f.write(v2.model_dump_json() + "\n")
                return
            except Exception:
                pass

        if "timestamp" not in event:
            event = {
                **event,
                "timestamp": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }

        print(json.dumps(event))

        events_dir = Path.cwd() / ".devex"
        events_dir.mkdir(parents=True, exist_ok=True)
        events_file = events_dir / "dora-events.jsonl"
        with events_file.open("a") as f:
            f.write(json.dumps(event) + "\n")
