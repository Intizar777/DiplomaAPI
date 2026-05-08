# Stopping Sync Tasks

Guide for stopping running synchronization and cleanup tasks.

---

## Quick Commands

### Stop ALL Running Tasks

```bash
curl -X POST http://localhost:8000/api/v1/sync/stop
```

**Response:**
```json
{
  "message": "Stopped 5 task(s)",
  "stopped": ["kpi", "sales", "orders", "quality", "products"],
  "status": "ok"
}
```

### Stop Specific Task

```bash
curl -X POST http://localhost:8000/api/v1/sync/stop/output
```

**Response:**
```json
{
  "message": "Task 'output' stopped",
  "stopped": ["output"],
  "status": "ok"
}
```

### Stop Cleanup Task

```bash
curl -X POST http://localhost:8000/api/v1/sync/stop/cleanup
```

---

## View Running Tasks

```bash
curl http://localhost:8000/api/v1/sync/running | jq .
```

**Response:**
```json
{
  "running_tasks": [
    {
      "name": "kpi",
      "done": false,
      "cancelled": false
    },
    {
      "name": "sales",
      "done": false,
      "cancelled": false
    }
  ],
  "count": 2
}
```

---

## Workflow Examples

### Example 1: Start Sync, Then Stop

```bash
# 1. Start all tasks
curl -X POST http://localhost:8000/api/v1/sync/trigger

# 2. Check what's running
curl http://localhost:8000/api/v1/sync/running

# 3. Realize we need to stop
curl -X POST http://localhost:8000/api/v1/sync/stop

# 4. Verify stopped
curl http://localhost:8000/api/v1/sync/running
```

### Example 2: Stop Only One Task

```bash
# Start all
curl -X POST http://localhost:8000/api/v1/sync/trigger

# Only stop output sync (expensive query)
curl -X POST http://localhost:8000/api/v1/sync/stop/output

# Others continue running
curl http://localhost:8000/api/v1/sync/running
```

### Example 3: Emergency Cleanup Abort

```bash
# Trigger cleanup (long running)
curl -X POST http://localhost:8000/api/v1/sync/cleanup

# Decide to cancel
curl -X POST http://localhost:8000/api/v1/sync/stop/cleanup

# Verify
curl http://localhost:8000/api/v1/sync/running
```

---

## API Endpoints

### Stop All Tasks

```
POST /api/v1/sync/stop
```

**Response codes:**
- `200` — Tasks stopped successfully
- `200` with `stopped=[]` — No tasks running

---

### Stop Specific Task

```
POST /api/v1/sync/stop/{task_name}
```

**Path Parameters:**
- `task_name` — Task to stop (kpi, sales, orders, quality, products, output, sensors, inventory, personnel, cleanup)

**Response codes:**
- `200` — Task stopped
- `200` with `status=not_found` — Task not running
- `200` with `status=completed` — Task already finished

---

### Get Running Tasks

```
GET /api/v1/sync/running
```

**Response:**
```json
{
  "running_tasks": [
    {
      "name": "string",
      "done": "boolean",
      "cancelled": "boolean"
    }
  ],
  "count": "number"
}
```

---

## Behavior Details

### What Happens When You Stop?

1. **Task is cancelled** — asyncio.Task.cancel() is called
2. **Task removed from tracker** — No longer appears in /running
3. **Graceful cleanup** — Pending database operations are rolled back
4. **Log entry created** — "task_cancelled" event logged

### Important Notes

- ✅ Stopping is **immediate** — no graceful shutdown period
- ✅ Partial data **may be committed** — depends on transaction state
- ✅ Safe to stop — Won't corrupt database due to FK constraints
- ✅ Can restart — Rerun /trigger after stopping

### Recovery After Stop

If you stop a sync task mid-way:

```bash
# Check what happened
curl http://localhost:8000/api/v1/sync/status | jq '.tasks[] | select(.task_name=="output")'

# Restart if needed
curl -X POST http://localhost:8000/api/v1/sync/trigger/output
```

---

## Common Scenarios

### Scenario: Sync is Taking Too Long

```bash
# Check running tasks
curl http://localhost:8000/api/v1/sync/running

# If output sync is slow, stop it
curl -X POST http://localhost:8000/api/v1/sync/stop/output

# Resume later
curl -X POST http://localhost:8000/api/v1/sync/trigger/output
```

### Scenario: Wrong Data Sync Triggered

```bash
# Realize mistake immediately
curl -X POST http://localhost:8000/api/v1/sync/stop

# Check logs to see what happened
tail logs/sync.log | grep "task_cancelled"

# Reset database if needed
python scripts/reset_database.py
```

### Scenario: Database Maintenance

```bash
# Need to perform maintenance
# 1. Stop all running tasks
curl -X POST http://localhost:8000/api/v1/sync/stop

# 2. Do maintenance (backups, repairs, etc.)
# ...

# 3. Resume syncs
curl -X POST http://localhost:8000/api/v1/sync/trigger
```

---

## Monitoring & Debugging

### View Cancelled Tasks in Logs

```bash
grep "task_cancelled" logs/*.log | jq .
```

**Example output:**
```json
{
  "event": "task_cancelled",
  "task_name": "output",
  "timestamp": "2026-05-08T23:10:45Z"
}
```

### Check Task Status After Stopping

```bash
# View status of all tasks
curl http://localhost:8000/api/v1/sync/status | jq '.tasks'

# Tasks that were stopped will show:
# - status: "failed" or last status before cancel
# - records_processed: whatever was done before cancel
```

---

## Related

- [Testing Cron Triggers](testing-cron-triggers.md)
- [Data Cleanup](data-cleanup.md)
- [Architecture: Sync & Data Flow](architecture.md#sync)
