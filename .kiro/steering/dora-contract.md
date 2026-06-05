# DORA Contract

The `DoraEvent` is the shared telemetry unit of the devex-platform ecosystem. Every team emits the same schema so that DORA metrics are comparable across a Python Lambda team and a Go service team without post-processing.

## Schema (version 1.0)

Every `DoraEvent` must be a JSON object with exactly these fields:

| Field | Type | Allowed values |
|-------|------|----------------|
| `version` | string | `"1.0"` — always this literal string |
| `work_id` | string | Work ID matching `^[A-Z]+-\d+$`, e.g. `"FIN-123"` |
| `team` | string | Team name from `.devex/config.yaml` |
| `stack` | string | `python-lambda-cdk`, `go`, `typescript`, or `clojure` |
| `stage` | string | See valid stages below |
| `environment` | string | `sandbox`, `staging`, `production`, or `local` |
| `status` | string | `success` or `failure` |
| `duration_ms` | integer | Elapsed milliseconds; `0` if not measurable |
| `timestamp` | string | ISO 8601 UTC, e.g. `"2026-01-01T00:00:00Z"` |

A valid check: parse the JSON and assert every field is present and its value matches the constraint above.

## Valid Stages

The `stage` field must be one of:

- `init` — emitted by `devex init`
- `branch-create` — emitted by `devex branch`
- `check` — emitted by `devex check`
- `pr-pipeline` — emitted by the PR pipeline top-level job
- `deploy-sandbox` — emitted by the sandbox deployment step
- `deploy-staging` — emitted by the staging deployment step
- `deploy-production` — emitted by the production deployment step
- `integration-pipeline` — emitted by the integration pipeline top-level job

A valid check: the `stage` value in any emitted event must be in this list.

## Emission Rules

**CLI commands** emit the event to two destinations simultaneously:
1. `stdout` (one JSON line)
2. `.devex/dora-events.jsonl` (appended, one JSON line per event)

**Pipeline stages** emit to `stdout` only. CloudWatch ingests the event from the pipeline log stream.

Always emit — even when the operation fails. A `status: "failure"` event is required data. Suppressing an event on an error path means a deployment failure goes unrecorded in DORA metrics.

A valid check: find every error-handling branch in `cli/src/devex_cli/commands/*.py` and confirm each branch calls the DORA emitter before raising `typer.Exit`.

## Cross-Team Comparability

All teams use the same schema with no extensions. This is what makes DORA metrics comparable.

Never add team-specific fields to the event. If a team needs additional telemetry, that data belongs in a separate log line or a separate observability system, not in the `DoraEvent`.

A valid check: the `DoraEvent` TypeScript type in `framework/src/` must not have optional fields. Every field is required and present in every event.
