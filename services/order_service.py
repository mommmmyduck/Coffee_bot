# services/order_service.py
from database.database import SessionLocal
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem
from database.models.product import Product
from database.models.user import User
from datetime import datetime, timedelta
from database.models.customization import OrderItemCustomization
import pytz 
from sqlalchemy import select
from sqlalchemy.orm import selectinload

BONUS_RATE = 0.05  # 5% от суммы заказа в бонусы

# ----------------------------
# Корзина пользователя
# ----------------------------
async def get_user_cart(user_id: int) -> Order | None:
    """Получить текущую корзину пользователя (pending order) с товарами, продуктами и кастомизацией"""
    async with SessionLocal() as session:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
            .where(Order.user_id == user_id, Order.status == OrderStatus.pending)
        )
        result = await session.execute(stmt)
        return result.scalars().first()


async def update_order_total(order_id: int) -> None:
    """Обновить общую сумму заказа"""
    async with SessionLocal() as session:
        # Получаем заказ с товарами
        stmt = (
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.id == order_id)
        )
        result = await session.execute(stmt)
        order = result.scalars().first()
        
        if not order:
            return
        
        # Пересчитываем сумму
        total = 0.0
        for item in order.items:
            price = float(item.product.price)
            total += price * item.quantity
        
        order.total_price = total
        await session.commit()


async def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> Order:
    """Добавить товар в корзину"""
    async with SessionLocal() as session:
        # Делаем запрос корзины прямо в этой сессии, чтобы не терять объект
        stmt_order = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
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
        
        # 👇 ОБНОВЛЯЕМ СУММУ ПОСЛЕ ДОБАВЛЕНИЯ
        await update_order_total(order.id)
        
        # Обновляем объект со всеми связями перед возвратом
        stmt_refresh = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
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
            order_id = item.order_id
            await session.delete(item)
            await session.commit()
            
            # 👇 ОБНОВЛЯЕМ СУММУ ПОСЛЕ УДАЛЕНИЯ
            await update_order_total(order_id)
            
        return item


async def confirm_order(order_id: int, payment_method: str) -> Order | None:
    """Подтвердить заказ с указанием способа оплаты"""
    async with SessionLocal() as session:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
            .where(Order.id == order_id)
        )
        result = await session.execute(stmt)
        order = result.scalars().first()
        if not order:
            return None

        # Вычисляем общую сумму
        total = 0.0
        for item in order.items:
            price = float(item.product.price)
            total += price * item.quantity

        order.total_price = total
        order.payment_method = payment_method
        
        # Если оплата картой - ставим статус awaiting_payment
        if payment_method == "card":
            order.status = OrderStatus.awaiting_payment
        else:  # наличные
            order.status = OrderStatus.processing
            
        await session.commit()
        await session.refresh(order)
        return order


async def list_user_orders(user_id: int) -> list[Order]:
    """Получить все заказы пользователя, кроме корзины"""
    async with SessionLocal() as session:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
            .where(Order.user_id == user_id, Order.status != OrderStatus.pending)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


# ----------------------------
# Функции для сотрудников и админа
# ----------------------------
async def list_orders_by_role(role: str) -> list[Order]:
    """Получить заказы в зависимости от роли пользователя"""
    async with SessionLocal() as session:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
        )
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
    # Преобразуем Decimal в float для вычислений
    total = 0.0
    cups_count = 0
    
    for item in order.items:
        price = float(item.product.price)
        total += price * item.quantity
        # Считаем количество чашек кофе
        if item.product.category == "coffee":  # или другой признак
            cups_count += item.quantity
    
    order.total_price = total
    bonus_to_add = int(total * BONUS_RATE)
    order.bonus_points = bonus_to_add
    order.status = OrderStatus.completed
    
    async with SessionLocal() as session:
        # Сохраняем заказ
        session.add(order)
        await session.commit()
        await session.refresh(order)
        
        # 👇 ВАЖНО: Начисляем бонусы пользователю
        stmt = select(User).where(User.id == order.user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.bonus_points += bonus_to_add
            user.total_cups += cups_count
            await session.commit()
            await session.refresh(user)
            print(f"✅ Начислено бонусов: {bonus_to_add}, всего: {user.bonus_points}")  # для отладки
    
    return order


async def get_user_order_history_today(user_id: int) -> list[Order]:
    """
    Получить историю заказов пользователя за сегодня (только completed)
    """
    async with SessionLocal() as session:
        # Получаем московское время
        msk_tz = pytz.timezone('Europe/Moscow')
        now_msk = datetime.now(msk_tz)
        today_start_msk = now_msk.replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
            .where(
                Order.user_id == user_id,
                Order.status == OrderStatus.completed,
                Order.created_at >= today_start_msk
            )
            .order_by(Order.created_at.desc())
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all()) 

