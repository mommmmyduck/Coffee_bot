# drop_tables.py
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import engine
from sqlalchemy import text

async def drop_specific_tables():
    """
    Удалить только таблицы order_item_customizations, order_items, orders, products
    """
    print("⚠️  Будут удалены таблицы:")
    print("   - order_item_customizations")
    print("   - order_items")
    print("   - orders")
    print("   - products")
    print("\n🔴 Нажми Ctrl+C для отмены или подожди 3 секунды...")
    
    for i in range(3, 0, -1):
        print(f"⏳ {i}...")
        await asyncio.sleep(1)
    
    async with engine.begin() as conn:
        # Отключаем проверку внешних ключей
        await conn.execute(text("SET session_replication_role = 'replica';"))
        
        # Удаляем таблицы в правильном порядке (сначала зависимые)
        tables_to_drop = [
            'order_item_customizations',  # зависит от order_items
            'order_items',                 # зависит от orders и products
            'orders',                      # зависит от users
            'products'                     # независимая
        ]
        
        for table in tables_to_drop:
            try:
                await conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE;'))
                print(f"✅ Удалена таблица {table}")
            except Exception as e:
                print(f"❌ Ошибка при удалении {table}: {e}")
        
        # Включаем обратно проверку внешних ключей
        await conn.execute(text("SET session_replication_role = 'origin';"))
    
    print("\n🔄 Создаем таблицы заново с обновленной структурой...")
    

if __name__ == "__main__":
    asyncio.run(drop_specific_tables())