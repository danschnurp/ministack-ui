import { useQuery } from '@tanstack/react-query'
import { listLogGroups, listLogStreams, getLogEvents } from '../aws/cloudwatch'

export const useLogGroups = () =>
  useQuery({ queryKey: ['cloudwatch-log-groups'], queryFn: listLogGroups, refetchInterval: 10000 })

export const useLogStreams = (logGroupName: string) =>
  useQuery({ 
    queryKey: ['cloudwatch-log-streams', logGroupName], 
    queryFn: () => listLogStreams(logGroupName), 
    enabled: !!logGroupName 
  })

export const useLogEvents = (logGroupName: string, logStreamName: string) =>
  useQuery({ 
    queryKey: ['cloudwatch-log-events', logGroupName, logStreamName], 
    queryFn: () => getLogEvents(logGroupName, logStreamName), 
    enabled: !!logGroupName && !!logStreamName 
  })
