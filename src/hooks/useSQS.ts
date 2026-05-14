import { useQuery } from '@tanstack/react-query'
import { listMessages, listQueues } from '../aws/sqs'

export const useSQQueues = () =>
  useQuery({ queryKey: ['sqs-queues'], queryFn: listQueues })

export const useSQMessages = (queueUrl?: string) =>
  useQuery({
    queryKey: queueUrl ? ['sqs-messages', queueUrl] : [],
    queryFn: () => listMessages(queueUrl!),
    enabled: !!queueUrl,
  })
