import { describe, expect, it } from "vitest";
import { ZodError } from "zod";

import {
  DoraEventSchema,
  DoraEventV1Schema,
  DoraEventV2Schema,
  parseEvent,
} from "../src/dora-event.js";

const baseV1 = {
  version: "1.0" as const,
  work_id: "FIN-123",
  team: "platform",
  stack: "python-lambda-cdk",
  stage: "check" as const,
  status: "success" as const,
  duration_ms: 0,
  timestamp: "2026-06-06T12:00:00.000Z",
};

describe("DoraEventSchema", () => {
  it("parses valid v1 event", () => {
    const event = DoraEventV1Schema.parse(baseV1);
    expect(event.version).toBe("1.0");
    expect(event.work_id).toBe("FIN-123");
    expect(event.environment).toBe("local");
  });

  it("parses valid v2 event with all optional fields", () => {
    const event = DoraEventV2Schema.parse({
      ...baseV1,
      version: "2.0",
      event_id: "550e8400-e29b-41d4-a716-446655440000",
      correlation_id: "corr-abc",
      repo: "transactionify",
      service: "payments-api",
      commit_sha: "abc123def456",
      pr_number: 42,
      workflow_run_id: "123456789",
      actor: "luis",
      failure_reason: "timeout",
      status: "failure",
    });
    expect(event.version).toBe("2.0");
    expect(event.repo).toBe("transactionify");
    expect(event.pr_number).toBe(42);
  });

  it("rejects unknown version string", () => {
    expect(() =>
      DoraEventSchema.parse({
        ...baseV1,
        version: "3.0",
      }),
    ).toThrow(ZodError);
  });

  it("v2 event_id must be valid UUID format", () => {
    expect(() =>
      DoraEventV2Schema.parse({
        ...baseV1,
        version: "2.0",
        event_id: "not-a-uuid",
      }),
    ).toThrow(ZodError);
  });

  it("discriminated union routes correctly by version field", () => {
    const v1 = DoraEventSchema.parse(baseV1);
    expect(v1.version).toBe("1.0");

    const v2 = DoraEventSchema.parse({
      ...baseV1,
      version: "2.0",
      event_id: "550e8400-e29b-41d4-a716-446655440000",
    });
    expect(v2.version).toBe("2.0");
    if (v2.version === "2.0") {
      expect(v2.event_id).toBe("550e8400-e29b-41d4-a716-446655440000");
    }
  });

  it("parseEvent throws ZodError on invalid data", () => {
    expect(() => parseEvent({ work_id: "FIN-123" })).toThrow(ZodError);
  });
});
