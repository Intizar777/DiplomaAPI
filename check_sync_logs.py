import asyncio
from app.database import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT task_name, status, error_message, started_at, completed_at "
            "FROM sync_logs ORDER BY started_at DESC LIMIT 20"
        ))
        rows = result.fetchall()
        print(f"{'Task':<15} {'Status':<15} {'Started':<25} {'Completed':<25} {'Error Message'}")
        print("-" * 120)
        for row in rows:
            task, status, error, started, completed = row
            print(f"{task:<15} {status:<15} {str(started):<25} {str(completed):<25} {error[:50] if error else ''}")

if __name__ == "__main__":
    asyncio.run(check())
