import { useState } from 'react'
import { useLogGroups, useLogEvents } from '../hooks/useServices'

export default function LogsPage() {
  const [group, setGroup] = useState('')
  const [stream, setStream] = useState('')
  const { data: groups, isLoading, isError } = useLogGroups()
  const { data: events } = useLogEvents(group, stream)

  if (isLoading) return <p className="text-muted small p-3">Loading log groups…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      {/* group list */}
      <div style={{ width: 200, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Log Groups</p>
        <div className="list-group list-group-flush">
          {groups?.map(g => (
            <button
              key={g.logGroupName}
              type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${group === g.logGroupName ? 'active' : ''}`}
              style={{ fontSize: 12, borderRadius: 4, wordBreak: 'break-all', textAlign: 'left' }}
              onClick={() => { setGroup(g.logGroupName!); setStream('') }}
            >
              {g.logGroupName}
            </button>
          ))}
        </div>
      </div>

      {/* stream + events */}
      <div className="flex-fill d-flex flex-column gap-2 overflow-auto">
        {group ? (
          <>
            <div className="input-group input-group-sm" style={{ maxWidth: 360 }}>
              <span className="input-group-text">Stream</span>
              <input
                className="form-control"
                placeholder="log stream name"
                value={stream}
                onChange={e => setStream(e.target.value)}
              />
            </div>

            {stream && (
              <div
                className="flex-fill overflow-auto rounded p-2"
                style={{ background: '#1e1e1e', fontFamily: 'monospace', fontSize: 12 }}
              >
                {events?.length ? events.map((e, i) => (
                  <div key={i} style={{ marginBottom: 4 }}>
                    <span style={{ color: '#888', marginRight: 12 }}>
                      {e.timestamp ? new Date(e.timestamp).toISOString() : '—'}
                    </span>
                    <span style={{ color: '#d4d4d4' }}>{e.message}</span>
                  </div>
                )) : <span style={{ color: '#888' }}>No events found.</span>}
              </div>
            )}
          </>
        ) : (
          <p className="text-muted small">Select a log group.</p>
        )}
      </div>
    </div>
  )
}
