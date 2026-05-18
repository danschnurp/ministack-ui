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
