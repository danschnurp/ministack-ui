import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listDeliveryStreams, describeDeliveryStream } from '../aws/firehose'

export default function FirehosePage() {
  const [selected, setSelected] = useState('')
  const { data: streams, isLoading, isError } = useQuery({ queryKey: ['firehose-streams'], queryFn: listDeliveryStreams, retry: 0 })
  const { data: desc } = useQuery({ queryKey: ['firehose-desc', selected], queryFn: () => describeDeliveryStream(selected), enabled: !!selected })

  const STATUS_BADGE: Record<string, string> = {
    ACTIVE: 'bg-success', CREATING: 'bg-warning text-dark', DELETING: 'bg-danger',
    CREATING_FAILED: 'bg-danger', DELETING_FAILED: 'bg-danger',
  }

  if (isLoading) return <p className="text-muted small p-3">Loading delivery streams…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      <div style={{ width: 200, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Delivery Streams</p>
        <div className="list-group list-group-flush">
          {streams?.map(s => (
            <button key={s} type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selected === s ? 'active' : ''}`}
              style={{ fontSize: 13, borderRadius: 4 }} onClick={() => setSelected(s)}>
              {s}
            </button>
          ))}
          {streams?.length === 0 && <p className="text-muted small">No delivery streams.</p>}
        </div>
      </div>

      <div className="flex-fill overflow-auto">
        {desc ? (
          <>
            <div className="d-flex justify-content-between align-items-center mb-3">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{selected}</span>
              <span className={`badge ${STATUS_BADGE[desc.DeliveryStreamStatus ?? ''] ?? 'bg-secondary'}`} style={{ fontSize: 11 }}>
                {desc.DeliveryStreamStatus}
              </span>
            </div>
            <table className="table table-sm mb-3" style={{ fontSize: 13 }}>
              <tbody>
                <tr><td className="text-muted">Type</td><td>{desc.DeliveryStreamType}</td></tr>
                <tr><td className="text-muted">Created</td><td>{desc.CreateTimestamp?.toISOString().slice(0, 10)}</td></tr>
                <tr><td className="text-muted">ARN</td><td style={{ wordBreak: 'break-all', fontSize: 11 }}>{desc.DeliveryStreamARN}</td></tr>
              </tbody>
            </table>

            {desc.Destinations?.map((dest, i) => {
              const s3 = dest.S3DestinationDescription ?? dest.ExtendedS3DestinationDescription
              return (
                <div key={dest.DestinationId} className="border rounded p-2 mb-2">
                  <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Destination {i + 1}</p>
                  {s3 ? (
                    <table className="table table-sm mb-0" style={{ fontSize: 12 }}>
                      <tbody>
                        <tr><td className="text-muted">Bucket ARN</td><td style={{ wordBreak: 'break-all' }}>{s3.BucketARN ?? '—'}</td></tr>
                        <tr><td className="text-muted">Prefix</td><td>{(s3 as any).Prefix ?? '(none)'}</td></tr>
                        <tr><td className="text-muted">Compression</td><td>{(s3 as any).CompressionFormat ?? '—'}</td></tr>
                        <tr><td className="text-muted">Buffer interval</td><td>{(s3 as any).BufferingHints?.IntervalInSeconds ?? '—'} s</td></tr>
                        <tr><td className="text-muted">Buffer size</td><td>{(s3 as any).BufferingHints?.SizeInMBs ?? '—'} MB</td></tr>
                      </tbody>
                    </table>
                  ) : (
                    <p className="text-muted small mb-0">Destination ID: {dest.DestinationId}</p>
                  )}
                </div>
              )
            })}
          </>
        ) : selected ? (
          <p className="text-muted small">Loading…</p>
        ) : (
          <p className="text-muted small">Select a delivery stream.</p>
        )}
      </div>
    </div>
  )
}
