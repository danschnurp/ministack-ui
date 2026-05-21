import { kms, withTimeout } from './clients'
import {
  ListKeysCommand,
  DescribeKeyCommand,
  ListAliasesCommand,
} from '@aws-sdk/client-kms'

export const listKeys = () =>
  withTimeout(kms.send(new ListKeysCommand({}))).then(r => r.Keys ?? [])

export const describeKey = (KeyId: string) =>
  withTimeout(kms.send(new DescribeKeyCommand({ KeyId }))).then(r => r.KeyMetadata)

export const listAliases = (KeyId: string) =>
  withTimeout(kms.send(new ListAliasesCommand({ KeyId }))).then(r => r.Aliases ?? [])
