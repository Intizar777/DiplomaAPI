"""Resync products with correct UUIDs and update product_name in related tables."""
import asyncio
from sqlalchemy import text
from app.database import engine, AsyncSessionLocal
from app.services import GatewayClient, ProductService


async def run():
    # Step 1: Clear products table (will re-sync with correct UUIDs)
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM products"))
        print("Cleared products table")

    # Step 2: Re-sync products from Gateway (preserving original UUIDs)
    async with AsyncSessionLocal() as db:
        gateway = GatewayClient()
        service = ProductService(db, gateway)
        count = await service.sync_from_gateway()
        print(f"Re-synced products: {count}")
        await gateway.close()

    # Step 3: Update product_name via JOIN
    async with engine.begin() as conn:
        r = await conn.execute(text(
            "UPDATE inventory_snapshots i SET product_name = p.name "
            "FROM products p WHERE i.product_id = p.id"
        ))
        print(f"inventory_snapshots updated: {r.rowcount} rows")

        r2 = await conn.execute(text(
            "UPDATE production_output o SET product_name = p.name "
            "FROM products p WHERE o.product_id = p.id"
        ))
        print(f"production_output updated: {r2.rowcount} rows")

        r3 = await conn.execute(text(
            "UPDATE sale_records s SET product_name = p.name "
            "FROM products p WHERE s.product_id = p.id"
        ))
        print(f"sale_records updated: {r3.rowcount} rows")

        # Verify
        for table in ["inventory_snapshots", "production_output", "sale_records"]:
            v = await conn.execute(text(
                f"SELECT COUNT(*) FROM {table} WHERE product_name IS NOT NULL"
            ))
            total = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            print(f"{table}: {v.scalar()}/{total.scalar()} rows have product_name")


if __name__ == "__main__":
    asyncio.run(run())
