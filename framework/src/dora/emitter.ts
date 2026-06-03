import type { DoraEvent, DoraStage, DoraStatus, DoraEnvironment } from "./types.js";

export class DoraEmitter {
  emit(event: DoraEvent): void {
    console.log(JSON.stringify(event));
  }

  build(params: {
    work_id: string;
    stage: DoraStage;
    status: DoraStatus;
    team?: string;
    stack?: string;
    environment?: DoraEnvironment;
    duration_ms?: number;
  }): DoraEvent {
    return {
      version: "1.0",
      work_id: params.work_id,
      team: params.team ?? "platform",
      stack: params.stack ?? "unknown",
      stage: params.stage,
      environment: params.environment ?? "local",
      status: params.status,
      duration_ms: params.duration_ms ?? 0,
      timestamp: new Date().toISOString(),
    };
  }
}
