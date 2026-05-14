import { useQuery } from '@tanstack/react-query'
import { listBuckets, listObjects } from '../aws/s3'

export const useS3Buckets = () =>
  useQuery({ queryKey: ['s3-buckets'], queryFn: listBuckets, refetchInterval: 5000 })

export const useS3Objects = (bucket: string) =>
  useQuery({ queryKey: ['s3-objects', bucket], queryFn: () => listObjects(bucket), enabled: !!bucket })
