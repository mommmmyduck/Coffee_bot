import asyncio
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.database import init_db
from services.menu_service import create_product
from database.models.product import ProductCategory

async def add_test_products():
    """
    Добавить тестовые товары в меню
    """
    print("🔄 Инициализация базы данных...")
    await init_db()
    print("✅ База данных готова\n")
    
    products = [
        # ========== КОФЕ ==========
        {
            "name": "Эспрессо",
            "price": 120.00,
            "category": ProductCategory.coffee,
            "description": "Классический крепкий кофе",
            "volume": "30",
            "image_url": "https://images.unsplash.com/photo-1510591509098-f4fdc6d0ff04?w=400",
        },
        {
            "name": "Американо",
            "price": 150.00,
            "category": ProductCategory.coffee,
            "description": "Эспрессо с горячей водой",
            "volume": "200",
            "image_url": "https://images.unsplash.com/photo-1494314671902-399b18174975?w=400",
        },
        {
            "name": "Капучино",
            "price": 180.00,
            "category": ProductCategory.coffee,
            "description": "Кофе с молочной пенкой",
            "volume": "200",
            "image_url": "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=400",
        },
        {
            "name": "Латте",
            "price": 200.00,
            "category": ProductCategory.coffee,
            "description": "Нежный кофе с молоком",
            "volume": "300",
            "image_url": "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400",
        },
        {
            "name": "Флэт Уайт",
            "price": 190.00,
            "category": ProductCategory.coffee,
            "description": "Двойной эспрессо с бархатистой молочной пеной",
            "volume": "200",
            "image_url": "https://images.unsplash.com/photo-1497935586351-b67a49e012bf?w=400",
        },
        {
            "name": "Раф",
            "price": 220.00,
            "category": ProductCategory.coffee,
            "description": "Сливочный кофе с ванилью",
            "volume": "300",
            "image_url": "https://images.unsplash.com/photo-1511920170033-f8396924c348?w=400",
        },
        
        # ========== НАПИТКИ БЕЗ КОФЕ ==========
        {
            "name": "Чай зелёный",
            "price": 100.00,
            "category": ProductCategory.non_coffee,
            "description": "Ароматный китайский зелёный чай",
            "volume": "250",
            "image_url": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400",
        },
        {
            "name": "Чай чёрный",
            "price": 100.00,
            "category": ProductCategory.non_coffee,
            "description": "Классический чёрный чай",
            "volume": "250",
            "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400",
        },
        {
            "name": "Какао",
            "price": 150.00,
            "category": ProductCategory.non_coffee,
            "description": "Горячий шоколадный напиток",
            "volume": "300",
            "image_url": "https://images.unsplash.com/photo-1517578239113-b03992dcdd25?w=400",
        },
        {
            "name": "Матча латте",
            "price": 250.00,
            "category": ProductCategory.non_coffee,
            "description": "Японский зелёный чай с молоком",
            "volume": "300",
            "image_url": "https://images.unsplash.com/photo-1536013772375-b14d2c7a2c91?w=400",
        },
        {
            "name": "Апельсиновый фреш",
            "price": 180.00,
            "category": ProductCategory.non_coffee,
            "description": "Свежевыжатый апельсиновый сок",
            "volume": "300",
            "image_url": "https://images.unsplash.com/photo-1600271886742-f049cd451bba?w=400",
        },
        
        # ========== ВЫПЕЧКА ==========
        {
            "name": "Круассан классический",
            "price": 150.00,
            "category": ProductCategory.bakery,
            "description": "Свежий французский круассан",
            "weight": 80,
            "image_url": "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400",
        },
        {
            "name": "Круассан с шоколадом",
            "price": 170.00,
            "category": ProductCategory.bakery,
            "description": "Круассан с бельгийским шоколадом",
            "weight": 90,
            "image_url": "https://images.unsplash.com/photo-1623334044303-241021148842?w=400",
        },
        {
            "name": "Синнабон",
            "price": 200.00,
            "category": ProductCategory.bakery,
            "description": "Булочка с корицей и сливочным кремом",
            "weight": 150,
            "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400",
        },
        {
            "name": "Маффин черничный",
            "price": 130.00,
            "category": ProductCategory.bakery,
            "description": "Воздушный маффин с черникой",
            "weight": 100,
            "image_url": "https://images.unsplash.com/photo-1607920591413-4ec007e70023?w=400",
        },
        {
            "name": "Багет",
            "price": 80.00,
            "category": ProductCategory.bakery,
            "description": "Хрустящий французский багет",
            "weight": 200,
            "image_url": "https://images.unsplash.com/photo-1534620808146-d33bb39128b2?w=400",
        },
        
        # ========== ДЕСЕРТЫ ==========
        {
            "name": "Чизкейк Нью-Йорк",
            "price": 250.00,
            "category": ProductCategory.desserts,
            "description": "Классический американский чизкейк",
            "weight": 120,
            "image_url": "https://images.unsplash.com/photo-1533134486753-c833f0ed4866?w=400",
        },
        {
            "name": "Тирамису",
            "price": 280.00,
            "category": ProductCategory.desserts,
            "description": "Итальянский десерт с маскарпоне и кофе",
            "weight": 130,
            "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400",
        },
        {
            "name": "Брауни",
            "price": 180.00,
            "category": ProductCategory.desserts,
            "description": "Шоколадный пирог с орехами",
            "weight": 100,
            "image_url": "https://images.unsplash.com/photo-1607920591413-4ec007e70023?w=400",
        },
        {
            "name": "Эклер",
            "price": 150.00,
            "category": ProductCategory.desserts,
            "description": "Заварное пирожное с кремом",
            "weight": 80,
            "image_url": "https://images.unsplash.com/photo-1612201142855-c9d74a8f50a3?w=400",
        },
        {
            "name": "Макарон (набор 3 шт)",
            "price": 200.00,
            "category": ProductCategory.desserts,
            "description": "Французское миндальное печенье, ассорти",
            "weight": 60,
            "image_url": "https://images.unsplash.com/photo-1569864358642-9d1684040f43?w=400",
        },
    ]
    
    print("📦 Добавление товаров...\n")
    
    created_count = 0
    for product_data in products:
        try:
            product = await create_product(**product_data)
            created_count += 1
            
            # Красивый вывод
            category_emoji = {
                ProductCategory.coffee: "☕",
                ProductCategory.non_coffee: "🍵",
                ProductCategory.bakery: "🥐",
                ProductCategory.desserts: "🍰",
            }
            
            emoji = category_emoji.get(product.category, "📦")
            print(f"{emoji} [{product.category.value:12}] {product.name:30} — {product.price} ₽")
            
        except Exception as e:
            print(f"❌ Ошибка при создании товара {product_data['name']}: {e}")
    
    print(f"\n✅ Успешно добавлено товаров: {created_count}/{len(products)}")
    print("\n🎉 Готово! Товары добавлены в базу данных")
    print("\n💡 Теперь запусти бота и попробуй команду /menu")

if __name__ == "__main__":
    asyncio.run(add_test_products())