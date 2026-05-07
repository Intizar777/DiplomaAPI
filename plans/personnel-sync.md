# Plan: Personnel Sync Feature

## Context

DiplomaAPI does not sync any Personnel data from EFKO Gateway, even though the Gateway exposes a full `/personnel` API with departments, positions, employees, locations, production lines, and workstations. These entities are needed to enrich analytics with employee names, department context, and production line information.

Success criteria:
1. All existing tests pass + new tests green
2. DB stores and syncs personnel entities
3. E2E tests (integration tests hitting real Postgres) pass

---

## Sync Order (FK dependencies)

Sync must happen in this order:

1. **Locations** (no deps)
2. **Production Lines** (deps: Location)
3. **Departments** (deps: Location; self-referencing `parent_id` — two-pass upsert)
4. **Positions** (deps: Department)
5. **Workstations** (deps: Location, ProductionLine)
6. **Employees** (deps: Position, Workstation)

---

## Files to Create

### `app/models/personnel.py`
Six models: `Location`, `ProductionLine`, `Department`, `Position`, `Workstation`, `Employee`.
- All: `Base, UUIDMixin, TimestampMixin`
- UUID PKs preserved from Gateway (same pattern as `Product`)
- FKs nullable (avoid insert order issues; Gateway data may reference IDs not yet synced)
- No ORM relationships (keep it flat, consistent with existing models)
- Pattern: `product.py` — `Column(String, Boolean, Integer, UUID, Index)`

### `app/schemas/personnel.py`
Response schemas for all 6 entities + list wrappers.
- Pattern: `quality.py` schemas — `BaseModel`, `Config: from_attributes = True`
- `LocationResponse`, `ProductionLineResponse`, `DepartmentResponse`, `PositionResponse`, `WorkstationResponse`, `EmployeeResponse`
- `PersonnelSummaryResponse` — top-level response with counts per entity

### `app/services/personnel_service.py`
`PersonnelService(db, gateway)` with:
- `get_departments(type=None)` → query local DB
- `get_positions(department_id=None)` → query local DB
- `get_employees(department_id=None, status=None)` → query local DB
- `get_locations(type=None)` → query local DB
- `sync_from_gateway()` → full upsert of all 6 entities in dependency order, returns total records count

`sync_from_gateway()` uses **product_service upsert pattern**: `select by id`, update if found, `add` if not, `flush()` every 100, single `commit()` at end of each entity type.

**Two-pass for departments** (self-referencing): first pass inserts all without `parent_id`, second pass updates `parent_id`. This avoids FK violation when parent doesn't exist yet.

### `app/services/gateway_client.py` — add methods
```python
get_personnel_locations() → _fetch_all_pages("/personnel/locations", "locations")
get_personnel_departments() → _fetch_all_pages("/personnel/departments", "departments")
get_personnel_positions() → _fetch_all_pages("/personnel/positions", "positions")
get_personnel_production_lines() → _fetch_all_pages("/personnel/production-lines", "productionLines")
get_personnel_workstations() → _fetch_all_pages("/personnel/workstations", "workstations")
get_personnel_employees() → _fetch_all_pages("/personnel/employees", "employees")
```
All paginated (max 100 per page), no date filters (reference data).

### `app/routers/personnel.py`
`APIRouter(prefix="/api/v1/personnel", tags=["Personnel"])`

Endpoints:
- `GET /departments` — optional `?type=`
- `GET /positions` — optional `?department_id=`
- `GET /employees` — optional `?department_id=`, `?status=`
- `GET /locations` — optional `?type=`
- `GET /summary` — counts per entity (for quick health check)

Pattern: `quality.py` router — `get_services()` dependency, no date filters here.

### `app/cron/jobs.py` — add `sync_personnel_task()`
Pattern: `sync_products_task()` (no incremental logic, always full upsert).
```python
async def sync_personnel_task():
    async with AsyncSessionLocal() as db:
        log = await create_sync_log(db, "personnel")
        gateway = GatewayClient()
        service = PersonnelService(db, gateway)
        try:
            records = await service.sync_from_gateway()
            await complete_sync_log(db, log, SyncStatus.COMPLETED, records)
        except Exception as e:
            await complete_sync_log(db, log, SyncStatus.FAILED, error_message=str(e))
            raise
        finally:
            await gateway.close()
```

### `app/cron/scheduler.py` — add job
`CronTrigger(minute=40)` — slot is currently free.

### Alembic migration
`alembic revision --autogenerate -m "add_personnel_tables"`
Add `from app.models import personnel` to `alembic/env.py`.

---

## Files to Modify

| File | Change |
|------|--------|
| `app/models/__init__.py` | Add imports: `Location, ProductionLine, Department, Position, Workstation, Employee` |
| `app/schemas/__init__.py` | Add personnel schemas |
| `app/services/__init__.py` | Add `PersonnelService` |
| `app/routers/__init__.py` | Add `personnel_router` |
| `app/cron/jobs.py` | Add `sync_personnel_task`, update imports |
| `app/cron/scheduler.py` | Add job at minute=40, import task |
| `app/main.py` | `app.include_router(personnel_router)` |
| `alembic/env.py` | `from app.models import personnel` |
| `tests/conftest.py` | Add fixtures: `sample_locations`, `sample_departments`, `sample_positions`, `sample_employees` |

---

## Files to Create (tests)

### `tests/unit/test_personnel_service.py`
Tests against real Postgres (session fixture), gateway=None:
- `test_get_departments_returns_all`
- `test_get_departments_filter_by_type`
- `test_get_positions_filter_by_department`
- `test_get_employees_filter_by_status`
- `test_get_locations_filter_by_type`
- `test_sync_from_gateway_upserts_correctly` — mock gateway, insert once, call again with changed name, verify updated

### `tests/integration/test_personnel_routes.py`
Tests against real Postgres via httpx client:
- `test_get_departments_returns_200`
- `test_get_departments_filter_by_type`
- `test_get_positions_returns_200`
- `test_get_employees_returns_200`
- `test_get_locations_returns_200`
- `test_get_summary_returns_counts`
- `test_empty_tables_return_empty_lists`
- `test_unknown_filter_type_returns_empty` (future date / invalid filter)

---

## Verification

```bash
# 1. Create migration
alembic revision --autogenerate -m "add_personnel_tables"
alembic upgrade head

# 2. Run all tests
pytest tests/ -v

# 3. Type check
mypy app/ --ignore-missing-imports

# 4. Manual E2E
uvicorn app.main:app --reload
# POST /api/v1/sync/trigger (trigger personnel sync manually)
# GET /api/v1/personnel/departments
# GET /api/v1/personnel/summary
```

---

## Implementation Order

1. `app/models/personnel.py`
2. Update `app/models/__init__.py` + `alembic/env.py`
3. Run `alembic revision --autogenerate` + `alembic upgrade head`
4. `app/schemas/personnel.py` + update `app/schemas/__init__.py`
5. Add gateway methods to `app/services/gateway_client.py`
6. `app/services/personnel_service.py` + update `app/services/__init__.py`
7. `app/routers/personnel.py` + update `app/routers/__init__.py` + `app/main.py`
8. `app/cron/jobs.py` + `app/cron/scheduler.py`
9. `tests/conftest.py` fixtures
10. `tests/unit/test_personnel_service.py`
11. `tests/integration/test_personnel_routes.py`
12. `pytest tests/ -v` — all green
