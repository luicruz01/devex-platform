import * as lambda from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import { Tags, Duration } from "aws-cdk-lib";
import { DoraEmitter } from "../dora/emitter.js";

export interface LambdaServiceProps {
  handlerPath: string;
  codePath?: string;
  runtime?: string;
  tableNameEnvVar?: string;
  table: any;
  timeout?: number;
  environment?: Record<string, string>;
  workId?: string;
}

export class LambdaServiceConstruct extends Construct {
  readonly function: lambda.Function;

  constructor(scope: Construct, id: string, props: LambdaServiceProps) {
    super(scope, id);

    const codePath = props.codePath ?? "src/python";
    const timeoutSeconds = props.timeout ?? 30;
    const tableNameEnvVar = props.tableNameEnvVar ?? "TABLE_NAME";

    this.function = new lambda.Function(this, "Function", {
      runtime: lambda.Runtime.PYTHON_3_9,
      code: lambda.Code.fromAsset(codePath),
      handler: props.handlerPath,
      environment: {
        [tableNameEnvVar]: props.table.tableName,
        ...props.environment,
      },
      timeout: Duration.seconds(timeoutSeconds),
    });

    Tags.of(this.function).add("devex:work-id", props.workId ?? "untracked");
    Tags.of(this.function).add("devex:managed", "true");

    props.table.grantReadWriteData(this.function);

    const emitter = new DoraEmitter();
    emitter.emit(
      emitter.build({
        work_id: props.workId ?? "untracked",
        stage: "deploy-sandbox",
        status: "success",
      })
    );
  }
}
