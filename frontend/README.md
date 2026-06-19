# Frontend — Jayanth Trading Tiles System

Next.js 15 (App Router) + React 19 + TypeScript + Tailwind + shadcn/ui.

## Run via Docker (recommended)
From project root:

    docker-compose up frontend

## Run locally

    npm install
    npm run dev

Opens on `http://localhost:3000`. Backend must be reachable at `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`).

## Locked after creation
Per ASES rule 6, once /ases-ui-scaffold has run for a sprint, execution agents may only edit `src/lib/api.ts` and other integration_points. Component code is the UI agent's territory.
