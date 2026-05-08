import asyncio
from sqlalchemy import select, desc
from app.database import AsyncSessionLocal
from app.models import SyncLog, SyncStatus

async def check_recent_logs():
    """Check recent sync logs."""
    async with AsyncSessionLocal() as db:
        # Get recent sync logs (all statuses)
        query = select(SyncLog).order_by(desc(SyncLog.started_at)).limit(15)
        
        result = await db.execute(query)
        recent_logs = result.scalars().all()
        
        print(f"Recent sync logs (all statuses):")
        print("-" * 100)
        for log in recent_logs:
            print(f"\nTask: {log.task_name}")
            print(f"Started: {log.started_at}")
            print(f"Completed: {log.completed_at}")
            print(f"Status: {log.status}")
            print(f"Records processed: {log.records_processed}")
            if log.error_message:
                print(f"Error: {log.error_message}")
            print("-" * 100)

if __name__ == "__main__":
    asyncio.run(check_recent_logs())
