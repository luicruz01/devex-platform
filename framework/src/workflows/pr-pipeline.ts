import type { SupportedStack } from "./stack-detector.js";

export interface PipelineConfig {
  work_id_pattern: string;
  stack: SupportedStack;
  team: string;
  environments: string[];
  aws_region?: string;
}

function testSteps(stack: SupportedStack): string {
  switch (stack) {
    case "python-lambda-cdk":
      return `      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run pytest
        run: pytest test/ -v
      - name: Run ruff
        run: pip install ruff && ruff check .`;
    case "go":
      return `      - name: Run tests
        run: go test ./...`;
    case "typescript":
      return `      - name: Install and test
        run: pnpm install && pnpm test`;
    case "clojure":
      return `      - name: Run tests
        run: lein test`;
  }
}

export class PrPipelineGenerator {
  generate(config: PipelineConfig): string {
    const region = config.aws_region ?? "us-east-1";
    const stackName = `${config.team}-${config.stack}-sandbox`;

    return `name: PR Pipeline - ${config.team}
on: pull_request

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate branch name
        run: |
          if [[ ! "$GITHUB_HEAD_REF" =~ ${config.work_id_pattern} ]]; then
            echo "Branch '$GITHUB_HEAD_REF' does not match required pattern '${config.work_id_pattern}'"
            exit 1
          fi

  test:
    needs: [validate]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
${testSteps(config.stack)}

  contract-validation:
    needs: [test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Contract validation
        if: hashFiles('openapi.yaml') != ''
        run: pip install schemathesis && schemathesis run openapi.yaml --dry-run

  deploy-sandbox:
    needs: [contract-validation]
    runs-on: ubuntu-latest
    environment: sandbox
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: \${{ secrets.DEVEX_DEPLOY_ROLE_ARN_SANDBOX }}
          aws-region: ${region}
      - name: Deploy to sandbox
        run: cdk deploy ${stackName} --require-approval never
`;
  }
}
