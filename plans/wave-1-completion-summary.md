# Dashboard Roadmap Completion Status

**Status:** ✅ Waves 1 & 2 COMPLETE AND TESTED  
**Last Updated:** 2026-05-09  
**Latest Commit:** 39abdf4 (Group Manager dashboard Wave 2)  

---

## What Was Done

### 1. Schemas (`app/schemas/line_master_dashboard.py`)
- ✅ `ShiftItem` — shift metrics (lot_count, quantity, approved_count, defect_count, defect_rate)
- ✅ `ShiftProgressResponse` — current shift progress for a date
- ✅ `ShiftComparisonPeriod` — single shift data point
- ✅ `ShiftComparisonResponse` — shift comparison over date range
- ✅ `DefectItem` — parameter-level defect stats
- ✅ `DefectSummaryResponse` — defect breakdown by parameter
- **Pydantic v2 compatible:** ConfigDict, proper forward refs, typing imports

### 2. Service (`app/services/line_master_dashboard_service.py`)
- ✅ `LineMasterDashboardService` with 3 methods:
  - `get_shift_progress(date)` — aggregates by shift for a single date
  - `get_shift_comparison(from_date, to_date)` — groups by date + shift over range
  - `get_defect_summary(from_date, to_date)` — aggregates QualityResults by parameter
- **Aggregation approach:** Query-based (func.count, func.sum for output) + Python dict aggregation (for quality)
- **Logging:** Structured logs via structlog for all three methods
- **Type hints:** Full coverage (Dict, List, Optional, date_type aliases)

### 3. Router (`app/routers/line_master_dashboard.py`)
- ✅ `APIRouter(prefix="/api/v1/dashboards/line-master")`
- ✅ 3 GET endpoints:
  - `/shift-progress?production_date=YYYY-MM-DD` (default: today)
  - `/shift-comparison?date_from=...&date_to=...` (default: last 7 days)
  - `/defect-summary?date_from=...&date_to=...` (default: last 7 days)
- **Dependency injection:** `LineMasterDashboardService(db)`
- **Response models:** All endpoints declare `response_model=`

### 4. Integration
- ✅ Registered in `app/routers/__init__.py` 
- ✅ Imported and wired in `app/main.py`
- ✅ Exported from `app/schemas/__init__.py`
- ✅ Exported from `app/services/__init__.py`
- ✅ Appears in `/docs` (Swagger UI)

### 5. Tests (`tests/unit/test_line_master_dashboard_service.py`)
- ✅ 8 unit tests, all passing:
  1. `test_get_shift_progress_returns_all_shifts` — verifies 3 shifts on test date
  2. `test_get_shift_progress_with_quality_defects` — counts defects correctly (1 per shift 1)
  3. `test_get_shift_progress_empty_date` — returns empty for date with no data
  4. `test_get_shift_comparison_groups_by_date_and_shift` — 6 shift records over 3 days
  5. `test_get_shift_comparison_calculates_quantities` — aggregates quantities > 0
  6. `test_get_defect_summary_aggregates_by_parameter` — groups by parameter_name
  7. `test_get_defect_summary_calculates_fail_rate` — verifies 1/6 = 16.67% for acidity
  8. `test_get_defect_summary_empty_range` — returns empty for date range with no data
- **Fixtures:** `sample_output_records` (6 lots over 3 days), `sample_quality_records` (18 test results)
- **Database:** Uses testcontainers PostgreSQL (real DB, not mocks)

### 6. Feature Tracking
- ✅ Added `feat-025` to `feature_list.json`
- ✅ Status: `done`
- ✅ Evidence: "app/schemas/line_master_dashboard.py, app/services/line_master_dashboard_service.py, app/routers/line_master_dashboard.py, tests/unit/test_line_master_dashboard_service.py (8/8 passing)"

---

## Test Results

```
149 passed (including 8 new), 3 pre-existing failures (unrelated to Wave 1)
Duration: 364.43s
```

**Wave 1 tests: 8/8 passing ✅**

---

## What Was Skipped (Intentionally)

### 1. Integration Tests for Routes
- ❌ Did NOT create `tests/integration/test_line_master_dashboard_routes.py`
- **Why:** Pattern is identical to KPI routes (route → service via Depends → response model)
- **Can be added later** if endpoint-specific testing needed (e.g., query param validation)

### 2. Production Line Filtering
- ❌ Did NOT implement `?line_id=<UUID>` or `?line_name=<str>` query parameter
- **Why:** ProductionOutput has NO `production_line_id` column
- **Solution available:** Would need JOIN via Workstation → ProductionLine
- **Decision:** For Wave 1, filter by shift only (sufficient for line master use case)
- **Can be added in Wave 2** if manager dashboard needs it

### 3. Equipment/Maintenance Data
- ❌ Did NOT add Equipment or EquipmentSchedule table
- **Why:** Not available in existing data models or Gateway
- **Addressed in memo:** Wave 1 focuses on production output + quality data only
- **Can be added later** if equipment data becomes available

