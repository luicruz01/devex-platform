# Architecture Decision Record

## devex-platform Shared Ecosystem

**Date:** 2026-06-06  
**Author:** Luis Alberto Cruz  
**Status:** Accepted  
**Scope:** Current repository state only

## Context and Problem Statement

The platform must standardize delivery across 10+ service teams without taking ownership of every repository. If each team defines its own branch rules, CI stages, infrastructure patterns, and telemetry, the result is local autonomy but no shared operating model, no comparable DORA metrics, and a permanent platform support burden. If the platform centralizes all implementation, teams lose delivery speed and the platform becomes a bottleneck.

`devex-platform` resolves that tension by standardizing a small set of reusable primitives while leaving service code with each team. The current repository contains a Python CLI, a TypeScript framework, a shared telemetry schema, a collector, a warehouse metrics engine, an LLM analyst, and a Streamlit dashboard demo, backed by 88 passing tests.

## 1. Architecture Diagram: How CLI and Framework Create a Shared Ecosystem

The CLI and Framework do not call each other directly at runtime. They interact through shared conventions: the same `work_id`, the same environment model, and the same `DoraEvent` schema. That contract lets many services behave consistently without a central orchestration service.

```text
                       Per-service repository owned by each team

  Developer laptop                               GitHub Actions / AWS
  -----------------                              --------------------
  devex init                                      PrPipelineGenerator
  devex branch  ---------- work_id ----------->   IntegrationPipelineGenerator
  devex check                                     LambdaServiceConstruct
  git hooks                                       GitHub Environments
  .devex/config.yaml                              sandbox -> staging -> production
        |                                                  |
        +---------------- emits DoraEvent -----------------+
                               |
                               v
                 analytics/schema (Pydantic + Zod contract)
                               |
                               v
        analytics/collector (FastAPI + Mangum + enrichment + validation)
                               |
                               v
                     DynamoDB single table event store
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
   analytics/warehouse               analytics/dashboard
   DF, LT, CFR, MTTR                 adoption and team views
                 |
                 v
         analytics/agent
   weekly digest and risk flags
```

The CLI standardizes local behavior through `devex init`, `devex branch`, and `devex check`. The Framework standardizes CI/CD and infrastructure through workflow generators and `LambdaServiceConstruct`. `analytics/schema` is the interoperability layer, and the remaining analytics packages close the loop from event validation to metrics, analysis, and reporting. This creates a shared ecosystem because every team adopts the same delivery vocabulary while keeping control of its own repository and business code.

## 2. Homologation: How 10+ Teams Adopt CLI and Framework

The adoption problem is economic, not technical. Teams adopt
tools when the cost of non-adoption exceeds the cost of
adoption. The design addresses this at four levels.

**Zero-friction onboarding.** `devex init` detects the stack
from signal files (`pyproject.toml`, `go.mod`, `package.json`,
`deps.edn`), writes `.devex/config.yaml`, and installs
`pre-commit` and `pre-push` hooks in under 10 seconds.
A new engineer gets the full golden path before their first
commit without reading documentation.

**Visible cost of divergence.** The DORA dashboard makes
adoption measurable. A team that bypasses `devex branch`
produces `work_id='N/A'` events — their lead time metric
degrades visibly relative to peers. Compliance is enforced
by metrics, not by the platform team.

**Configurable, not prescriptive.** Work ID pattern,
environments, and team name live in `.devex/config.yaml`.
A team using Linear instead of Jira changes one regex.
The platform does not need to be involved.

**Context travels with the repository.** `.cursor/rules/`
and `.kiro/steering/` files encode platform conventions into
the development environment. New engineers receive guidance
from their IDE and spec-validation agent — platform mentoring
at zero marginal cost per engineer onboarded.

## 3. Scalability: How the Platform Team Avoids Becoming a Bottleneck

