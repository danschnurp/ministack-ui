import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listDatabases, listTables, listJobs, listJobRuns, listCrawlers } from '../aws/glue'

export default function GluePage() {
  const [tab, setTab] = useState<'databases' | 'jobs' | 'crawlers'>('databases')
  const [selDb, setSelDb] = useState('')
  const [selJob, setSelJob] = useState('')

  const { data: dbs, isLoading, isError } = useQuery({ queryKey: ['glue-dbs'], queryFn: listDatabases, retry: 0 })
  const { data: tables } = useQuery({ queryKey: ['glue-tables', selDb], queryFn: () => listTables(selDb), enabled: !!selDb })
  const { data: jobs } = useQuery({ queryKey: ['glue-jobs'], queryFn: listJobs, retry: 0 })
  const { data: runs } = useQuery({ queryKey: ['glue-runs', selJob], queryFn: () => listJobRuns(selJob), enabled: !!selJob })
  const { data: crawlers } = useQuery({ queryKey: ['glue-crawlers'], queryFn: listCrawlers, retry: 0 })

  if (isLoading) return <p className="text-muted small p-3">Loading Glue resources…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  const STATE_BADGE: Record<string, string> = {
    SUCCEEDED: 'bg-success', RUNNING: 'bg-primary', FAILED: 'bg-danger',
    STOPPED: 'bg-warning text-dark', STARTING: 'bg-info text-dark',
  }

  return (
    <div className="p-3 h-100 overflow-auto">
      <div className="d-flex gap-2 mb-3">
        {(['databases', 'jobs', 'crawlers'] as const).map(t => (
          <button key={t} className={`btn btn-sm ${tab === t ? 'btn-primary' : 'btn-outline-secondary'}`}
            onClick={() => setTab(t)}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'databases' && (
        <div className="d-flex gap-3">
          <div style={{ width: 180, flexShrink: 0 }}>
            <div className="list-group list-group-flush">
              {dbs?.map(d => (
                <button key={d.Name} type="button"
                  className={`list-group-item list-group-item-action py-1 px-2 ${selDb === d.Name ? 'active' : ''}`}
                  style={{ fontSize: 13, borderRadius: 4 }} onClick={() => setSelDb(d.Name!)}>
                  {d.Name}
                </button>
              ))}
              {dbs?.length === 0 && <p className="text-muted small">No databases.</p>}
            </div>
          </div>
          <div className="flex-fill">
            {selDb ? (
              <>
                <p className="text-muted small mb-2">{tables?.length ?? 0} table(s) in <strong>{selDb}</strong></p>
                <table className="table table-sm table-hover" style={{ fontSize: 12 }}>
                  <thead className="table-light"><tr><th>Table</th><th>Type</th><th>Location</th><th>Created</th></tr></thead>
                  <tbody>
                    {tables?.map(t => (
                      <tr key={t.Name}>
                        <td style={{ fontWeight: 500 }}>{t.Name}</td>
                        <td>{t.TableType ?? '—'}</td>
                        <td className="text-muted" style={{ fontSize: 11, wordBreak: 'break-all' }}>{t.StorageDescriptor?.Location ?? '—'}</td>
                        <td className="text-muted">{t.CreateTime?.toISOString().slice(0, 10) ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            ) : <p className="text-muted small">Select a database.</p>}
          </div>
        </div>
      )}

      {tab === 'jobs' && (
        <div className="d-flex gap-3">
          <div style={{ width: 180, flexShrink: 0 }}>
            <div className="list-group list-group-flush">
              {jobs?.map(j => (
                <button key={j.Name} type="button"
                  className={`list-group-item list-group-item-action py-1 px-2 ${selJob === j.Name ? 'active' : ''}`}
                  style={{ fontSize: 13, borderRadius: 4 }} onClick={() => setSelJob(j.Name!)}>
                  {j.Name}
                </button>
              ))}
              {jobs?.length === 0 && <p className="text-muted small">No jobs.</p>}
            </div>
          </div>
          <div className="flex-fill">
            {selJob ? (
              <>
                {jobs?.filter(j => j.Name === selJob).map(j => (
                  <div key={j.Name}>
                    <table className="table table-sm mb-3" style={{ fontSize: 13 }}>
                      <tbody>
                        <tr><td className="text-muted">Type</td><td>{j.Command?.Name ?? '—'}</td></tr>
                        <tr><td className="text-muted">Role</td><td>{j.Role?.split('/').pop() ?? '—'}</td></tr>
                        <tr><td className="text-muted">Workers</td><td>{j.NumberOfWorkers ?? '—'}</td></tr>
                        <tr><td className="text-muted">Worker type</td><td>{j.WorkerType ?? '—'}</td></tr>
                      </tbody>
                    </table>
                  </div>
                ))}
                <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Recent Runs</p>
                <table className="table table-sm table-hover" style={{ fontSize: 12 }}>
                  <thead className="table-light"><tr><th>Run ID</th><th>State</th><th>Started</th><th className="text-end">Duration (s)</th></tr></thead>
                  <tbody>
                    {runs?.map(r => (
                      <tr key={r.Id}>
                        <td style={{ fontSize: 11 }}>{r.Id?.slice(0, 14)}…</td>
                        <td><span className={`badge ${STATE_BADGE[r.JobRunState ?? ''] ?? 'bg-secondary'}`} style={{ fontSize: 10 }}>{r.JobRunState}</span></td>
                        <td className="text-muted">{r.StartedOn?.toISOString().slice(0, 19).replace('T', ' ')}</td>
                        <td className="text-end">{r.ExecutionTime ?? '—'}</td>
                      </tr>
                    ))}
                    {runs?.length === 0 && <tr><td colSpan={4} className="text-muted">No runs found.</td></tr>}
                  </tbody>
                </table>
              </>
            ) : <p className="text-muted small">Select a job.</p>}
          </div>
        </div>
      )}

      {tab === 'crawlers' && (
        <table className="table table-sm table-hover" style={{ fontSize: 13 }}>
          <thead className="table-light"><tr><th>Crawler</th><th>State</th><th>Database</th><th>Last Run</th></tr></thead>
          <tbody>
            {crawlers?.map(c => {
              const state = c.State ?? '—'
              const badge = state === 'READY' ? 'bg-success' : state === 'RUNNING' ? 'bg-primary' : 'bg-secondary'
              return (
                <tr key={c.Name}>
                  <td style={{ fontWeight: 500 }}>{c.Name}</td>
                  <td><span className={`badge ${badge}`} style={{ fontSize: 10 }}>{state}</span></td>
                  <td>{c.DatabaseName ?? '—'}</td>
                  <td className="text-muted">{(c.LastCrawl as any)?.StartTime?.toISOString().slice(0, 10) ?? '—'}</td>
                </tr>
              )
            })}
            {crawlers?.length === 0 && <tr><td colSpan={4} className="text-muted">No crawlers found.</td></tr>}
          </tbody>
        </table>
      )}
    </div>
  )
}
