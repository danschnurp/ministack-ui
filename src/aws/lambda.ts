import { cwLogs } from './clients'
import { InvokeCommand, GetLogEventsCommand } from '@aws-sdk/client-lambda'
import { Client } from '@aws-sdk/client-lambda'

const lambdaClient = new Client({
  endpoint: 'http://localhost:5173/api',
  region: 'us-east-1',
  credentials: { accessKeyId: 'test', secretAccessKey: 'test' },
})

export const listFunctions = async () => {
  const res = await lambdaClient.listFunctions({})
  return res.Functions?.map(f => f.FunctionName) ?? []
}

export const invokeFunction = async (functionName: string) => {
  return await lambdaClient.invoke({
    FunctionName: functionName,
    Payload: JSON.stringify({ message: 'Hello from MiniStack UI!' }),
  })
}

export const getFunctionLogs = async (functionName: string) => {
  const res = await cwLogs.send(new GetLogEventsCommand({
    logGroupName: `/aws/lambda/${functionName}`,
  }))
  return res.events ?? []
}
