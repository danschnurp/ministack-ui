import { iam, withTimeout } from './clients'
import {
  ListUsersCommand,
  ListRolesCommand,
  ListPoliciesCommand,
  ListGroupsForUserCommand,
  ListAttachedUserPoliciesCommand,
} from '@aws-sdk/client-iam'

export const listUsers = () =>
  withTimeout(iam.send(new ListUsersCommand({}))).then(r => r.Users ?? [])

export const listRoles = () =>
  withTimeout(iam.send(new ListRolesCommand({}))).then(r => r.Roles ?? [])

export const listPolicies = () =>
  withTimeout(iam.send(new ListPoliciesCommand({ Scope: 'Local' }))).then(r => r.Policies ?? [])

export const listGroupsForUser = (UserName: string) =>
  withTimeout(iam.send(new ListGroupsForUserCommand({ UserName }))).then(r => r.Groups ?? [])

export const listAttachedUserPolicies = (UserName: string) =>
  withTimeout(iam.send(new ListAttachedUserPoliciesCommand({ UserName }))).then(r => r.AttachedPolicies ?? [])
