import { useQuery } from '@tanstack/react-query'
import { listTables, scanTable } from '../aws/dynamo'

export const useDynamoTables = () =>
  useQuery({ queryKey: ['dynamo-tables'], queryFn: listTables })

export const useDynamoItems = (tableName: string) =>
  useQuery({ queryKey: ['dynamo-items', tableName], queryFn: () => scanTable(tableName), enabled: !!tableName })
