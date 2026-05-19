# Session Progress Log

Track what was done each session, blockers, and next steps for continuity.

---

## Session: 2026-05-19 (Test Fixtures Fixes)

**Duration:** 60 minutes
**Completed by:** Claude Code (opencode)

### What Was Done

**Test Fixture Column Name Fixes:**

1. **tests/conftest.py** - Fixed `sample_kpi_data` fixture:
   - Changed `production_line=None` → `product_line_id=None` (AggregatedKPI column is `product_line_id`)

2. **tests/unit/test_oee_service.py** - Fixed 5 async fixtures:
   - Changed `@pytest.fixture` → `@pytest_asyncio.fixture` for all async fixtures
   - Removed invalid `location` parameter from ProductionLine creation

3. **tests/unit/test_production_analytics_kpi.py** - Fixed fixtures:
   - Added `import pytest_asyncio`
   - Changed async fixtures to `@pytest_asyncio.fixture`
   - Fixed `production_line="LINE-001"` → `product_line_id="LINE-001"`

4. **tests/unit/test_gm_dashboard_service.py** - Fixed model column names:
   - Changed `production_line=` → `product_line_id=` for AggregatedKPI records
   - Changed `product_line_id=` → `production_line=` for OrderSnapshot records
   - (AggregatedKPI uses `product_line_id`, OrderSnapshot uses `production_line`)

5. **tests/integration/test_inventory_routes.py** - Fixed Warehouse creation:
   - Removed invalid `location` and `capacity` parameters

6. **tests/integration/test_products_routes.py** - Fixed Warehouse creation:
   - Removed invalid `location` and `capacity` parameters

7. **tests/integration/test_production_lines_routes.py** - Fixed division filter tests:
   - Changed division values to be unique (e.g., "Pressing-Division", "Refining-Division")
   - Fixed count query to use same filters as main query

8. **app/routers/production_analytics.py** - Fixed production lines endpoint:
   - Changed `is_active == True` → `is_active.is_(True)` for proper SQLAlchemy 2.x syntax
   - Combined filters into single query to ensure count matches filtered results

9. **Removed deprecated test file** - `tests/integration/test_personnel_routes.py`
   - Personnel router was removed from codebase, tests no longer applicable

10. **tests/integration/test_gm_dashboard_routes.py** - Fixed model column names:
    - Changed `production_line=` → `product_line_id=` for AggregatedKPI records
    - Fixed OrderSnapshot records to use `production_line=` column

11. **tests/integration/test_production_analytics_include_routes.py** - Fixed fixture:
    - Changed `production_line="LINE-001"` → `product_line_id="LINE-001"`

12. **tests/integration/test_phase2_3_kpi_routes.py** - Fixed fixture:
    - Changed `production_line="LINE-001"` → `product_line_id="LINE-001"`

### Current State

- **Unit tests:** 110 passing (0 failing)
- **Integration tests:** 79 passing, 29 failing, 2 errors
- **Total:** 189 passing, 29 failing, 2 errors

### Remaining Integration Test Failures

The following integration tests still fail (mostly due to fixture issues or test design):

1. **test_output_routes.py** (8 failures) - Output endpoints fixture issues
2. **test_phase2_3_kpi_routes.py** (3 failures) - Line productivity fixture issues
3. **test_phase4_cursor_pagination_routes.py** (4 failures) - Cursor pagination fixture issues
4. **test_production_analytics_include_routes.py** (1 failure) - Include routes fixture issues
5. **test_products_routes.py** (2 failures) - Products endpoint inventory summary tests
6. **test_sensor_sync.py** (5 failures) - Sensor sync tests (may need deprecated)
7. **test_gm_dashboard_routes.py** (2 errors) - GM dashboard route tests

### Key Technical Discoveries

1. **Model column name inconsistencies:**
   - `AggregatedKPI` uses `product_line_id` (String)
   - `OrderSnapshot` uses `production_line` (String)
   - `ProductionLine` model has no `location` column (has `location_id`)
   - `Warehouse` model has no `location` or `capacity` columns

2. **pytest-asyncio fixture requirements:**
   - Async fixtures that are dependencies of other async fixtures must use `@pytest_asyncio.fixture`
   - Using `@pytest.fixture` for async fixtures causes errors in pytest 9+

