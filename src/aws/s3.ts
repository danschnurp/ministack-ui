import { s3 } from './clients'
import { ListBucketsCommand, ListObjectsV2Command } from '@aws-sdk/client-s3'

export const listBuckets = async () => {
  const res = await s3.send(new ListBucketsCommand({}))
  return res.Buckets ?? []
}

export const listObjects = async (bucket: string, prefix = '') => {
  const res = await s3.send(new ListObjectsV2Command({ Bucket: bucket, Prefix: prefix }))
  return res.Contents ?? []
}
