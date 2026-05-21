import { eb, withTimeout } from './clients'
import {
  ListRulesCommand,
  ListTargetsByRuleCommand,
  ListEventBusesCommand,
} from '@aws-sdk/client-eventbridge'

export const listRules = () =>
  withTimeout(eb.send(new ListRulesCommand({}))).then(r => r.Rules ?? [])

export const listTargets = (Rule: string) =>
  withTimeout(eb.send(new ListTargetsByRuleCommand({ Rule }))).then(r => r.Targets ?? [])

export const listEventBuses = () =>
  withTimeout(eb.send(new ListEventBusesCommand({}))).then(r => r.EventBuses ?? [])
