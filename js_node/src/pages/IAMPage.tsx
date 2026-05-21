import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listUsers, listRoles, listPolicies, listGroupsForUser, listAttachedUserPolicies } from '../aws/iam'

export default function IAMPage() {
  const [tab, setTab] = useState<'users' | 'roles' | 'policies'>('users')
  const [selUser, setSelUser] = useState('')
  const [roleFilter, setRoleFilter] = useState('')

  const { data: users, isLoading, isError } = useQuery({ queryKey: ['iam-users'], queryFn: listUsers, retry: 0 })
  const { data: roles } = useQuery({ queryKey: ['iam-roles'], queryFn: listRoles, retry: 0 })
  const { data: policies } = useQuery({ queryKey: ['iam-policies'], queryFn: listPolicies, retry: 0 })
  const { data: groups } = useQuery({ queryKey: ['iam-groups', selUser], queryFn: () => listGroupsForUser(selUser), enabled: !!selUser })
  const { data: attached } = useQuery({ queryKey: ['iam-attached', selUser], queryFn: () => listAttachedUserPolicies(selUser), enabled: !!selUser })

  const user = users?.find(u => u.UserName === selUser)
  const filteredRoles = roles?.filter(r => r.RoleName?.toLowerCase().includes(roleFilter.toLowerCase()))

  if (isLoading) return <p className="text-muted small p-3">Loading IAM…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="p-3 h-100 overflow-auto">
      <div className="d-flex gap-2 mb-3">
        {(['users', 'roles', 'policies'] as const).map(t => (
          <button key={t} className={`btn btn-sm ${tab === t ? 'btn-primary' : 'btn-outline-secondary'}`}
            onClick={() => { setTab(t); setSelUser('') }}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {tab === 'users' && (
        <div className="d-flex gap-3">
          <div style={{ width: 180, flexShrink: 0 }}>
            <div className="list-group list-group-flush">
              {users?.map(u => (
                <button key={u.UserName} type="button"
                  className={`list-group-item list-group-item-action py-1 px-2 ${selUser === u.UserName ? 'active' : ''}`}
                  style={{ fontSize: 13, borderRadius: 4 }} onClick={() => setSelUser(u.UserName!)}>
                  {u.UserName}
                </button>
              ))}
              {users?.length === 0 && <p className="text-muted small">No users.</p>}
            </div>
          </div>
          <div className="flex-fill">
            {user ? (
              <>
                <span style={{ fontSize: 13, fontWeight: 500 }}>{user.UserName}</span>
                <p className="text-muted small mb-3" style={{ wordBreak: 'break-all' }}>{user.Arn}</p>

                <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Groups ({groups?.length ?? 0})</p>
                {groups?.length ? (
                  <table className="table table-sm mb-3" style={{ fontSize: 12 }}>
                    <tbody>{groups.map(g => <tr key={g.GroupName}><td>{g.GroupName}</td></tr>)}</tbody>
                  </table>
                ) : <p className="text-muted small mb-3">No groups.</p>}

                <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Attached Policies ({attached?.length ?? 0})</p>
                {attached?.length ? (
                  <table className="table table-sm" style={{ fontSize: 12 }}>
                    <tbody>{attached.map(p => <tr key={p.PolicyName}><td>{p.PolicyName}</td></tr>)}</tbody>
                  </table>
                ) : <p className="text-muted small">No attached policies.</p>}
              </>
            ) : <p className="text-muted small">Select a user.</p>}
          </div>
        </div>
      )}

      {tab === 'roles' && (
        <>
          <input className="form-control form-control-sm mb-2" placeholder="Filter roles…" value={roleFilter}
            onChange={e => setRoleFilter(e.target.value)} />
          <table className="table table-sm table-hover" style={{ fontSize: 13 }}>
            <thead className="table-light"><tr><th>Role</th><th>Created</th><th>ARN</th></tr></thead>
            <tbody>
              {filteredRoles?.map(r => (
                <tr key={r.RoleName}>
                  <td style={{ fontWeight: 500 }}>{r.RoleName}</td>
                  <td className="text-muted">{r.CreateDate?.toISOString().slice(0, 10)}</td>
                  <td style={{ fontSize: 11, wordBreak: 'break-all' }}>{r.Arn}</td>
                </tr>
              ))}
              {filteredRoles?.length === 0 && <tr><td colSpan={3} className="text-muted">No roles match.</td></tr>}
            </tbody>
          </table>
        </>
      )}

      {tab === 'policies' && (
        <table className="table table-sm table-hover" style={{ fontSize: 13 }}>
          <thead className="table-light"><tr><th>Policy</th><th className="text-end">Attachments</th><th>Created</th></tr></thead>
          <tbody>
            {policies?.map(p => (
              <tr key={p.PolicyName}>
                <td style={{ fontWeight: 500 }}>{p.PolicyName}</td>
                <td className="text-end">{p.AttachmentCount ?? 0}</td>
                <td className="text-muted">{p.CreateDate?.toISOString().slice(0, 10)}</td>
              </tr>
            ))}
            {policies?.length === 0 && <tr><td colSpan={3} className="text-muted">No customer-managed policies.</td></tr>}
          </tbody>
        </table>
      )}
    </div>
  )
}
