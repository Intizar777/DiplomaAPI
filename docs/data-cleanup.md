# Data Cleanup Guide

## Overview

Data cleanup removes old records based on retention policy defined in `.env` via `RETENTION_DAYS` setting.

---

## Method 1: API Endpoint (Recommended)

### Trigger Cleanup via REST API

```bash
curl -X POST http://localhost:8000/api/v1/sync/cleanup
```

**Response:**
```json
{
  "message": "Data cleanup completed successfully",
  "status": "completed"
}
```

**Error Response (if already running):**
```json
{
  "message": "Cleanup task is already running",
  "status": "running"
}
```

### What Gets Deleted

Records **older than** `RETENTION_DAYS` from these tables:

| Table | Purpose |
|-------|---------|
| `OrderSnapshot` | Order snapshots from Gateway |
| `QualityResult` | Quality test results |
| `ProductionOutput` | Line production data |
| `SensorReading` | Equipment sensor data |
| `InventorySnapshot` | Warehouse inventory |
| `SaleRecord` | Raw sales records |
| `SyncLog` | Sync task logs |

### Configuration

Set in `.env`:
```bash
RETENTION_DAYS=90  # Keep last 90 days of data
```

---

## Method 2: Command Line Script

### Run Cleanup Synchronously

```bash
python scripts/cleanup_data.py
```

**Exit Codes:**
- `0` — Cleanup succeeded
- `1` — Cleanup failed

---

## Monitoring

### Check Cleanup Logs

View structured logs for cleanup operations:
```bash
grep "cleanup" logs/*.log | jq .
```

### Typical Log Output

**Success:**
```json
{
  "event": "cleanup_task_completed",
  "task": "cleanup_old_data",
  "orders_deleted": 125,
  "quality_deleted": 340,
  "output_deleted": 89,
  "sensors_deleted": 456,
  "inventory_deleted": 12,
  "sales_raw_deleted": 203,
  "logs_deleted": 5
}
```

**Error:**
```json
{
  "event": "cleanup_task_failed",
  "task": "cleanup_old_data",
  "error_type": "DatabaseError",
  "error_message": "Connection refused"
}
```

---

## Best Practices

1. **Monitor Disk Space** — Cleanup frees up database storage
2. **Run During Off-Peak** — Trigger via API/script during low-traffic hours
3. **Verify Success** — Check logs and disk usage after cleanup
4. **Set Appropriate Retention** — Balance compliance vs. historical data needs:
   - `30` days: Minimal storage, recent data only
   - `90` days: Standard (DEFAULT)
   - `180` days: Long-term analytics
   - `365` days: Full year retention
5. **Check Error Logs** — Verify each cleanup completes successfully

---

## Troubleshooting

### "Cleanup task is already running"
Another cleanup is in progress. Wait 5-10 minutes or check logs.

### "Foreign key constraint violation"
Data has dependencies. Ensure `on_delete=CASCADE` is set in related models.

### Database connection timeout
Check `.env` `DATABASE_URL` and ensure PostgreSQL is running.

---

## Related

- [Architecture: Sync & Data Flow](architecture.md#sync)
- [Configuration: .env Settings](../README.md#configuration)
- [Monitoring: Logs & Metrics](monitoring.md)
