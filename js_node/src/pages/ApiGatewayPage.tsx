import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listApis, listResources, listStages } from '../aws/apigateway'

function useApis() {
  return useQuery({ queryKey: ['apigw-apis'], queryFn: listApis, refetchInterval: 10000, retry: 0 })
}
function useApiDetail(id: string) {
  return useQuery({
    queryKey: ['apigw-detail', id],
    queryFn: () => Promise.all([listResources(id), listStages(id)]),
    enabled: !!id,
    retry: 0,
  })
}

const METHOD_COLORS: Record<string, string> = {
  GET: 'bg-success', POST: 'bg-primary', PUT: 'bg-warning text-dark',
  DELETE: 'bg-danger', PATCH: 'bg-info text-dark', ANY: 'bg-secondary',
}

export default function ApiGatewayPage() {
  const [selected, setSelected] = useState('')
  const { data: apis, isLoading, isError } = useApis()
  const { data: detail } = useApiDetail(selected)
  const [resources, stages] = detail ?? []

  if (isLoading) return <p className="text-muted small p-3">Loading APIs…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      <div style={{ width: 180, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>REST APIs</p>
        <div className="list-group list-group-flush">
          {apis?.map(a => (
            <button key={a.id} type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selected === a.id ? 'active' : ''}`}
              style={{ fontSize: 13, borderRadius: 4 }}
              onClick={() => setSelected(a.id!)}>
              {a.name}
            </button>
          ))}
          {apis?.length === 0 && <p className="text-muted small">No APIs found.</p>}
        </div>
      </div>

      <div className="flex-fill overflow-auto">
        {selected && resources ? (
          <>
            <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Resources</p>
            <table className="table table-sm table-hover mb-3" style={{ fontSize: 13 }}>
              <thead className="table-light"><tr><th>Path</th><th>Methods</th></tr></thead>
              <tbody>
                {resources.map(r => (
                  <tr key={r.id}>
                    <td><code style={{ fontSize: 12 }}>{r.path}</code></td>
                    <td>
                      {Object.keys(r.resourceMethods ?? {}).map(m => (
                        <span key={m} className={`badge me-1 ${METHOD_COLORS[m] ?? 'bg-secondary'}`} style={{ fontSize: 10 }}>{m}</span>
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Stages</p>
            <table className="table table-sm" style={{ fontSize: 13 }}>
              <thead className="table-light"><tr><th>Stage</th><th>Last deployed</th></tr></thead>
              <tbody>
                {stages?.map(s => (
                  <tr key={s.stageName}>
                    <td>{s.stageName}</td>
                    <td className="text-muted">{s.lastUpdatedDate?.toString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : selected ? (
          <p className="text-muted small">Loading…</p>
        ) : (
          <p className="text-muted small">Select an API.</p>
        )}
      </div>
    </div>
  )
}
