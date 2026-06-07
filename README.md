# devex-platform

Teams that standardize local workflow but leave branch policy, CI/CD generation, infrastructure patterns, and telemetry format to each service repository end up with recurring setup work and DORA data that cannot be compared across teams. `devex-platform` is for platform teams and service teams that want one golden path from laptop to deployment while keeping service code in each team repository. The repository publishes a Python CLI for local enforcement, a TypeScript framework for CDK and pipeline generation, and analytics packages that validate, collect, compute, analyze, and visualize DORA events.

## Repository Structure

```text
devex-platform/
├── README.md                            # Repository overview, install commands, and adoption path.
├── CONTRIBUTING.md                      # Contribution workflow and repository standards.
├── AGENTS.md                            # Repository-specific agent instructions for local tooling.
├── .gitignore                           # Git ignore rules for local artifacts and build output.
├── .devex/                              # Example local DevEx state and emitted event log.
│   └── dora-events.jsonl                # JSONL file written by local DORA emission flows.
├── cli/                                 # Python CLI package distributed as `devex`.
│   ├── src/devex_cli/                   # CLI commands, config loading, DORA emission, and git hooks.
│   ├── tests/                           # CLI tests for commands, config, and Work ID validation.
│   ├── pyproject.toml                   # Package metadata and uv entry point definition.
│   ├── pyrightconfig.json               # Static analysis settings for the CLI package.
│   └── uv.lock                          # Locked Python dependencies for reproducible CLI installs.
├── framework/                           # TypeScript framework package for CDK and GitHub Actions generation.
│   ├── src/                             # Source for constructs, workflow generators, and DORA types.
│   ├── tests/                           # Framework tests for pipelines, construct behavior, and types.
│   ├── package.json                     # Package metadata for `@luicruz01/devex-framework`.
│   ├── pnpm-workspace.yaml              # pnpm workspace settings for the framework package.
│   ├── pnpm-lock.yaml                   # Locked Node dependencies for the framework package.
│   └── tsconfig.json                    # TypeScript compiler configuration.
├── analytics/                           # Analytics packages for schema validation, ingestion, metrics, analysis, and dashboards.
│   ├── schema/                          # Shared `DoraEvent` contract in Python and TypeScript.
│   │   ├── python/                      # Pydantic schema package, emit helpers, and tests.
│   │   ├── typescript/                  # Zod schema package, type exports, and tests.
│   │   └── README.md                    # Schema versions, field reference, and usage examples.
│   ├── collector/                       # FastAPI collector Lambda and DynamoDB persistence layer.
│   │   ├── cdk/                         # CDK construct for deploying the collector Lambda.
│   │   ├── src/collector/               # API handlers, enrichment, config, and storage logic.
│   │   ├── tests/                       # Collector tests for endpoints, enrichment, and DynamoDB writes.
│   │   ├── pyproject.toml               # Collector package metadata and dependencies.
│   │   └── uv.lock                      # Locked Python dependencies for the collector.
│   ├── warehouse/                       # Metrics engine that computes the four DORA metrics.
│   │   ├── src/warehouse/               # Query services, data models, and metric calculations.
│   │   ├── tests/                       # Warehouse tests for query behavior and metric computation.
│   │   ├── pyproject.toml               # Warehouse package metadata and dependencies.
│   │   └── uv.lock                      # Locked Python dependencies for the warehouse.
│   ├── agent/                           # LLM analyst that produces weekly digests and risk flags.
│   │   ├── src/agent/                   # Analyst runtime, prompts, config, and Lambda entry point.
│   │   ├── tests/                       # Agent tests for LLM analysis flow and prompt construction.
│   │   ├── pyproject.toml               # Agent package metadata and dependencies.
│   │   └── uv.lock                      # Locked Python dependencies for the analyst.
│   └── dashboard/                       # Streamlit dashboard for DORA and adoption reporting.
│       ├── app.py                       # Streamlit application entry point.
│       ├── components/                  # Reusable dashboard UI components.
│       ├── data/                        # Mock data and data typing helpers.
│       ├── views/                       # Overview, team detail, and adoption screens.
│       ├── README.md                    # Dashboard usage and local run instructions.
│       ├── pyproject.toml               # Dashboard package metadata and dependencies.
│       ├── docker-compose.yml           # Local container entry point for dashboard development.
│       └── uv.lock                      # Locked Python dependencies for the dashboard.
├── docs/                                # Repository architecture documents.
│   ├── adr.md                           # Architecture decision record for the current repository state.
│   └── devex-platform-adr.pdf           # PDF export of the architecture decision record.
├── .cursor/                             # Cursor-specific repository guidance.
│   └── rules/                           # Cursor rules that encode contributor conventions.
└── .kiro/                               # Kiro-specific repository guidance.
    └── steering/                        # Steering documents for agent boundaries, DORA contract, and golden path rules.
```

