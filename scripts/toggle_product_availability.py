import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import init_db
from services.menu_service import get_all_products, toggle_product_active

async def toggle_products():
    """
    Сделать несколько товаров недоступными для теста
    """
    await init_db()
    
    # Получаем все товары
    products = await get_all_products(active_only=False)
    
    print("📋 Список товаров:\n")
    for p in products:
        status = "✅" if p.is_active else "❌"
        print(f"{p.id:3}. {status} {p.name:30} — {p.price} ₽")
    
    print("\n" + "="*60)
    print("💡 Сейчас сделаем несколько товаров недоступными для теста")
    print("="*60 + "\n")
    
    # Делаем 2-3 товара недоступными
    test_unavailable = [1, 5, 10]  # ID товаров
    
    for product_id in test_unavailable:
        product = await toggle_product_active(product_id)
        if product:
            status = "✅ В наличии" if product.is_active else "❌ Нет в наличии"
            print(f"Товар {product.name}: {status}")
    
    print("\n✅ Готово! Теперь в меню будут товары с разным статусом")

if __name__ == "__main__":
    asyncio.run(toggle_products())