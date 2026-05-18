import { sqs, withTimeout } from './clients'
import {
  ListQueuesCommand,
  ReceiveMessageCommand,
  SendMessageCommand,
} from '@aws-sdk/client-sqs'

export const listQueues = () =>
  withTimeout(sqs.send(new ListQueuesCommand({}))).then(r => r.QueueUrls ?? [])

export const receiveMessages = (queueUrl: string, max = 10) =>
  withTimeout(sqs.send(new ReceiveMessageCommand({ QueueUrl: queueUrl, MaxNumberOfMessages: max }))).then(r => r.Messages ?? [])

export const sendMessage = (queueUrl: string, body: string) =>
  withTimeout(sqs.send(new SendMessageCommand({ QueueUrl: queueUrl, MessageBody: body })))