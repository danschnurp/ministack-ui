import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listStreams, describeStream, listShards } from '../aws/kinesis'

function useStreams() {
  return useQuery({ queryKey: ['kinesis-streams'], queryFn: listStreams, refetchInterval: 5000, retry: 0 })
}
function useStreamDetail(name: string) {
  return useQuery({
    queryKey: ['kinesis-detail', name],
    queryFn: () => Promise.all([describeStream(name), listShards(name)]),
    enabled: !!name,
    retry: 0,
  })
}

export default function KinesisPage() {
  const [selected, setSelected] = useState('')
  const { data: streams, isLoading, isError } = useStreams()
  const { data: detail } = useStreamDetail(selected)
  const [summary, shards] = detail ?? []

  if (isLoading) return <p className="text-muted small p-3">Loading streams…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      <div style={{ width: 180, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Streams</p>
        <div className="list-group list-group-flush">
          {streams?.map(s => (
            <button key={s} type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selected === s ? 'active' : ''}`}
              style={{ fontSize: 13, borderRadius: 4 }}
              onClick={() => setSelected(s)}>
              {s}
            </button>
          ))}
          {streams?.length === 0 && <p className="text-muted small">No streams found.</p>}
        </div>
      </div>

      <div className="flex-fill overflow-auto">
        {selected && summary ? (
          <>
            <div className="d-flex justify-content-between align-items-center mb-3">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{selected}</span>
              <span className={`badge ${summary.StreamStatus === 'ACTIVE' ? 'bg-success' : 'bg-secondary'}`} style={{ fontSize: 11 }}>
                {summary.StreamStatus}
              </span>
            </div>

            <table className="table table-sm mb-3" style={{ fontSize: 13 }}>
              <tbody>
                <tr><td className="text-muted">ARN</td><td style={{ wordBreak: 'break-all' }}>{summary.StreamARN}</td></tr>
                <tr><td className="text-muted">Retention (hrs)</td><td>{summary.RetentionPeriodHours}</td></tr>
                <tr><td className="text-muted">Open shards</td><td>{summary.OpenShardCount}</td></tr>
                <tr><td className="text-muted">Encryption</td><td>{summary.EncryptionType ?? 'NONE'}</td></tr>
              </tbody>
            </table>

            <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Shards</p>
            <table className="table table-sm table-bordered" style={{ fontSize: 12 }}>
              <thead className="table-light">
                <tr><th>Shard ID</th><th>Starting key</th><th>Ending key</th></tr>
              </thead>
              <tbody>
                {shards?.map(sh => (
                  <tr key={sh.ShardId}>
                    <td>{sh.ShardId}</td>
                    <td className="text-muted">{sh.HashKeyRange?.StartingHashKey?.slice(0, 12)}…</td>
                    <td className="text-muted">{sh.HashKeyRange?.EndingHashKey?.slice(0, 12)}…</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : selected ? (
          <p className="text-muted small">Loading…</p>
        ) : (
          <p className="text-muted small">Select a stream.</p>
        )}
      </div>
    </div>
  )
}
