from database.database import SessionLocal
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem
from database.models.product import Product
from database.models.user import User

from sqlalchemy import select
from sqlalchemy.orm import selectinload

BONUS_RATE = 0.05  # 5% от суммы заказа в бонусы

# ----------------------------
# Корзина пользователя
# ----------------------------
async def get_user_cart(user_id: int) -> Order | None:
    """Получить текущую корзину пользователя (pending order) с товарами и продуктами"""
    async with SessionLocal() as session:
        stmt = (
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.user_id == user_id, Order.status == OrderStatus.pending)
        )
        result = await session.execute(stmt)
        return result.scalars().first()


async def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> Order:
    """Добавить товар в корзину"""
    async with SessionLocal() as session:
        # Делаем запрос корзины прямо в этой сессии, чтобы не терять объект
        stmt_order = (
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.user_id == user_id, Order.status == OrderStatus.pending)
        )
        result = await session.execute(stmt_order)
        order = result.scalars().first()

        if not order:
            order = Order(user_id=user_id)
            session.add(order)
            await session.commit()
            await session.refresh(order)

        stmt = select(OrderItem).where(
            OrderItem.order_id == order.id,
            OrderItem.product_id == product_id
        )
        result = await session.execute(stmt)
        item = result.scalars().first()

        if item:
            item.quantity += quantity
        else:
            item = OrderItem(order_id=order.id, product_id=product_id, quantity=quantity)
            session.add(item)

        await session.commit()
        
        # Обновляем объект со всеми связями перед возвратом
        stmt_refresh = (
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.id == order.id)
        )
        result = await session.execute(stmt_refresh)
        return result.scalars().first()

async def remove_from_cart(order_item_id: int) -> OrderItem | None:
    """Удалить товар из корзины"""
    async with SessionLocal() as session:
        stmt = select(OrderItem).where(OrderItem.id == order_item_id)
        result = await session.execute(stmt)
        item = result.scalars().first()
        if item:
            await session.delete(item)
            await session.commit()
        return item


async def confirm_order(order_id: int) -> Order | None:
    """Подтвердить корзину и сделать заказ активным"""
    async with SessionLocal() as session:
        stmt = select(Order).options(selectinload(Order.items).selectinload(OrderItem.product)).where(Order.id == order_id)
        result = await session.execute(stmt)
        order = result.scalars().first()
        if not order:
            return None

        order.status = OrderStatus.processing
        order.total_price = sum(item.product.price * item.quantity for item in order.items)
        await session.commit()
        await session.refresh(order)
        return order


async def list_user_orders(user_id: int) -> list[Order]:
    """Получить все заказы пользователя, кроме корзины"""
    async with SessionLocal() as session:
        stmt = select(Order).where(Order.user_id == user_id, Order.status != OrderStatus.pending)
        result = await session.execute(stmt)
        return result.scalars().all()


# ----------------------------
# Функции для сотрудников и админа
# ----------------------------
async def list_orders_by_role(role: str) -> list[Order]:
    """Получить заказы в зависимости от роли пользователя"""
    async with SessionLocal() as session:
        stmt = select(Order).options(selectinload(Order.items).selectinload(OrderItem.product))
        if role == "employee":
            stmt = stmt.where(Order.status.in_([OrderStatus.pending, OrderStatus.processing]))
        elif role == "admin":
            pass  # видит все
        else:
            stmt = stmt.where(Order.status != OrderStatus.pending)
        result = await session.execute(stmt)
        return result.scalars().all()


async def cancel_order(order_id: int) -> Order | None:
    """Отменить заказ"""
    async with SessionLocal() as session:
        stmt = select(Order).where(Order.id == order_id)
        result = await session.execute(stmt)
        order = result.scalars().first()
        if not order:
            return None
        order.status = OrderStatus.cancelled
        await session.commit()
        await session.refresh(order)
        return order


async def finalize_order(order: Order) -> Order:
    """Подсчёт итоговой суммы и начисление бонусов, завершение заказа"""
    order.total_price = sum(item.product.price * item.quantity for item in order.items)
    order.bonus_points = int(order.total_price * BONUS_RATE)
    order.status = OrderStatus.completed
    async with SessionLocal() as session:
        session.add(order)
        await session.commit()
        await session.refresh(order)
    return order