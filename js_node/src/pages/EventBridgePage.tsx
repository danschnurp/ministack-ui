import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listRules, listTargets, listEventBuses } from '../aws/eventbridge'

export default function EventBridgePage() {
  const [tab, setTab] = useState<'rules' | 'buses'>('rules')
  const [selected, setSelected] = useState('')

  const { data: rules, isLoading, isError } = useQuery({ queryKey: ['eb-rules'], queryFn: listRules, retry: 0 })
  const { data: buses } = useQuery({ queryKey: ['eb-buses'], queryFn: listEventBuses, retry: 0 })
  const { data: targets } = useQuery({ queryKey: ['eb-targets', selected], queryFn: () => listTargets(selected), enabled: !!selected })

  const rule = rules?.find(r => r.Name === selected)

  if (isLoading) return <p className="text-muted small p-3">Loading…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="p-3 h-100 overflow-auto">
      <div className="d-flex gap-2 mb-3">
        {(['rules', 'buses'] as const).map(t => (
          <button key={t} className={`btn btn-sm ${tab === t ? 'btn-primary' : 'btn-outline-secondary'}`}
            onClick={() => { setTab(t); setSelected('') }}>
            {t === 'rules' ? 'Rules' : 'Event Buses'}
          </button>
        ))}
      </div>

      {tab === 'rules' && (
        <div className="d-flex gap-3">
          <div style={{ width: 200, flexShrink: 0 }}>
            <div className="list-group list-group-flush">
              {rules?.map(r => (
                <button key={r.Name} type="button"
                  className={`list-group-item list-group-item-action py-1 px-2 ${selected === r.Name ? 'active' : ''}`}
                  style={{ fontSize: 13, borderRadius: 4 }}
                  onClick={() => setSelected(r.Name!)}>
                  <div>{r.Name}</div>
                  <span className={`badge ${r.State === 'ENABLED' ? 'bg-success' : 'bg-secondary'}`} style={{ fontSize: 10 }}>{r.State}</span>
                </button>
              ))}
              {rules?.length === 0 && <p className="text-muted small">No rules found.</p>}
            </div>
          </div>

          <div className="flex-fill">
            {rule ? (
              <>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <span style={{ fontSize: 13, fontWeight: 500 }}>{rule.Name}</span>
                  <span className={`badge ${rule.State === 'ENABLED' ? 'bg-success' : 'bg-secondary'}`} style={{ fontSize: 11 }}>{rule.State}</span>
                </div>
                <table className="table table-sm mb-3" style={{ fontSize: 13 }}>
                  <tbody>
                    <tr><td className="text-muted">Event Bus</td><td>{rule.EventBusName ?? 'default'}</td></tr>
                    {rule.ScheduleExpression && <tr><td className="text-muted">Schedule</td><td><code>{rule.ScheduleExpression}</code></td></tr>}
                    {rule.Description && <tr><td className="text-muted">Description</td><td>{rule.Description}</td></tr>}
                  </tbody>
                </table>
                {rule.EventPattern && (
                  <>
                    <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Event Pattern</p>
                    <pre className="border rounded p-2 bg-light" style={{ fontSize: 12 }}>{rule.EventPattern}</pre>
                  </>
                )}
                {targets && targets.length > 0 && (
                  <>
                    <p className="text-uppercase text-muted mb-1 mt-2" style={{ fontSize: 11, fontWeight: 500 }}>Targets ({targets.length})</p>
                    <table className="table table-sm" style={{ fontSize: 12 }}>
                      <thead className="table-light"><tr><th>ID</th><th>ARN</th></tr></thead>
                      <tbody>{targets.map(t => <tr key={t.Id}><td>{t.Id}</td><td style={{ wordBreak: 'break-all' }}>{t.Arn}</td></tr>)}</tbody>
                    </table>
                  </>
                )}
              </>
            ) : (
              <p className="text-muted small">Select a rule.</p>
            )}
          </div>
        </div>
      )}

      {tab === 'buses' && (
        <table className="table table-sm table-hover" style={{ fontSize: 13 }}>
          <thead className="table-light"><tr><th>Name</th><th>ARN</th></tr></thead>
          <tbody>
            {buses?.map(b => (
              <tr key={b.Name}><td style={{ fontWeight: 500 }}>{b.Name}</td><td style={{ wordBreak: 'break-all' }}>{b.Arn ?? '—'}</td></tr>
            ))}
            {buses?.length === 0 && <tr><td colSpan={2} className="text-muted">No event buses found.</td></tr>}
          </tbody>
        </table>
      )}
    </div>
  )
}