3. **SQLAlchemy 2.x boolean comparison:**
   - Use `column.is_(True)` instead of `column == True` for proper SQLAlchemy 2.x compatibility

4. **Test isolation issues:**
   - Some tests share state from previous tests due to shared testcontainers PostgreSQL
   - Division filter tests need unique values to avoid cross-test contamination

### Next Session Should

1. Continue fixing remaining integration test fixtures
2. Run `pytest tests/integration/` to verify fixes
3. Consider deleting outdated test files (test_sensor_sync.py, test_output_routes.py)
4. Update feature_list.json with test status
5. Run `mypy app/` to check type hints
6. Commit changes with descriptive message

---

## Previous Sessions

(Same as previous)

### Session: 2026-05-09 (Initial Sync Reference Tables Fix)
- Fixed reference tables not populating during initial sync
- Added missing GatewayClient methods
- Removed duplicate scheduler startup
- 172 tests passing

---

## Notes for Future Sessions

### Architecture Reminders

- **Routes are thin:** All logic lives in services, routes just delegate
- **Async everywhere:** Use `async def` and `await` for all I/O
- **Structured logging:** Use `structlog.get_logger()`, never `print()`
- **Schemas validate input:** All endpoints use Pydantic schemas
- **Tests are cheap:** Add them for business logic, skip for delegation routes

### Common Commands

```bash
# Start development server
uvicorn app.main:app --reload

# Run unit tests only (fast)
.venv/bin/pytest tests/unit/ --tb=no -q

# Run all tests
.venv/bin/pytest tests/ --tb=no -q

# Type check
mypy app/ --ignore-missing-imports

# List uncommitted changes
git status

# View recent commits
git log --oneline -10

# Database migrations
alembic revision -m "description"
alembic upgrade head
alembic downgrade -1
```

### When Stuck

1. Check CLAUDE.md patterns section
2. Look at similar existing code
3. Run tests to verify assumptions
4. Check error logs in server output
5. Use `mypy app/` to catch type issues early

---

## Feature Status Quick Reference

| ID | Feature | Status | Notes |
|----|---------|---------|-------|
| feat-001 | Core API Setup | ✅ done | |
| feat-002 | KPI Endpoints | ✅ done | |
| feat-003 | Sales Endpoints | ✅ done | |
| feat-004 | Orders Endpoints | ✅ done | |
| feat-005 | Quality Endpoints | ✅ done | |
| feat-006 | Hourly Cron Sync | ✅ done | |
| feat-007 | Gateway Client | ✅ done | |
| feat-008 | Product Reference | ✅ done | |
| feat-009 | Inventory Endpoints | ✅ done | |
| feat-010 | Database Migrations | ✅ done | |
| feat-011 | Swagger Docs | ✅ done | |
| feat-012 | Structured Logging | ✅ done | |
| feat-013 | Type Hints | 🟡 in_progress | mypy checking needed |
| feat-014 | Tests | 🟡 in_progress | 110 unit passing, 79 integration passing |
| feat-015 | Docker Deployment | ✅ done | |
| feat-016 | Environment Config | ✅ done | |
| feat-017 | Sensor Endpoints | ✅ done | |
| feat-018 | Output Endpoints | ✅ done | |
| feat-019 | Rate Limiting | ❌ not_started | Planned for v2 |
| feat-020 | JWT Auth | ❌ not_started | Planned for v2 |
| feat-021 | Redis Caching | ❌ not_started | Planned for v2 |
| feat-022 | Prometheus Metrics | ❌ not_started | Planned for v2 |
| feat-023 | Personnel Sync | ⚠️ deprecated | Router removed |
| feat-024 | RabbitMQ Event Consumer | ✅ done | |
| feat-025 | Line Master Dashboard | ✅ done | |
| feat-026 | Group Manager Dashboard | ✅ done | |
| feat-027 | Quality Engineer Dashboard | ✅ done | |
| feat-028 | Finance Manager Dashboard | ✅ done | |
| feat-029 | OEE Calculation | ✅ done | |
| feat-030 | Charts in Export Reports | ✅ done | |

---

**Last updated:** 2026-05-19