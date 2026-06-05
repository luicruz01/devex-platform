# Agent Boundaries

Three AI agents operate in the devex-platform ecosystem. Each agent has a fixed scope — what it receives, what it can do, and what it cannot do. These boundaries are not suggestions. Violating them (e.g. an agent that approves PRs, or a spec validator that generates code) undermines the trust model of the platform.

## Agent 1 — PR Reviewer (Amazon Q Developer)

**Triggered by:** A PR being opened or updated.

**Context it receives:**
- `git diff` of the PR
- `openapi.yaml` (if present in the repo)
- `.devex/config.yaml`

**CAN:**
- Comment on security issues in changed code
- Flag convention violations (Work ID missing from PR title, wrong branch format, missing `DoraEvent` emission)
- Detect API contract drift between the diff and `openapi.yaml`
- Flag missing error handling in handlers

**CANNOT:**
- Approve PRs
- Merge PRs
- Modify any file in the repository
- Access production secrets or environment variables

**Output format:** Inline PR comments. Each comment carries a severity level:
- `info` — suggestion, no action required
- `warn` — should be fixed before merge, not a blocker
- `block` — must be fixed before merge

A valid check: the agent's output contains only inline PR comments. Any output that is not an inline comment (e.g. a new commit, a file edit, a merge action) is a boundary violation.

## Agent 2 — Spec Validator (AWS Kiro)

**Triggered by:** An engineer opening a spec or design document in the Kiro interface.

**Context it receives:**
- The spec or design document being authored
- All `.kiro/steering/*.md` files from the current repository

**CAN:**
- Validate that the spec follows Golden Path rules from `.kiro/steering/golden-path.md`
- Suggest the correct CDK construct for a described infrastructure need (e.g. suggest `LambdaServiceConstruct` for a new Lambda)
- Flag technology choices that are not part of the Golden Path
- Point to the specific steering rule that a design violates

**CANNOT:**
- Generate implementation code
- Make architecture decisions on behalf of the team
- Override rules defined in `.kiro/steering/*.md` files
- Approve a spec for implementation

**Output format:** Inline feedback on the spec document, referencing the specific steering rule that applies.

A valid check: Kiro's output contains no code blocks and no statements of the form "here is the implementation." All output must be feedback on the spec, not a replacement for it.

## Agent 3 — DORA Analyst

**Triggered by:** A scheduled daily job, or an on-demand request from a platform team member.

**Context it receives:**
- `DoraEvent` stream from CloudWatch for the configured time window

**CAN:**
- Calculate DORA metrics (deployment frequency, lead time, change failure rate, MTTR) per team and cross-team
- Detect anomalies in the event stream (e.g. a team that has not emitted a `deploy-production` event in 14 days)
- Compare DORA metrics across teams using the shared schema
- Generate a natural language digest summarising the period

**CANNOT:**
- Make deployment decisions or trigger deployments
- Assign blame to individuals
- Access application source code
- Access secrets, credentials, or environment variables

**Output format:** A natural language digest. Any anomaly in the digest must reference specific Work IDs from the event stream so the platform team can investigate.

A valid check: the digest does not contain individual developer names — only team names and Work IDs. Any deployment decision language ("you should deploy", "this is ready for production") is a boundary violation.
