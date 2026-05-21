import { sfn, withTimeout } from './clients'
import {
  ListStateMachinesCommand,
  DescribeStateMachineCommand,
  ListExecutionsCommand,
  DescribeExecutionCommand,
} from '@aws-sdk/client-sfn'

export const listStateMachines = () =>
  withTimeout(sfn.send(new ListStateMachinesCommand({}))).then(r => r.stateMachines ?? [])

export const describeStateMachine = (stateMachineArn: string) =>
  withTimeout(sfn.send(new DescribeStateMachineCommand({ stateMachineArn })))

export const listExecutions = (stateMachineArn: string) =>
  withTimeout(sfn.send(new ListExecutionsCommand({ stateMachineArn, maxResults: 20 }))).then(r => r.executions ?? [])

export const describeExecution = (executionArn: string) =>
  withTimeout(sfn.send(new DescribeExecutionCommand({ executionArn })))
