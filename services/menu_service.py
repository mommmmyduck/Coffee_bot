#services/menu_service.py
from sqlalchemy import select
from database.database import SessionLocal
from database.models.product import Product, ProductCategory

async def get_all_products(active_only: bool = True) -> list[Product]:
    """
    Получить все продукты.
    
    Args:
        active_only: Если True, возвращает только активные товары
    """
    async with SessionLocal() as session:
        stmt = select(Product)
        
        if active_only:
            stmt = stmt.where(Product.is_active == True)
        
        result = await session.execute(stmt)
        products = result.scalars().all()
        return list(products)


async def get_products_by_category(
    category: ProductCategory, 
    active_only: bool = True
) -> list[Product]:
    """
    Получить продукты по категории.
    """
    async with SessionLocal() as session:
        stmt = select(Product).where(Product.category == category)
        
        if active_only:
            stmt = stmt.where(Product.is_active == True)
        
        result = await session.execute(stmt)
        products = result.scalars().all()
        return list(products)


async def get_product_by_id(product_id: int) -> Product | None:
    """
    Получить продукт по ID.
    """
    async with SessionLocal() as session:
        stmt = select(Product).where(Product.id == product_id)
        result = await session.execute(stmt)
        product = result.scalars().first()
        return product


async def create_product(
    name: str,
    price: float,
    category: ProductCategory,
    description: str | None = None,
    volume: str | None = None,
    weight: int | None = None,
    image_url: str | None = None,
) -> Product:
    """
    Создать новый продукт.
    """
    async with SessionLocal() as session:
        product = Product(
            name=name,
            price=price,
            category=category,
            description=description,
            volume=volume,
            weight=weight,
            image_url=image_url,
        )
        
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product


async def update_product_price(product_id: int, new_price: float) -> Product | None:
    """
    Обновить цену продукта.
    """
    async with SessionLocal() as session:
        stmt = select(Product).where(Product.id == product_id)
        result = await session.execute(stmt)
        product = result.scalars().first()
        
        if not product:
            return None
        
        product.price = new_price
        await session.commit()
        await session.refresh(product)
        return product


async def toggle_product_active(product_id: int) -> Product | None:
    """
    Переключить активность продукта (доступен/недоступен).
    """
    async with SessionLocal() as session:
        stmt = select(Product).where(Product.id == product_id)
        result = await session.execute(stmt)
        product = result.scalars().first()
        
        if not product:
            return None
        
        product.is_active = not product.is_active
        await session.commit()
        await session.refresh(product)
        return product
    
# services/menu_service.py

# ... существующий код ...

def format_product_status(product) -> str:
    """
    Форматировать статус товара для отображения
    
    Returns:
        "✅ В наличии" или "❌ Нет в наличии"
    """
    if product.is_active:
        return "✅ В наличии"
    else:
        return "❌ Нет в наличии"


def format_product_name(product) -> str:
    """
    Форматировать название товара с учётом наличия
    
    Returns:
        "Капучино ✅" или "Капучино ❌"
    """
    emoji = "✅" if product.is_active else "❌"
    return f"{product.name} {emoji}"