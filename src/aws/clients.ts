import { S3Client } from '@aws-sdk/client-s3'
import { DynamoDBClient } from '@aws-sdk/client-dynamodb'
import { SQSClient } from '@aws-sdk/client-sqs'
import { CloudWatchLogsClient } from '@aws-sdk/client-cloudwatch-logs'

const config = {
  endpoint: 'http://localhost:5173/api', // routed through Vite proxy → :4566
  region: 'us-east-1',
  credentials: { accessKeyId: 'test', secretAccessKey: 'test' },
  forcePathStyle: true,
}

export const s3     = new S3Client(config)
export const dynamo = new DynamoDBClient(config)
export const sqs    = new SQSClient(config)
export const cwLogs = new CloudWatchLogsClient(config)

/** Wrap any SDK send() call with a hard timeout (default 3 s). */
export function withTimeout<T>(promise: Promise<T>, ms = 3000): Promise<T> {
  return Promise.race([
    promise,
    new Promise<never>((_, reject) =>
      setTimeout(() => reject(new Error(`Request timed out after ${ms} ms`)), ms)
    ),
  ])
}