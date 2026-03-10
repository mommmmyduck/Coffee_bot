import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import init_db, SessionLocal
from database.models.product import Product

async def clear_products():
    """
    Удалить все товары из базы данных
    """
    await init_db()
    
    async with SessionLocal() as session:
        # Удаляем все товары
        from sqlalchemy import delete
        stmt = delete(Product)
        result = await session.execute(stmt)
        await session.commit()
        
        deleted_count = result.rowcount
        print(f"🗑️  Удалено товаров: {deleted_count}")
        print("✅ База данных очищена")

if __name__ == "__main__":
    asyncio.run(clear_products())