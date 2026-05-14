# MiniStack UI — Build Guide

A visual service browser web app for MiniStack (free LocalStack alternative).

---

## Prerequisites

### Required software

| Tool    | Version | Install             |
|---------|---------|---------------------|
| Node.js | 18+     | https://nodejs.org  |
| npm     | 9+      | bundled with Node   |
| Docker  | 24+     | https://docker.com  |
| Git     | any     | https://git-scm.com |

### MiniStack running locally

```bash
docker run -p 4566:4566 ministackorg/ministack  
```

Verify it's up:

```bash
curl http://localhost:4566/health
# → {"status":"ok"}
```

---

## Tech Stack

| Layer              | Choice                                             |
|--------------------|----------------------------------------------------|
| Bundler            | Vite 5                                             |
| UI framework       | React 18                                           |
| Styling            | TailwindCSS 3 + shadcn/ui                          |
| Data fetching      | TanStack Query v5                                  |
| AWS SDK            | `@aws-sdk` v3 (S3, DynamoDB, SQS, CloudWatch Logs) |
| Language           | TypeScript                                         |
| Desktop (optional) | Tauri v2                                           |

---

## 1. Scaffold the project

```bash
npm create vite@latest ministack-ui -- --template react-ts
cd ministack-ui
npm install
```

Install dependencies:

```bash
# AWS SDK clients
npm install @aws-sdk/client-s3 \
            @aws-sdk/client-dynamodb \
            @aws-sdk/client-sqs \
            @aws-sdk/client-cloudwatch-logs

# Data fetching + UI
npm install @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Install shadcn/ui:

```bash
npx shadcn@latest init
# Choose: TypeScript, Default style, CSS variables
```

---

## 2. Project structure

```
ministack-ui/
├── src/
│   ├── aws/
│   │   ├── clients.ts        # all SDK clients configured
│   │   ├── s3.ts             # listBuckets, listObjects, getObject
│   │   ├── dynamo.ts         # listTables, scanTable
│   │   └── sqs.ts            # listQueues, receiveMessages, sendMessage
│   ├── pages/
│   │   ├── S3Page.tsx
│   │   ├── DynamoPage.tsx
│   │   └── SQSPage.tsx
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   ├── DataTable.tsx
│   │   └── StatusBar.tsx
│   ├── hooks/
│   │   ├── useS3.ts
│   │   ├── useDynamo.ts
│   │   └── useSQS.ts
│   └── main.tsx
├── vite.config.ts
└── package.json
```

---

## 3. Vite proxy (fixes CORS)

Browsers block requests from `localhost:5173` → `localhost:4566`. Fix with Vite's dev proxy:

```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:4566',
        rewrite: path => path.replace(/^\/api/, ''),
        changeOrigin: true,
      },
    },
  },
})
```

---

## 4. AWS SDK clients

```ts
// src/aws/clients.ts
import { S3Client } from '@aws-sdk/client-s3'
import { DynamoDBClient } from '@aws-sdk/client-dynamodb'
import { SQSClient } from '@aws-sdk/client-sqs'
import { CloudWatchLogsClient } from '@aws-sdk/client-cloudwatch-logs'

const config = {
  endpoint: 'http://localhost:5173/api', // goes through Vite proxy
  region: 'us-east-1',
  credentials: { accessKeyId: 'test', secretAccessKey: 'test' },
  forcePathStyle: true,                  // required for S3
}

export const s3      = new S3Client(config)
export const dynamo  = new DynamoDBClient(config)
export const sqs     = new SQSClient(config)
export const cwLogs  = new CloudWatchLogsClient(config)
```

---

## 5. S3 service layer

```ts
// src/aws/s3.ts
import { s3 } from './clients'
import { ListBucketsCommand, ListObjectsV2Command } from '@aws-sdk/client-s3'

export const listBuckets = async () => {
  const res = await s3.send(new ListBucketsCommand({}))
  return res.Buckets ?? []
}

export const listObjects = async (bucket: string, prefix = '') => {
  const res = await s3.send(new ListObjectsV2Command({ Bucket: bucket, Prefix: prefix }))
  return res.Contents ?? []
}
```

---

## 6. TanStack Query hooks

```ts
// src/hooks/useS3.ts
import { useQuery } from '@tanstack/react-query'
import { listBuckets, listObjects } from '../aws/s3'

