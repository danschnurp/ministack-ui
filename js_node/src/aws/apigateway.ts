import { APIGatewayClient, GetRestApisCommand, GetResourcesCommand, GetStagesCommand } from '@aws-sdk/client-api-gateway'
import { sharedConfig, withTimeout } from './clients'

const apigw = new APIGatewayClient(sharedConfig)

export const listApis = () =>
  withTimeout(apigw.send(new GetRestApisCommand({}))).then(r => r.items ?? [])

export const listResources = (restApiId: string) =>
  withTimeout(apigw.send(new GetResourcesCommand({ restApiId }))).then(r => r.items ?? [])

export const listStages = (restApiId: string) =>
  withTimeout(apigw.send(new GetStagesCommand({ restApiId }))).then(r => r.item ?? [])
