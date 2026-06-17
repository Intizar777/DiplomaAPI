import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.models import Warehouse, Product, InventorySnapshot, UnitOfMeasure, Customer, OrderSnapshot, QualityResult, ProductionOutput, SensorReading

async def check():
    async with AsyncSessionLocal() as db:
        for model in [Warehouse, Product, InventorySnapshot, UnitOfMeasure, Customer, OrderSnapshot, QualityResult, ProductionOutput, SensorReading]:
            res = await db.execute(select(func.count()).select_from(model))
            count = res.scalar()
            print(f"{model.__name__} count: {count}")

if __name__ == "__main__":
    asyncio.run(check())
