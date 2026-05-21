import { glue, withTimeout } from './clients'
import {
  GetDatabasesCommand,
  GetTablesCommand,
  GetJobsCommand,
  GetJobRunsCommand,
  GetCrawlersCommand,
} from '@aws-sdk/client-glue'

export const listDatabases = () =>
  withTimeout(glue.send(new GetDatabasesCommand({}))).then(r => r.DatabaseList ?? [])

export const listTables = (DatabaseName: string) =>
  withTimeout(glue.send(new GetTablesCommand({ DatabaseName }))).then(r => r.TableList ?? [])

export const listJobs = () =>
  withTimeout(glue.send(new GetJobsCommand({}))).then(r => r.Jobs ?? [])

export const listJobRuns = (JobName: string) =>
  withTimeout(glue.send(new GetJobRunsCommand({ JobName, MaxResults: 10 }))).then(r => r.JobRuns ?? [])

export const listCrawlers = () =>
  withTimeout(glue.send(new GetCrawlersCommand({}))).then(r => r.Crawlers ?? [])