## Quick Install

### CLI via `uvx`

```bash
uvx --from git+https://github.com/luicruz01/devex-platform#subdirectory=cli devex
```

### Framework via `pnpm`

```bash
pnpm add github:luicruz01/devex-platform#main \
  --filter @luicruz01/devex-framework
```

## Quick Start

### 1. Install the CLI

```bash
uvx --from git+https://github.com/luicruz01/devex-platform#subdirectory=cli devex
```

### 2. Run `devex init` in your service repository

```bash
cd your-service-repo
devex init
```

`devex init` detects the stack from signal files, writes `.devex/config.yaml`, and installs `pre-commit` and `pre-push` hooks.

### 3. Create a branch with a Work ID

```bash
devex branch WORK-123 feat/description
```

The CLI creates a branch named `WORK-123/feat/description` and emits a DORA event for branch creation.

### 4. Add `LambdaServiceConstruct` to your CDK stack

```typescript
import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import { LambdaServiceConstruct } from "@luicruz01/devex-framework";

export class ServiceStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string) {
    super(scope, id);

    const table = new dynamodb.Table(this, "DataTable", {
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
    });

    new LambdaServiceConstruct(this, "ApiHandler", {
      handlerPath: "handler.main",
      table,
      workId: "WORK-123",
    });
  }
}
```

`LambdaServiceConstruct` packages a Lambda handler with table access, environment wiring, timeout defaults, and `devex:` tags.

### 5. Generate your pipelines with `PrPipelineGenerator`

```typescript
import { mkdirSync, writeFileSync } from "node:fs";
import { PrPipelineGenerator } from "@luicruz01/devex-framework";

const config = {
  work_id_pattern: "^[A-Z]+-\\d+$",
  stack: "python-lambda-cdk" as const,
  team: "platform",
  environments: ["sandbox", "staging", "production"],
};

mkdirSync(".github/workflows", { recursive: true });
writeFileSync(
  ".github/workflows/pr-pipeline.yml",
  new PrPipelineGenerator().generate(config)
);
```

The same configuration can be reused with `IntegrationPipelineGenerator` for mainline promotion workflows.

## Supported Stacks

| Stack | Signal file | Test command | Lint |
| --- | --- | --- | --- |
| `python-lambda-cdk` | `pyproject.toml` | `pytest test/ -v` | `ruff check .` |
| `go` | `go.mod` | `go test ./...` | `planned` |
| `typescript` | `package.json` | `pnpm test` | `eslint .` |
| `clojure` | `deps.edn` | `lein test` | `planned` |

## Analytics

See `analytics/README.md` for the end-to-end analytics guide. The analytics packages are split by responsibility:

- `analytics/schema/` defines the `DoraEvent` v2 schema in Pydantic and Zod.
- `analytics/collector/` runs a FastAPI collector Lambda that validates events and stores them in DynamoDB.
- `analytics/warehouse/` computes deployment frequency, lead time for changes, change failure rate, and MTTR.
- `analytics/agent/` runs the DORA Analyst flow that produces a weekly digest and risk flags.
- `analytics/dashboard/` provides the Streamlit dashboard for team, overview, and adoption views.

Run the dashboard locally with:

```bash
cd analytics/dashboard && uv run streamlit run app.py
```

## Known gaps

- PR title Work ID enforcement requires a GitHub branch protection ruleset or webhook — the CLI enforces branch name and commit message format only.
- Property-based testing (PBT) at the unit level is not implemented. API contract validation via schemathesis runs in the PR pipeline.
- Go and Clojure lint steps are planned but not yet implemented in the CLI or generated pipelines.

## Test Coverage

| Package | Tests | Coverage |
| --- | ---: | --- |
| `cli/` | 15 | commands, config, Work ID validation |
| `framework/` | 16 | pipelines, CDK construct, DORA types |
| `analytics/schema/` | 8 | DoraEvent v1/v2 parsing and emission |
| `analytics/collector/` | 24 | API endpoints, DynamoDB, enrichment |
| `analytics/warehouse/` | 14 | DORA metrics computation |
| `analytics/agent/` | 11 | LLM analysis, prompts, risk flags |
| Total | 88 | - |

## Reference Adoption

[transactionify](https://github.com/luicruz01/transactionify) is the reference project that consumes this platform end to end.

## Architecture

See [docs/adr.md](docs/adr.md) for the architecture decision record and current system model.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution workflow, coding standards, and review expectations.
