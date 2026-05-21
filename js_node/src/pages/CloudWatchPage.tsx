import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listMetrics, getMetricStats, listAlarms } from '../aws/cloudwatch'

export default function CloudWatchPage() {
  const [tab, setTab] = useState<'metrics' | 'alarms'>('metrics')
  const [selNs, setSelNs] = useState('')
  const [selMetric, setSelMetric] = useState('')
  const [hours, setHours] = useState(3)

  const { data: metrics, isLoading, isError } = useQuery({ queryKey: ['cw-metrics'], queryFn: listMetrics, retry: 0 })
  const { data: alarms } = useQuery({ queryKey: ['cw-alarms'], queryFn: listAlarms, retry: 0 })
  const { data: stats } = useQuery({
    queryKey: ['cw-stats', selNs, selMetric, hours],
    queryFn: () => getMetricStats(selNs, selMetric, hours),
    enabled: !!selNs && !!selMetric,
  })

  const namespaces = [...new Set((metrics ?? []).map(m => m.Namespace!))]
  const nsMetrics = [...new Set((metrics ?? []).filter(m => m.Namespace === selNs).map(m => m.MetricName!))]

  if (isLoading) return <p className="text-muted small p-3">Loading metrics…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="p-3 h-100 overflow-auto">
      <div className="d-flex gap-2 mb-3">
        {(['metrics', 'alarms'] as const).map(t => (
          <button key={t} className={`btn btn-sm ${tab === t ? 'btn-primary' : 'btn-outline-secondary'}`}
            onClick={() => setTab(t)}>
            {t === 'metrics' ? 'Metrics' : 'Alarms'}
          </button>
        ))}
      </div>

      {tab === 'metrics' && (
        <>
          <div className="row g-2 mb-3">
            <div className="col-md-4">
              <label className="form-label small text-muted text-uppercase fw-semibold" style={{ fontSize: 11 }}>Namespace</label>
              <select className="form-select form-select-sm" value={selNs} onChange={e => { setSelNs(e.target.value); setSelMetric('') }}>
                <option value="">— select —</option>
                {namespaces.map(ns => <option key={ns} value={ns}>{ns}</option>)}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label small text-muted text-uppercase fw-semibold" style={{ fontSize: 11 }}>Metric</label>
              <select className="form-select form-select-sm" value={selMetric} onChange={e => setSelMetric(e.target.value)} disabled={!selNs}>
                <option value="">— select —</option>
                {nsMetrics.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            <div className="col-md-4">
              <label className="form-label small text-muted text-uppercase fw-semibold" style={{ fontSize: 11 }}>Range (hrs)</label>
              <input type="number" className="form-control form-control-sm" min={1} max={24} value={hours}
                onChange={e => setHours(+e.target.value)} />
            </div>
          </div>

          {stats && stats.length > 0 ? (
            <table className="table table-sm table-hover" style={{ fontSize: 12 }}>
              <thead className="table-light">
                <tr><th>Timestamp</th><th className="text-end">Average</th><th className="text-end">Sum</th><th className="text-end">Max</th><th>Unit</th></tr>
              </thead>
              <tbody>
                {stats.map((dp, i) => (
                  <tr key={i}>
                    <td className="text-muted">{dp.Timestamp?.toISOString().slice(0, 19).replace('T', ' ')}</td>
                    <td className="text-end">{dp.Average?.toFixed(4) ?? '—'}</td>
                    <td className="text-end">{dp.Sum?.toFixed(4) ?? '—'}</td>
                    <td className="text-end">{dp.Maximum?.toFixed(4) ?? '—'}</td>
                    <td className="text-muted">{dp.Unit ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : selMetric ? (
            <p className="text-muted small">No datapoints in this range.</p>
          ) : (
            <p className="text-muted small">Select a namespace and metric to view datapoints.</p>
          )}
        </>
      )}

      {tab === 'alarms' && (
        <>
          {!alarms?.length ? (
            <p className="text-muted small">No alarms configured.</p>
          ) : (
            <table className="table table-sm table-hover" style={{ fontSize: 13 }}>
              <thead className="table-light">
                <tr><th>Alarm</th><th>State</th><th>Metric</th><th>Namespace</th><th className="text-end">Threshold</th></tr>
              </thead>
              <tbody>
                {alarms.map(a => {
                  const state = a.StateValue ?? '—'
                  const badge = state === 'OK' ? 'bg-success' : state === 'ALARM' ? 'bg-danger' : 'bg-warning text-dark'
                  return (
                    <tr key={a.AlarmName}>
                      <td style={{ fontWeight: 500 }}>{a.AlarmName}</td>
                      <td><span className={`badge ${badge}`} style={{ fontSize: 11 }}>{state}</span></td>
                      <td>{a.MetricName}</td>
                      <td className="text-muted">{a.Namespace}</td>
                      <td className="text-end">{a.Threshold}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  )
}
