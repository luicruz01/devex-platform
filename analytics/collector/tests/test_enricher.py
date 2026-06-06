from dora_event import DoraEventV2

from collector.enricher import EventEnricher


def _event(**overrides) -> DoraEventV2:
    defaults = {
        "work_id": "feat-456",
        "team": "payments",
        "stack": "python-lambda-cdk",
        "stage": "check",
        "environment": "local",
        "status": "success",
    }
    defaults.update(overrides)
    return DoraEventV2(**defaults)


def test_enrich_sets_correlation_id():
    enricher = EventEnricher()
    event = _event(correlation_id=None)

    enriched = enricher.enrich(event)

    assert enriched.correlation_id == event.work_id


def test_enrich_does_not_mutate_input():
    enricher = EventEnricher()
    event = _event(correlation_id=None)
    original_correlation_id = event.correlation_id

    enricher.enrich(event)

    assert event.correlation_id == original_correlation_id


def test_auto_enrich_from_github_env(monkeypatch):
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/transactionify")
    monkeypatch.setenv("GITHUB_ACTOR", "dev-user")
    monkeypatch.setenv("GITHUB_SHA", "abc123def456")
    monkeypatch.setenv("GITHUB_RUN_ID", "987654321")

    enricher = EventEnricher()
    event = _event()

    enriched = enricher.auto_enrich_from_environment(event)

    assert enriched.repo == "acme/transactionify"
    assert enriched.actor == "dev-user"
    assert enriched.commit_sha == "abc123def456"
    assert enriched.workflow_run_id == "987654321"
    assert event.repo is None
    assert event.actor is None
