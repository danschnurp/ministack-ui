import { wafv2, withTimeout } from './clients'
import {
  ListWebACLsCommand,
  GetWebACLCommand,
  ListIPSetsCommand,
  GetIPSetCommand,
} from '@aws-sdk/client-wafv2'

export type WafScope = 'REGIONAL' | 'CLOUDFRONT'

export const listWebACLs = (Scope: WafScope) =>
  withTimeout(wafv2.send(new ListWebACLsCommand({ Scope }))).then(r => r.WebACLs ?? [])

export const getWebACL = (Name: string, Id: string, Scope: WafScope) =>
  withTimeout(wafv2.send(new GetWebACLCommand({ Name, Id, Scope }))).then(r => r.WebACL)

export const listIPSets = (Scope: WafScope) =>
  withTimeout(wafv2.send(new ListIPSetsCommand({ Scope }))).then(r => r.IPSets ?? [])

export const getIPSet = (Name: string, Id: string, Scope: WafScope) =>
  withTimeout(wafv2.send(new GetIPSetCommand({ Name, Id, Scope }))).then(r => r.IPSet)
