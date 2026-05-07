# AGENTS.md

FastAPI analytics service for EFKO microservices data aggregation. Dashboard API provides KPI, sales, orders, quality, and inventory analytics with automatic cron-based synchronization.

## Startup Workflow

**Before writing code, Claude Code must:**

1. Read this file (AGENTS.md) — understand project scope and rules
2. Read CLAUDE.md — understand architecture, patterns, and tech decisions
3. Read feature_list.json — see what's in progress and what's blocked
4. Read recent git commits — understand current state and ongoing work
5. Run `./init.sh` — verify environment, run type checks, execute tests

**Expected total time: 2-3 minutes**

## Project Structure

```
app/
├── main.py              # FastAPI entry point, lifespan, middleware
├── config.py            # Settings from .env
├── database.py          # SQLAlchemy async setup
├── models/              # ORM models (KPI, Sales, Orders, etc.)
├── schemas/             # Pydantic request/response schemas
├── routers/             # API endpoints organized by domain
├── services/            # Business logic (queries, aggregations, sync)
├── cron/                # Background jobs (hourly data sync)
└── tests/               # Unit and integration tests

alembic/                # Database migration definitions
requirements.txt        # Python dependencies
docker-compose.yml      # Local postgres + app stack
Dockerfile             # Production image
.env                   # Runtime configuration
```

## Domain Model

The API is organized into logical domains, each with routes, schemas, services, and database models:

| Domain | Purpose | Key Endpoints |
|--------|---------|---------------|
| **KPI** | Production metrics aggregation | `/api/v1/kpi/current`, `/api/v1/kpi/history`, `/api/v1/kpi/compare` |
| **Sales** | Sales data, trends, regional breakdowns | `/api/v1/sales/summary`, `/api/v1/sales/trends`, `/api/v1/sales/top-products` |
| **Orders** | Order status, fulfillment tracking | `/api/v1/orders/status-summary`, `/api/v1/orders/list`, `/api/v1/orders/{id}` |
| **Quality** | Quality metrics, defect trends, lot tracking | `/api/v1/quality/summary`, `/api/v1/quality/defect-trends`, `/api/v1/quality/lots` |
| **Inventory** | Stock levels, warehouse data | `/api/v1/inventory/levels`, aggregated from external source |
| **Sync** | Cron synchronization control | `/api/v1/sync/status`, `/api/v1/sync/trigger` |
| **System** | Health, documentation | `/health`, `/docs` |

## Working Rules

**Follow these rules to keep the codebase maintainable and predictable:**

1. **One feature at a time** — Complete a feature before starting another. Update feature_list.json status as you work.

2. **No architecture changes without discussion** — Adding new services, models, or routers must be approved. Ask first.

3. **All data integrations go through services** — Routes must never query the database directly. Use `app/services/*.py`.

4. **Schemas are single-source-of-truth for APIs** — All routes use Pydantic schemas. Never accept unvalidated JSON.

5. **Tests first for business logic** — New queries, aggregations, calculations must have tests. Routes can skip tests if they only delegate to tested services.

6. **Database migrations are immutable** — Never edit or delete migrations. Create new ones with `alembic revision -m "message"`.

7. **Environment variables are lowercase with underscores** — `DATABASE_URL`, `GATEWAY_TOKEN`, `SYNC_INTERVAL_MINUTES`. Never hardcode secrets.

8. **Logging is structured (not print statements)** — Use `structlog.get_logger()` for all logging. Never use `print()`.

9. **Async/await is required** — All database queries and HTTP calls must be async. Use `async def` and `await`.

10. **Error handling is specific** — Catch specific exceptions, log context, return meaningful HTTP status codes (400, 404, 500, etc.).

## Definition of Done

A feature is **done** when:

- ✅ Implementation complete and matches feature description
- ✅ All new code has type hints (`def func(...) -> ReturnType:`)
- ✅ Tests pass: `pytest tests/` → all green
- ✅ Type check passes: `mypy app/` → no errors
- ✅ Manual verification in `/docs` (Swagger UI) or using the test scripts
- ✅ Relevant migration created (if database schema changed)
- ✅ feature_list.json status updated to `done`
- ✅ Commit message documents WHY, not WHAT
- ✅ No debug code, hardcoded values, or commented-out lines left behind

## End of Session

**Before finishing, you must:**

