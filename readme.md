# ministack-ui

A minimal browser UI for [MiniStack](https://github.com/ministackorg/ministack) — a free LocalStack alternative for local AWS development.

Browse and interact with local AWS services without leaving your browser.

---

## Supported services

| Group | Service | Features |
|---|---|---|
| Storage | S3 | List buckets, browse objects with size |
| Storage | DynamoDB | List tables, scan items |
| Streaming | Kinesis | List streams, shard info, stream metadata |
| Messaging | SQS | List queues, view messages, send messages |
| Messaging | SNS | List topics, subscriptions, publish messages |
| Compute | Lambda | List functions, invoke with payload, view response |
| Compute | API Gateway | List REST APIs, resources with HTTP methods, stages |
| Observability | CloudWatch Logs | Browse log groups, tail log streams |

---

## Prerequisites

| Tool | Version |
|---|---|
| Node.js | 18+ |
| npm | 9+ |
| Docker | 24+ |

---

## Getting started

**1. Start MiniStack**

```bash
docker run -p 4566:4566 ministackorg/ministack
```

Verify it's up:

```bash
curl http://localhost:4566/health
# → {"status":"ok"}
```

**2. Install dependencies**

```bash
npm install
```

**3. Run the dev server**

```bash
npm run dev
# → http://localhost:5173
```

---

## How it works

All AWS SDK calls are proxied through Vite's dev server to avoid CORS issues:

```
browser → localhost:5173/api/* → localhost:4566/*
```

The proxy is configured in `vite.config.ts`. SDK clients point at `http://localhost:5173/api` and use dummy credentials (`test` / `test`), which is all MiniStack requires.

Every request has a 3-second timeout (10 seconds for Lambda invocations). If MiniStack is unreachable the UI fails fast and shows an error — no hanging.

---

## Project structure

```
src/
├── aws/
│   ├── clients.ts       # shared SDK config + withTimeout() helper
│   ├── s3.ts
│   ├── dynamo.ts
│   ├── kinesis.ts
│   ├── sqs.ts
│   ├── sns.ts
│   ├── lambda.ts
│   ├── apigateway.ts
│   └── logs.ts
├── pages/
│   ├── S3Page.tsx
│   ├── DynamoPage.tsx
│   ├── KinesisPage.tsx
│   ├── SQSPage.tsx
│   ├── SNSPage.tsx
│   ├── LambdaPage.tsx
│   ├── ApiGatewayPage.tsx
│   └── LogsPage.tsx
├── components/
│   └── StatusBar.tsx    # live :4566 health indicator
├── hooks/
│   └── useServices.ts   # TanStack Query hooks
├── App.tsx              # sidebar routing
└── main.tsx             # QueryClient setup
```

---

## Tech stack

| Layer | Choice |
|---|---|
| Bundler | Vite 5 |
| UI framework | React 18 + TypeScript |
| Styling | Bootstrap 5 |
| Data fetching | TanStack Query v5 |
| AWS SDK | `@aws-sdk` v3 |

---

## Seed test data

```bash
# S3
aws --endpoint-url=http://localhost:4566 s3 mb s3://my-bucket
echo "hello" | aws --endpoint-url=http://localhost:4566 s3 cp - s3://my-bucket/hello.txt

# DynamoDB
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
  --table-name Users \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# SQS
aws --endpoint-url=http://localhost:4566 sqs create-queue --queue-name my-queue

# SNS
aws --endpoint-url=http://localhost:4566 sns create-topic --name my-topic

# Lambda (requires a zip with handler code)
aws --endpoint-url=http://localhost:4566 lambda create-function \
  --function-name my-fn \
  --runtime nodejs20.x \
  --role arn:aws:iam::000000000000:role/lambda-role \
  --handler index.handler \
  --zip-file fileb://function.zip

# Kinesis
aws --endpoint-url=http://localhost:4566 kinesis create-stream \
  --stream-name my-stream \
  --shard-count 2

# API Gateway
aws --endpoint-url=http://localhost:4566 apigateway create-rest-api --name my-api
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `NetworkError` on SDK calls | Check Vite proxy config and that MiniStack is running on `:4566` |
| `InvalidSignatureException` | Credentials must be `accessKeyId: 'test', secretAccessKey: 'test'` |
| S3 path-style errors | `forcePathStyle: true` is set in `clients.ts` — don't remove it |
| CORS errors | All calls must go through the `/api` Vite proxy, never directly to `:4566` |
| UI shows error immediately | MiniStack is not running — start it with the Docker command above |
| Lambda page blank | Cold-start timeout is 10 s — wait a moment and retry |