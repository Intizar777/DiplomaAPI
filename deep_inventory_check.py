import asyncio
from datetime import date
from decimal import Decimal
from typing import Dict, List, Set

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.services.gateway_client import GatewayClient
from app.models import InventorySnapshot, Product, Warehouse

async def deep_inventory_reconciliation():
    """
    Perform a deep reconciliation between Gateway inventory and local database.
    """
    print("=" * 80)
    print(f"🔍 DEEP INVENTORY RECONCILIATION - {date.today()}")
    print("=" * 80)

    gateway = GatewayClient()
    
    # 1. Fetch data from Gateway
    print("\n[1/3] Fetching data from Gateway...")
    try:
        inventory_response = await gateway.get_inventory()
        gateway_items = {str(item.id): item for item in inventory_response.inventory}
        print(f"✅ Found {len(gateway_items)} items in Gateway")
    except Exception as e:
        print(f"❌ Error fetching from Gateway: {e}")
        return

    # 2. Fetch data from Local DB
    print("\n[2/3] Fetching data from Local Database (today's snapshots)...")
    async with AsyncSessionLocal() as db:
        stmt = select(InventorySnapshot).where(InventorySnapshot.snapshot_date == date.today())
        result = await db.execute(stmt)
        db_snapshots = {str(s.id): s for s in result.scalars().all()}
        print(f"✅ Found {len(db_snapshots)} snapshots in DB for today")

        # Fetch warehouses to check for placeholders
        wh_stmt = select(Warehouse)
        wh_result = await db.execute(wh_stmt)
        warehouses = {str(w.id): w for w in wh_result.scalars().all()}

    # 3. Compare and Analyze
    print("\n[3/3] Analyzing discrepancies...")
    
    missing_in_db: List[str] = []
    missing_in_gateway: List[str] = []
    quantity_mismatches: List[Dict] = []
    placeholder_warehouses: Set[str] = set()
    
    # Check Gateway vs DB
    for g_id, g_item in gateway_items.items():
        if g_id not in db_snapshots:
            missing_in_db.append(g_id)
            continue
            
        db_item = db_snapshots[g_id]
        g_qty = Decimal(str(g_item.quantity))
        db_qty = db_item.quantity
        
        if abs(g_qty - db_qty) > Decimal("0.0001"):
            quantity_mismatches.append({
                "id": g_id,
                "product_id": str(g_item.productId),
                "gateway_qty": g_qty,
                "db_qty": db_qty,
                "diff": g_qty - db_qty
            })
            
        # Check if warehouse is a placeholder
        wh_code = db_item.warehouse_code
        if wh_code and wh_code.startswith("WH-UNKNOWN-"):
            placeholder_warehouses.add(f"{wh_code} (ID: {db_item.warehouse_id})")

    # Check DB vs Gateway (items that might be stale in DB)
    for db_id in db_snapshots:
        if db_id not in gateway_items:
            missing_in_gateway.append(db_id)

    # Output Results
    print("\n" + "-" * 40)
    print("📊 RECONCILIATION SUMMARY")
    print("-" * 40)
    
    if not any([missing_in_db, missing_in_gateway, quantity_mismatches, placeholder_warehouses]):
        print("🟢 PERFECT MATCH: All records are synchronized correctly!")
    else:
        if missing_in_db:
            print(f"🔴 MISSING IN DB: {len(missing_in_db)} records exist in Gateway but not in DB")
            for item_id in missing_in_db[:5]:
                item = gateway_items[item_id]
                print(f"   - ID: {item_id}, Product: {item.productId}, Warehouse: {item.warehouseId}")
            if len(missing_in_db) > 5: print(f"   ... and {len(missing_in_db)-5} more")

        if missing_in_gateway:
            print(f"🟡 STALE IN DB: {len(missing_in_gateway)} records exist in DB but not in Gateway")
            for item_id in missing_in_gateway[:5]:
                print(f"   - ID: {item_id}")
            if len(missing_in_gateway) > 5: print(f"   ... and {len(missing_in_gateway)-5} more")

        if quantity_mismatches:
            print(f"🟠 QUANTITY MISMATCH: {len(quantity_mismatches)} records have different quantities")
            for m in quantity_mismatches[:5]:
                print(f"   - ID: {m['id']}, GW: {m['gateway_qty']}, DB: {m['db_qty']} (Diff: {m['diff']})")
            if len(quantity_mismatches) > 5: print(f"   ... and {len(quantity_mismatches)-5} more")

        if placeholder_warehouses:
            print(f"🟣 PLACEHOLDER WAREHOUSES: {len(placeholder_warehouses)} unknown warehouses found")
            for wh in list(placeholder_warehouses)[:5]:
                print(f"   - {wh}")

    print("\n" + "=" * 80)
    
    # Close gateway client
    await gateway.close()

if __name__ == "__main__":
    asyncio.run(deep_inventory_reconciliation())
