import { useState } from 'react'
import S3Page from './pages/S3Page'
import DynamoPage from './pages/DynamoPage'
import SQSPage from './pages/SQSPage'
import LogsPage from './pages/LogsPage'
import KinesisPage from './pages/KinesisPage'
import FirehosePage from './pages/FirehosePage'
import LambdaPage from './pages/LambdaPage'
import ApiGatewayPage from './pages/ApiGatewayPage'
import SNSPage from './pages/SNSPage'
import CloudWatchPage from './pages/CloudWatchPage'
import EC2Page from './pages/EC2Page'
import VPCPage from './pages/VPCPage'
import EventBridgePage from './pages/EventBridgePage'
import GluePage from './pages/GluePage'
import IAMPage from './pages/IAMPage'
import KMSPage from './pages/KMSPage'
import StepFunctionsPage from './pages/StepFunctionsPage'
import WAFPage from './pages/WAFPage'
import StatusBar from './components/StatusBar'

const PAGES = [
  { id: 's3',             label: 'S3',                group: 'Storage',       el: <S3Page /> },
  { id: 'dynamo',         label: 'DynamoDB',          group: 'Storage',       el: <DynamoPage /> },
  { id: 'ec2',            label: 'EC2',               group: 'Compute',       el: <EC2Page /> },
  { id: 'lambda',         label: 'Lambda',            group: 'Compute',       el: <LambdaPage /> },
  { id: 'vpc',            label: 'VPC',               group: 'Networking',    el: <VPCPage /> },
  { id: 'apigateway',     label: 'API Gateway',       group: 'Networking',    el: <ApiGatewayPage /> },
  { id: 'waf',            label: 'WAF',               group: 'Networking',    el: <WAFPage /> },
  { id: 'kinesis',        label: 'Kinesis Data Stream', group: 'Streaming',   el: <KinesisPage /> },
  { id: 'firehose',       label: 'Kinesis Firehose',  group: 'Streaming',     el: <FirehosePage /> },
  { id: 'sqs',            label: 'SQS',               group: 'Messaging',     el: <SQSPage /> },
  { id: 'sns',            label: 'SNS',               group: 'Messaging',     el: <SNSPage /> },
  { id: 'eventbridge',    label: 'EventBridge',       group: 'Messaging',     el: <EventBridgePage /> },
  { id: 'stepfunctions',  label: 'Step Functions',    group: 'Orchestration', el: <StepFunctionsPage /> },
  { id: 'glue',           label: 'Glue',              group: 'Data',          el: <GluePage /> },
  { id: 'iam',            label: 'IAM',               group: 'Security',      el: <IAMPage /> },
  { id: 'kms',            label: 'KMS',               group: 'Security',      el: <KMSPage /> },
  { id: 'cloudwatch',     label: 'CloudWatch',        group: 'Observability', el: <CloudWatchPage /> },
  { id: 'logs',           label: 'Logs',              group: 'Observability', el: <LogsPage /> },
]

const GROUPS = ['Storage', 'Compute', 'Networking', 'Streaming', 'Messaging', 'Orchestration', 'Data', 'Security', 'Observability']

export default function App() {
  const [page, setPage] = useState('s3')
  const current = PAGES.find(p => p.id === page)!

  return (
    <div className="d-flex" style={{ height: '100vh', overflow: 'hidden' }}>
      <nav className="d-flex flex-column border-end bg-light" style={{ width: 186, flexShrink: 0 }}>
        <div className="px-3 py-3 border-bottom">
          <span className="fw-semibold" style={{ fontSize: 14 }}>🗂️ MiniStack</span>
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
