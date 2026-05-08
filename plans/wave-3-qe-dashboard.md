# Wave 3: Quality Engineer Dashboard

## Context

Waves 1 (Line Master) and 2 (Group Manager) are complete with 20 passing tests. Wave 3 adds a Quality Engineer Dashboard under `/api/v1/dashboards/qe/` providing parameter-level quality analytics: trend charts with spec bands, batch deviation drill-down, and a Pareto chart for defect prioritization.

**User decisions:**
- Parameter trends: daily aggregation (avg + out-of-spec %) + spec limits from QualitySpec
- Batch analysis: only lots with deviations, with per-parameter deviation detail and magnitude
- Pareto: cumulative % + optional `?product_id=` filter

---

## Files to Create

| File | Purpose |
|------|---------|
| `app/schemas/qe_dashboard.py` | Pydantic response models |
| `app/services/qe_dashboard_service.py` | Business logic, 3 query methods |
| `app/routers/qe_dashboard.py` | 3 GET endpoints |
| `tests/unit/test_qe_dashboard_service.py` | 9 unit tests |
| `tests/integration/test_qe_dashboard_routes.py` | 6 integration tests |

Plus one-liner additions to `app/schemas/__init__.py`, `app/services/__init__.py`, `app/routers/__init__.py`, `app/main.py`.

---

## 1. Schemas (`app/schemas/qe_dashboard.py`)

All schemas: Pydantic v2 `ConfigDict(from_attributes=True)`, `Field(description="...")`, `Decimal` (not float), `from datetime import date as date_type`.

### Endpoint 1 — Parameter Trends

**`TrendDataPoint`** (one per day per parameter):
- `test_date: date_type`
- `avg_value: Decimal` — avg result_value for that day (4dp)
- `test_count: int` — total rows that day
- `out_of_spec_count: int` — count where `in_spec=False`
- `out_of_spec_pct: Decimal` — out_of_spec_count / test_count * 100 (2dp; 0 if no tests)
- `lower_limit: Optional[Decimal]` — from joined QualitySpec
- `upper_limit: Optional[Decimal]` — from joined QualitySpec

**`ParameterTrendItem`** (one per parameter):
- `parameter_name: str`
- `total_tests: int`, `total_out_of_spec: int`, `overall_out_of_spec_pct: Decimal`
- `trend: List[TrendDataPoint]` — ascending by date

**`ParameterTrendsResponse`**: `period_from`, `period_to`, `parameters: List[ParameterTrendItem]`

### Endpoint 2 — Batch Analysis

**`DeviationItem`** (one per failing QualityResult row):
- `parameter_name: str`
- `result_value: Decimal`
- `lower_limit: Optional[Decimal]`, `upper_limit: Optional[Decimal]`
- `deviation_magnitude: Decimal` — |result − breached limit|, 4dp; 0 if limits are None

**`BatchAnalysisItem`** (one per deviating lot):
- `lot_number: str`
- `product_name: Optional[str]`, `production_date: Optional[date_type]`, `shift: Optional[str]`
- `fail_count: int`
- `deviations: List[DeviationItem]`

**`BatchAnalysisResponse`**: `period_from`, `period_to`, `lot_count: int`, `lots: List[BatchAnalysisItem]`

### Endpoint 3 — Defect Pareto

**`ParetoItem`** (one per parameter):
- `parameter_name: str`
- `defect_count: int`, `total_tests: int`
- `defect_pct: Decimal` — 2dp
- `cumulative_pct: Decimal` — running sum ranked by defect_count DESC, 2dp

**`DefectParetoResponse`**: `period_from`, `period_to`, `product_id: Optional[UUID]`, `total_defects: int`, `parameters: List[ParetoItem]`

---

## 2. Service (`app/services/qe_dashboard_service.py`)

```python
class QualityEngineerDashboardService:
    def __init__(self, db: AsyncSession) -> None: self.db = db
```

### Method 1: `get_parameter_trends(date_from, date_to) → ParameterTrendsResponse`

**Single SQL query** (GROUP BY parameter_name + test_date):
```sql
SELECT qr.parameter_name, qr.test_date,
       AVG(qr.result_value) AS avg_value,
       COUNT(qr.id) AS test_count,
       SUM(CASE WHEN qr.in_spec = FALSE THEN 1 ELSE 0 END) AS out_of_spec_count,
       MAX(qs.lower_limit) AS lower_limit,
       MAX(qs.upper_limit) AS upper_limit
FROM quality_results qr
LEFT JOIN quality_specs qs ON qs.id = qr.quality_spec_id
WHERE qr.test_date BETWEEN :date_from AND :date_to
GROUP BY qr.parameter_name, qr.test_date
ORDER BY qr.parameter_name, qr.test_date ASC
```

