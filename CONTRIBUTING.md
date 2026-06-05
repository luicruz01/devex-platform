# Contributing to devex-platform

devex-platform is an inner-source project — contributions from any engineering team are welcome and encouraged. Whether you are fixing a bug, adding support for a new language stack, or extending pipeline stages, follow the process below so changes stay reviewable and compatible across all adopting teams.

## Before you start

There are two types of contributions:

1. **Bug fixes and documentation** — open a PR directly against `main`.
2. **New features or breaking changes** — open a proposal issue first and wait for platform team approval before writing code.

## Proposal process

For new features:

1. Open a GitHub Issue titled: `[PROPOSAL] your description`
2. Include:
   - **Problem statement** — what pain point does this solve?
   - **Proposed solution** — concrete design, affected files, API shape
   - **Affected teams** — which teams benefit or need to migrate?
   - **Estimated effort** — rough sizing (hours or days)
3. Wait for a platform team label: `approved` or `needs-discussion`
4. Only start coding after the issue is labeled `approved`

## Development setup

```bash
# Clone
git clone git@github.com:luicruz01/devex-platform.git

# Install CLI deps
cd cli && uv sync --dev

# Install Framework deps
cd ../framework && pnpm install

# Run all tests
cd ../cli && uv run pytest
cd ../framework && pnpm test
```

## Adding a new stack

This is the most common contribution. Follow every step — skipping one leaves teams with inconsistent local checks and CI behavior.

1. **Add to `SupportedStack` type** in `framework/src/workflows/stack-detector.ts`
2. **Add signal file detection** in `StackDetector.detect()` — check for the stack's canonical marker file (e.g. `Cargo.toml` for Rust)
3. **Add test and lint steps** in `PrPipelineGenerator` — extend the `testSteps()` switch in `framework/src/workflows/pr-pipeline.ts`
4. **Add stack detection test** in `framework/tests/framework.test.ts` — create a temp directory with the signal file and assert detection
5. **Update the supported stacks table** in `README.md`
6. **Add a CLI check for the stack** in `cli/src/devex_cli/commands/check.py` — extend `_run_lint()` with the stack's lint command

## PR requirements

- Branch created with: `devex branch {WORK_ID} {description}`
- Title format: `WORK-ID: description` (e.g. `FIN-456: add rust stack support`)
- Two reviewers — one must be a platform team member
- All tests passing: `uv run pytest` + `pnpm test`
- `devex check` passing on the branch
- No changes to `DoraEvent` schema without platform approval

## What needs platform team approval

- `DoraEvent` schema changes (any field addition, removal, or type change)
- `LambdaServiceConstruct` API changes
- New CLI commands
- `config.yaml` schema changes
- Changes to pipeline stage order (validate → test → contract-validation → deploy)

## Code style

### CLI (Python)

- All output via Rich `Console` — never `print()` for user-facing messages
- All commands emit a `DoraEvent` on completion — both success and failure paths
- Exit code `0` on success, `1` on failure
- Type hints on all functions

### Framework (TypeScript)

- Strict TypeScript — no `any` except where documented (e.g. CDK table prop)
- All public APIs have JSDoc comments
- `DoraEmitter` for all event emission — `console.log` is reserved for DORA JSON output to stdout
