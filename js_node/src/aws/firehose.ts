import { firehose, withTimeout } from './clients'
import {
  ListDeliveryStreamsCommand,
  DescribeDeliveryStreamCommand,
} from '@aws-sdk/client-firehose'

export const listDeliveryStreams = () =>
  withTimeout(firehose.send(new ListDeliveryStreamsCommand({}))).then(r => r.DeliveryStreamNames ?? [])

export const describeDeliveryStream = (DeliveryStreamName: string) =>
  withTimeout(firehose.send(new DescribeDeliveryStreamCommand({ DeliveryStreamName }))).then(r => r.DeliveryStreamDescription)
