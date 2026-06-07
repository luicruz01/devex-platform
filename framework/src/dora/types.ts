export type DoraStage =
  | "init"
  | "branch-create"
  | "check"
  | "pr-pipeline"
  | "deploy-sandbox"
  | "deploy-staging"
  | "deploy-production"
  | "integration-pipeline";

export type DoraStatus = "success" | "failure";

export type DoraEnvironment = "sandbox" | "staging" | "production" | "local";

export interface DoraEvent {
  version: "1.0";
  work_id: string;
  team: string;
  stack: string;
  stage: DoraStage;
  environment: DoraEnvironment;
  status: DoraStatus;
  duration_ms: number;
  timestamp: string;
}

export interface DoraEventV2 extends Omit<DoraEvent, "version"> {
  version: "2.0";
  event_id: string;
  correlation_id?: string;
  repo?: string;
  service?: string;
  commit_sha?: string;
  pr_number?: number;
  workflow_run_id?: string;
  actor?: string;
  failure_reason?: string;
}

export type AnyDoraEvent = DoraEvent | DoraEventV2;
