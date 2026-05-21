import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listVpcs, listSubnets, listSecurityGroups, listRouteTables } from '../aws/ec2'

function tagName(item: any) {
  return item.Tags?.find((t: any) => t.Key === 'Name')?.Value
}

export default function VPCPage() {
  const [selected, setSelected] = useState('')
  const [subTab, setSubTab] = useState<'subnets' | 'sgs' | 'routes'>('subnets')

  const { data: vpcs, isLoading, isError } = useQuery({ queryKey: ['vpcs'], queryFn: listVpcs, retry: 0 })
  const { data: subnets } = useQuery({ queryKey: ['subnets', selected], queryFn: () => listSubnets(selected), enabled: !!selected })
  const { data: sgs } = useQuery({ queryKey: ['sgs', selected], queryFn: () => listSecurityGroups(selected), enabled: !!selected })
  const { data: rts } = useQuery({ queryKey: ['rts', selected], queryFn: () => listRouteTables(selected), enabled: !!selected })

  const vpc = vpcs?.find(v => v.VpcId === selected)

  if (isLoading) return <p className="text-muted small p-3">Loading VPCs…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      <div style={{ width: 200, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>VPCs</p>
        <div className="list-group list-group-flush">
          {vpcs?.map(v => (
            <button key={v.VpcId} type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selected === v.VpcId ? 'active' : ''}`}
              style={{ fontSize: 13, borderRadius: 4 }}
              onClick={() => setSelected(v.VpcId!)}>
              <div>{tagName(v) ?? v.VpcId}</div>
              <div className="text-muted" style={{ fontSize: 11 }}>{v.CidrBlock} {v.IsDefault && <span className="badge bg-light text-dark border">default</span>}</div>
            </button>
          ))}
          {vpcs?.length === 0 && <p className="text-muted small">No VPCs found.</p>}
        </div>
      </div>

      <div className="flex-fill overflow-auto">
        {vpc ? (
          <>
            <div className="d-flex justify-content-between align-items-center mb-3">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{tagName(vpc) ?? vpc.VpcId}</span>
              <span className="badge bg-secondary" style={{ fontSize: 11 }}>{vpc.State}</span>
            </div>
            <table className="table table-sm mb-3" style={{ fontSize: 13 }}>
              <tbody>
                <tr><td className="text-muted">VPC ID</td><td><code>{vpc.VpcId}</code></td></tr>
                <tr><td className="text-muted">CIDR</td><td>{vpc.CidrBlock}</td></tr>
                <tr><td className="text-muted">Default</td><td>{vpc.IsDefault ? 'Yes' : 'No'}</td></tr>
              </tbody>
            </table>

            <div className="d-flex gap-2 mb-3">
              {(['subnets', 'sgs', 'routes'] as const).map(t => (
                <button key={t} className={`btn btn-sm ${subTab === t ? 'btn-primary' : 'btn-outline-secondary'}`}
                  onClick={() => setSubTab(t)}>
                  {t === 'subnets' ? `Subnets (${subnets?.length ?? 0})` : t === 'sgs' ? `Security Groups (${sgs?.length ?? 0})` : `Route Tables (${rts?.length ?? 0})`}
                </button>
              ))}
            </div>

            {subTab === 'subnets' && (
              <table className="table table-sm table-hover" style={{ fontSize: 12 }}>
                <thead className="table-light"><tr><th>Subnet ID</th><th>CIDR</th><th>AZ</th><th className="text-end">Free IPs</th><th>Public</th></tr></thead>
                <tbody>
                  {subnets?.map(s => (
                    <tr key={s.SubnetId}>
                      <td><code style={{ fontSize: 11 }}>{s.SubnetId}</code></td>
                      <td>{s.CidrBlock}</td>
                      <td className="text-muted">{s.AvailabilityZone}</td>
                      <td className="text-end">{s.AvailableIpAddressCount}</td>
                      <td>{s.MapPublicIpOnLaunch ? '✓' : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {subTab === 'sgs' && (
              <table className="table table-sm table-hover" style={{ fontSize: 12 }}>
                <thead className="table-light"><tr><th>Group ID</th><th>Name</th><th>Description</th></tr></thead>
                <tbody>
                  {sgs?.map(sg => (
                    <tr key={sg.GroupId}>
                      <td><code style={{ fontSize: 11 }}>{sg.GroupId}</code></td>
                      <td>{sg.GroupName}</td>
                      <td className="text-muted">{sg.Description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {subTab === 'routes' && rts?.map(rt => (
              <div key={rt.RouteTableId} className="mb-3">
                <p className="text-muted mb-1" style={{ fontSize: 12 }}><code>{rt.RouteTableId}</code></p>
                <table className="table table-sm table-bordered" style={{ fontSize: 12 }}>
                  <thead className="table-light"><tr><th>Destination</th><th>Target</th><th>State</th></tr></thead>
                  <tbody>
                    {rt.Routes?.map((r, i) => (
                      <tr key={i}>
                        <td>{r.DestinationCidrBlock ?? r.DestinationPrefixListId ?? '—'}</td>
                        <td>{r.GatewayId ?? r.NatGatewayId ?? r.InstanceId ?? '—'}</td>
                        <td><span className={`badge ${r.State === 'active' ? 'bg-success' : 'bg-secondary'}`} style={{ fontSize: 10 }}>{r.State}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </>
        ) : (
          <p className="text-muted small">Select a VPC.</p>
        )}
      </div>
    </div>
  )
}
