# Golden Path

The Golden Path defines the non-negotiable architectural decisions shared across all teams using the devex-platform ecosystem. Every team that adopts devex-platform agrees to these rules. Deviations require a platform team decision and a `[PROPOSAL]` issue.

## Work ID

Every branch, every commit, every PR, and every DORA event must carry a Work ID.

The Work ID is the audit thread — it is the single token that connects a line of deployed code back to the business intent that justified it.

Format: `{PROJECT}-{NUMBER}` — e.g. `FIN-123`, `PLAT-42`.

The Work ID pattern is configured per-project in `.devex/config.yaml` under the `work_id_pattern` key. The default is `^[A-Z]+-\d+$`. A project may narrow this (e.g. `^FIN-\d+$`) but may not remove it.

A branch, commit, or PR that lacks a valid Work ID prefix is non-compliant and must not be merged.

## Pipeline Structure

All teams use the same two-pipeline structure.

**PR Pipeline** (runs on every PR):

```
validate → test → contract-validation → deploy-sandbox
```

**Integration Pipeline** (runs after PR merge):

```
deploy-sandbox → deploy-staging → deploy-production
```

These four stages (and the two pipelines) are fixed. Teams may add steps within a stage. Teams may not remove a stage, rename a stage, or reorder stages.

A valid check: look at the generated YAML from `PrPipelineGenerator` and `IntegrationPipelineGenerator` in `framework/src/` — any stage missing from the output is a violation.

## DORA Telemetry

Every pipeline stage emits a `DoraEvent` to stdout.

CloudWatch ingests these events from pipeline logs for cross-team DORA metric calculation.

Schema version is always `"1.0"`. Omitting any required field is a violation.

A valid check: parse every line of pipeline stdout and confirm it is valid JSON that matches the `DoraEvent` type from `framework/src/`.

## Authentication

AWS access uses OIDC only. Long-lived IAM access keys are not permitted in any environment.

Each team has one IAM role per environment. The role ARN is stored as a GitHub Actions secret named `DEVEX_DEPLOY_ROLE_ARN_{ENV}` where `{ENV}` is `SANDBOX`, `STAGING`, or `PRODUCTION`.

A valid check: the pipeline YAML must not contain `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`. It must contain an OIDC `permissions: id-token: write` block and an `aws-actions/configure-aws-credentials` step using `role-to-assume`.

## Environments

Three environments exist: `sandbox`, `staging`, `production`.

**Sandbox**: Deployed automatically on every PR. Used for PR validation.

**Staging**: Deployed automatically after a PR merges to the main branch. Used for integration testing.

**Production**: Requires manual approval via a GitHub environment protection rule before deployment proceeds. No automated deployments to production.

A valid check: the integration pipeline YAML must have a `deploy-production` job that references a GitHub environment with at least one required reviewer configured.
