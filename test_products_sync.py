import asyncio
from app.database import AsyncSessionLocal
from app.services import GatewayClient, ProductService
from app.models import Product

async def test_products_sync():
    """Test products sync directly."""
    async with AsyncSessionLocal() as db:
        gateway = GatewayClient()
        service = ProductService(db, gateway)
        
        try:
            print("Starting products sync...")
            records = await service.sync_from_gateway(None, None)
            print(f"Sync completed successfully! Records processed: {records}")
        except Exception as e:
            print(f"Sync failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await gateway.close()

if __name__ == "__main__":
    asyncio.run(test_products_sync())
