import { useState } from 'react'
import { useSQSQueues, useSQSMessages, useSendMessage } from '../hooks/useServices'

export default function SQSPage() {
  const [selected, setSelected] = useState('')
  const [body, setBody] = useState('')
  const { data: queues, isLoading, isError } = useSQSQueues()
  const { data: messages } = useSQSMessages(selected)
  const send = useSendMessage(selected)

  if (isLoading) return <p className="text-muted small p-3">Loading queues…</p>
  if (isError)   return <p className="text-danger small p-3">Failed to reach MiniStack.</p>

  const queueName = (url: string) => url.split('/').pop() ?? url

  const handleSend = () => {
    if (!body.trim() || !selected) return
    send.mutate(body.trim(), { onSuccess: () => setBody('') })
  }

  return (
    <div className="d-flex gap-3 p-3 h-100">
      {/* queue list */}
      <div style={{ width: 190, flexShrink: 0 }}>
        <p className="text-uppercase text-muted mb-2" style={{ fontSize: 11, fontWeight: 500 }}>Queues</p>
        <div className="list-group list-group-flush">
          {queues?.map(url => (
            <button
              key={url}
              type="button"
              className={`list-group-item list-group-item-action py-1 px-2 ${selected === url ? 'active' : ''}`}
              style={{ fontSize: 13, borderRadius: 4 }}
              onClick={() => setSelected(url)}
            >
              {queueName(url)}
            </button>
          ))}
        </div>
      </div>

      {/* message list + send */}
      <div className="flex-fill d-flex flex-column gap-2 overflow-auto">
        {selected ? (
          <>
            <div className="d-flex justify-content-between align-items-center">
              <span style={{ fontSize: 13, fontWeight: 500 }}>{queueName(selected)}</span>
              <span className="badge bg-secondary" style={{ fontSize: 11 }}>{messages?.length ?? 0} messages</span>
            </div>

            <div className="flex-fill overflow-auto">
              {messages?.length ? messages.map(m => (
                <div key={m.MessageId} className="border rounded p-2 mb-2 bg-light" style={{ fontSize: 12 }}>
                  <div className="text-muted mb-1" style={{ fontSize: 11 }}>{m.MessageId}</div>
                  <pre className="mb-0" style={{ fontSize: 12, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                    {m.Body}
                  </pre>
                </div>
              )) : <p className="text-muted small">No messages in flight.</p>}
            </div>

            {/* send panel */}
            <div className="border-top pt-2">
              <textarea
                className="form-control form-control-sm mb-2"
                rows={3}
                placeholder='{"key": "value"}'
                value={body}
                onChange={e => setBody(e.target.value)}
              />
              <button
                className="btn btn-sm btn-primary"
                onClick={handleSend}
                disabled={send.isPending || !body.trim()}
              >
                {send.isPending ? 'Sending…' : 'Send message'}
              </button>
            </div>
          </>
        ) : (
          <p className="text-muted small">Select a queue.</p>
        )}
      </div>
    </div>
  )
}
