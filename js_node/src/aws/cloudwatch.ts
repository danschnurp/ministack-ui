import { cw, withTimeout } from './clients'
import {
  ListMetricsCommand,
  GetMetricStatisticsCommand,
  DescribeAlarmsCommand,
} from '@aws-sdk/client-cloudwatch'

export const listMetrics = () =>
  withTimeout(cw.send(new ListMetricsCommand({}))).then(r => r.Metrics ?? [])

export const getMetricStats = (Namespace: string, MetricName: string, hours = 3) => {
  const EndTime = new Date()
  const StartTime = new Date(EndTime.getTime() - hours * 3600 * 1000)
  return withTimeout(cw.send(new GetMetricStatisticsCommand({
    Namespace, MetricName, StartTime, EndTime,
    Period: 300,
    Statistics: ['Average', 'Sum', 'Maximum'],
  }))).then(r => (r.Datapoints ?? []).sort((a, b) => +a.Timestamp! - +b.Timestamp!))
}

export const listAlarms = () =>
  withTimeout(cw.send(new DescribeAlarmsCommand({}))).then(r => r.MetricAlarms ?? [])