1. Update `feature_list.json` with current feature status
2. Update `progress.md` with what was done and what's blocked
3. Run `pytest tests/` one final time to confirm tests pass
4. Run `mypy app/` to confirm type check passes
5. Commit with clear message: `git commit -m "feature: description of what changed and why"`
6. Push if appropriate: `git push origin main`
7. Leave a restart path: Update `progress.md` with next steps for the next session

## Required Artifacts

- `feature_list.json` — Feature state tracker (update after each feature)
- `progress.md` — Session continuity log (update at end of session)
- `init.sh` — Verification script (run at session start)
- `.env` — Environment configuration (must exist before running)
- `tests/` — Test suite (must pass before claiming done)

## Verification Commands

Run these before claiming a feature is done:

```bash
# Run all tests
pytest tests/ -v

# Check types
mypy app/

# Lint and format check
ruff check app/

# Manual API testing (requires running server)
uvicorn app.main:app --reload
# Then visit http://localhost:8000/docs to test endpoints
```

## Common Patterns

**Adding a new endpoint:**
1. Create schema in `app/schemas/{domain}.py`
2. Create or extend service method in `app/services/{domain}_service.py`
3. Add route to `app/routers/{domain}_router.py`
4. Add tests to `tests/test_{domain}.py`
5. Document expected behavior in commit message

**Adding a new database table:**
1. Create model in `app/models/{domain}.py`
2. Create migration: `alembic revision -m "add table_name"`
3. Edit migration file to define schema
4. Test migration: `alembic upgrade head`
5. Add service methods to query the new table
6. Add endpoints + schemas

**Fixing a bug:**
1. Write a test that reproduces the bug
2. Fix the code
3. Verify test passes
4. Check for similar patterns elsewhere (use grep)
5. Commit with "fix: description of root cause"

## Architectural Constraints

**You must respect these constraints:**

- **PostgreSQL is the source of truth** — No in-memory caches without explicit invalidation strategy
- **Gateway API is the external source** — Dashboard API receives data from gateway, never queries its database directly
- **Cron jobs run hourly** — Sync happens via `app/cron/scheduler.py` every 60 minutes (configurable)
- **JSON for all APIs** — No XML, CSV, or other formats; use Pydantic schemas for serialization
- **No authentication required for v1** — All endpoints are read-only; future auth will be in v2
- **Soft delete is allowed but not required** — Use `is_deleted` flag or hard delete; be consistent within a domain

## Tech Stack Reference

| Layer | Technology | Location |
|-------|-----------|----------|
| Framework | FastAPI 0.104+ | `app/main.py` |
| ORM | SQLAlchemy 2.x async | `app/database.py` |
| Validation | Pydantic v2 | `app/schemas/` |
| Database | PostgreSQL 14+ | `.env` → `DATABASE_URL` |
| Migrations | Alembic 1.12+ | `alembic/` |
| HTTP Client | httpx | `app/services/gateway_client.py` |
| Logging | structlog + JSON | `app/config.py` |
| Testing | pytest + pytest-asyncio | `tests/` |
| Task Scheduler | APScheduler 3.x | `app/cron/scheduler.py` |

## When Stuck

**Common blockers and how to unblock:**

| Problem | Solution |
|---------|----------|
| Type check fails on model field | Add type hints to model: `field_name: str \| None = None` |
| Test fails in async function | Use `@pytest.mark.asyncio` decorator |
| Alembic migration fails | Check `.env` `DATABASE_URL` is correct, run `alembic downgrade base` then `upgrade head` |
| Import error in routes | Check `app/routers/__init__.py` exports the router |
| Endpoint returns 500 | Check server logs, look for exceptions in error handling |
| Gateway sync times out | Check `GATEWAY_URL` and `GATEWAY_TOKEN` in `.env` |

## Communication

- **Questions about architecture?** → Read CLAUDE.md first, then ask
- **Unsure about scope?** → Check feature_list.json and current progress.md
- **Need to change a pattern?** → Document decision in commit message
- **Found a bug in existing code?** → Fix it immediately, don't wait for permission
- **Want to refactor?** → Check CLAUDE.md patterns first, then propose in commit message

## Next Steps

1. Run `./init.sh` to verify environment
2. Read `feature_list.json` to see what's in progress
3. Read `progress.md` to understand prior session context
4. Open a feature and start coding

---

**Last updated:** 2026-05-07  
**Harness version:** 1.0 (comprehensive)
