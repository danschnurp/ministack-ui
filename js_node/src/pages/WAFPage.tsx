import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listWebACLs, getWebACL, listIPSets, getIPSet, WafScope } from '../aws/waf'

export default function WAFPage() {
  const [scope, setScope] = useState<WafScope>('REGIONAL')
  const [tab, setTab] = useState<'acls' | 'ipsets'>('acls')
  const [selACL, setSelACL] = useState<{ name: string; id: string } | null>(null)
  const [selIPSet, setSelIPSet] = useState<{ name: string; id: string } | null>(null)

  const { data: acls, isLoading, isError } = useQuery({ queryKey: ['waf-acls', scope], queryFn: () => listWebACLs(scope), retry: 0 })
  const { data: ipSets } = useQuery({ queryKey: ['waf-ipsets', scope], queryFn: () => listIPSets(scope), retry: 0 })
  const { data: aclDetail } = useQuery({
    queryKey: ['waf-acl-detail', selACL?.name, scope],
    queryFn: () => getWebACL(selACL!.name, selACL!.id, scope),
    enabled: !!selACL,
  })
  const { data: ipSetDetail } = useQuery({
    queryKey: ['waf-ipset-detail', selIPSet?.name, scope],
    queryFn: () => getIPSet(selIPSet!.name, selIPSet!.id, scope),
    enabled: !!selIPSet,
  })

  if (isLoading) return <p className="text-muted small p-3">Loading WAF resources…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="p-3 h-100 overflow-auto">
      <div className="d-flex gap-3 mb-3 align-items-center">
        <div className="d-flex gap-2">
          {(['REGIONAL', 'CLOUDFRONT'] as WafScope[]).map(s => (
            <button key={s} className={`btn btn-sm ${scope === s ? 'btn-dark' : 'btn-outline-secondary'}`}
              onClick={() => { setScope(s); setSelACL(null); setSelIPSet(null) }}>
              {s}
            </button>
          ))}
        </div>
        <div className="d-flex gap-2">
          {(['acls', 'ipsets'] as const).map(t => (
            <button key={t} className={`btn btn-sm ${tab === t ? 'btn-primary' : 'btn-outline-secondary'}`}
              onClick={() => { setTab(t); setSelACL(null); setSelIPSet(null) }}>
              {t === 'acls' ? 'Web ACLs' : 'IP Sets'}
            </button>
          ))}
        </div>
      </div>

      {tab === 'acls' && (
        <div className="d-flex gap-3">
          <div style={{ width: 200, flexShrink: 0 }}>
            <div className="list-group list-group-flush">
              {acls?.map(a => (
                <button key={a.Id} type="button"
                  className={`list-group-item list-group-item-action py-1 px-2 ${selACL?.id === a.Id ? 'active' : ''}`}
                  style={{ fontSize: 13, borderRadius: 4 }}
                  onClick={() => setSelACL({ name: a.Name!, id: a.Id! })}>
                  {a.Name}
                </button>
              ))}
              {acls?.length === 0 && <p className="text-muted small">No Web ACLs ({scope}).</p>}
            </div>
          </div>

          <div className="flex-fill">
            {aclDetail ? (
              <>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{aclDetail.Name}</span>
                <p className="text-muted small mb-3" style={{ wordBreak: 'break-all', fontSize: 11 }}>{aclDetail.ARN}</p>

                <table className="table table-sm mb-3" style={{ fontSize: 13 }}>
                  <tbody>
                    <tr><td className="text-muted">Default Action</td><td>{Object.keys(aclDetail.DefaultAction ?? {})[0] ?? '—'}</td></tr>
                    <tr><td className="text-muted">Rules</td><td>{aclDetail.Rules?.length ?? 0}</td></tr>
                  </tbody>
                </table>

                {aclDetail.Rules && aclDetail.Rules.length > 0 && (
                  <>
                    <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Rules</p>
                    <table className="table table-sm table-hover" style={{ fontSize: 12 }}>
                      <thead className="table-light"><tr><th>Rule</th><th className="text-end">Priority</th><th>Action</th></tr></thead>
                      <tbody>
                        {aclDetail.Rules.map(r => (
                          <tr key={r.Name}>
                            <td style={{ fontWeight: 500 }}>{r.Name}</td>
                            <td className="text-end">{r.Priority}</td>
                            <td>{Object.keys(r.Action ?? r.OverrideAction ?? { '—': null })[0]}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                )}
              </>
            ) : selACL ? (
              <p className="text-muted small">Loading…</p>
            ) : (
              <p className="text-muted small">Select a Web ACL.</p>
            )}
          </div>
        </div>
      )}

      {tab === 'ipsets' && (
        <div className="d-flex gap-3">
          <div style={{ width: 200, flexShrink: 0 }}>
            <div className="list-group list-group-flush">
              {ipSets?.map(s => (
                <button key={s.Id} type="button"
                  className={`list-group-item list-group-item-action py-1 px-2 ${selIPSet?.id === s.Id ? 'active' : ''}`}
                  style={{ fontSize: 13, borderRadius: 4 }}
                  onClick={() => setSelIPSet({ name: s.Name!, id: s.Id! })}>
                  {s.Name}
                </button>
              ))}
              {ipSets?.length === 0 && <p className="text-muted small">No IP Sets ({scope}).</p>}
            </div>
          </div>
          <div className="flex-fill">
            {ipSetDetail ? (
              <>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <span style={{ fontSize: 13, fontWeight: 500 }}>{ipSetDetail.Name}</span>
                  <span className="badge bg-secondary" style={{ fontSize: 11 }}>{ipSetDetail.IPAddressVersion}</span>
                </div>
                <p className="text-muted small mb-2">{ipSetDetail.Addresses?.length ?? 0} address(es)</p>
                <table className="table table-sm" style={{ fontSize: 12 }}>
                  <thead className="table-light"><tr><th>CIDR</th></tr></thead>
                  <tbody>{ipSetDetail.Addresses?.map(a => <tr key={a}><td><code>{a}</code></td></tr>)}</tbody>
                </table>
              </>
            ) : selIPSet ? (
              <p className="text-muted small">Loading…</p>
            ) : (
              <p className="text-muted small">Select an IP Set.</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