**SQLAlchemy:** `isouter=True` on join (quality_spec_id is nullable). Use `func.sum(case(...))` for out_of_spec_count. `MAX()` for limits collapses to the single spec value per (param, day).

**Python post-processing:** Group rows by parameter_name into dict → build TrendDataPoint list → compute running totals for ParameterTrendItem.

**Decimal precision:** `avg_value` → 4dp; `out_of_spec_pct` → 2dp.

---

### Method 2: `get_batch_analysis(date_from, date_to) → BatchAnalysisResponse`

**Two-pass approach** (avoids cross-product from multi-snapshot ProductionOutput):

**Pass 1** — fetch failing QualityResult rows + spec limits:
```sql
SELECT qr.lot_number, qr.parameter_name, qr.result_value,
       qs.lower_limit, qs.upper_limit
FROM quality_results qr
LEFT JOIN quality_specs qs ON qs.id = qr.quality_spec_id
WHERE qr.test_date BETWEEN :date_from AND :date_to AND qr.in_spec = FALSE
ORDER BY qr.lot_number
```

Collect in Python: `lot_to_deviations: Dict[str, List[DeviationItem]]`, `failing_lot_numbers: set[str]`.

Deviation magnitude: `result − upper_limit` if over-spec, `lower_limit − result` if under-spec, `0.00` if limits are None.

**Pass 2** — production metadata (only if failing_lot_numbers non-empty):
```sql
SELECT lot_number, product_name, production_date, shift
FROM production_output
WHERE lot_number IN :lot_numbers
ORDER BY production_date DESC
```
Dedup in Python (first-seen-wins after DESC sort = latest snapshot).

**Assembly:** Iterate lot_to_deviations, look up Pass 2 results, build BatchAnalysisItem. Sort lots by `production_date` ascending (None last).

---

### Method 3: `get_defect_pareto(date_from, date_to, product_id) → DefectParetoResponse`

**Single SQL query** (GROUP BY parameter_name):
```sql
SELECT qr.parameter_name,
       COUNT(qr.id) AS total_tests,
       SUM(CASE WHEN qr.in_spec = FALSE THEN 1 ELSE 0 END) AS defect_count
FROM quality_results qr
WHERE qr.test_date BETWEEN :date_from AND :date_to
  [AND qr.product_id = :product_id]
GROUP BY qr.parameter_name
ORDER BY defect_count DESC
```

**Python post-processing for cumulative_pct:** After sorted rows, iterate maintaining `running_sum`. For each row: `running_sum += defect_count`; `cumulative_pct = running_sum / grand_total * 100` (guard divide-by-zero). Quantize to 2dp.

All 3 methods end with `logger.info("event_name", date_from=..., date_to=..., ...)`.

---

## 3. Router (`app/routers/qe_dashboard.py`)

```python
router = APIRouter(prefix="/api/v1/dashboards/qe", tags=["Quality Engineer Dashboard"])

async def get_service(db: AsyncSession = Depends(get_db)) -> QualityEngineerDashboardService:
    return QualityEngineerDashboardService(db)
```

**Endpoints:**

| Path | Params | Response |
|------|--------|----------|
| `GET /parameter-trends` | `date_from` (default: today-30), `date_to` (default: today) | `ParameterTrendsResponse` |
| `GET /batch-analysis` | `date_from`, `date_to` | `BatchAnalysisResponse` |
| `GET /defect-pareto` | `date_from`, `date_to`, `product_id: Optional[UUID] = None` | `DefectParetoResponse` |

All dates use `Query(default_factory=lambda: date.today() - timedelta(days=30))`.

---

## 4. Unit Tests (`tests/unit/test_qe_dashboard_service.py`)

### Fixture: `sample_qe_data(session)`

Creates:
- **2 QualitySpec** rows: `spec_ph` (pH, lower=6.5, upper=7.5), `spec_viscosity` (viscosity, lower=100, upper=200) — both for `pid_a`
- **8 QualityResult** rows:
  - Day `today-5`: Lot-001 pH=7.0 ✓, Lot-001 viscosity=150 ✓, Lot-002 pH=8.5 ✗ (>7.5)
  - Day `today-3`: Lot-003 pH=6.0 ✗ (<6.5), Lot-003 viscosity=250 ✗ (>200), Lot-004 pH=7.2 ✓, Lot-004 viscosity=180 ✓
  - Day `today-60`: Lot-OLD pH=5.0 ✗ (outside 30-day window)
