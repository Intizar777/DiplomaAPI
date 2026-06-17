import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.models import AggregatedKPI, AggregatedSales, SalesTrends, SaleRecord

async def check():
    async with AsyncSessionLocal() as db:
        for model in [AggregatedKPI, AggregatedSales, SalesTrends, SaleRecord]:
            res = await db.execute(select(func.count()).select_from(model))
            count = res.scalar()
            print(f"{model.__name__} count: {count}")

if __name__ == "__main__":
    asyncio.run(check())
