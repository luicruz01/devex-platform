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
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: \${{ secrets.DEVEX_DEPLOY_ROLE_ARN_SANDBOX }}
          aws-region: ${region}
      - name: Deploy to sandbox
        run: cdk deploy ${sandboxStack} --require-approval never

  deploy-staging:
    needs: [deploy-sandbox]
    runs-on: ubuntu-latest
    environment: staging
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: \${{ secrets.DEVEX_DEPLOY_ROLE_ARN_STAGING }}
          aws-region: ${region}
      - name: Deploy to staging
        run: cdk deploy ${stagingStack} --require-approval never

  deploy-production:
    needs: [deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: \${{ secrets.DEVEX_DEPLOY_ROLE_ARN_PRODUCTION }}
          aws-region: ${region}
      - name: Deploy to production
        run: cdk deploy ${productionStack} --require-approval never

  emit-dora:
    needs: [deploy-production]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Emit DORA event
        run: |
          echo '{"version":"1.0","work_id":"${config.team}","team":"${config.team}","stack":"${config.stack}","stage":"integration-pipeline","environment":"production","status":"success","duration_ms":0,"timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'
`;
  }
}
