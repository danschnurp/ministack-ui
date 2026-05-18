import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listBuckets, listObjects } from '../aws/s3'
import { listTables, scanTable } from '../aws/dynamo'
import { listQueues, receiveMessages, sendMessage } from '../aws/sqs'
import { listLogGroups, getLogEvents } from '../aws/logs'

// ── S3 ────────────────────────────────────────────────────────────────────────

export const useS3Buckets = () =>
  useQuery({ queryKey: ['s3-buckets'], queryFn: listBuckets, refetchInterval: 5000 })

export const useS3Objects = (bucket: string) =>
  useQuery({
    queryKey: ['s3-objects', bucket],
    queryFn: () => listObjects(bucket),
    enabled: !!bucket,
  })

// ── DynamoDB ──────────────────────────────────────────────────────────────────

export const useDynamoTables = () =>
  useQuery({ queryKey: ['dynamo-tables'], queryFn: listTables, refetchInterval: 5000 })

export const useDynamoScan = (table: string) =>
  useQuery({
    queryKey: ['dynamo-scan', table],
    queryFn: () => scanTable(table),
    enabled: !!table,
  })

// ── SQS ───────────────────────────────────────────────────────────────────────

export const useSQSQueues = () =>
  useQuery({ queryKey: ['sqs-queues'], queryFn: listQueues, refetchInterval: 5000 })

export const useSQSMessages = (queueUrl: string) =>
  useQuery({
    queryKey: ['sqs-messages', queueUrl],
    queryFn: () => receiveMessages(queueUrl),
    enabled: !!queueUrl,
    refetchInterval: 3000,
  })

export const useSendMessage = (queueUrl: string) => {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: string) => sendMessage(queueUrl, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sqs-messages', queueUrl] }),
  })
}

// ── CloudWatch Logs ───────────────────────────────────────────────────────────

export const useLogGroups = () =>
  useQuery({ queryKey: ['log-groups'], queryFn: listLogGroups, refetchInterval: 10000 })

export const useLogEvents = (logGroupName: string, logStreamName: string) =>
  useQuery({
    queryKey: ['log-events', logGroupName, logStreamName],
    queryFn: () => getLogEvents(logGroupName, logStreamName),
    enabled: !!logGroupName && !!logStreamName,
    refetchInterval: 5000,
  })