export const useS3Buckets = () =>
  useQuery({ queryKey: ['s3-buckets'], queryFn: listBuckets, refetchInterval: 5000 })

export const useS3Objects = (bucket: string) =>
  useQuery({ queryKey: ['s3-objects', bucket], queryFn: () => listObjects(bucket), enabled: !!bucket })
```

---

## 7. S3 page component

```tsx
// src/pages/S3Page.tsx
import { useState } from 'react'
import { useS3Buckets, useS3Objects } from '../hooks/useS3'

export default function S3Page() {
  const [selected, setSelected] = useState('')
  const { data: buckets, isLoading } = useS3Buckets()
  const { data: objects } = useS3Objects(selected)

  if (isLoading) return <p>Loading buckets…</p>

  return (
    <div className="flex gap-4 p-4">
      <ul className="w-48 border rounded">
        {buckets?.map(b => (
          <li key={b.Name}
              className={`p-2 cursor-pointer hover:bg-gray-100 ${selected === b.Name ? 'bg-blue-50 font-medium' : ''}`}
              onClick={() => setSelected(b.Name!)}>
            {b.Name}
          </li>
        ))}
      </ul>

      <div className="flex-1 border rounded p-2">
        {objects?.map(o => (
          <div key={o.Key} className="flex justify-between py-1 border-b text-sm">
            <span>{o.Key}</span>
            <span className="text-gray-400">{o.Size} B</span>
          </div>
        ))}
      </div>
    </div>
  )
}
```

---

## 8. App entry + sidebar

```tsx
// src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'

const qc = new QueryClient()
ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={qc}><App /></QueryClientProvider>
)
```

```tsx
// src/App.tsx — minimal sidebar routing
import { useState } from 'react'
import S3Page from './pages/S3Page'
import DynamoPage from './pages/DynamoPage'
import SQSPage from './pages/SQSPage'

const PAGES: Record<string, JSX.Element> = {
  S3: <S3Page />, DynamoDB: <DynamoPage />, SQS: <SQSPage />
}

export default function App() {
  const [page, setPage] = useState('S3')
  return (
    <div className="flex h-screen">
      <nav className="w-40 border-r bg-gray-50 p-4 flex flex-col gap-2">
        <p className="text-xs font-semibold text-gray-400 mb-2">SERVICES</p>
        {Object.keys(PAGES).map(p => (
          <button key={p} onClick={() => setPage(p)}
                  className={`text-left px-2 py-1 rounded ${page === p ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}>
            {p}
          </button>
        ))}
      </nav>
      <main className="flex-1 overflow-auto">{PAGES[page]}</main>
    </div>
  )
}
```

---

## 9. Run it

```bash
npm run dev
# → http://localhost:5173
```

Make sure MiniStack is running on `:4566` before opening the browser.

---

## 10. Seed some test data (optional)

```bash
# Create an S3 bucket and upload a file
aws --endpoint-url=http://localhost:4566 s3 mb s3://my-bucket
echo "hello world" | aws --endpoint-url=http://localhost:4566 s3 cp - s3://my-bucket/hello.txt

# Create a DynamoDB table
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
  --table-name Users \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

---

## Phase 2 additions (later)

- **DynamoDB:** item editor with JSON diff, batch delete
- **SQS:** send message panel, dead-letter queue inspector
- **Lambda:** invoke panel + real-time log tail
- **Status bar:** connection health indicator polling `/health`

---

## Optional: Package as a desktop app with Tauri

```bash
npm install -D @tauri-apps/cli
npx tauri init
npx tauri dev      # dev mode
npx tauri build    # → .app / .exe / .deb
```

The React code is unchanged — Tauri just wraps it in a native webview window (~10 MB binary vs Electron's ~150 MB).

---


## Troubleshooting

| Problem                     | Fix                                                                      |
|-----------------------------|--------------------------------------------------------------------------|
| `NetworkError` on SDK calls | Check Vite proxy config and that MiniStack is running                    |
| `InvalidSignatureException` | Ensure `credentials: { accessKeyId: 'test', secretAccessKey: 'test' }`   |
| S3 path-style errors        | Add `forcePathStyle: true` to S3Client config                            |
| CORS errors in browser      | All calls must go through the `/api` Vite proxy, not directly to `:4566` |
