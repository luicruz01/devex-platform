import { Duration, Tags } from "aws-cdk-lib";
import * as apigwv2 from "aws-cdk-lib/aws-apigatewayv2";
import * as integrations from "aws-cdk-lib/aws-apigatewayv2-integrations";
import { ITable } from "aws-cdk-lib/aws-dynamodb";
import * as lambda from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";

export interface CollectorProps {
  table: ITable;
  environment: string;
  workId?: string;
}

export class CollectorConstruct extends Construct {
  readonly function: lambda.Function;
  readonly api: apigwv2.HttpApi;

  constructor(scope: Construct, id: string, props: CollectorProps) {
    super(scope, id);

    this.function = new lambda.Function(this, "Function", {
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset("../"),
      handler: "collector.main.handler",
      timeout: Duration.seconds(30),
      environment: {
        DEVEX_EVENTS_TABLE: props.table.tableName,
        DEVEX_ENVIRONMENT: props.environment,
      },
    });

    props.table.grantReadWriteData(this.function);

    this.api = new apigwv2.HttpApi(this, "HttpApi", {
      defaultIntegration: new integrations.HttpLambdaIntegration(
        "LambdaIntegration",
        this.function,
      ),
    });

    Tags.of(this.function).add("devex:managed", "true");
    Tags.of(this.function).add("devex:component", "collector");
    Tags.of(this.function).add("devex:environment", props.environment);

    if (props.workId) {
      Tags.of(this.function).add("devex:work-id", props.workId);
    }
  }
}
