import { useState } from 'react'
import S3Page from './pages/S3Page'
import DynamoPage from './pages/DynamoPage'
import SQSPage from './pages/SQSPage'
import LogsPage from './pages/LogsPage'
import KinesisPage from './pages/KinesisPage'
import LambdaPage from './pages/LambdaPage'
import ApiGatewayPage from './pages/ApiGatewayPage'
import SNSPage from './pages/SNSPage'
import StatusBar from './components/StatusBar'

const PAGES = [
  { id: 's3',          label: 'S3',          group: 'Storage',   el: <S3Page /> },
  { id: 'dynamo',      label: 'DynamoDB',    group: 'Storage',   el: <DynamoPage /> },
  { id: 'kinesis',     label: 'Kinesis',     group: 'Streaming', el: <KinesisPage /> },
  { id: 'sqs',         label: 'SQS',         group: 'Messaging', el: <SQSPage /> },
  { id: 'sns',         label: 'SNS',         group: 'Messaging', el: <SNSPage /> },
  { id: 'lambda',      label: 'Lambda',      group: 'Compute',   el: <LambdaPage /> },
  { id: 'apigateway',  label: 'API Gateway', group: 'Compute',   el: <ApiGatewayPage /> },
  { id: 'logs',        label: 'Logs',        group: 'Observability', el: <LogsPage /> },
]

const GROUPS = ['Storage', 'Streaming', 'Messaging', 'Compute', 'Observability']

export default function App() {
  const [page, setPage] = useState('s3')
  const current = PAGES.find(p => p.id === page)!

  return (
    <div className="d-flex" style={{ height: '100vh', overflow: 'hidden' }}>
      <nav className="d-flex flex-column border-end bg-light" style={{ width: 180, flexShrink: 0 }}>
        <div className="px-3 py-3 border-bottom">
          <span className="fw-semibold" style={{ fontSize: 14 }}>MiniStack</span>
        </div>

        <div className="p-2 flex-fill overflow-auto">
          {GROUPS.map(group => {
            const items = PAGES.filter(p => p.group === group)
            return (
              <div key={group} className="mb-2">
                <p className="text-uppercase text-muted px-2 mb-1" style={{ fontSize: 10, fontWeight: 600 }}>
                  {group}
                </p>
                {items.map(p => (
                  <button key={p.id}
                    className={`btn btn-sm w-100 text-start mb-1 ${page === p.id ? 'btn-primary' : 'btn-light'}`}
                    onClick={() => setPage(p.id)}>
                    {p.label}
                  </button>
                ))}
              </div>
            )
          })}
        </div>

        <StatusBar />
      </nav>

      <main className="flex-fill overflow-auto">
        {current.el}
      </main>
    </div>
  )
}
