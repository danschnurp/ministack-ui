import { useState } from 'react'
import S3Page from './pages/S3Page'
import DynamoPage from './pages/DynamoPage'
import SQSPage from './pages/SQSPage'
import LogsPage from './pages/LogsPage'
import StatusBar from './components/StatusBar'

const PAGES = [
  { id: 's3',     label: 'S3',       el: <S3Page /> },
  { id: 'dynamo', label: 'DynamoDB', el: <DynamoPage /> },
  { id: 'sqs',    label: 'SQS',      el: <SQSPage /> },
  { id: 'logs',   label: 'Logs',     el: <LogsPage /> },
]

export default function App() {
  const [page, setPage] = useState('s3')
  const current = PAGES.find(p => p.id === page)!

  return (
    <div className="d-flex" style={{ height: '100vh', overflow: 'hidden' }}>
      {/* sidebar */}
      <nav
        className="d-flex flex-column border-end bg-light"
        style={{ width: 180, flexShrink: 0 }}
      >
        <div className="px-3 py-3 border-bottom">
          <span className="fw-semibold" style={{ fontSize: 14 }}>MiniStack</span>
        </div>
        <div className="p-2 flex-fill">
          <p className="text-uppercase text-muted px-2 mb-1" style={{ fontSize: 10, fontWeight: 600 }}>
            Services
          </p>
          {PAGES.map(p => (
            <button
              key={p.id}
              className={`btn btn-sm w-100 text-start mb-1 ${page === p.id ? 'btn-primary' : 'btn-light'}`}
              onClick={() => setPage(p.id)}
            >
              {p.label}
            </button>
          ))}
        </div>
        <StatusBar />
      </nav>

      {/* main */}
      <main className="flex-fill overflow-auto">
        {current.el}
      </main>
    </div>
  )
}
