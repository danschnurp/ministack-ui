import { dynamo, withTimeout } from './clients'
import {
  ListTablesCommand,
  ScanCommand,
  AttributeValue,
} from '@aws-sdk/client-dynamodb'

function unmarshall(item: Record<string, AttributeValue>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(item).map(([k, v]) => [k, unwrap(v)]))
}

function unwrap(v: AttributeValue): unknown {
  if ('S' in v) return v.S
  if ('N' in v) return v.N
  if ('BOOL' in v) return v.BOOL
  if ('NULL' in v) return null
  if ('L' in v) return v.L?.map(unwrap)
  if ('M' in v) return unmarshall(v.M as Record<string, AttributeValue>)
  if ('SS' in v) return v.SS
  if ('NS' in v) return v.NS
  return JSON.stringify(v)
}

export const listTables = () =>
  withTimeout(dynamo.send(new ListTablesCommand({}))).then(r => r.TableNames ?? [])

export const scanTable = (table: string) =>
  withTimeout(dynamo.send(new ScanCommand({ TableName: table }))).then(r =>
    (r.Items ?? []).map(item => unmarshall(item))
  )