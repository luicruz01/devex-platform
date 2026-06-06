import { describe, expect, it, beforeEach, afterEach } from "vitest";
import * as fs from "node:fs";
import * as path from "node:path";
import * as os from "node:os";

import { DEVEX_VERSION } from "../src/index.js";
import { DoraEmitter } from "../src/dora/emitter.js";
import { StackDetector } from "../src/workflows/stack-detector.js";
import { PrPipelineGenerator } from "../src/workflows/pr-pipeline.js";
import { IntegrationPipelineGenerator } from "../src/workflows/integration-pipeline.js";

describe("devex-framework", () => {
  it("exports DEVEX_VERSION", () => {
    expect(DEVEX_VERSION).toBe("0.1.0");
  });
});

describe("DoraEmitter", () => {
  const emitter = new DoraEmitter();

  it("builds event with required fields", () => {
    const event = emitter.build({ work_id: "FIN-123", stage: "check", status: "success" });
    expect(event.work_id).toBe("FIN-123");
    expect(event.stage).toBe("check");
    expect(event.status).toBe("success");
  });

  it("defaults version to '1.0'", () => {
    const event = emitter.build({ work_id: "FIN-123", stage: "check", status: "success" });
    expect(event.version).toBe("1.0");
  });

  it("defaults environment to 'local'", () => {
    const event = emitter.build({ work_id: "FIN-123", stage: "check", status: "success" });
    expect(event.environment).toBe("local");
  });

  it("timestamp is valid ISO 8601", () => {
    const event = emitter.build({ work_id: "FIN-123", stage: "check", status: "success" });
    const date = new Date(event.timestamp);
    expect(date.toISOString()).toBe(event.timestamp);
  });
});

describe("StackDetector", () => {
  const detector = new StackDetector();
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "devex-test-"));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true });
  });

  it("detects python-lambda-cdk from pyproject.toml", () => {
    fs.writeFileSync(path.join(tmpDir, "pyproject.toml"), "");
    expect(detector.detect(tmpDir)).toBe("python-lambda-cdk");
  });

  it("detects go from go.mod", () => {
    fs.writeFileSync(path.join(tmpDir, "go.mod"), "");
    expect(detector.detect(tmpDir)).toBe("go");
  });

  it("returns unknown when no signal file is found", () => {
    expect(detector.detect(tmpDir)).toBe("unknown");
  });
});

describe("PrPipelineGenerator", () => {
  const generator = new PrPipelineGenerator();
  const config = {
    work_id_pattern: "^(FIN|PLAT)-[0-9]+",
    stack: "python-lambda-cdk" as const,
    team: "platform",
    environments: ["sandbox", "staging", "production"],
  };

  it("generated YAML contains 'on: pull_request'", () => {
    const yaml = generator.generate(config);
    expect(yaml).toContain("on: pull_request");
  });

  it("generated YAML contains stack-specific test command (pytest)", () => {
    const yaml = generator.generate(config);
    expect(yaml).toContain("pytest");
  });

  it("generated YAML contains 'environment: sandbox'", () => {
    const yaml = generator.generate(config);
    expect(yaml).toContain("environment: sandbox");
  });

  it("generated YAML contains the work_id_pattern", () => {
    const yaml = generator.generate(config);
    expect(yaml).toContain(config.work_id_pattern);
  });
});

describe("IntegrationPipelineGenerator", () => {
  const generator = new IntegrationPipelineGenerator();
  const config = {
    work_id_pattern: "^(FIN|PLAT)-[0-9]+",
    stack: "python-lambda-cdk" as const,
    team: "platform",
    environments: ["sandbox", "staging", "production"],
  };

  it("generated YAML contains 'on:\\n  push:'", () => {
    const yaml = generator.generate(config);
    expect(yaml).toContain("on:\n  push:");
  });

  it("generated YAML contains 'environment: production'", () => {
    const yaml = generator.generate(config);
    expect(yaml).toContain("environment: production");
  });

  it("generated YAML contains 'environment: staging'", () => {
    const yaml = generator.generate(config);
    expect(yaml).toContain("environment: staging");
  });

  it("generated YAML contains 'emit-dora'", () => {
    const yaml = generator.generate(config);
    expect(yaml).toContain("emit-dora");
  });
});
