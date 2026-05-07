import asyncio
from app.database import AsyncSessionLocal
from app.services import GatewayClient, KPIService
from app.models import AggregatedKPI
from datetime import date, timedelta

async def test_kpi_sync():
    """Test KPI sync directly."""
    async with AsyncSessionLocal() as db:
        gateway = GatewayClient()
        service = KPIService(db, gateway)
        
        # Use same date range as cron job
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        from_date = sunday - timedelta(days=30)
        to_date = sunday
        
        try:
            print(f"Starting KPI sync from {from_date} to {to_date}...")
            records = await service.sync_from_gateway(from_date, to_date)
            print(f"Sync completed successfully! Records processed: {records}")
        except Exception as e:
            print(f"Sync failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await gateway.close()

if __name__ == "__main__":
    asyncio.run(test_kpi_sync())
