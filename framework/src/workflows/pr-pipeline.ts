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
    case "unknown":
      return `      - name: No stack detected
        run: echo "Stack unknown — add signal file (pyproject.toml, go.mod, etc.)"`;
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
      - name: Record start time
        run: echo "JOB_START=$SECONDS" >> $GITHUB_ENV
      - name: Contract validation
        if: hashFiles('openapi.yaml') != ''
        run: pip install schemathesis && schemathesis run openapi.yaml --dry-run
      - name: Emit DORA event
        if: always()
        run: |
          STATUS="success"
          if [ "\${{ job.status }}" != "success" ]; then
            STATUS="failure"
          fi
          WORK_ID=$(echo "\${{ github.head_ref }}" | grep -oE '[A-Z]+-[0-9]+' | head -1)
          DURATION=$(( (SECONDS - \${JOB_START:-0}) * 1000 ))
          echo "{\"version\":\"2.0\",\"work_id\":\"$WORK_ID\",\"team\":\"${config.team}\",\"stack\":\"${config.stack}\",\"stage\":\"pr-pipeline\",\"environment\":\"sandbox\",\"status\":\"$STATUS\",\"duration_ms\":$DURATION,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

  deploy-sandbox:
    needs: [contract-validation]
    runs-on: ubuntu-latest
    environment: sandbox
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Record start time
        run: echo "JOB_START=$SECONDS" >> $GITHUB_ENV
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: \${{ secrets.DEVEX_DEPLOY_ROLE_ARN_SANDBOX }}
          aws-region: ${region}
      - name: Deploy to sandbox
        run: cdk deploy ${stackName} --require-approval never
      - name: Emit DORA event
        if: always()
        run: |
          STATUS="success"
          if [ "\${{ job.status }}" != "success" ]; then
            STATUS="failure"
          fi
          WORK_ID=$(echo "\${{ github.head_ref }}" | grep -oE '[A-Z]+-[0-9]+' | head -1)
          DURATION=$(( (SECONDS - \${JOB_START:-0}) * 1000 ))
          echo "{\"version\":\"2.0\",\"work_id\":\"$WORK_ID\",\"team\":\"${config.team}\",\"stack\":\"${config.stack}\",\"stage\":\"deploy-sandbox\",\"environment\":\"sandbox\",\"status\":\"$STATUS\",\"duration_ms\":$DURATION,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
`;
  }
}
