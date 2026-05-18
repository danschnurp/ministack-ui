import { KinesisClient, ListStreamsCommand, DescribeStreamSummaryCommand, ListShardsCommand } from '@aws-sdk/client-kinesis'
import { sharedConfig, withTimeout } from './clients'

const kinesis = new KinesisClient(sharedConfig)

export const listStreams = () =>
  withTimeout(kinesis.send(new ListStreamsCommand({}))).then(r => r.StreamNames ?? [])

export const describeStream = (StreamName: string) =>
  withTimeout(kinesis.send(new DescribeStreamSummaryCommand({ StreamName }))).then(r => r.StreamDescriptionSummary)

export const listShards = (StreamName: string) =>
  withTimeout(kinesis.send(new ListShardsCommand({ StreamName }))).then(r => r.Shards ?? [])
