from __future__ import annotations

from fastapi import Depends, FastAPI
from mangum import Mangum
from dora_event import DoraEventV2

from collector.config import Settings, get_settings
from collector.enricher import EventEnricher
from collector.store import EventStore

app = FastAPI(
    title="DevEx Event Collector",
    description="Ingests and validates DoraEvent telemetry",
    version="0.1.0",
)


@app.post("/events", status_code=202)
async def collect_event(
    payload: DoraEventV2,
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Receive a DoraEvent v2, enrich it, and persist it.
    Returns 202 Accepted with the stored event_id.
    """
    enricher = EventEnricher()
    enriched = enricher.enrich(payload)
    enriched = enricher.auto_enrich_from_environment(enriched)

    store = EventStore(settings.table_name, settings.aws_region)
    store.save(enriched)

    return {
        "accepted": True,
        "event_id": enriched.event_id,
        "work_id": enriched.work_id,
        "stage": enriched.stage,
    }


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/events/{team}")
async def get_team_events(
    team: str,
    limit: int = 100,
    settings: Settings = Depends(get_settings),
) -> dict:
    """Get recent events for a team."""
    store = EventStore(settings.table_name, settings.aws_region)
    events = store.get_team_events(team, limit)
    return {"team": team, "events": events, "count": len(events)}


handler = Mangum(app, lifespan="off")
