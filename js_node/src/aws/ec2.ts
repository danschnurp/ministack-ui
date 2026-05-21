import { ec2, withTimeout } from './clients'
import {
  DescribeInstancesCommand,
  DescribeVpcsCommand,
  DescribeSubnetsCommand,
  DescribeSecurityGroupsCommand,
  DescribeRouteTablesCommand,
} from '@aws-sdk/client-ec2'

export const listInstances = () =>
  withTimeout(ec2.send(new DescribeInstancesCommand({}))).then(r =>
    (r.Reservations ?? []).flatMap(res => res.Instances ?? [])
  )

export const listVpcs = () =>
  withTimeout(ec2.send(new DescribeVpcsCommand({}))).then(r => r.Vpcs ?? [])

export const listSubnets = (vpcId: string) =>
  withTimeout(ec2.send(new DescribeSubnetsCommand({
    Filters: [{ Name: 'vpc-id', Values: [vpcId] }],
  }))).then(r => r.Subnets ?? [])

export const listSecurityGroups = (vpcId: string) =>
  withTimeout(ec2.send(new DescribeSecurityGroupsCommand({
    Filters: [{ Name: 'vpc-id', Values: [vpcId] }],
  }))).then(r => r.SecurityGroups ?? [])

export const listRouteTables = (vpcId: string) =>
  withTimeout(ec2.send(new DescribeRouteTablesCommand({
    Filters: [{ Name: 'vpc-id', Values: [vpcId] }],
  }))).then(r => r.RouteTables ?? [])
