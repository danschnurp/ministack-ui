import { sqs } from './clients'
import { ListQueuesCommand } from '@aws-sdk/client-sqs'
import { ReceiveMessageCommand } from '@aws-sdk/client-sqs'

export const listQueues = async () => {
  const res = await sqs.send(new ListQueuesCommand({}))
  return res.QueueUrls ?? []
}

export const listMessages = async (queueUrl: string) => {
  const res = await sqs.send(
    new ReceiveMessageCommand({
      QueueUrl: queueUrl,
      MaxNumberOfMessages: 10,
      WaitTimeSeconds: 0,
    })
  )
  return res.Messages ?? []
}