async def get_active_orders() -> list[Order]:
    """
    Получить все активные заказы (processing) для бариста
    """
    async with SessionLocal() as session:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
            .where(Order.status == OrderStatus.processing)
            .order_by(Order.created_at.asc())
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def mark_order_as_completed(order_id: int) -> Order | None:
    """
    Отметить заказ как выполненный
    """
    async with SessionLocal() as session:
        stmt = select(Order).where(Order.id == order_id)
        result = await session.execute(stmt)
        order = result.scalars().first()
        
        if not order:
            return None
        
        order.status = OrderStatus.completed
        await session.commit()
        await session.refresh(order)
        return order
    

async def add_to_cart_with_customization(
    user_id: int,
    product_id: int,
    quantity: int,
    customization_data: dict
) -> Order:
    """
    Добавить товар в корзину с кастомизацией
    """
    async with SessionLocal() as session:
        # Получаем или создаём корзину
        stmt_order = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
            .where(Order.user_id == user_id, Order.status == OrderStatus.pending)
        )
        result = await session.execute(stmt_order)
        order = result.scalars().first()

        if not order:
            order = Order(user_id=user_id)
            session.add(order)
            await session.commit()
            await session.refresh(order)

        # Создаём позицию заказа
        order_item = OrderItem(
            order_id=order.id,
            product_id=product_id,
            quantity=quantity
        )
        session.add(order_item)
        await session.commit()
        await session.refresh(order_item)
        
        # Создаём кастомизацию
        toppings = customization_data.get("toppings", {})
        customization = OrderItemCustomization(
            order_item_id=order_item.id,
            milk_type=customization_data.get("milk_type"),
            sugar_count=customization_data.get("sugar_count", 0),
            temperature=customization_data.get("temperature"),
            whipped_cream=toppings.get("whipped_cream", False),
            cinnamon=toppings.get("cinnamon", False),
            cocoa=toppings.get("cocoa", False),
            caramel_syrup=toppings.get("caramel_syrup", False),
            vanilla_syrup=toppings.get("vanilla_syrup", False)
        )
        session.add(customization)
        await session.commit()
        
        # 👇 ОБНОВЛЯЕМ СУММУ ПОСЛЕ ДОБАВЛЕНИЯ С КАСТОМИЗАЦИЕЙ
        await update_order_total(order.id)
        
        # Обновляем объект со всеми связями
        stmt_refresh = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
            .where(Order.id == order.id)
        )
        result = await session.execute(stmt_refresh)
        return result.scalars().first()


async def get_order_by_id(order_id: int) -> Order | None:
    """Получить заказ по ID"""
    async with SessionLocal() as session:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
            .where(Order.id == order_id)
        )
        result = await session.execute(stmt)
        return result.scalars().first()


async def update_order_payment(order_id: int, payment_method: str) -> Order | None:
    """Обновить способ оплаты заказа"""
    async with SessionLocal() as session:
        stmt = select(Order).where(Order.id == order_id)
        result = await session.execute(stmt)
        order = result.scalars().first()
        
        if not order:
            return None
        
        order.payment_method = payment_method
        await session.commit()
        await session.refresh(order)
        return order


