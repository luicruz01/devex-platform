# Analytics Layer

The analytics layer turns `DoraEvent` telemetry into measurable engineering outcomes. It is split into five packages with single-purpose responsibilities: `analytics/schema` defines the shared event contract, `analytics/collector` ingests and stores events, `analytics/warehouse` computes DORA metrics, `analytics/agent` generates structured analysis, and `analytics/dashboard` visualizes the results. All packages communicate through the versioned `DoraEvent` v2 schema.

## Architecture

```text
CLI / GitHub Actions
     |
     v (DoraEvent v2 JSON)
analytics/collector  <-->  DynamoDB single table
     |
     v
analytics/warehouse  (metrics engine)
     |
     v
analytics/agent      (LLM digest via Claude API)
     |
     v
analytics/dashboard  (Streamlit UI)

analytics/schema is the shared contract used by all packages.
```

## Package Reference

### analytics/schema

What it is: the versioned `DoraEvent` contract in Python and TypeScript.

#### DoraEvent v1 fields

All v1 fields are required unless a default is noted in code:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `version` | `"1.0"` | yes | Schema version discriminator for v1 payloads |
| `work_id` | `str` | yes | Ticket or work item identifier |
| `team` | `str` | yes | Owning team |
| `stack` | `str` | yes | Emitting stack identifier |
| `stage` | `DoraStage` | yes | Pipeline stage that produced the event |
| `environment` | `DoraEnvironment` | yes | Target environment; defaults to `local` |
| `status` | `DoraStatus` | yes | Stage outcome |
| `duration_ms` | `int` | yes | Stage duration; defaults to `0` |
| `timestamp` | ISO 8601 string | yes | UTC event timestamp |

#### DoraEvent v2 fields

`DoraEventV2` includes every v1 field and adds these 9 optional fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `event_id` | UUID string | no | Event identifier generated at emit time in Python |
| `correlation_id` | string | no | Cross-stage correlation key |
| `repo` | string | no | Repository name |
| `service` | string | no | Service or application name |
| `commit_sha` | string | no | Git commit SHA |
| `pr_number` | integer | no | Pull request number |
| `workflow_run_id` | string | no | CI workflow run identifier |
| `actor` | string | no | User or automation actor |
| `failure_reason` | string | no | Human-readable failure cause |

#### Install as a path dependency

Python packages in this repo consume the schema through `pyproject.toml` path sources:

```toml
[tool.uv.sources]
devex-schema = { path = "../schema/python" }
```

#### Use in Python

```python
from devex_schema import DoraEventV2, emit_event
event = DoraEventV2(work_id="FIN-123", team="payments", stack="python-lambda-cdk", stage="deploy-production", status="success")
emit_event(event)
```

#### Use in TypeScript

```ts
import { parseEvent } from "@luicruz01/devex-schema";
const event = parseEvent(payload);
console.log(event.stage);
```

#### Run tests

```bash
cd analytics/schema/python
uv run pytest
```

### analytics/collector

What it is: a FastAPI Lambda that receives, validates, enriches, and persists `DoraEvent` v2 payloads.

#### Endpoints

- `POST /events` returns `202 Accepted` after validating, enriching, and storing the payload.
- `GET /health` returns service status and version.
- `GET /events/{team}` returns recent stored events for a team.

#### Enrichment

`EventEnricher.auto_enrich_from_environment()` pulls the following GitHub Actions metadata when present:

- `repo` from `GITHUB_REPOSITORY`
- `actor` from `GITHUB_ACTOR`
- `commit_sha` from `GITHUB_SHA`
- `workflow_run_id` from `GITHUB_RUN_ID`

It also defaults `correlation_id` to `work_id` when no correlation key is supplied.

#### DynamoDB table design

The collector writes a single-table item shape:

- `PK = TEAM#{team}`
- `SK = EVENT#{timestamp}#{event_id}`
- `GSI1PK = REPO#{repo}`
- `GSI1SK = EVENT#{timestamp}`
- `GSI2PK = STAGE#{stage}`
- `GSI2SK = STATUS#{status}#{timestamp}`
- `ttl = now + 90 days`

#### Run locally

```bash
cd analytics/collector
uv sync --dev
uvicorn collector.main:app
```

#### Run tests

```bash
cd analytics/collector
uv run pytest tests/ -v
```

#### CDK construct

Infrastructure for the collector Lambda and HTTP API lives in `cdk/collector_construct.ts` as `CollectorConstruct`.

### analytics/warehouse

What it is: a pure Python metrics engine that computes DORA metrics over stored events without infrastructure-specific logic in the calculations themselves.

#### Metrics computed

- Deployment Frequency: successful `deploy-production` events in the window, normalized per day and per week.
- Lead Time: time from `branch-create` to successful `deploy-production`, grouped by `work_id`.
- Change Failure Rate: failed `deploy-production` events divided by total production deploys.
- MTTR: time from a failed production deploy to the next successful production deploy for the same team.

