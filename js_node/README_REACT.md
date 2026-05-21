# React UI for MiniStack

A modern web interface for MiniStack built with React, TypeScript, and Vite.

---

## Features

- **Real-time updates** with TanStack Query
- **Responsive design** using Bootstrap 5
- **Type-safe** AWS SDK calls
- **Fast development** with Vite HMR

---

## Prerequisites

| Tool | Version |
|---|---|
| Node.js | 18+ |
| npm | 9+ |
| Docker | 24+ |

---

## Getting Started

### 1. Install dependencies

```bash
cd js_node
npm install
```

### 2. Start the development server

```bash
npm run dev
```

The app will be available at: http://localhost:5173

### 3. Build for production

```bash
npm run build
```

---

## Project Structure

```
js_node/
├── public/                  # Static files
├── src/
│   ├── assets/              # Images and fonts
│   ├── components/          # Reusable components
│   ├── hooks/               # Custom hooks
│   ├── pages/               # Page components
│   ├── services/            # AWS service integrations
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── vite-env.d.ts        # TypeScript declarations
├── index.html               # HTML template
├── package.json             # Project configuration
├── tsconfig.json            # TypeScript configuration
├── vite.config.ts           # Vite configuration
└── Dockerfile               # Docker configuration
```

---

## Configuration

Environment variables can be configured in `.env`:

```env
VITE_AWS_ENDPOINT=http://localhost:4566
VITE_AWS_REGION=us-east-1
```

---

## Docker

To run the React UI in Docker:

```bash
cd js_node
docker build -t ministack-react-ui .
docker run -p 5173:5173 -e VITE_AWS_ENDPOINT=http://host.docker.internal:4566 ministack-react-ui
```

---

## Docker Compose

A `docker-compose.yml` file is available in the `ministack-docker/` directory to run both MiniStack and the React UI together:

```bash
cd ministack-docker
docker-compose up
```

This will start:
- MiniStack on port 4566
- React UI on port 5173

