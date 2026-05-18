import { cwLogs, withTimeout } from './clients'
import { DescribeLogGroupsCommand, GetLogEventsCommand } from '@aws-sdk/client-cloudwatch-logs'

export const listLogGroups = () =>
  withTimeout(cwLogs.send(new DescribeLogGroupsCommand({}))).then(r => r.logGroups ?? [])

export const getLogEvents = (logGroupName: string, logStreamName: string) =>
  withTimeout(cwLogs.send(new GetLogEventsCommand({ logGroupName, logStreamName, limit: 100 }))).then(r => r.events ?? [])