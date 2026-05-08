# Testing Cron Triggers

Guide for testing data synchronization and cron job execution.

---

## Quick Start: Reset & Test

### Step 1: Reset Database

```bash
python scripts/reset_database.py
```

**What happens:**
- ✓ Deletes ALL data from all tables
- ✓ Requires confirmation (type `yes`)
- ✓ Logs truncated tables
- ✓ Ready for fresh sync

**Output:**
```
============================================================
⚠️  DATABASE RESET UTILITY
============================================================

This will DELETE ALL DATA from:
  - Production data (ProductionOutput)
  - Quality results
  - Inventory, Orders, Sales
  - Sensor readings
  - Sync logs
  - All aggregated data (KPI, Sales)

Type 'yes' to confirm reset: yes

============================================================
✓ DATABASE RESET COMPLETE
============================================================

All data has been deleted.
Next cron run will perform full sync from Gateway.
```

### Step 2: Trigger Sync

Manual sync via API:

```bash
# Trigger all tasks
curl -X POST http://localhost:8000/api/v1/sync/trigger

# Or specific task
curl -X POST http://localhost:8000/api/v1/sync/trigger/output
```

Or wait for next scheduled cron run:
```
Minute 0:  kpi sync
Minute 5:  sales sync
Minute 10: orders sync
Minute 15: quality sync
Minute 20: products sync
Minute 25: output sync
Minute 30: sensors sync
Minute 35: inventory sync
Minute 40: personnel sync
```

### Step 3: Verify Data

```bash
# Check sync status
curl http://localhost:8000/api/v1/sync/status | jq .

# Expected: All tasks show COMPLETED status
```

---

## Testing Workflow

### 1. Test New Sync Task

```bash
# Reset
python scripts/reset_database.py

# Trigger specific task
curl -X POST http://localhost:8000/api/v1/sync/trigger/output

# Verify data
psql $DATABASE_URL -c "SELECT COUNT(*) FROM ProductionOutput"
```

### 2. Test Full Sync Pipeline

```bash
# Reset
python scripts/reset_database.py

# Wait for 00:00, 00:05, 00:10, ... (cron runs)
# OR trigger all manually
curl -X POST http://localhost:8000/api/v1/sync/trigger

# Check all tables populated
curl http://localhost:8000/api/v1/sync/status
```

### 3. Test Data Cleanup

```bash
# Setup: Run sync to populate data
python scripts/reset_database.py
curl -X POST http://localhost:8000/api/v1/sync/trigger

# Trigger cleanup
curl -X POST http://localhost:8000/api/v1/sync/cleanup

# Verify old data removed (nothing removed since data is fresh)
```

---

## Cron Schedule Reference

Default schedule (every hour):

| Minute | Task | Source | Records |
|--------|------|--------|---------|
| 00 | KPI | Gateway | Last 30 days |
| 05 | Sales | Gateway | Last 30 days |
| 10 | Orders | Gateway | Last 1 day |
| 15 | Quality | Gateway | Last 1 day |
| 20 | Products | Gateway | Full upsert |
| 25 | Output | Gateway | Last 1 day |
| 30 | Sensors | Gateway | Last 1 day |
| 35 | Inventory | Gateway | Full snapshot |
| 40 | Personnel | Gateway | Full upsert |

**Next run:** Every hour at these intervals (e.g., 1:00, 1:05, 1:10, ...)

---

## Monitoring Sync

### View Logs

```bash
# Real-time sync logs
tail -f logs/*.log | grep -i sync

# Structured log output
cat logs/sync.log | jq 'select(.event | contains("sync"))'
```

### Check Sync Status

```bash
curl http://localhost:8000/api/v1/sync/status | jq '.tasks[] | {task_name, status, last_run, records_processed}'
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "Sync already running" | Wait 5-10 min or check cron schedule |
| Empty tables after reset | Trigger sync manually or wait for cron |
| Gateway connection error | Verify `GATEWAY_URL` in `.env` |
| Database connection timeout | Check PostgreSQL is running |

---

## Advanced: Test Incremental vs Full Sync

### Test Full Sync (Initial)

```bash
# First run is always full
python scripts/reset_database.py
curl -X POST http://localhost:8000/api/v1/sync/trigger/kpi

# Check logs
tail logs/*.log | grep "full_sync\|initial_sync_detected"
```

### Test Incremental Sync

```bash
# Reset
python scripts/reset_database.py

# First run (full sync - populates data)
curl -X POST http://localhost:8000/api/v1/sync/trigger/kpi

# Second run (incremental - fetches only new/changed)
curl -X POST http://localhost:8000/api/v1/sync/trigger/kpi

# Check logs - second run should say "incremental_sync"
tail logs/*.log | grep "incremental_sync"
```

---

## Performance Testing

### Measure Sync Time

```bash
# Time a single sync
time curl -X POST http://localhost:8000/api/v1/sync/trigger/output

# Results show:
# real    0m2.345s
# user    0m0.100s
# sys     0m0.050s
```

### Measure Data Volume

```bash
# Before sync
python scripts/reset_database.py

# After sync
curl -X POST http://localhost:8000/api/v1/sync/trigger

# Check counts
psql $DATABASE_URL << EOF
SELECT 'ProductionOutput' as table_name, COUNT(*) as rows FROM ProductionOutput
UNION ALL
SELECT 'QualityResult', COUNT(*) FROM QualityResult
UNION ALL
SELECT 'ProductionLine', COUNT(*) FROM ProductionLine;
EOF
```

---

## Related

- [Data Cleanup Guide](data-cleanup.md)
- [Architecture: Sync & Data Flow](architecture.md#sync)
- [CLAUDE.md: Cron Rules](../CLAUDE.md)
