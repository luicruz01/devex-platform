# DoraEvent Schema

The DoraEvent schema is the shared telemetry contract for devex-platform. It defines a versioned JSON event format emitted by the Python CLI, TypeScript framework, and analytics collector so every pipeline stage reports DORA metrics through one consistent structure.

## Version history

- **v1.0**: core fields (`work_id`, `team`, `stack`, `stage`, `environment`, `status`, `duration_ms`, `timestamp`)
- **v2.0**: adds `event_id`, `correlation_id`, `repo`, `service`, `commit_sha`, `pr_number`, `workflow_run_id`, `actor`, `failure_reason`

## Usage — Python

```python
from devex_schema import DoraEventV2, emit_event

event = DoraEventV2(
    work_id="FIN-123",
    team="payments",
    stack="python-lambda-cdk",
    stage="deploy-production",
    status="success",
    repo="transactionify",
    actor="luis",
    duration_ms=4200,
)
emit_event(event)
```

## Usage — TypeScript

```typescript
import { DoraEventV2Schema } from "@luicruz01/devex-schema";

const event = DoraEventV2Schema.parse({
  version: "2.0",
  work_id: "FIN-123",
  team: "payments",
  stack: "python-lambda-cdk",
  stage: "deploy-production",
  status: "success",
  event_id: "550e8400-e29b-41d4-a716-446655440000",
  repo: "transactionify",
  actor: "luis",
  duration_ms: 4200,
  timestamp: "2026-06-06T12:00:00.000Z",
});
```

## Field reference

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `version` | `"1.0"` \| `"2.0"` | yes | Schema version discriminator |
| `work_id` | string | yes | Ticket or work item identifier (e.g. `FIN-123`) |
| `team` | string | yes | Owning team name |
| `stack` | string | yes | Detected stack type (e.g. `python-lambda-cdk`) |
| `stage` | enum | yes | Pipeline stage that produced the event |
| `environment` | enum | no (default: `local`) | Target environment |
| `status` | `"success"` \| `"failure"` | yes | Outcome of the stage |
| `duration_ms` | integer | no (default: `0`) | Stage duration in milliseconds |
| `timestamp` | string (ISO 8601) | yes | UTC time the event was recorded |
| `event_id` | UUID string | v2 only | Unique identifier for this event |
| `correlation_id` | string | v2 optional | Links related events across stages |
| `repo` | string | v2 optional | Repository name |
| `service` | string | v2 optional | Service or application name |
| `commit_sha` | string | v2 optional | Git commit SHA |
| `pr_number` | positive integer | v2 optional | Pull request number |
| `workflow_run_id` | string | v2 optional | CI workflow run identifier |
| `actor` | string | v2 optional | User or system that triggered the stage |
| `failure_reason` | string | v2 optional | Human-readable failure cause when `status` is `failure` |
