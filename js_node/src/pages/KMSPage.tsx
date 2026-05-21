import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listKeys, describeKey, listAliases } from '../aws/kms'

export default function KMSPage() {
  const [selected, setSelected] = useState('')
  const { data: keys, isLoading, isError } = useQuery({ queryKey: ['kms-keys'], queryFn: listKeys, retry: 0 })
  const { data: meta } = useQuery({ queryKey: ['kms-meta', selected], queryFn: () => describeKey(selected), enabled: !!selected })
  const { data: aliases } = useQuery({ queryKey: ['kms-aliases', selected], queryFn: () => listAliases(selected), enabled: !!selected })

  if (isLoading) return <p className="text-muted small p-3">Loading KMS keys…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      <div style={{ width: 220, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>{keys?.length ?? 0} Key(s)</p>
        <div className="list-group list-group-flush">
          {keys?.map(k => (
            <button key={k.KeyId} type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selected === k.KeyId ? 'active' : ''}`}
              style={{ fontSize: 12, borderRadius: 4, fontFamily: 'monospace' }}
              onClick={() => setSelected(k.KeyId!)}>
              {k.KeyId?.slice(0, 8)}…
            </button>
          ))}
          {keys?.length === 0 && <p className="text-muted small">No keys found.</p>}
        </div>
      </div>

      <div className="flex-fill overflow-auto">
        {meta ? (
          <>
            <div className="d-flex justify-content-between align-items-center mb-3">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{meta.Description || meta.KeyId}</span>
              <span className={`badge ${meta.Enabled ? 'bg-success' : 'bg-danger'}`} style={{ fontSize: 11 }}>
                {meta.KeyState}
              </span>
            </div>

            <table className="table table-sm mb-3" style={{ fontSize: 13 }}>
              <tbody>
                <tr><td className="text-muted">Key ID</td><td><code style={{ fontSize: 11 }}>{meta.KeyId}</code></td></tr>
                <tr><td className="text-muted">ARN</td><td style={{ wordBreak: 'break-all', fontSize: 11 }}>{meta.Arn}</td></tr>
                <tr><td className="text-muted">Usage</td><td>{meta.KeyUsage}</td></tr>
                <tr><td className="text-muted">Spec</td><td>{meta.KeySpec}</td></tr>
                <tr><td className="text-muted">Origin</td><td>{meta.Origin}</td></tr>
                <tr><td className="text-muted">Manager</td><td>{meta.KeyManager}</td></tr>
                <tr><td className="text-muted">Multi-region</td><td>{meta.MultiRegion ? 'Yes' : 'No'}</td></tr>
                <tr><td className="text-muted">Created</td><td>{meta.CreationDate?.toISOString().slice(0, 19).replace('T', ' ')}</td></tr>
              </tbody>
            </table>

            {aliases && aliases.length > 0 && (
              <>
                <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Aliases ({aliases.length})</p>
                <table className="table table-sm" style={{ fontSize: 12 }}>
                  <tbody>{aliases.map(a => <tr key={a.AliasName}><td><code>{a.AliasName}</code></td></tr>)}</tbody>
                </table>
              </>
            )}
          </>
        ) : selected ? (
          <p className="text-muted small">Loading…</p>
        ) : (
          <p className="text-muted small">Select a key.</p>
        )}
      </div>
    </div>
  )
}
