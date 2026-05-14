import { dynamo } from './clients'
import { ListTablesCommand, ScanCommand } from '@aws-sdk/client-dynamodb'

export const listTables = async () => {
  const res = await dynamo.send(new ListTablesCommand({}))
  return res.TableNames ?? []
}

export const scanTable = async (tableName: string) => {
  const res = await dynamo.send(new ScanCommand({ TableName: tableName }))
  return res.Items ?? []
}
