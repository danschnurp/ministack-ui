import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listStateMachines, describeStateMachine, listExecutions, describeExecution } from '../aws/stepfunctions'

const EX_BADGE: Record<string, string> = {
  RUNNING: 'bg-primary', SUCCEEDED: 'bg-success', FAILED: 'bg-danger',
  TIMED_OUT: 'bg-warning text-dark', ABORTED: 'bg-secondary',
}

function formatJson(raw: string | undefined): string {
  if (!raw) return '—'
  try {
    return JSON.stringify(JSON.parse(raw), null, 2)
  } catch {
    return raw
  }
}

export default function StepFunctionsPage() {
  const [selSm, setSelSm] = useState('')
  const [selEx, setSelEx] = useState('')

  const { data: machines, isLoading, isError } = useQuery({ queryKey: ['sfn-machines'], queryFn: listStateMachines, retry: 0 })
  const { data: desc } = useQuery({ queryKey: ['sfn-desc', selSm], queryFn: () => describeStateMachine(selSm), enabled: !!selSm })
  const { data: executions } = useQuery({ queryKey: ['sfn-execs', selSm], queryFn: () => listExecutions(selSm), enabled: !!selSm })
  const { data: exDesc } = useQuery({ queryKey: ['sfn-exdesc', selEx], queryFn: () => describeExecution(selEx), enabled: !!selEx })

  if (isLoading) return <p className="text-muted small p-3">Loading state machines…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      <div style={{ width: 200, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>State Machines</p>
        <div className="list-group list-group-flush">
          {machines?.map(m => (
            <button key={m.stateMachineArn} type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selSm === m.stateMachineArn ? 'active' : ''}`}
              style={{ fontSize: 13, borderRadius: 4 }}
              onClick={() => { setSelSm(m.stateMachineArn!); setSelEx('') }}>
              <div>{m.name}</div>
              <div className="text-muted" style={{ fontSize: 11 }}>{m.type}</div>
            </button>
          ))}
          {machines?.length === 0 && <p className="text-muted small">No state machines.</p>}
        </div>
      </div>

      <div className="flex-fill overflow-auto">
        {desc ? (
          <>
            <div className="d-flex justify-content-between align-items-center mb-3">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{machines?.find(m => m.stateMachineArn === selSm)?.name}</span>
              <div className="d-flex gap-2">
                <span className="badge bg-secondary" style={{ fontSize: 11 }}>{desc.type}</span>
                <span className="badge bg-secondary" style={{ fontSize: 11 }}>{desc.status}</span>
              </div>
            </div>

            <details className="mb-3">
              <summary className="text-muted small" style={{ cursor: 'pointer' }}>Definition (ASL)</summary>
              <pre className="border rounded p-2 bg-light mt-1 font-monospace" style={{ fontSize: 11, maxHeight: 360, overflow: 'auto', whiteSpace: 'pre' }}>
                {formatJson(desc.definition)}
              </pre>
            </details>

            <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>
              Recent Executions ({executions?.length ?? 0})
            </p>
            <table className="table table-sm table-hover mb-3" style={{ fontSize: 12 }}>
              <thead className="table-light"><tr><th>Name</th><th>Status</th><th>Started</th><th>Stopped</th></tr></thead>
              <tbody>
                {executions?.map(ex => (
                  <tr key={ex.executionArn}
                    style={{ cursor: 'pointer', background: selEx === ex.executionArn ? '#eef' : undefined }}
                    onClick={() => setSelEx(selEx === ex.executionArn ? '' : ex.executionArn!)}>
                    <td style={{ fontSize: 11 }}>{ex.name}</td>
                    <td><span className={`badge ${EX_BADGE[ex.status ?? ''] ?? 'bg-secondary'}`} style={{ fontSize: 10 }}>{ex.status}</span></td>
                    <td className="text-muted">{ex.startDate?.toISOString().slice(0, 19).replace('T', ' ')}</td>
                    <td className="text-muted">{ex.stopDate?.toISOString().slice(0, 19).replace('T', ' ') ?? '—'}</td>
                  </tr>
                ))}
                {executions?.length === 0 && <tr><td colSpan={4} className="text-muted">No executions.</td></tr>}
              </tbody>
            </table>

            {exDesc && (
              <div className="border rounded p-2">
                <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Execution Detail</p>
                {exDesc.error && <div className="alert alert-danger py-1 px-2 mb-2" style={{ fontSize: 12 }}>{exDesc.error}: {exDesc.cause}</div>}
                <details open><summary className="text-muted small" style={{ cursor: 'pointer' }}>Input</summary>
                  <pre className="bg-light p-2 rounded mt-1 font-monospace" style={{ fontSize: 11, maxHeight: 240, overflow: 'auto', whiteSpace: 'pre' }}>{formatJson(exDesc.input)}</pre>
                </details>
                {exDesc.output && (
                  <details className="mt-1"><summary className="text-muted small" style={{ cursor: 'pointer' }}>Output</summary>
                    <pre className="bg-light p-2 rounded mt-1 font-monospace" style={{ fontSize: 11, maxHeight: 240, overflow: 'auto', whiteSpace: 'pre' }}>{formatJson(exDesc.output)}</pre>
                  </details>
                )}
              </div>
            )}
          </>
        ) : (
          <p className="text-muted small">Select a state machine.</p>
        )}
      </div>
    </div>
  )
}
