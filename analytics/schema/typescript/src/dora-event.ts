import { z } from "zod";

export const DoraStatusSchema = z.enum(["success", "failure"]);
export const DoraEnvironmentSchema = z.enum([
  "sandbox",
  "staging",
  "production",
  "local",
]);
export const DoraStageSchema = z.enum([
  "init",
  "branch-create",
  "check",
  "pr-pipeline",
  "deploy-sandbox",
  "deploy-staging",
  "deploy-production",
  "integration-pipeline",
  "collect",
  "analyze",
]);

export const DoraEventV1Schema = z.object({
  version: z.literal("1.0"),
  work_id: z.string(),
  team: z.string(),
  stack: z.string(),
  stage: DoraStageSchema,
  environment: DoraEnvironmentSchema.default("local"),
  status: DoraStatusSchema,
  duration_ms: z.number().int().default(0),
  timestamp: z.string(),
});

export const DoraEventV2Schema = DoraEventV1Schema.extend({
  version: z.literal("2.0"),
  event_id: z.string().uuid(),
  correlation_id: z.string().optional(),
  repo: z.string().optional(),
  service: z.string().optional(),
  commit_sha: z.string().optional(),
  pr_number: z.number().int().positive().optional(),
  workflow_run_id: z.string().optional(),
  actor: z.string().optional(),
  failure_reason: z.string().optional(),
});

export const DoraEventSchema = z.discriminatedUnion("version", [
  DoraEventV1Schema,
  DoraEventV2Schema,
]);

export type DoraEventV1 = z.infer<typeof DoraEventV1Schema>;
export type DoraEventV2 = z.infer<typeof DoraEventV2Schema>;
export type DoraEvent = z.infer<typeof DoraEventSchema>;

export function parseEvent(data: unknown): DoraEvent {
  return DoraEventSchema.parse(data);
}
