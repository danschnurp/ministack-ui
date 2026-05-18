import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { listFunctions, invokeFunction } from '../aws/lambda'

function useFunctions() {
  return useQuery({ queryKey: ['lambda-functions'], queryFn: listFunctions, refetchInterval: 5000, retry: 0 })
}

export default function LambdaPage() {
  const [selected, setSelected] = useState('')
  const [payload, setPayload] = useState('{}')
  const [result, setResult] = useState<{ statusCode?: number; payload: string; error?: string } | null>(null)
  const { data: fns, isLoading, isError } = useFunctions()

  const invoke = useMutation({
    mutationFn: () => invokeFunction(selected, payload),
    onSuccess: r => setResult(r),
  })

  const fn = fns?.find(f => f.FunctionName === selected)

  if (isLoading) return <p className="text-muted small p-3">Loading functions…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      <div style={{ width: 180, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Functions</p>
        <div className="list-group list-group-flush">
          {fns?.map(f => (
            <button key={f.FunctionName} type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selected === f.FunctionName ? 'active' : ''}`}
              style={{ fontSize: 13, borderRadius: 4 }}
              onClick={() => { setSelected(f.FunctionName!); setResult(null) }}>
              {f.FunctionName}
            </button>
          ))}
          {fns?.length === 0 && <p className="text-muted small">No functions found.</p>}
        </div>
      </div>

      <div className="flex-fill d-flex flex-column gap-2 overflow-auto">
        {selected && fn ? (
          <>
            <div className="d-flex justify-content-between align-items-center">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{fn.FunctionName}</span>
              <span className="badge bg-secondary" style={{ fontSize: 11 }}>{fn.Runtime}</span>
            </div>

            <table className="table table-sm" style={{ fontSize: 13 }}>
              <tbody>
                <tr><td className="text-muted">Handler</td><td>{fn.Handler}</td></tr>
                <tr><td className="text-muted">Memory</td><td>{fn.MemorySize} MB</td></tr>
                <tr><td className="text-muted">Timeout</td><td>{fn.Timeout} s</td></tr>
                <tr><td className="text-muted">Last modified</td><td>{fn.LastModified}</td></tr>
              </tbody>
            </table>

            <div className="border-top pt-2">
              <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Invoke</p>
              <textarea
                className="form-control form-control-sm mb-2"
                rows={3}
                value={payload}
                onChange={e => setPayload(e.target.value)}
                placeholder="{}"
              />
              <button
                className="btn btn-sm btn-primary"
                onClick={() => invoke.mutate()}
                disabled={invoke.isPending}>
                {invoke.isPending ? 'Invoking…' : 'Invoke'}
              </button>
            </div>

            {result && (
              <div className="mt-2">
                <div className="d-flex gap-2 align-items-center mb-1">
                  <span style={{ fontSize: 12, fontWeight: 500 }}>Response</span>
                  <span className={`badge ${result.error ? 'bg-danger' : 'bg-success'}`} style={{ fontSize: 11 }}>
                    {result.statusCode}
                  </span>
                  {result.error && <span className="badge bg-danger" style={{ fontSize: 11 }}>{result.error}</span>}
                </div>
                <pre className="border rounded p-2 bg-light" style={{ fontSize: 12, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                  {result.payload}
                </pre>
              </div>
            )}
          </>
        ) : (
          <p className="text-muted small">Select a function.</p>
        )}
      </div>
    </div>
  )
}
