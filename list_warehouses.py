import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import select
from app.models import Warehouse

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Warehouse.id, Warehouse.code))
        rows = res.all()
        for r in rows:
            print(f"{r[0]} | {r[1]}")

if __name__ == "__main__":
    asyncio.run(check())
