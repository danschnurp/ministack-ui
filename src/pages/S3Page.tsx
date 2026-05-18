import { useState } from 'react'
import { useS3Buckets, useS3Objects } from '../hooks/useServices'

function fmtSize(bytes?: number) {
  if (!bytes) return '0 B'
  if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB'
  if (bytes >= 1024) return Math.round(bytes / 1024) + ' KB'
  return bytes + ' B'
}

export default function S3Page() {
  const [selected, setSelected] = useState('')
  const { data: buckets, isLoading, isError } = useS3Buckets()
  const { data: objects } = useS3Objects(selected)

  if (isLoading) return <p className="text-muted small p-3">Loading buckets…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      {/* bucket list */}
      <div style={{ width: 180, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Buckets</p>
        <div className="list-group list-group-flush">
          {buckets?.map(b => (
            <button
              key={b.Name}
              type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selected === b.Name ? 'active' : ''}`}
              style={{ fontSize: 13, borderRadius: 4 }}
              onClick={() => setSelected(b.Name!)}
            >
              {b.Name}
            </button>
          ))}
        </div>
      </div>

      {/* object list */}
      <div className="flex-fill overflow-auto">
        {selected ? (
          <>
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{selected}</span>
              <span className="badge bg-secondary" style={{ fontSize: 11 }}>{objects?.length ?? 0} objects</span>
            </div>
            <table className="table table-sm table-hover">
              <thead><tr><th>Key</th><th className="text-end">Size</th></tr></thead>
              <tbody>
                {objects?.map(o => (
                  <tr key={o.Key}>
                    <td style={{ fontSize: 13 }}>{o.Key}</td>
                    <td className="text-end text-muted" style={{ fontSize: 13 }}>{fmtSize(o.Size)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <p className="text-muted small">Select a bucket.</p>
        )}
      </div>
    </div>
  )
}
