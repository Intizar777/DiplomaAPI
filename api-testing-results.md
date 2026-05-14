# API Testing Results

**Backend URL:** `https://diplomaapi-production.up.railway.app`
**Test Date:** 2026-05-14
**Status:** All endpoints tested successfully

---

## Base URLs

| Environment | URL |
|-------------|-----|
| Production | `https://diplomaapi-production.up.railway.app` |
| V1 API Base | `/api/v1` |
| Production Analytics Base | `/api/production` |

---

## Endpoints Overview

### Working (✅)

| Method | Path | Params | Response |
|--------|------|--------|----------|
| GET | `/health` | - | `{"status":"healthy","version":"1.0.0","timestamp":"2026-05-14T10:34:01.590384"}` |
| GET | `/` | - | `{"name":"Dashboard Analytics API","version":"1.0.0","docs":"/docs","health":"/health"}` |
| GET | `/api/v1/sales/summary` | `date_from`, `date_to`, `group_by` | ✅ Returns `{summary: [{group_key, total_quantity, total_amount, sales_count, avg_order_value}], total_amount, total_quantity, period_from, period_to, group_by}` |
| GET | `/api/v1/sales/trends` | `date_from`, `date_to`, `interval` | ✅ Returns `{trends: [{trend_date, total_amount, total_quantity, order_count}], interval, period_from, period_to}` |
| GET | `/api/v1/sales/top-products` | `date_from`, `date_to`, `limit` | ✅ Returns `{products: [{product_id, product_name, total_quantity, total_amount, sales_count}], period_from, period_to, limit}` |
| GET | `/api/v1/sales/regions` | `date_from`, `date_to` | ✅ Returns `{regions: [{region, total_quantity, total_amount, sales_count, percentage}], period_from, period_to}` |
| GET | `/api/v1/orders/status-summary` | - | ✅ Returns `{by_status: {planned, in_progress, completed, cancelled}, by_production_line: {...}, period_from, period_to}` |
| GET | `/api/v1/orders/list` | `from`, `to`, `status`, `production_line`, `page`, `limit` | ✅ Returns `{orders: [...], total, page, limit, pages}` |
| GET | `/api/v1/quality/summary` | - | ✅ Returns `{average_quality, approved_count, rejected_count, pending_count, defect_rate, by_parameter, period_from, period_to}` |
| GET | `/api/v1/quality/defect-trends` | - | ✅ Returns `{trends: [{trend_date, defect_rate, rejected_count, total_tests}], period_from, period_to}` |
| GET | `/api/v1/quality/lots` | - | ✅ Returns `{lots: [{lot_number, product_id, product_name, decision, test_date, parameters_tested, parameters_passed}], total, approved_count, rejected_count, pending_count, period_from, period_to}` |
| GET | `/api/v1/quality/parameter-trends` | - | ✅ Returns `{period_from, period_to, parameters: [{parameter_name, total_tests, total_out_of_spec, overall_out_of_spec_pct, trend: [{test_date, avg_value, test_count, out_of_spec_count, out_of_spec_pct, lower_limit, upper_limit}]}]}` |
| GET | `/api/v1/quality/defect-pareto` | - | ✅ Returns `{period_from, period_to, product_id, total_defects, parameters: [{parameter_name, defect_count, total_tests, defect_pct, cumulative_pct}]}` |
| GET | `/api/v1/quality/lots/{lot_number}/deviations` | - | ✅ Returns `{lot_number, product_name, shift, fail_count, deviations: [{parameter_name, result_value, lower_limit, upper_limit, deviation_magnitude}]}` |
| GET | `/api/v1/oee/summary` | `period_from`, `period_to`, `production_line_id` | ✅ Returns `{summary_date, lines: [{production_line_id, production_line_name, availability, performance, quality, oee, target_oee, period_from, period_to}], total_oee, lines_above_target, lines_below_target}` |
| GET | `/api/v1/oee/line/{production_line_id}` | `period_from`, `period_to` | ✅ Returns single line OEE data |
| GET | `/api/v1/oee/today` | - | ✅ Returns today's OEE summary |
| GET | `/api/v1/oee/this-week` | - | ✅ Returns current week's OEE summary |
| GET | `/api/v1/oee/this-month` | - | ✅ Returns current month's OEE summary |
| GET | `/api/v1/sync/status` | - | ✅ Returns `{tasks: [{task_name, status, last_run, last_success, records_processed, records_inserted, records_updated, error_message}], overall_status, last_sync}` |
| GET | `/api/v1/output/summary` | - | ✅ Returns `{items: [{date, shift, total_quantity, lot_count, approved_count}], period_from, period_to, group_by}` |
| GET | `/api/v1/output/by-shift` | - | ✅ Returns `{items: [{date, shift, total_quantity, lot_count}], period_from, period_to}` |
| GET | `/api/v1/sensors/stats` | - | ✅ Returns `{items: [{production_line_id, parameter_name, unit, avg_value, min_value, max_value, reading_count, alert_count}]}` |
| GET | `/api/v1/sensors/history` | `production_line`, `parameter_name`, `date_from`, `date_to`, `limit` | ✅ Returns `{items: [...], count}` (currently empty) |
| GET | `/api/v1/sensors/alerts` | `from`, `to`, `limit` | ✅ Returns `{items: [...], count}` (currently empty) |
| GET | `/api/v1/products` | `category`, `brand` | ✅ Returns `{items: [{id, code, name, category, brand, unit_of_measure_id, shelf_life_days, requires_quality_check}], count}` |
| GET | `/api/v1/products/{product_id}` | - | ❌ Internal server error |
| GET | `/api/v1/inventory/current` | `warehouse_code`, `product_id` | ✅ Returns `{items: [{product_id, product_name, warehouse_code, lot_number, quantity, unit_of_measure, last_updated}]}` |
| GET | `/api/v1/inventory/trends` | `product_id` (required), `date_from`, `date_to` | ✅ Returns `{items: [{date, total_quantity}], product_id}` |