The platform team avoids the bottleneck by owning primitives instead of per-team implementations. The CLI removes repeated repo setup, the Framework removes hand-authored pipeline scaffolding, and the schema package prevents contract drift. The analytics path is also chosen for low coordination cost: DynamoDB single-table storage avoids cross-team schema migration work, and the metrics engine stays in pure Python instead of requiring warehouse infrastructure. The platform team therefore owns releases, contract evolution, and metric definitions; service teams own day-2 delivery inside the paved road.

## 4. Shift-Left Strategy

The shift-left strategy is implemented as a chain of earlier, cheaper feedback loops:

| Stage | Mechanism in repo | Failure caught early |
| --- | --- | --- |
| Repo bootstrap | `devex init` stack detection and config generation | missing platform setup before the first PR |
| Local authoring | `devex branch` | missing or invalid `work_id` before branch creation |
| Local validation | `devex check` and git hooks | invalid branch, invalid commit message, and lint failures before push |
| Pull request CI | `PrPipelineGenerator` | branch policy violations, test failures, contract issues, and sandbox deploy failures before merge |
| Mainline CI | `IntegrationPipelineGenerator` + GitHub Environments | promotion failures before production rollout |
| Telemetry ingest | FastAPI + Pydantic validation in collector | malformed events rejected synchronously with HTTP 422 instead of corrupting downstream metrics |
| Analytics | warehouse + agent + dashboard | regression visibility, risk flags, and adoption drift before the next planning cycle |

Shift-left here starts at repository setup, continues through local and CI validation, and ends with rejecting invalid telemetry before it pollutes downstream metrics.

## Key Decisions

| Decision | Chosen option | Rejected alternative | Reason |
| --- | --- | --- | --- |
| Event storage | DynamoDB single-table | RDS | Telemetry is append-heavy, query patterns are predictable, and avoiding schema migrations matters more than relational flexibility at this stage. |
| Event ingestion | FastAPI + Mangum | Kinesis-first ingestion | HTTP ingestion gives synchronous validation, local testability, and immediate HTTP 422 responses for bad events. |
| Workflow generation | TypeScript template literals | `github-actions-workflow-ts` | Readable emitted YAML is easier for teams to inspect and debug than an abstraction optimized for compile-time safety. |
| Shared contract | Pydantic + Zod | JSON Schema only | Native runtime validation in Python and TypeScript is simpler for producers and consumers than maintaining schema generation toolchains. |
| Metrics engine | Pure Python | dbt | The repository needs deterministic, unit-tested metrics logic without warehouse infrastructure dependencies. |
| Delivery model | Trunk-based development + GitHub Environments | branch-per-environment | Promotion through environments keeps release flow simple and avoids long-lived environment branches. |

## PoC vs. Production Gaps

| Area | Proven in repository | Not production-ready yet |
| --- | --- | --- |
| Local developer workflow | CLI commands, hooks, config loading, and DORA emission are implemented and tested | Adoption across service repos is still package-by-package, not centrally rolled out |
| CI/CD standardization | PR and integration workflow generators exist and emit deploy stages and DORA events | AWS OIDC roles are not provisioned; current state is `cdk synth`, not deployed pipelines |
| Telemetry contract | Versioned `DoraEventV1` and `DoraEventV2` schemas exist in Python and TypeScript | The collector is not deployed to AWS, so ingestion is not live |
| Metrics and intelligence | Warehouse computes deployment frequency, lead time, change failure rate, and MTTR; agent generates analysis and risk flags | The analyst Lambda requires `ANTHROPIC_API_KEY` and is not operational without that secret |
| Visualization and adoption reporting | Streamlit dashboard demonstrates overview, team detail, and adoption views | Dashboard uses mock data for demo mode, not a live production feed |
| AI-assisted review | The architecture anticipates Amazon Q in the PR path | Amazon Q is not wired to live pull requests in this repository |

This ADR records a multi-package platform PoC with working local workflow, CI/CD generators, telemetry contracts, metrics logic, and demo reporting. The remaining gaps are deployment, live integrations, and operational hardening.
