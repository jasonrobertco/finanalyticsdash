# Finance Analytics Dashboard

Production-style full-stack finance analytics platform that ingests external stock market data, stores time-series data in Postgres/TimescaleDB, computes analytics, and serves a low-latency interactive dashboard.

## Stack
- Frontend: Next.js, TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy, Pydantic
- Database: PostgreSQL + TimescaleDB
- Cache: Redis
- Jobs: background worker + scheduled ingestion
- Deployment: Docker, Vercel, Render/Railway/Fly

## Core Features
- Ingest daily OHLCV stock market data from an external API
- Store and query time-series price data efficiently
- Compute analytics such as returns, moving averages, and volatility
- Compare stock performance against a benchmark
- Cache analytics endpoints for low-latency reads
- Refresh market data asynchronously through scheduled jobs

## Architecture
Next.js frontend -> FastAPI backend -> Redis / Postgres + TimescaleDB / background worker -> external market data API

## Status
Initial project setup complete. Backend, frontend, database schema, and ingestion pipeline are next.

## Goals
- full-stack engineering
- backend and API design
- time-series data modeling
- caching and performance thinking
- asynchronous job processing
- production-style system architecture