async def get_awaiting_payment_order(user_id: int) -> Order | None:
    """Получить заказ, ожидающий оплаты"""
    async with SessionLocal() as session:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.items).selectinload(OrderItem.customization)
            )
            .where(
                Order.user_id == user_id, 
                Order.status == OrderStatus.awaiting_payment
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first()


async def cancel_order_payment(order_id: int) -> Order | None:
    """Отменить оплату - вернуть заказ в статус pending"""
    async with SessionLocal() as session:
        stmt = select(Order).where(Order.id == order_id)
        result = await session.execute(stmt)
        order = result.scalars().first()
        
        if not order:
            return None
        
        order.status = OrderStatus.pending
        order.payment_method = None
        await session.commit()
        await session.refresh(order)
        return order


async def confirm_payment(order_id: int) -> Order | None:
    """Подтвердить оплату - перевести заказ в processing"""
    async with SessionLocal() as session:
        stmt = select(Order).where(Order.id == order_id)
        result = await session.execute(stmt)
        order = result.scalars().first()
        
        if not order:
            return None
        
        order.status = OrderStatus.processing
        await session.commit()
        await session.refresh(order)
        return order


# ========================
# 👇 НОВЫЕ ФУНКЦИИ ДЛЯ БОНУСОВ
# ========================

async def spend_bonus_points(user_id: int, amount: int) -> User | None:
    """
    Списать бонусные баллы (при оплате)
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return None
        
        if user.bonus_points < amount:
            return None  # Недостаточно баллов
        
        user.bonus_points -= amount
        await session.commit()
        await session.refresh(user)
        return user


async def add_bonus_points(user_id: int, amount: int) -> User | None:
    """
    Начислить бонусные баллы пользователю (например, за заказ)
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return None
        
        user.bonus_points += amount
        await session.commit()
        await session.refresh(user)
        return user


async def increment_total_cups(user_id: int, cups: int = 1) -> User | None:
    """
    Увеличить счетчик выпитых чашек
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return None
        
        user.total_cups += cups
        await session.commit()
        await session.refresh(user)
        return user


async def format_cart_text(order) -> str:
    """
    Форматировать текст корзины с кастомизацией
    Единая функция для всех мест, где показывается корзина
    """
    if not order or not order.items:
        return "🛒 Корзина пуста"
    
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    
    for item in order.items:
        # Название товара и количество
        text += f"• {item.product.name} x{item.quantity}\n"
        
        # Цена за позицию
        item_total = float(item.product.price) * item.quantity
        text += f"  💰 {item_total} ₽\n"
        
        # Показываем кастомизацию если есть
        if hasattr(item, 'customization') and item.customization:
            c = item.customization
            customizations = []
            
            # Молоко
            if c.milk_type and c.milk_type != "regular":
                milk_names = {
                    "almond": "миндальное молоко",
                    "coconut": "кокосовое молоко",
                    "soy": "соевое молоко",
                    "lactose_free": "безлактозное молоко"
                }
                if c.milk_type in milk_names:
                    customizations.append(milk_names[c.milk_type])
            
            # Сахар
            if c.sugar_count and c.sugar_count > 0:
                sugar_text = {1: "🍬 1 ложка", 2: "🍬🍬 2 ложки", 3: "🍬🍬🍬 3 ложки"}
                customizations.append(sugar_text.get(c.sugar_count, f"сахар {c.sugar_count} л."))
            
            # Температура
            if c.temperature:
                temp_names = {
                    "cold": "❄️ айс",
                    "warm": "🔥 тёплый",
                    "hot": "☕️ горячий"
                }
                if c.temperature in temp_names:
                    customizations.append(temp_names[c.temperature])
            
            # Топпинги
            toppings = []
            if c.whipped_cream:
                toppings.append("🥛 сливки")
            if c.cinnamon:
                toppings.append("⚜️ корица")
            if c.cocoa:
                toppings.append("🍫 какао")
            if c.caramel_syrup:
                toppings.append("🍯 карамель")
            if c.vanilla_syrup:
                toppings.append("🌿 ваниль")
            
            if toppings:
                customizations.append("➕ " + ", ".join(toppings))
            
            if customizations:
                text += f"  <i>({', '.join(customizations)})</i>\n"
        
        text += "\n"
    
    # Итоговая сумма
    text += f"<b>Итого: {order.total_price} ₽</b>"
    
    return text


async def format_cart_text_short(order) -> str:
    """
    Краткий текст корзины (без деталей кастомизации)
    Используется в уведомлениях
    """
    if not order or not order.items:
        return "🛒 Корзина пуста"
    
    items_count = sum(item.quantity for item in order.items)
    return f"🛒 Корзина: {items_count} товаров на {order.total_price} ₽"

async def get_user_active_orders(user_id: int) -> list[Order]:
    """
    Получить активные заказы пользователя 
    (awaiting_payment, processing, completed за последние 2 часа)
    """
    from datetime import datetime, timedelta
    
    async with SessionLocal() as session:
        # Заказы за последние 2 часа
        two_hours_ago = datetime.utcnow() - timedelta(hours=2)
        
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items)
                .selectinload(OrderItem.product)
            )
            .options(
                selectinload(Order.items)
                .selectinload(OrderItem.customization)
            )
            .where(
                Order.user_id == user_id,
                Order.status.in_([
                    OrderStatus.awaiting_payment,
                    OrderStatus.processing,
                    OrderStatus.completed
                ]),
                Order.created_at >= two_hours_ago
            )
            .order_by(Order.created_at.desc())
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_order_by_id(order_id: int) -> Order | None:
    """
    Получить заказ по ID с полной информацией
    """
    async with SessionLocal() as session:
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items)
                .selectinload(OrderItem.product)
            )
            .options(
                selectinload(Order.items)
                .selectinload(OrderItem.customization)
            )
            .where(Order.id == order_id)
        )
        
        result = await session.execute(stmt)
        return result.scalars().first()