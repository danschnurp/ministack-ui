import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listInstances } from '../aws/ec2'

const STATE_BADGE: Record<string, string> = {
  running: 'bg-success', stopped: 'bg-danger', pending: 'bg-warning text-dark',
  stopping: 'bg-warning text-dark', terminated: 'bg-secondary',
}

function tagName(inst: any) {
  return inst.Tags?.find((t: any) => t.Key === 'Name')?.Value ?? '—'
}

export default function EC2Page() {
  const [selected, setSelected] = useState('')
  const { data: instances, isLoading, isError } = useQuery({ queryKey: ['ec2-instances'], queryFn: listInstances, refetchInterval: 10000, retry: 0 })
  const inst = instances?.find(i => i.InstanceId === selected)

  if (isLoading) return <p className="text-muted small p-3">Loading instances…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      <div style={{ width: 200, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Instances</p>
        <div className="list-group list-group-flush">
          {instances?.map(i => {
            const state = i.State?.Name ?? '—'
            return (
              <button key={i.InstanceId} type="button"
                className={`list-group-item list-group-item-action py-1 px-2 ${selected === i.InstanceId ? 'active' : ''}`}
                style={{ fontSize: 13, borderRadius: 4 }}
                onClick={() => setSelected(i.InstanceId!)}>
                <div>{tagName(i)}</div>
                <div className="d-flex align-items-center gap-1 mt-1">
                  <span className={`badge ${STATE_BADGE[state] ?? 'bg-secondary'}`} style={{ fontSize: 10 }}>{state}</span>
                  <span className="text-muted" style={{ fontSize: 11 }}>{i.InstanceType}</span>
                </div>
              </button>
            )
          })}
          {instances?.length === 0 && <p className="text-muted small">No instances found.</p>}
        </div>
      </div>

      <div className="flex-fill overflow-auto">
        {inst ? (
          <>
            <div className="d-flex justify-content-between align-items-center mb-3">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{tagName(inst)} <span className="text-muted fw-normal">({inst.InstanceId})</span></span>
              <span className={`badge ${STATE_BADGE[inst.State?.Name ?? ''] ?? 'bg-secondary'}`} style={{ fontSize: 11 }}>{inst.State?.Name}</span>
            </div>

            <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Details</p>
            <table className="table table-sm mb-3" style={{ fontSize: 13 }}>
              <tbody>
                <tr><td className="text-muted">Type</td><td>{inst.InstanceType}</td></tr>
                <tr><td className="text-muted">AMI</td><td>{inst.ImageId}</td></tr>
                <tr><td className="text-muted">AZ</td><td>{inst.Placement?.AvailabilityZone}</td></tr>
                <tr><td className="text-muted">Key pair</td><td>{inst.KeyName ?? '—'}</td></tr>
                <tr><td className="text-muted">Launch time</td><td>{inst.LaunchTime?.toISOString().slice(0, 19).replace('T', ' ')}</td></tr>
              </tbody>
            </table>

            <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Network</p>
            <table className="table table-sm mb-3" style={{ fontSize: 13 }}>
              <tbody>
                <tr><td className="text-muted">Private IP</td><td>{inst.PrivateIpAddress ?? '—'}</td></tr>
                <tr><td className="text-muted">Public IP</td><td>{inst.PublicIpAddress ?? '—'}</td></tr>
                <tr><td className="text-muted">VPC</td><td>{inst.VpcId ?? '—'}</td></tr>
                <tr><td className="text-muted">Subnet</td><td>{inst.SubnetId ?? '—'}</td></tr>
              </tbody>
            </table>

            {inst.Tags && inst.Tags.length > 0 && (
              <>
                <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Tags</p>
                <table className="table table-sm" style={{ fontSize: 12 }}>
                  <thead className="table-light"><tr><th>Key</th><th>Value</th></tr></thead>
                  <tbody>{inst.Tags.map(t => <tr key={t.Key}><td>{t.Key}</td><td>{t.Value}</td></tr>)}</tbody>
                </table>
              </>
            )}
          </>
        ) : (
          <p className="text-muted small">Select an instance.</p>
        )}
      </div>
    </div>
  )
}
