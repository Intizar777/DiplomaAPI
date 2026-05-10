# AGENTS.md

FastAPI analytics service aggregating KPI, sales, orders, quality, inventory data from EFKO microservices. Auto-syncs hourly via cron.

## Startup (2-3 minutes)

1. Read CLAUDE.md (architecture, patterns)
2. Read feature_list.json (current status)
3. Run `./init.sh` (verify environment)
4. Read progress.md (prior session context)

## Working Rules

1. **One feature at a time** — Update feature_list.json as you go
2. **No architecture changes without discussion** — New services/models/routers need approval
3. **Business logic in services** — Routes never query database directly
4. **Schemas validate all input** — All routes use Pydantic schemas
5. **Test business logic** — Service methods must have tests
6. **Migrations immutable** — Never edit; create new ones with `alembic revision -m "msg"`
7. **Env vars lowercase_with_underscores** — Never hardcode secrets
8. **Structured logging only** — Use `structlog.get_logger()`, never `print()`
9. **Async/await required** — All I/O must be async
10. **Specific error handling** — Catch specific exceptions, return meaningful HTTP codes

## Definition of Done

Feature is done when:
- ✅ Implementation complete
- ✅ Type hints on all new code
- ✅ `pytest tests/` passes
- ✅ `mypy app/` passes
- ✅ Manual verification in `/docs`
- ✅ Migration created (if needed)
- ✅ feature_list.json updated
- ✅ Commit documents WHY, not WHAT
- ✅ No debug code or comments
- ✅ Docs updated after changes

## Before Session End

1. Update feature_list.json + progress.md
2. Run `pytest tests/ && mypy app/`
3. Commit: `git commit -m "feature: description and why"`
4. Update progress.md with next steps

## Structure

```
app/
├── main.py       # FastAPI entry, lifespan, middleware
├── config.py     # Settings from .env
├── database.py   # SQLAlchemy async setup
├── models/       # ORM models (KPI, Sales, Orders, etc.)
├── schemas/      # Pydantic request/response
├── routers/      # API endpoints by domain
├── services/     # Business logic
├── cron/         # Hourly sync jobs
└── tests/        # Unit + integration tests
```

## Domains & Endpoints

| Domain | Purpose | Endpoints |
|--------|---------|-----------|
| KPI | Production metrics | `/api/v1/kpi/current`, `/history`, `/compare` |
| Sales | Sales data, trends | `/api/v1/sales/summary`, `/trends`, `/top-products` |
| Orders | Order tracking | `/api/v1/orders/status-summary`, `/list`, `/{id}` |
| Quality | Quality metrics | `/api/v1/quality/summary`, `/defect-trends`, `/lots` |
| Inventory | Stock levels | `/api/v1/inventory/levels` |
| Sync | Cron control | `/api/v1/sync/status`, `/trigger` |

## Patterns

**New endpoint:**
1. Schema in `app/schemas/{domain}.py`
2. Service in `app/services/{domain}_service.py`
3. Route in `app/routers/{domain}_router.py`
4. Tests in `tests/unit/test_{domain}_service.py`

**New table:**
1. Model in `app/models/{domain}.py`
2. Migration: `alembic revision -m "add table_name"`
3. Service methods + endpoints

**Fix bug:**
1. Write test reproducing bug
2. Fix code
3. Verify test passes
4. Commit: `fix: root cause description`

## Constraints

- **PostgreSQL = truth** — No in-memory caches without invalidation
- **Gateway = external source** — Never query gateway DB directly
- **Cron hourly** — Sync via `app/cron/scheduler.py` every 60 min
- **JSON only** — Use Pydantic for serialization
- **No auth in v1** — Read-only endpoints; auth planned for v2
- Use ConfigDict instead of class Config for Pydantic Models

## Tech Stack

| Component | Tech | Location |
|-----------|------|----------|
| Framework | FastAPI 0.104+ | `app/main.py` |
| ORM | SQLAlchemy 2.x async | `app/database.py` |
| Validation | Pydantic v2 | `app/schemas/` |
| DB | PostgreSQL 14+ | `.env` → `DATABASE_URL` |
| Migrations | Alembic 1.12+ | `alembic/` |
| HTTP | httpx | `app/services/gateway_client.py` |
| Logging | structlog (JSON) | `app/config.py` |
| Testing | pytest + testcontainers | `tests/` |
| Scheduler | APScheduler 3.x | `app/cron/scheduler.py` |

## Verification Commands
```bash
pytest tests/ -v              # Run tests (testcontainers PostgreSQL)
mypy app/                     # Type check
ruff check app/               # Lint
uvicorn app.main:app --reload # Dev server → http://localhost:8000/docs
```

