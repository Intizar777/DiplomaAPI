# Tech Stack & Build

## Core Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Runtime | Python 3.12, uvicorn |
| ORM | SQLAlchemy 2.x (async) |
| Database | PostgreSQL 14+ via asyncpg |
| Migrations | Alembic |
| Validation | Pydantic v2 + pydantic-settings |
| HTTP Client | httpx (async) |
| Scheduler | APScheduler 3.x |
| Message Queue | aio-pika (RabbitMQ) |
| Logging | structlog (JSON output) |
| Testing | pytest, pytest-asyncio, testcontainers |
| Reports | openpyxl |

## Common Commands

```bash
# Run all tests (uses testcontainers for PostgreSQL)
pytest tests/ -v

# Type checking
mypy app/ --ignore-missing-imports

# Linting
ruff check app/

# Dev server (port 8000, Swagger at /docs)
uvicorn app.main:app --reload

# Create a new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Install dependencies
pip install -r requirements.txt
```

## Configuration

All config is loaded from environment variables (`.env` file) via `pydantic-settings`. Key variables:

- `DATABASE_URL` — async PostgreSQL connection string
- `GATEWAY_URL` — upstream EFKO Gateway base URL
- `GATEWAY_AUTH_EMAIL` / `GATEWAY_AUTH_PASSWORD` — Gateway credentials
- `RABBITMQ_URL` — AMQP connection string
- `SYNC_INTERVAL_MINUTES` — cron interval (default 60)
- `LOG_LEVEL` — structlog level (default INFO)

## Conventions

- Use `ConfigDict` instead of `class Config` for Pydantic models
- All I/O functions must be `async def`
- Use `structlog.get_logger()` for logging — never `print()`
- Env variable names are UPPER_CASE; Python settings fields are lower_snake_case
- Never hardcode secrets
