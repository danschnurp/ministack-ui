# MiniStack UI

A visual service browser web app for MiniStack (free LocalStack alternative).

## Prerequisites

- Node.js 18+
- npm 9+
- Docker 24+

## Setup

1. Make sure MiniStack is running:
```bash
docker run -p 4566:4566 ministackorg/ministack
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

4. Open http://localhost:5173 in your browser

## Features

- Browse S3 buckets and objects
- DynamoDB table management
- SQS queue management
- CloudWatch Logs viewing

## Architecture

- **UI Framework**: React 18 with TailwindCSS + shadcn/ui
- **Data Fetching**: TanStack Query v5
- **AWS SDK**: @aws-sdk v3 (S3, DynamoDB, SQS, CloudWatch Logs)
- **TypeScript**: Full type safety

## Troubleshooting

- CORS errors? Make sure all calls go through the `/api` Vite proxy
- Network errors? Check that MiniStack is running on localhost:4566
- S3 path-style errors? The SDK is configured with `forcePathStyle: true`
