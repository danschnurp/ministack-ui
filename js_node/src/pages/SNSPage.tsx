import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listTopics, listSubscriptions, publishMessage } from '../aws/sns'

function useTopics() {
  return useQuery({ queryKey: ['sns-topics'], queryFn: listTopics, refetchInterval: 5000, retry: 0 })
}
function useSubscriptions() {
  return useQuery({ queryKey: ['sns-subs'], queryFn: listSubscriptions, refetchInterval: 5000, retry: 0 })
}

const topicName = (arn: string) => arn.split(':').pop() ?? arn

export default function SNSPage() {
  const [selected, setSelected] = useState('')
  const [message, setMessage] = useState('')
  const [subject, setSubject] = useState('')
  const [sent, setSent] = useState(false)
  const qc = useQueryClient()

  const { data: topics, isLoading, isError } = useTopics()
  const { data: allSubs } = useSubscriptions()

  const subs = allSubs?.filter(s => s.TopicArn === selected) ?? []

  const publish = useMutation({
    mutationFn: () => publishMessage(selected, message, subject || undefined),
    onSuccess: () => { setSent(true); setMessage(''); setSubject(''); setTimeout(() => setSent(false), 3000) },
  })

  if (isLoading) return <p className="text-muted small p-3">Loading topics…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  return (
    <div className="d-flex gap-3 p-3 h-100">
      <div style={{ width: 180, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Topics</p>
        <div className="list-group list-group-flush">
          {topics?.map(t => (
            <button key={t.TopicArn} type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selected === t.TopicArn ? 'active' : ''}`}
              style={{ fontSize: 13, borderRadius: 4 }}
              onClick={() => { setSelected(t.TopicArn!); setSent(false) }}>
              {topicName(t.TopicArn!)}
            </button>
          ))}
          {topics?.length === 0 && <p className="text-muted small">No topics found.</p>}
        </div>
      </div>

      <div className="flex-fill d-flex flex-column gap-2 overflow-auto">
        {selected ? (
          <>
            <div className="d-flex justify-content-between align-items-center">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{topicName(selected)}</span>
              <span className="badge bg-secondary" style={{ fontSize: 11 }}>{subs.length} subscriptions</span>
            </div>

            {subs.length > 0 && (
              <table className="table table-sm table-bordered" style={{ fontSize: 12 }}>
                <thead className="table-light"><tr><th>Protocol</th><th>Endpoint</th><th>Status</th></tr></thead>
                <tbody>
                  {subs.map(s => (
                    <tr key={s.SubscriptionArn}>
                      <td>{s.Protocol}</td>
                      <td style={{ wordBreak: 'break-all' }}>{s.Endpoint}</td>
                      <td>{s.SubscriptionArn === 'PendingConfirmation'
                        ? <span className="badge bg-warning text-dark" style={{ fontSize: 10 }}>Pending</span>
                        : <span className="badge bg-success" style={{ fontSize: 10 }}>Confirmed</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            <div className="border-top pt-2">
              <p className="text-uppercase text-muted mb-1" style={{ fontSize: 11, fontWeight: 500 }}>Publish</p>
              <input
                className="form-control form-control-sm mb-2"
                placeholder="Subject (optional)"
                value={subject}
                onChange={e => setSubject(e.target.value)}
              />
              <textarea
                className="form-control form-control-sm mb-2"
                rows={3}
                placeholder="Message body"
                value={message}
                onChange={e => setMessage(e.target.value)}
              />
              <div className="d-flex align-items-center gap-2">
                <button
                  className="btn btn-sm btn-primary"
                  onClick={() => publish.mutate()}
                  disabled={publish.isPending || !message.trim()}>
                  {publish.isPending ? 'Publishing…' : 'Publish'}
                </button>
                {sent && <span className="text-success" style={{ fontSize: 12 }}>✓ Published</span>}
                {publish.isError && <span className="text-danger" style={{ fontSize: 12 }}>Failed</span>}
              </div>
            </div>
          </>
        ) : (
          <p className="text-muted small">Select a topic.</p>
        )}
      </div>
    </div>
  )
}
