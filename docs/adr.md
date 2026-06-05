# Architecture Decision Record

## devex-platform — Golden Path Ecosystem

**Date:** June 2026  
**Author:** Luis Cruz  
**Status:** Accepted

## Context

Ten or more independent engineering teams need to operate under the same conventions — branch naming, commit messages, pipeline stages, infrastructure patterns — and report comparable DORA metrics, without a platform team becoming a bottleneck for every custom request. Today each team invents its own hooks, YAML, and CDK patterns, making cross-team measurement impossible and platform support unsustainable.

The solution is a two-component ecosystem: a **CLI** (`devex`) for local enforcement on engineer machines, and a **Framework** (`@luicruz01/devex-framework`) for CI/CD pipeline generation and reusable CDK constructs. Both share a single integration contract — the **Work ID** — and a fixed **DoraEvent** telemetry schema, so behavior and metrics are consistent regardless of language stack.

## 1. Architecture

The CLI runs on engineer machines. It enforces conventions locally: Work ID validation on branches and commits, git hook installation, and standards checks via `devex check`. Config resolves in priority order: CLI argument → `DEVEX_WORK_ID` environment variable → `.devex/config.yaml`.

The Framework runs in CI/CD. It generates typed GitHub Actions workflows (`PrPipelineGenerator`, `IntegrationPipelineGenerator`) and provides CDK constructs (`LambdaServiceConstruct`) that abstract infrastructure patterns with built-in tagging and DORA emission.

The Work ID is the integration contract. It threads through branch name → commit message → PR title → pipeline environment variable → DORA event, creating a complete audit trail from code change to deployment.

Three AI agents augment the ecosystem:

- **PR Reviewer (Amazon Q)** — automated code review on every PR
- **Spec Validator (Kiro)** — validates designs before code is written
- **DORA Analyst** — converts event streams into actionable insights

```
[Engineer] → devex branch FIN-123 → git hooks → PR
                                                  ↓
[Framework] generates ←→ PR Pipeline → sandbox deploy
                                     → DORA event → CloudWatch
                                                         ↓
[DORA Analyst] ←───────────────────────────── event stream
```

## 2. Homologation — ensuring 10+ teams adopt the ecosystem

**a) Convention over configuration.** `devex init` generates everything a team needs in one command: `.devex/config.yaml`, git hooks, and stack detection. The path of least resistance is the golden path — teams do not configure; they adopt.

**b) Installable from git — no registry required.**

```bash
uvx --from git+https://github.com/luicruz01/devex-platform#subdirectory=cli devex
pnpm add github:luicruz01/devex-platform#main
```

Zero infrastructure to maintain for distribution. Works in air-gapped environments with git access. Version pinning via git SHA.

**c) Escape hatches without forking.** `PrPipelineGenerator` accepts pre-hooks and post-hooks. Teams extend behavior without modifying platform code. Pipeline stages are fixed (validate → test → contract-validation → deploy); the steps within stages are flexible.

**d) Context engineering.** Every repo gets `.cursor/rules/` and `.kiro/steering/` files. New engineers receive platform guidance from their IDE and spec-validation agents — no onboarding sessions required. Knowledge travels with the repository.

## 3. Scalability — avoiding platform team bottleneck

**a) Inner-source model.** Teams propose changes via GitHub Issues (`[PROPOSAL]` prefix). The platform team approves proposals, not implementations. Teams own their PRs; platform reviews and merges, never rewrites.

**b) AI agents as first-level support.** Amazon Q reviews every PR before a human does. Kiro validates designs before code is written. The platform team only sees issues that AI could not resolve — security escalations, schema changes, and architectural disputes.

**c) Typed escape hatches.** `LambdaServiceConstruct` accepts additional environment variables via the `environment` prop and runtime overrides via the `timeout` prop — teams extend behavior without modifying platform constructs. `PipelineConfig` is designed for extension via additional fields in a future version; teams needing custom steps today fork the generated YAML locally, which the platform team tracks as a known gap.

## 4. Shift-Left Strategy

Defect detection moves earlier through four layers:

**Layer 1 — Design time (earliest).** Kiro steering files validate architecture decisions before a single line of code is written. A team proposing a raw Lambda instead of `LambdaServiceConstruct` gets corrected during design review, not in a PR comment.

**Layer 2 — Commit time.** The `pre-commit` hook runs `devex check` — Work ID validation, lint, commit message format. Defects caught in seconds on the engineer's machine.

**Layer 3 — Push time.** The `pre-push` hook runs the full unit test suite locally. Integration failures caught before reaching GitHub.

**Layer 4 — PR time.** The PR Pipeline runs tests, API contract validation, and sandbox deploy. Amazon Q reviews for security and convention violations. Lead time is measured from branch creation to sandbox deploy.

The result: a defect introduced at 9:00 AM is caught by 9:01 AM (pre-commit), not at 2:00 PM when a reviewer finds it in GitHub.

## Key technical decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Branching strategy | Trunk-based + GitHub Environments | Industry standard; eliminates long-lived branches; GitHub environment protection handles approval gates |
| Pipeline generation | TypeScript template literals | Type-safe; no YAML library dependency; readable output teams can inspect |
| DORA telemetry | Structured JSON to stdout | CloudWatch ingests from logs automatically; same schema works for all stacks |
| Distribution | git-based (uv + pnpm) | No registry infrastructure; works in air-gapped environments; version pinning via git SHA |
| Work ID | Configurable regex pattern | Works with any tracker (Jira, Linear, GitHub Issues) without platform team changes |

## What this PoC demonstrates vs production gaps

| Demonstrated | Production gaps (known, intentional for PoC scope) |
|--------------|---------------------------------------------------|
| CLI installable and functional via `uvx` | AWS OIDC roles not provisioned (`cdk synth`, not `cdk deploy`) |
| Framework generates valid GitHub Actions YAML | Amazon Q integration is architectural — not wired to live PRs |
| CDK synth passes with `LambdaServiceConstruct` | DORA Analyst agent designed, not implemented |
| DORA events emitted with correct schema | No package registry — git-based install only |
| Context layer (Cursor rules + Kiro steering) in place | `PipelineConfig` extension hooks (`pre_steps`/`post_steps`) not yet implemented |
