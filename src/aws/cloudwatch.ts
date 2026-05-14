import { cwLogs } from './clients'
import { DescribeLogStreamsCommand, GetLogEventsCommand } from '@aws-sdk/client-cloudwatch-logs'

export const listLogGroups = async () => {
  const res = await cwLogs.send(new DescribeLogStreamsCommand({ logGroupNamePrefix: '' }))
  return res.logGroups?.map(g => g.logGroupName) ?? []
}

export const listLogStreams = async (logGroupName: string) => {
  const res = await cwLogs.send(new DescribeLogStreamsCommand({ logGroupName }))
  return res.logStreams?.map(s => s.logStreamName) ?? []
}

export const getLogEvents = async (logGroupName: string, logStreamName: string) => {
  const res = await cwLogs.send(new GetLogEventsCommand({
    logGroupName,
    logStreamName,
  }))
  return res.events ?? []
}
