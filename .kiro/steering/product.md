# Product Overview

Dashboard Analytics API — a FastAPI service that aggregates and serves production KPI, sales, orders, quality, inventory, and personnel data from EFKO's microservice ecosystem.

## Purpose

Provides a unified analytics layer for dashboards consumed by line masters, general managers, quality engineers, and finance teams. Data is pulled hourly from an upstream API Gateway and via RabbitMQ events, stored in PostgreSQL, and exposed through read-only REST endpoints.

## Key Capabilities

- Hourly cron-based data synchronization from the EFKO Gateway API
- Real-time event ingestion via RabbitMQ (production events)
- Period comparison, trend analysis, and aggregated summaries
- Role-specific dashboard endpoints (line master, GM, QE, finance)
- Excel report generation

## Constraints

- Read-only API (no auth in v1)
- PostgreSQL is the single source of truth for aggregated data
- Never queries the Gateway database directly — always goes through the Gateway HTTP API
- All data has a configurable retention window (default 90 days)
