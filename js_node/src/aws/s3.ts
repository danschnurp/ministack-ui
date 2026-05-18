import { s3, withTimeout } from './clients'
import { ListBucketsCommand, ListObjectsV2Command } from '@aws-sdk/client-s3'

export const listBuckets = () =>
  withTimeout(s3.send(new ListBucketsCommand({}))).then(r => r.Buckets ?? [])

export const listObjects = (bucket: string, prefix = '') =>
  withTimeout(s3.send(new ListObjectsV2Command({ Bucket: bucket, Prefix: prefix }))).then(r => r.Contents ?? [])