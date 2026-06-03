import { glue, withTimeout } from './clients'
import {
  GetDatabasesCommand,
  GetTablesCommand,
  GetJobsCommand,
  GetJobRunsCommand,
  GetCrawlersCommand,
  ListRegistriesCommand,
  ListSchemasCommand,
  GetSchemaCommand,
  ListSchemaVersionsCommand,
  GetSchemaVersionCommand,
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

export const listRegistries = () =>
  withTimeout(glue.send(new ListRegistriesCommand({}))).then(r => r.Registries ?? [])

export const listSchemas = (RegistryName: string) =>
  withTimeout(glue.send(new ListSchemasCommand({ RegistryId: { RegistryName } }))).then(
    r => r.Schemas ?? [],
  )

export const getSchema = (RegistryName: string, SchemaName: string) =>
  withTimeout(
    glue.send(new GetSchemaCommand({ SchemaId: { RegistryName, SchemaName } })),
  )

export const listSchemaVersions = (RegistryName: string, SchemaName: string) =>
  withTimeout(
    glue.send(new ListSchemaVersionsCommand({ SchemaId: { RegistryName, SchemaName } })),
  ).then(r => r.Schemas ?? [])

export const getSchemaVersion = (SchemaVersionId: string) =>
  withTimeout(glue.send(new GetSchemaVersionCommand({ SchemaVersionId })))