#### DORA elite thresholds

- Deploy frequency `>= 1/day` -> elite
- Lead time median `<= 24h` -> elite
- Change failure rate `<= 5%` -> elite
- MTTR median `<= 1h` -> elite

#### DoraReport

`DoraReport` aggregates all four metrics plus `overall_rating`, which is derived as:

- `elite` when all four metrics are elite
- `high` when at least three are elite
- `medium` when at least two are elite
- `low` otherwise

#### Run tests

```bash
cd analytics/warehouse
uv run pytest tests/ -v
```

### analytics/agent

What it is: a Lambda handler that generates a `DoraReport` for a team and optionally calls the Claude API to produce a structured digest.

#### Input

The handler expects:

- `team` as the required team name
- `window_days` as an optional lookback window
- `dry_run` as an optional flag to skip the LLM call

Inputs can come from EventBridge schedules or direct invocation.

#### Output

The analysis path returns an `AnalystResult`-shaped response with:

- `summary`
- `top_insight`
- `recommendation`
- `has_risk_flag`
- `overall_rating`

The handler response also includes `team` and `generated_at`.

#### Risk flag triggers

- `change_failure_rate.failure_rate_pct > 15`
- `lead_time.median_hours > 168`
- `mttr.median_hours > 24`
- `deployment_frequency.deployments_per_week < 1`

#### dry_run mode

When `dry_run` is `True`, the handler skips the Claude call and returns the raw `DoraReport` payload.

#### Required environment variable

- `ANTHROPIC_API_KEY`

Other runtime settings include `DEVEX_EVENTS_TABLE`, `AWS_REGION`, `DEVEX_ANALYST_MODEL`, and `DEVEX_ANALYST_WINDOW_DAYS`.

#### Run tests

```bash
cd analytics/agent
uv run pytest tests/ -v
```

#### Invoke locally in dry run

```bash
cd analytics/agent
python -c "from agent.main import handler; print(handler({'team': 'payments', 'dry_run': True}, None))"
```

### analytics/dashboard

What it is: a Streamlit application that presents DORA metrics and analyst output in a three-page interface.

#### Pages

- Overview: cross-team DORA metrics, team gauges, summary table, and lead time chart
- Team Detail: single-team metrics with AI analysis panels
- Golden Path Adoption: adoption counts, metric-by-metric elite coverage, and team ratings

#### Demo mode

The dashboard runs from mock data by default, so it can be used without AWS credentials.

#### Run locally

```bash
cd analytics/dashboard
uv run streamlit run app.py
```

#### Run with Docker

```bash
cd analytics/dashboard
docker-compose up
```

#### Connect to real DynamoDB

```bash
export DEVEX_EVENTS_TABLE=your-table-name
export AWS_REGION=us-east-1
uv run streamlit run app.py
```

## Running All Tests

```bash
cd analytics/schema/python && uv run pytest
cd analytics/collector && uv run pytest
cd analytics/warehouse && uv run pytest
cd analytics/agent && uv run pytest
```

## Event Schema Reference

### DoraEvent v2 fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `version` | `"1.0"` or `"2.0"` | yes | Schema version discriminator |
| `work_id` | string | yes | Ticket or work item identifier |
| `team` | string | yes | Owning team |
| `stack` | string | yes | Emitting stack identifier |
| `stage` | enum | yes | Pipeline stage that emitted the event |
| `environment` | enum | yes | Target environment; defaults to `local` in code |
| `status` | `"success"` or `"failure"` | yes | Stage outcome |
| `duration_ms` | integer | yes | Duration in milliseconds; defaults to `0` in code |
| `timestamp` | ISO 8601 string | yes | UTC event timestamp |
| `event_id` | UUID string | no | Unique event identifier |
| `correlation_id` | string | no | Correlates related events |
| `repo` | string | no | Repository name |
| `service` | string | no | Service or application name |
| `commit_sha` | string | no | Git commit SHA |
| `pr_number` | integer | no | Pull request number |
| `workflow_run_id` | string | no | Workflow run identifier |
| `actor` | string | no | Triggering user or automation |
| `failure_reason` | string | no | Failure detail for unsuccessful stages |

### Valid stage values

- `init`
- `branch-create`
- `check`
- `pr-pipeline`
- `deploy-sandbox`
- `deploy-staging`
- `deploy-production`
- `integration-pipeline`
- `collect`
- `analyze`

### Valid environment values

- `sandbox`
- `staging`
- `production`
- `local`

## Extending The Platform

To add a new metric to the warehouse:

1. Add a method to `DoraMetricsEngine` in `warehouse/src/warehouse/metrics.py`.
2. Add the new field to `DoraReport` in `warehouse/src/warehouse/models.py`.
3. Add or update tests in `warehouse/tests/test_metrics.py`.
4. Open a `[PROPOSAL]` issue before adding fields to the `DoraEvent` schema.