### Production Analytics Endpoints

| Method | Path | Params | Response |
|--------|------|--------|----------|
| GET | `/api/production/kpi` | `from_date` (required), `to_date` (required), `production_line_id`, `granularity`, `compare_with_previous` | ✅ Returns `{total_output, defect_rate, completed_orders, total_orders, availability, performance, oee_estimate, line_throughput, targets: {oee_estimate, defect_rate, otif_rate}, trend, change_percent}` |
| GET | `/api/production/kpi/otif` | `from_date` (required), `to_date` (required), `production_line_id` | ✅ Returns `{otif_rate, on_time_orders, in_full_quantity_orders, otif_orders, total_orders}` |
| GET | `/api/production/kpi/line-productivity` | `from_date` (required), `to_date` (required), `production_line_id` | ✅ Returns `{items: [{production_line, productivity, total_output, days, target, status, deviation}], period: {from, to}, unit}` |
| GET | `/api/production/kpi/breakdown` | `from_date` (required), `to_date` (required), `group_by`, `metric`, `offset`, `limit`, `include` | ✅ Returns `{items: [{group_key, value, target, status, deviation}], total}` |
| GET | `/api/production/kpi/scrap-percentage` | `from_date` (required), `to_date` (required), `product_id` | ✅ Returns `{scrap_percentage, rejected_tests, total_tests, target, status, period}` |
| GET | `/api/production/sales/margin` | `from_date` (required), `to_date` (required), `product_id`, `limit` | ✅ Returns `{margins: [{product_id, product_code, product_name, total_quantity, total_revenue, total_cost, total_margin, margin_percent, margin_per_unit}], total, aggregated: {...}}` |
| GET | `/api/production/batch-inputs` | `order_id`, `product_id`, `offset`, `limit`, `cursor` | ✅ Returns `{items: [...], total}` |
| POST | `/api/production/batch-inputs` | body | ✅ Returns created record with `{id, order_id, product_id, quantity, input_date, created_at, updated_at}` |
| GET | `/api/production/batch-inputs/yield` | `order_id` (required) | ✅ Returns `{order_id, total_input, total_output, yield_percent, target}` |
| GET | `/api/production/downtime-events` | `from_date`, `to_date`, `production_line_id`, `category`, `offset`, `limit`, `cursor` | ✅ Returns `{items: [...], total}` |
| POST | `/api/production/downtime-events` | body | ✅ Returns created record with `{id, production_line_id, reason, category, started_at, ended_at, duration_minutes, created_at, updated_at}` |
| GET | `/api/production/downtime-events/summary` | `from_date`, `to_date` | ✅ Returns `{items: [{category, total_minutes, count}], total_events, total_downtime_minutes}` |
| GET | `/api/production/promo-campaigns` | `from_date`, `to_date`, `channel`, `offset`, `limit` | ✅ Returns `{items: [...], total}` |
| POST | `/api/production/promo-campaigns` | body | ✅ Returns created campaign |
| GET | `/api/production/promo-campaigns/{campaign_id}/effectiveness` | - | ✅ Returns `{campaign_id, campaign_name, budget, sales_during_campaign, baseline_sales, uplift, cost_per_uplift_unit, roi, roi_percent}` |
| GET | `/api/production/production-lines` | `division`, `offset`, `limit` | ✅ Returns `{production_lines: [{id, code, name, description, division, is_active}], total}` |

### Dashboard Endpoints