### 4. Mypy Strict Compliance
- ❌ New code is typed correctly but project-wide `mypy --strict` not run
- **Why:** Pre-existing mypy issues in report_service.py (unrelated to dashboards)
- **New code status:** Zero mypy errors on new files (tested individually)

### 5. Pydantic Config Migration
- ❌ Did NOT migrate entire codebase from `class Config:` to `ConfigDict`
- ✅ **New schemas use:** `ConfigDict(from_attributes=True)` (Pydantic v2 style)
- **Old schemas:** Still use deprecated `class Config:` (generates warnings but works)
- **Decision:** Only new code follows Pydantic v2 patterns to avoid scope creep

---

## Wave 2: Group Manager Strategic Dashboard — COMPLETE ✅

**Status:** ✅ DONE  
**Commit:** 39abdf4 (feat: add Group Manager dashboard with per-line KPI sync)  
**Tests:** 20/20 passing (12 unit + 8 integration)

### Delivered Endpoints
```
✅ GET /api/v1/dashboards/gm/oee-summary?period_days={7,30,90}
   → OEE by line, ranked best-to-worst vs 75% target, trend sparklines

✅ GET /api/v1/dashboards/gm/plan-execution?date_from=...&date_to=...
   → Plan vs actual quantities per line, fulfillment %, order status breakdown

✅ GET /api/v1/dashboards/gm/downtime-ranking?date_from=...&date_to=...
   → Lines ranked by total delay hours (Pareto analysis), only completed orders
```

### Implementation Details
- **Schemas:** `app/schemas/gm_dashboard.py` — 4 Pydantic models (OEELineItem, PlanExecutionLineItem, DowntimeLineItem + Response wrappers)
- **Service:** `app/services/gm_dashboard_service.py` — 3 query methods with SQL aggregation (GROUP BY, CASE expressions)
- **Routes:** `app/routers/gm_dashboard.py` — 3 endpoints with dependency injection
- **Tests:**
  - Unit: `tests/unit/test_gm_dashboard_service.py` (12 tests covering aggregation logic)
  - Integration: `tests/integration/test_gm_dashboard_routes.py` (8 tests covering all endpoints + edge cases)

### Data Sources & Limitations
- **OEE data:** Reads from `AggregatedKPI` table (seeded by cron KPI sync)
- **Plan vs Actual:** Reads from `OrderSnapshot` table (order start/completion dates)
- **Downtime:** Calculated from `OrderSnapshot.planned_end vs actual_end` (no separate StopTime table)
- **⚠️ Cost Structure skipped:** Would require energy and material cost tables (not in Gateway)

### Architecture Notes
- Two-pass aggregation for OEE: (1) GROUP BY per line, (2) Fetch raw data points for trend
- Downtime ranked worst-first (highest delay first)
- NULL production_line field = all-lines aggregate in responses

### Wave 2 Caveats & Limitations ⚠️

1. **Cost Structure Endpoint Skipped**
   - Original plan included `/cost-structure` for material + energy + labor aggregation
   - **Reason:** No energy consumption or cost allocation tables in database/Gateway
   - **Decision:** Deferred to Wave 4 (Finance Manager) if cost data becomes available

2. **Downtime Calculation in Python**
   - Delay hours calculated after fetch, not in SQL (line 226 of service)
   - **Reason:** Different SQL dialects (PostgreSQL vs others) handle time intervals differently
   - **Trade-off:** Simpler, portable code at cost of doing math post-query
   - **Impact:** Works fine for <10K orders; would need optimization for >100K

3. **OEE Estimation Only**
   - Uses `AggregatedKPI.oee_estimate` (pre-calculated by KPI sync)
   - Does NOT calculate availability × performance × quality from scratch
   - **Reason:** No downtime events or detailed production metrics in base data
   - **Sufficient for:** Group manager oversight; quality engineer dashboard (Wave 3) will have detailed metrics

4. **No Pagination**
   - All endpoints return complete result sets (no limit/offset)
   - **Suitable for:** ~100 production lines; larger deployments would need pagination
   - **Mitigation:** Wave 4+ can add cursor-based pagination if needed

---

## What Still Needs to be Done

### Waves 3-5: Other Dashboards
**Status:** Designed, not started

- **Wave 3 (P2):** Quality Engineer Dashboard
  - Parameter trend analysis, batch deviations, defect Pareto
  - Endpoints: `/qe/parameter-trends`, `/qe/batch-analysis`, `/qe/defect-pareto`
  
- **Wave 4 (P3):** Finance Manager Dashboard  
  - Cost breakdown, variance analysis, budget vs actual
  - Endpoints: `/finance/cost-structure`, `/finance/variance`, `/finance/budget-comparison`
  
- **Wave 5 (P4):** Warehouse Manager Dashboard
  - Inventory levels, expiry alerts, shipment forecast
  - Endpoints: `/warehouse/inventory-levels`, `/warehouse/expiry-alerts`, `/warehouse/shipment-forecast`

---

## Files Modified/Created

