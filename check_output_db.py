import asyncio
from app.database import AsyncSessionLocal
from app.models import ProductionOutput
from sqlalchemy import select, func

async def check():
    async with AsyncSessionLocal() as db:
        count = await db.execute(select(func.count(ProductionOutput.id)))
        min_date = await db.execute(select(func.min(ProductionOutput.production_date)))
        max_date = await db.execute(select(func.max(ProductionOutput.production_date)))
        print(f"Count: {count.scalar()}")
        print(f"Min date: {min_date.scalar()}")
        print(f"Max date: {max_date.scalar()}")

if __name__ == "__main__":
    asyncio.run(check())
