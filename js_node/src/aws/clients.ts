import { S3Client } from '@aws-sdk/client-s3'
import { DynamoDBClient } from '@aws-sdk/client-dynamodb'
import { SQSClient } from '@aws-sdk/client-sqs'
import { CloudWatchLogsClient } from '@aws-sdk/client-cloudwatch-logs'

// In dev, traffic goes through the Vite proxy to avoid CORS.
// In a Tauri build, the app is a native webview — no Vite proxy exists,
// so we talk directly to MiniStack on :4566.
export const SDK_ENDPOINT = import.meta.env.DEV
  ? 'http://localhost:5173/api'
  : 'http://localhost:4566'

export const sharedConfig = {
  endpoint: SDK_ENDPOINT,
  region: 'us-east-1',
  credentials: { accessKeyId: 'test', secretAccessKey: 'test' },
  forcePathStyle: true,
}

export const s3     = new S3Client(sharedConfig)
export const dynamo = new DynamoDBClient(sharedConfig)
export const sqs    = new SQSClient(sharedConfig)
export const cwLogs = new CloudWatchLogsClient(sharedConfig)

/** Race any SDK promise against a hard deadline (default 3 s). */
export function withTimeout<T>(promise: Promise<T>, ms = 3000): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`Timed out after ${ms} ms`)), ms)
    ),
  ])
}

import { LambdaClient } from '@aws-sdk/client-lambda'
import { KinesisClient } from '@aws-sdk/client-kinesis'
import { SNSClient } from '@aws-sdk/client-sns'
import { APIGatewayClient } from '@aws-sdk/client-api-gateway'
import { CloudWatchClient } from '@aws-sdk/client-cloudwatch'
import { EC2Client } from '@aws-sdk/client-ec2'
import { EventBridgeClient } from '@aws-sdk/client-eventbridge'
import { GlueClient } from '@aws-sdk/client-glue'
import { IAMClient } from '@aws-sdk/client-iam'
import { FirehoseClient } from '@aws-sdk/client-firehose'
import { KMSClient } from '@aws-sdk/client-kms'
import { SFNClient } from '@aws-sdk/client-sfn'
import { WAFV2Client } from '@aws-sdk/client-wafv2'

export const lambda    = new LambdaClient(sharedConfig)
export const kinesis   = new KinesisClient(sharedConfig)
export const sns       = new SNSClient(sharedConfig)
export const apigw     = new APIGatewayClient(sharedConfig)
export const cw        = new CloudWatchClient(sharedConfig)
export const ec2       = new EC2Client(sharedConfig)
export const eb        = new EventBridgeClient(sharedConfig)
export const glue      = new GlueClient(sharedConfig)
export const iam       = new IAMClient(sharedConfig)
export const firehose  = new FirehoseClient(sharedConfig)
export const kms       = new KMSClient(sharedConfig)
export const sfn       = new SFNClient(sharedConfig)
export const wafv2     = new WAFV2Client(sharedConfig)