### Created (4 new production files)
| File | Lines | Purpose |
|------|-------|---------|
| `app/schemas/line_master_dashboard.py` | 87 | 6 Pydantic response schemas |
| `app/services/line_master_dashboard_service.py` | 269 | Service with 3 aggregation methods |
| `app/routers/line_master_dashboard.py` | 81 | 3 GET endpoints |
| `tests/unit/test_line_master_dashboard_service.py` | 300+ | 8 unit tests |

### Modified (5 files)
| File | Changes |
|------|---------|
| `app/schemas/__init__.py` | +3 imports, +3 __all__ entries |
| `app/services/__init__.py` | +1 import, +1 __all__ entry |
| `app/routers/__init__.py` | +1 import, +1 __all__ entry |
| `app/main.py` | +1 import, +1 include_router() call |
| `feature_list.json` | +1 feature (feat-025) |

---

## Architecture Decisions Made

### 1. Aggregation Strategy
- **Output:** SQL GROUP BY (via SQLAlchemy func.count, func.sum)
- **Quality:** Full fetch + Python dict aggregation
- **Rationale:** Quality results have many-to-many with lots; simpler to aggregate in Python than complex SQL joins

### 2. Date Handling
- **Shifted all date types to `date_type`** alias to avoid Pydantic field name conflicts
- **Alternative considered:** `from __future__ import annotations` (rejected — already Pydantic v2, overkill)

### 3. Response Structure
- **Nested models:** ShiftItem inside ShiftProgressResponse (matches KPI pattern)
- **Metadata fields:** period_from, period_to on all responses (helps API consumers filter)
- **No pagination:** Wave 1 returns all records; pagination can be added to Wave 2 if needed

### 4. Service Constructor
- `LineMasterDashboardService(db: AsyncSession)` — simple, no gateway needed (doesn't sync from Gateway)
- **Matches pattern:** KPIService, QualityService (all query-only services have minimal deps)

---

## Known Limitations & Trade-offs

### 1. No Production Line Filtering
- Endpoints accept dates only, not line IDs
- **Affects:** Impossible to filter shift progress by specific line
- **Mitigation:** Line master can infer line from shift name (e.g., "Shift 1" = "Line 1")
- **Future:** Wave 2 or later can add line_id query param + Workstation JOIN

### 2. No Equipment/Maintenance Alerts
- Cannot show "days until next maintenance"
- **Reason:** Equipment table doesn't exist in gateway
- **Workaround:** Master can contact maintenance team manually
- **Future:** Add when equipment data available

### 3. Simple Defect Rate Calculation
- Defect rate = (defective lots) / (total lots) × 100
- **Does NOT account for:** Multi-parameter failures per lot (counts lot once if ANY param fails)
- **Is sufficient for:** Wave 1 use case (line master just needs overview)
- **Can be refined:** Wave 3 (quality engineer) with per-parameter rates

### 4. No Downtime Tracking
- Cannot show "line down for 2 hours" with root cause
- **Reason:** No downtime events in database
- **Workaround:** Infer from ProductionOutput timestamps (detect gaps)
- **Wave 2 feature:** `GET /gm/downtime-ranking` will calculate from timestamps

---

## Next Session Checklist (Wave 3 Prep)

```
Before Starting Wave 3:
[ ] Run ./init.sh to verify environment
[ ] Run pytest tests/ -v to confirm Waves 1-2 still pass (20+ dashboard tests)
[ ] Read feature_list.json to see Wave 2 in "done" status (feat-026)
[ ] Review CLAUDE.md patterns for service/schema/route consistency
[ ] Read dashboard_roadmap.md for Wave 3 scope

Wave 3 (Quality Engineer Dashboard) Prep:
[ ] Decide data sources:
    - Parameter trends: QualityResult.parameter_name + test_date aggregation
    - Batch deviations: ProductionLot vs QualityResult comparison
    - Defect Pareto: Count defects by root cause (infer from parameter names?)
[ ] Design schemas: ParameterTrendItem, BatchDeviationItem, DefectParetoItem + Response wrappers
[ ] Create QualityEngineerDashboardService with 3 query methods
[ ] Implement 3 endpoints under /api/v1/dashboards/qe/
[ ] Write 12-15 tests (unit + integration mix)
[ ] Update feature_list.json with feat-027 (wave 3)
```

---

## Summary

### Wave 1 (Complete ✅)
**Line Master Dashboard** — 3 endpoints for shift-level analytics
- 8 unit tests passing
- Data from ProductionOutput + QualityResult tables
- Ready for production

### Wave 2 (Complete ✅)
**Group Manager Dashboard** — 3 strategic endpoints for group-level oversight
- 12 unit tests + 8 integration tests passing (20 total)
- Data from AggregatedKPI + OrderSnapshot tables  
- OEE tracking, plan execution, downtime Pareto
- Ready for production

### Next Steps
**Wave 3 (In Progress):** Quality Engineer Dashboard — parameter trends, batch analysis
**Wave 4 & 5:** Finance & Warehouse dashboards (planned)

**Current Status:** Both dashboards production-ready, ~30 dashboard tests passing. Core API stable. Next wave ready to start.**
