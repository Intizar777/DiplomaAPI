import asyncio
from app.cron.jobs import sync_kpi_task

async def test_scheduled_sync():
    """Test scheduled sync task directly."""
    print("Testing scheduled sync task directly...")
    try:
        await sync_kpi_task()
        print("Scheduled sync task completed successfully")
    except Exception as e:
        print(f"Scheduled sync task failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_scheduled_sync())
