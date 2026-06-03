import { existsSync } from "node:fs";
import { join } from "node:path";

export type SupportedStack = "python-lambda-cdk" | "go" | "typescript" | "clojure";

export class StackDetector {
  detect(projectPath: string): SupportedStack {
    if (existsSync(join(projectPath, "pyproject.toml"))) return "python-lambda-cdk";
    if (existsSync(join(projectPath, "go.mod"))) return "go";
    if (existsSync(join(projectPath, "package.json"))) return "typescript";
    if (existsSync(join(projectPath, "deps.edn"))) return "clojure";
    return "python-lambda-cdk";
  }
}
