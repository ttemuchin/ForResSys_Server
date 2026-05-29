import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

sys.path.append(str(Path(__file__).parent.parent))

from db.session import engine
from db.models import Base

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        tables = result.fetchall()
        print("\nСозданные таблицы:")
        for table in tables:
            print(f"   - {table[0]}")

async def main():
    try:
        await init_db()
    except Exception as e:
        print(f"\nОшибка при создании таблиц: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())