- **4 ProductionOutput** rows: Lot-001..004 with product names Alpha/Beta, production_date, shift

### Tests (9 total)

| # | Test | Assertion |
|---|------|-----------|
| 1 | `test_parameter_trends_returns_both_parameters` | 2 parameters returned (pH + viscosity) |
| 2 | `test_parameter_trends_daily_out_of_spec_pct` | pH on today-5: test_count=2, out_of_spec=1, pct=50.00 |
| 3 | `test_parameter_trends_spec_limits_attached` | lower_limit=6.5, upper_limit=7.5 on pH trend points |
| 4 | `test_parameter_trends_excludes_old_records` | pH total_tests=4 (not 5; today-60 excluded) |
| 5 | `test_batch_analysis_only_lots_with_deviations` | lot_count=2; Lot-001 and Lot-004 absent; Lot-002, Lot-003 present |
| 6 | `test_batch_analysis_deviation_magnitude_upper_breach` | Lot-002 pH deviation_magnitude=Decimal("1.0000") (8.5−7.5) |
| 7 | `test_batch_analysis_production_metadata_attached` | Lot-003: product_name="Beta", shift="Shift 1" |
| 8 | `test_defect_pareto_ranked_descending_and_cumulative` | pH first (2 defects), viscosity second (1); cumulative_pct non-decreasing; last=100.00 |
| 9 | `test_batch_analysis_empty_when_all_in_spec` | Insert only in-spec rows → `lots==[]`, `lot_count==0` |

---

## 5. Integration Tests (`tests/integration/test_qe_dashboard_routes.py`)

Local fixture inserts compact dataset: 2 QualitySpec rows, 6 QualityResult rows (2 in-spec Lot-A, 2 out-of-spec Lot-B, 2 for product pid_b), 2 ProductionOutput rows.

| # | Test | Key Assertions |
|---|------|---------------|
| 1 | `test_parameter_trends_returns_200` | status=200, `parameters` key present, len≥1 |
| 2 | `test_parameter_trends_decimal_as_string` | `avg_value` and `out_of_spec_pct` are strings in JSON |
| 3 | `test_batch_analysis_only_deviated_lots` | status=200, all lots have `fail_count≥1`, `deviations` key present |
| 4 | `test_defect_pareto_returns_200` | status=200, `parameters`/`total_defects`/`product_id` keys; `product_id` is null |
| 5 | `test_defect_pareto_product_filter` | `?product_id={pid_a}` → `data["product_id"]==str(pid_a)`, no pid_b contamination |
| 6 | `test_all_endpoints_empty_database` | All 3 endpoints return 200 with empty lists, total_defects=0 |

---

## 6. Integration File Changes

### `app/schemas/__init__.py`
Add import block for all 8 schema classes from `qe_dashboard`. Add all to `__all__`.

### `app/services/__init__.py`
Add `from app.services.qe_dashboard_service import QualityEngineerDashboardService`. Add to `__all__`.

### `app/routers/__init__.py`
Add `from app.routers.qe_dashboard import router as qe_dashboard_router`. Add to `__all__`.

### `app/main.py`
Add `qe_dashboard_router` to import from `app.routers`. Add `app.include_router(qe_dashboard_router)` after gm router registration.

---

## 7. Key Design Decisions

- **MAX() for spec limits in GROUP BY** (parameter-trends): all rows for same (param, day) share one spec; MAX collapses correctly. LEFT JOIN ensures spec-less records still appear.
- **Two-pass for batch-analysis**: avoids cross-product with multi-snapshot ProductionOutput. Pass 1 = failing quality rows, Pass 2 = production metadata for those lots only.
- **Python cumulative_pct** (Pareto): simpler than SQL window functions, portable, consistent with existing downtime-ranking pattern.
- **feat-027** to be added to `feature_list.json` once complete.

---

## 8. Verification

```bash
# Run all tests (should stay green + 15 new passing)
pytest tests/ -v

# Type check new files
mypy app/schemas/qe_dashboard.py app/services/qe_dashboard_service.py app/routers/qe_dashboard.py --ignore-missing-imports

# Manual test
uvicorn app.main:app --reload
# Open /docs → QE Dashboard section, test each endpoint with no params
# Verify /qe/defect-pareto?product_id=<uuid> returns filtered results
```

**Expected test count after Wave 3:** ~149 existing + 15 new = ~164 passing.
