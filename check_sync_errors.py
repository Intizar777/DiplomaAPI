import asyncio
from sqlalchemy import select, desc
from app.database import AsyncSessionLocal
from app.models import SyncLog, SyncStatus

async def check_sync_errors():
    """Check detailed sync error logs."""
    async with AsyncSessionLocal() as db:
        # Get recent failed sync logs with full error details
        query = select(SyncLog).where(
            SyncLog.status == SyncStatus.FAILED.value
        ).order_by(desc(SyncLog.started_at)).limit(10)
        
        result = await db.execute(query)
        failed_logs = result.scalars().all()
        
        print(f"Recent failed sync logs:")
        print("-" * 100)
        for log in failed_logs:
            print(f"\nTask: {log.task_name}")
            print(f"Started: {log.started_at}")
            print(f"Completed: {log.completed_at}")
            print(f"Error: {log.error_message}")
            print(f"Records processed: {log.records_processed}")
            print("-" * 100)

if __name__ == "__main__":
    asyncio.run(check_sync_errors())
