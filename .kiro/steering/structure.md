# Project Structure

```
app/
├── main.py                 # FastAPI app, lifespan, middleware, router registration
├── config.py               # Settings (pydantic-settings, loads from .env)
├── database.py             # SQLAlchemy async engine & session factory
├── logging_config.py       # structlog configuration
├── models/                 # SQLAlchemy ORM models (one file per domain)
│   ├── base.py             # Declarative base
│   ├── kpi.py
│   ├── sales.py
│   ├── orders.py
│   ├── quality.py
│   ├── inventory.py
│   ├── output.py
│   ├── sensor.py
│   ├── personnel.py
│   ├── product.py
│   ├── reference.py        # Reference/lookup tables (3NF)
│   └── sync_log.py
├── schemas/                # Pydantic request/response schemas
│   ├── common.py           # Shared schemas (pagination, date ranges)
│   ├── gateway_responses.py # Schemas for Gateway API responses
│   └── {domain}.py         # Per-domain schemas
├── routers/                # API route handlers (thin — delegate to services)
│   └── {domain}.py
├── services/               # Business logic & data access
│   ├── gateway_client.py   # HTTP client for upstream Gateway API
│   └── {domain}_service.py
├── cron/                   # Scheduled sync jobs
│   ├── scheduler.py        # APScheduler setup
│   └── jobs.py             # Individual sync job definitions
├── messaging/              # RabbitMQ event consumption
│   ├── consumer.py         # Connection & channel management
│   ├── dispatcher.py       # Route messages to handlers
│   ├── schemas.py          # Message envelope schemas
│   └── handlers/           # Per-event-type handler functions
├── middleware/             # Custom ASGI middleware (request logging)
├── api/v1/                 # Supplementary route modules (reports)
└── utils/                  # Helpers (LLM docs formatter, logging utils)

alembic/                    # Database migrations
├── versions/               # Migration scripts (never edit existing ones)
└── env.py

tests/
├── conftest.py             # Shared fixtures (testcontainers DB, async session)
├── unit/                   # Service-layer unit tests
├── integration/            # Route-level tests (full HTTP round-trip)
└── e2e/                    # End-to-end tests
```

## Architecture Pattern

Three-layer architecture:

1. **Router** — HTTP interface, input validation, calls service
2. **Service** — Business logic, database queries (SQLAlchemy), Gateway calls
3. **Model/Schema** — Data representation (ORM models + Pydantic schemas)

## Adding a New Feature

1. Schema in `app/schemas/{domain}.py`
2. Service in `app/services/{domain}_service.py`
3. Router in `app/routers/{domain}.py` (register in `app/routers/__init__.py` and `main.py`)
4. Model in `app/models/{domain}.py` (if new table needed)
5. Migration via `alembic revision -m "add {table}"`
6. Tests in `tests/unit/test_{domain}_service.py` and `tests/integration/test_{domain}_routes.py`
