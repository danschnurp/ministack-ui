import { useState } from 'react'
import { useDynamoTables, useDynamoScan } from '../hooks/useServices'

export default function DynamoPage() {
  const [selected, setSelected] = useState('')
  const { data: tables, isLoading, isError } = useDynamoTables()
  const { data: items } = useDynamoScan(selected)

  if (isLoading) return <p className="text-muted small p-3">Loading tables…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  const cols = items?.length ? Object.keys(items[0]) : []

  return (
    <div className="d-flex gap-3 p-3 h-100">
      {/* table list */}
      <div style={{ width: 180, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Tables</p>
        <div className="list-group list-group-flush">
          {tables?.map(t => (
            <button
              key={t}
              type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selected === t ? 'active' : ''}`}
              style={{ fontSize: 13, borderRadius: 4 }}
              onClick={() => setSelected(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* item table */}
      <div className="flex-fill overflow-auto">
        {selected ? (
          <>
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{selected}</span>
              <span className="badge bg-secondary" style={{ fontSize: 11 }}>{items?.length ?? 0} items</span>
            </div>
            <table className="table table-sm table-bordered table-hover" style={{ tableLayout: 'fixed', fontSize: 13 }}>
              <thead className="table-light">
                <tr>{cols.map(c => <th key={c}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {items?.map((row, i) => (
                  <tr key={i}>
                    {cols.map(c => (
                      <td key={c} style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {String(row[c] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : (
          <p className="text-muted small">Select a table.</p>
        )}
      </div>
    </div>
  )
}