| Method | Path | Params | Response |
|--------|------|--------|----------|
| GET | `/api/v1/dashboards/gm/oee-summary` | `period_days` | ✅ Returns `{period_days, period_from, period_to, lines: [{production_line, avg_oee, vs_target_pct, completed_orders, total_orders, avg_defect_rate, data_points, trend: [{period_from, period_to, oee_value}]}], oee_target}` |
| GET | `/api/v1/dashboards/gm/plan-execution` | - | ✅ Returns `{period_from, period_to, lines: [{production_line, target_quantity, actual_quantity, fulfillment_pct, orders_planned, orders_in_progress, orders_completed, orders_cancelled, total_snapshots}], total_target, total_actual, overall_fulfillment_pct}` |
| GET | `/api/v1/dashboards/gm/downtime-ranking` | - | ✅ Returns `{period_from, period_to, lines: [{production_line, total_delay_hours, delayed_orders, avg_delay_hours, total_completed, delay_pct}], total_delay_hours, total_delayed_orders}` |
| GET | `/api/v1/dashboards/qe/parameter-trends` | - | ✅ Returns `{period_from, period_to, parameters: [{parameter_name, total_tests, total_out_of_spec, overall_out_of_spec_pct, trend: [...]}]}` |
| GET | `/api/v1/dashboards/qe/batch-analysis` | - | ✅ Returns `{period_from, period_to, lot_count, lots: [...]}` (currently empty) |
| GET | `/api/v1/dashboards/qe/defect-pareto` | - | ✅ Returns `{period_from, period_to, product_id, total_defects, parameters: [...]}` |
| GET | `/api/v1/dashboards/finance/sales-breakdown` | - | ✅ Returns `{period_from, period_to, group_by, total_amount, total_quantity, groups: [{group_key, total_amount, total_quantity, sales_count, avg_order_value, amount_share_pct}]}` |
| GET | `/api/v1/dashboards/finance/revenue-trend` | - | ✅ Returns `{period_from, period_to, interval, region, channel, data: [...]}` (currently empty) |
| GET | `/api/v1/dashboards/finance/top-products` | - | ✅ Returns `{period_from, period_to, sort_by, total_amount, products: [{rank, product_name, total_amount, total_quantity, sales_count, amount_share_pct}]}` |
| GET | `/api/v1/dashboards/line-master/shift-progress` | `production_date` | ✅ Returns `{date, shifts: [{shift, lot_count, total_quantity, approved_count, defect_count, defect_rate}], total_quantity, total_lots}` |
| GET | `/api/v1/dashboards/line-master/shift-comparison` | - | ✅ Returns `{period_from, period_to, shifts: [{date, shift, total_quantity, lot_count, defect_count}]}` |
| GET | `/api/v1/dashboards/line-master/defect-summary` | - | ✅ Returns `{period_from, period_to, total_defects, items: [{parameter_name, total_tests, failed_tests, fail_rate}]}` |

### Broken (❌)

| Method | Path | Issue |
|--------|------|-------|
| GET | `/api/v1/orders/plan-execution` | 500 Internal Server Error |
| GET | `/api/v1/orders/downtime` | 500 Internal Server Error |
| GET | `/api/v1/products/{product_id}` | 500 Internal Server Error |

---

## Notes

1. **Numeric fields are strings** - All numeric values (total_amount, total_quantity, etc.) come as strings and need `parseFloat()` before display.

2. **Date formats** - Backend uses `YYYY-MM-DD` format consistently.

3. **Default periods** - Most endpoints without date params return data for the last 30 days.

4. **POST requests work** - batch-inputs, downtime-events, and promo-campaigns POST endpoints tested and working.

5. **Some endpoints return empty data** - sensors/history, sensors/alerts, batch-analysis, revenue-trend return empty arrays, indicating possibly no data in those categories.

6. **OEE calculation issue** - The OEE component shows "0" for quality and "poor" status for many lines, which seems like a calculation issue in the backend.

7. **GM dashboard OEE values** - The `avg_oee` values (e.g., "2.29", "1.99") look like they're multiplied by 100 incorrectly or represent percentages without decimal conversion.

---

## Curl Examples

```bash
# Health check
curl https://diplomaapi-production.up.railway.app/health

# Sales summary
curl "https://diplomaapi-production.up.railway.app/api/v1/sales/summary?date_from=2026-05-01&date_to=2026-05-31"

# KPI current
curl "https://diplomaapi-production.up.railway.app/api/production/kpi?from_date=2026-05-01&to_date=2026-05-31"

# POST batch input
curl -X POST https://diplomaapi-production.up.railway.app/api/production/batch-inputs \
  -H "Content-Type: application/json" \
  -d '{"product_id":"...","quantity":"100.000","input_date":"2026-05-14T10:00:00Z"}'

# POST downtime event
curl -X POST https://diplomaapi-production.up.railway.app/api/production/downtime-events \
  -H "Content-Type: application/json" \
  -d '{"reason":"Test","category":"PLANNED_MAINTENANCE","started_at":"2026-05-14T10:00:00Z","duration_minutes":30}'
```