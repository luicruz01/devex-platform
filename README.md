# devex-platform

devex-platform is a Developer Experience ecosystem for engineering teams that need shared conventions, comparable DORA metrics, and a golden path from local development through CI/CD — without waiting on a central platform team for every change. It ships as two independent packages: a Python CLI for local enforcement and a TypeScript framework for pipeline generation and CDK infrastructure patterns. The reference adoption project [transactionify](https://github.com/luicruz01/transactionify) demonstrates end-to-end usage.

## Packages

### cli

Local Golden Path enforcement — Work ID validation, git hooks, standards checks, and DORA telemetry.

```bash
uvx --from git+https://github.com/luicruz01/devex-platform#subdirectory=cli devex
```

```bash
devex check
```

### framework

CI/CD pipeline generation and reusable CDK constructs, with typed DORA event emission.

```bash
pnpm add github:luicruz01/devex-platform#main \
  --filter @luicruz01/devex-framework
```

> The framework lives in the `framework/` subdirectory of the monorepo.

```typescript
import { PrPipelineGenerator } from "@luicruz01/devex-framework";

const yaml = new PrPipelineGenerator().generate({
  work_id_pattern: "^[A-Z]+-\\d+$",
  stack: "python-lambda-cdk",
  team: "platform",
  environments: ["sandbox", "staging", "production"],
});
```

## Quick start

### Step 1: Install the CLI

```bash
uvx --from git+https://github.com/luicruz01/devex-platform#subdirectory=cli devex
```

No global install or registry required — `uvx` fetches the CLI directly from the git repository.

### Step 2: Initialize your project

```bash
cd your-service
devex init
```

`devex init` detects your stack from signal files (`pyproject.toml`, `go.mod`, `package.json`, or `deps.edn`), writes `.devex/config.yaml` with team defaults, and installs `pre-commit` and `pre-push` git hooks that run `devex check` and your unit test suite before code leaves your machine.

### Step 3: Create a branch

```bash
devex branch FIN-123 feat/your-feature
```

Every change must be tied to a Work ID (e.g. `FIN-123` from Jira or Linear). The branch is created as `FIN-123/feat/your-feature` and a `DoraEvent` is emitted. Manual `git checkout -b` bypasses this audit trail.

### Step 4: Consume the Framework in your CDK stack

```bash
pnpm add github:luicruz01/devex-platform#main \
  --filter @luicruz01/devex-framework
```

> The framework lives in the `framework/` subdirectory of the monorepo.

```typescript
import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import { LambdaServiceConstruct } from "@luicruz01/devex-framework";

export class MyStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string) {
    super(scope, id);

    const table = new dynamodb.Table(this, "DataTable", {
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
    });

    new LambdaServiceConstruct(this, "ApiHandler", {
      handlerPath: "handler.main",
      table,
      workId: "FIN-123",
    });
  }
}
```

`LambdaServiceConstruct` wires runtime, IAM grants, environment variables, and `devex:` resource tags in one call.

### Step 5: Generate your pipelines

```typescript
import { writeFileSync, mkdirSync } from "node:fs";
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

The generated workflow validates the branch name, runs stack-specific tests and lint, performs API contract validation, and deploys to the sandbox environment on every pull request.

## Supported stacks

| Stack | Signal file | Test command | Lint command |
|-------|-------------|--------------|--------------|
| python-lambda-cdk | `pyproject.toml` | `pytest test/ -v` | `ruff check .` |
| go | `go.mod` | `go test ./...` | `golangci-lint (planned)` |
| typescript | `package.json` | `pnpm test` | `eslint .` |
| clojure | `deps.edn` | `lein test` | `clj-kondo (planned)` |

Stack detection runs automatically during `devex init` and drives both local checks and generated pipeline steps.

## DORA telemetry

Every CLI command and every pipeline stage emits a `DoraEvent` — a fixed-schema JSON object written to stdout and appended to `.devex/dora-events.jsonl`. Because the schema is identical across all teams and stacks, DORA metrics (deployment frequency, lead time, change failure rate, MTTR) are directly comparable between a Python Lambda team and a Go service team without post-processing.

```json
{
  "version": "1.0",
  "work_id": "FIN-123",
  "team": "platform",
  "stack": "python-lambda-cdk",
  "stage": "check",
  "environment": "local",
  "status": "success",
  "duration_ms": 142,
  "timestamp": "2026-06-05T14:30:00Z"
}
```

Events flow from local CLI → GitHub Actions stdout → CloudWatch Logs, where the DORA Analyst agent aggregates them into team-level insights.

## AI agents

**PR Reviewer (Amazon Q Developer)** — Runs automated code review on every pull request before a human reviewer is assigned. Flags security issues, convention violations (missing Work ID in PR title, wrong branch format), and missing `DoraEvent` emission in pipeline stages. Reduces platform team review load to escalations only.

**Spec Validator (AWS Kiro)** — Validates architecture and design decisions before code is written. Steering files in `.kiro/steering/` encode golden-path rules; Kiro checks proposed designs against them during planning, catching structural mistakes at design time rather than in a PR comment thread.

**DORA Analyst** — An LLM agent that reads the `DoraEvent` stream from CloudWatch and converts raw telemetry into actionable insights: deployment frequency trends, lead time regressions, and teams drifting from the golden path. Designed as a PoC; not yet wired to production data sources.

## Architecture

See [docs/adr.md](docs/adr.md) for the full architecture decision record, homologation strategy, scalability model, and shift-left approach.

```
  Engineer machine          GitHub                    AWS
  ─────────────────    ──────────────────────    ──────────────
  devex CLI          → PR Pipeline (Framework) → sandbox
  git hooks          → Integration Pipeline    → staging
  .devex/config.yaml → Amazon Q PR Review      → production
                     → DORA events → CloudWatch
```

## Repository structure

```
devex-platform/
├── cli/                          # Python CLI (devex)
│   ├── src/devex_cli/
│   │   ├── commands/             # init, branch, check commands
│   │   ├── config/               # config.yaml resolution and stack detection
│   │   ├── dora/                 # DORA event emitter (stdout + jsonl)
│   │   └── hooks/                # pre-commit and pre-push git hooks
│   ├── tests/                    # pytest suite (15 tests)
│   └── pyproject.toml            # package definition and uv entry point
├── framework/                    # TypeScript framework (@luicruz01/devex-framework)
│   ├── src/
│   │   ├── constructs/           # LambdaServiceConstruct CDK abstraction
│   │   ├── dora/                 # DoraEvent types and DoraEmitter
│   │   └── workflows/            # PrPipeline, IntegrationPipeline, StackDetector
│   ├── tests/                    # vitest suite (16 tests)
│   └── package.json
├── docs/
│   └── adr.md                    # Architecture Decision Record
├── .cursor/rules/                # Cursor context rules for contributors
└── .kiro/steering/               # Kiro steering files for AI agents
```
