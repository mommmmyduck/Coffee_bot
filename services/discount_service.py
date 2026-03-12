from sqlalchemy import select, update
from database.database import SessionLocal
from database.models.product import Product, ProductCategory

async def set_category_discount(category: ProductCategory, discount_percent: int):
    """
    Установить скидку на всю категорию
    
    Args:
        category: Категория товаров
        discount_percent: Процент скидки (0-100)
    """
    async with SessionLocal() as session:
        stmt = (
            update(Product)
            .where(Product.category == category)
            .values(discount=discount_percent)
        )
        
        await session.execute(stmt)
        await session.commit()
        
        # Возвращаем количество обновлённых товаров
        count_stmt = select(Product).where(Product.category == category)
        result = await session.execute(count_stmt)
        updated_count = len(result.scalars().all())
        
        return updated_count


async def remove_all_discounts():
    """
    Убрать все скидки
    """
    async with SessionLocal() as session:
        stmt = update(Product).values(discount=0)
        await session.execute(stmt)
        await session.commit()