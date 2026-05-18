import { SNSClient, ListTopicsCommand, ListSubscriptionsCommand, PublishCommand } from '@aws-sdk/client-sns'
import { sharedConfig, withTimeout } from './clients'

const sns = new SNSClient(sharedConfig)

export const listTopics = () =>
  withTimeout(sns.send(new ListTopicsCommand({}))).then(r => r.Topics ?? [])

export const listSubscriptions = () =>
  withTimeout(sns.send(new ListSubscriptionsCommand({}))).then(r => r.Subscriptions ?? [])

export const publishMessage = (TopicArn: string, Message: string, Subject?: string) =>
  withTimeout(sns.send(new PublishCommand({ TopicArn, Message, Subject })))
