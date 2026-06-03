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
  stage: string;
  environment: string;
  status: DoraStatus;
  duration_ms: number;
  timestamp: string;
}
