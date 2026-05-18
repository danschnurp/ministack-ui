import { LambdaClient, ListFunctionsCommand, InvokeCommand } from '@aws-sdk/client-lambda'
import { sharedConfig, withTimeout } from './clients'

const lambda = new LambdaClient(sharedConfig)

export const listFunctions = () =>
  withTimeout(lambda.send(new ListFunctionsCommand({}))).then(r => r.Functions ?? [])

export const invokeFunction = (FunctionName: string, payload: string) =>
  withTimeout(
    lambda.send(new InvokeCommand({
      FunctionName,
      Payload: new TextEncoder().encode(payload),
    })),
    10000  // cold starts need more headroom
  ).then(r => ({
    statusCode: r.StatusCode,
    payload: r.Payload ? new TextDecoder().decode(r.Payload) : '',
    error: r.FunctionError,
  }))
