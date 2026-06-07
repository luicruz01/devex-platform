import type { PipelineConfig } from "./pr-pipeline.js";

export class IntegrationPipelineGenerator {
  generate(config: PipelineConfig): string {
    const region = config.aws_region ?? "us-east-1";
    const sandboxStack = `${config.team}-${config.stack}-sandbox`;
    const stagingStack = `${config.team}-${config.stack}-staging`;
    const productionStack = `${config.team}-${config.stack}-production`;

    return `name: Integration Pipeline - ${config.team}
on:
  push:
    branches:
      - main

jobs:
  deploy-sandbox:
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
        run: cdk deploy ${sandboxStack} --require-approval never
      - name: Emit DORA event
        if: always()
        run: |
          WORK_ID=$(echo "\${{ github.event.head_commit.message }}" | grep -oE '[A-Z]+-[0-9]+' | head -1)
          STATUS="success"
          if [ "\${{ job.status }}" != "success" ]; then
            STATUS="failure"
          fi
          FAILURE_REASON=""
          if [ "$STATUS" = "failure" ]; then
            FAILURE_REASON=",\"failure_reason\":\"pipeline-step-failed\""
          fi
          DURATION=$(( (SECONDS - \${JOB_START:-0}) * 1000 ))
          echo "{\"version\":\"2.0\",\"work_id\":\"$WORK_ID\",\"team\":\"${config.team}\",\"stack\":\"${config.stack}\",\"stage\":\"deploy-sandbox\",\"environment\":\"sandbox\",\"status\":\"$STATUS\"$FAILURE_REASON,\"duration_ms\":$DURATION,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

  deploy-staging:
    needs: [deploy-sandbox]
    runs-on: ubuntu-latest
    environment: staging
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
          role-to-assume: \${{ secrets.DEVEX_DEPLOY_ROLE_ARN_STAGING }}
          aws-region: ${region}
      - name: Deploy to staging
        run: cdk deploy ${stagingStack} --require-approval never
      - name: Emit DORA event
        if: always()
        run: |
          WORK_ID=$(echo "\${{ github.event.head_commit.message }}" | grep -oE '[A-Z]+-[0-9]+' | head -1)
          STATUS="success"
          if [ "\${{ job.status }}" != "success" ]; then
            STATUS="failure"
          fi
          FAILURE_REASON=""
          if [ "$STATUS" = "failure" ]; then
            FAILURE_REASON=",\"failure_reason\":\"pipeline-step-failed\""
          fi
          DURATION=$(( (SECONDS - \${JOB_START:-0}) * 1000 ))
          echo "{\"version\":\"2.0\",\"work_id\":\"$WORK_ID\",\"team\":\"${config.team}\",\"stack\":\"${config.stack}\",\"stage\":\"deploy-staging\",\"environment\":\"staging\",\"status\":\"$STATUS\"$FAILURE_REASON,\"duration_ms\":$DURATION,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

  deploy-production:
    needs: [deploy-staging]
    runs-on: ubuntu-latest
    environment: production
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
          role-to-assume: \${{ secrets.DEVEX_DEPLOY_ROLE_ARN_PRODUCTION }}
          aws-region: ${region}
      - name: Deploy to production
        run: cdk deploy ${productionStack} --require-approval never
      - name: Emit DORA event
        if: always()
        run: |
          WORK_ID=$(echo "\${{ github.event.head_commit.message }}" | grep -oE '[A-Z]+-[0-9]+' | head -1)
          STATUS="success"
          if [ "\${{ job.status }}" != "success" ]; then
            STATUS="failure"
          fi
          FAILURE_REASON=""
          if [ "$STATUS" = "failure" ]; then
            FAILURE_REASON=",\"failure_reason\":\"pipeline-step-failed\""
          fi
          DURATION=$(( (SECONDS - \${JOB_START:-0}) * 1000 ))
          echo "{\"version\":\"2.0\",\"work_id\":\"$WORK_ID\",\"team\":\"${config.team}\",\"stack\":\"${config.stack}\",\"stage\":\"deploy-production\",\"environment\":\"production\",\"status\":\"$STATUS\"$FAILURE_REASON,\"duration_ms\":$DURATION,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

  emit-dora:
    needs: [deploy-production]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Record start time
        run: echo "JOB_START=$SECONDS" >> $GITHUB_ENV
      - name: Emit DORA event
        run: |
          WORK_ID=$(echo "\${{ github.event.head_commit.message }}" | grep -oE '[A-Z]+-[0-9]+' | head -1)
          STATUS="success"
          if [ "\${{ job.status }}" != "success" ]; then
            STATUS="failure"
          fi
          FAILURE_REASON=""
          if [ "$STATUS" = "failure" ]; then
            FAILURE_REASON=",\"failure_reason\":\"pipeline-step-failed\""
          fi
          DURATION=$(( (SECONDS - \${JOB_START:-0}) * 1000 ))
          echo "{\"version\":\"2.0\",\"work_id\":\"$WORK_ID\",\"team\":\"${config.team}\",\"stack\":\"${config.stack}\",\"stage\":\"integration-pipeline\",\"environment\":\"production\",\"status\":\"$STATUS\"$FAILURE_REASON,\"duration_ms\":$DURATION,\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"
`;
  }
}
