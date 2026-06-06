import json
from datetime import datetime, timezone
from pathlib import Path


class DoraEmitter:
    VERSION = "1.0"

    @staticmethod
    def build_event(
        work_id: str,
        stage: str,
        status: str,
        team: str = "platform",
        stack: str = "unknown",
        environment: str = "local",
        duration_ms: int = 0,
    ) -> dict:
        return {
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

    @staticmethod
    def emit(event: dict) -> None:
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
