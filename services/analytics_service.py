#services/analytics_service.py
from datetime import datetime, timedelta
import pytz
from sqlalchemy import select, func
from database.database import SessionLocal
from database.models.order import Order, OrderStatus
from database.models.order_item import OrderItem
from database.models.product import Product, ProductCategory
from database.models.user import User

# Московское время для статистики
MSK_TZ = pytz.timezone('Europe/Moscow')

# -----------------------
# Общая статистика
# -----------------------

async def get_total_statistics():
    """
    Получить общую статистику за всё время
    """
    async with SessionLocal() as session:
        # Общее количество заказов
        stmt = select(func.count(Order.id)).where(
            Order.status == OrderStatus.completed
        )
        total_orders = await session.scalar(stmt) or 0
        
        # Общая выручка
        stmt = select(func.sum(Order.total_price)).where(
            Order.status == OrderStatus.completed
        )
        total_revenue = await session.scalar(stmt) or 0.0
        
        # Средний чек
        avg_check = total_revenue / total_orders if total_orders > 0 else 0
        
        # Количество пользователей
        stmt = select(func.count(User.id))
        total_users = await session.scalar(stmt) or 0
        
        # Количество активных товаров
        stmt = select(func.count(Product.id)).where(Product.is_active == True)
        active_products = await session.scalar(stmt) or 0
        
        return {
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "average_check": float(avg_check),
            "total_users": total_users,
            "active_products": active_products,
        }


# -----------------------
# Статистика за период
# -----------------------

async def get_period_statistics(period: str = "today"):
    """
    Получить статистику за период
    period: 'today', 'week', 'month'
    """
    async with SessionLocal() as session:
        # Определяем начало периода по московскому времени
        now_msk = datetime.now(MSK_TZ)
        
        if period == "today":
            start_date = now_msk.replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "сегодня"
        elif period == "week":
            start_date = now_msk - timedelta(days=7)
            period_name = "за неделю"
        elif period == "month":
            start_date = now_msk - timedelta(days=30)
            period_name = "за месяц"
        else:
            start_date = now_msk.replace(hour=0, minute=0, second=0, microsecond=0)
            period_name = "сегодня"
        
        # Конвертируем в UTC для сравнения с БД
        start_date_utc = start_date.astimezone(pytz.UTC)
        
        # Количество заказов за период
        stmt = select(func.count(Order.id)).where(
            Order.status == OrderStatus.completed,
            Order.created_at >= start_date_utc
        )
        orders_count = await session.scalar(stmt) or 0
        
        # Выручка за период
        stmt = select(func.sum(Order.total_price)).where(
            Order.status == OrderStatus.completed,
            Order.created_at >= start_date_utc
        )
        revenue = await session.scalar(stmt) or 0.0
        
        # Средний чек за период
        avg_check = revenue / orders_count if orders_count > 0 else 0
        
        # Новые пользователи за период
        stmt = select(func.count(User.id.distinct())).select_from(Order).where(
            Order.created_at >= start_date_utc
        )
        active_users = await session.scalar(stmt) or 0
        
        return {
            "period": period_name,
            "orders_count": orders_count,
            "revenue": float(revenue),
            "average_check": float(avg_check),
            "active_users": active_users,
        }

# -----------------------
# Популярные товары
# -----------------------

async def get_popular_products(limit: int = 5, period_days: int | None = None):
    """
    Получить топ популярных товаров
    
    Args:
        limit: Количество товаров в топе
        period_days: Если указано, только за последние N дней
    """
    async with SessionLocal() as session:
        query = (
            select(
                Product.id,
                Product.name,
                Product.category,
                func.sum(OrderItem.quantity).label('total_sold'),
                func.sum(OrderItem.quantity * Product.price).label('total_revenue')
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status == OrderStatus.completed)
        )
        
        # ✅ НОВОЕ: Фильтр по периоду
        if period_days:
            cutoff = datetime.now(MSK_TZ) - timedelta(days=period_days)
            cutoff_utc = cutoff.astimezone(pytz.UTC)
            query = query.where(Order.created_at >= cutoff_utc)
        
        query = (
            query
            .group_by(Product.id)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
        )
        
        result = await session.execute(query)
        products = result.all()
        
        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category.value,
                "total_sold": p.total_sold,
                "total_revenue": float(p.total_revenue),
            }
            for p in products
        ]


# -----------------------
# Статистика по категориям
# -----------------------

async def get_category_statistics():
    """
    Получить статистику продаж по категориям
    """
    async with SessionLocal() as session:
        stmt = (
            select(
                Product.category,
                func.count(OrderItem.id).label('items_sold'),
                func.sum(OrderItem.quantity * Product.price).label('revenue')
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.status == OrderStatus.completed)
            .group_by(Product.category)
            .order_by(func.sum(OrderItem.quantity * Product.price).desc())
        )
        
        result = await session.execute(stmt)
        categories = result.all()
        
        category_names = {
            ProductCategory.coffee: "☕ Кофе",
            ProductCategory.non_coffee: "🍵 Напитки",
            ProductCategory.bakery: "🥐 Выпечка",
            ProductCategory.desserts: "🍰 Десерты",
        }
        
        return [
            {
                "category": category_names.get(c.category, c.category.value),
                "items_sold": c.items_sold,
                "revenue": float(c.revenue),
            }
            for c in categories
        ]


# -----------------------
# Программа лояльности
# -----------------------

async def get_loyalty_statistics():
    """
    Получить статистику программы лояльности
    """
    async with SessionLocal() as session:
        # Всего выдано бонусов
        stmt = select(func.sum(Order.bonus_points)).where(
            Order.status == OrderStatus.completed
        )
        total_bonus_issued = await session.scalar(stmt) or 0
        
        # Общий баланс бонусов у пользователей
        stmt = select(func.sum(User.bonus_points))
        total_bonus_balance = await session.scalar(stmt) or 0
        
        # Количество пользователей с бонусами
        stmt = select(func.count(User.id)).where(User.bonus_points > 0)
        users_with_bonus = await session.scalar(stmt) or 0
        
        # Топ-5 пользователей по бонусам
        stmt = (
            select(User.first_name, User.last_name, User.bonus_points)
            .where(User.bonus_points > 0)
            .order_by(User.bonus_points.desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        top_users = result.all()
        
        return {
            "total_bonus_issued": total_bonus_issued,
            "total_bonus_balance": total_bonus_balance,
            "users_with_bonus": users_with_bonus,
            "top_users": [
                {
                    "name": f"{u.first_name} {u.last_name or ''}".strip(),
                    "bonus_points": u.bonus_points
                }
                for u in top_users
            ]
        }


# -----------------------
# Активные пользователи
# -----------------------

async def get_user_activity_statistics():
    """
    Получить статистику активности пользователей
    """
    async with SessionLocal() as session:
        # Всего пользователей
        stmt = select(func.count(User.id))
        total_users = await session.scalar(stmt) or 0
        
        # ✅ НОВОЕ: Распределение по ролям
        stmt = select(User.role, func.count(User.id)).group_by(User.role)
        result = await session.execute(stmt)
        roles = dict(result.all())
        
        # Пользователи с заказами
        stmt = select(func.count(User.id.distinct())).select_from(Order)
        users_with_orders = await session.scalar(stmt) or 0
        
        # Активные за последние 7 дней
        week_ago = datetime.now(MSK_TZ) - timedelta(days=7)
        week_ago_utc = week_ago.astimezone(pytz.UTC)
        
        stmt = select(func.count(User.id.distinct())).select_from(Order).where(
            Order.created_at >= week_ago_utc
        )
        active_last_week = await session.scalar(stmt) or 0
        
        # Топ-5 самых активных
        stmt = (
            select(
                User.first_name,
                User.last_name,
                func.count(Order.id).label('orders_count'),
                func.sum(Order.total_price).label('total_spent')
            )
            .join(Order, Order.user_id == User.id)
            .where(Order.status == OrderStatus.completed)
            .group_by(User.id)
            .order_by(func.count(Order.id).desc())
            .limit(5)
        )
        result = await session.execute(stmt)
        top_customers = result.all()
        
        return {
            "total_users": total_users,
            "users_with_orders": users_with_orders,
            "active_last_week": active_last_week,
            # ✅ НОВОЕ: Распределение по ролям
            "roles_distribution": {
                "buyer": roles.get("buyer", 0),
                "seller": roles.get("seller", 0),
                "owner": roles.get("owner", 0),
            },
            "top_customers": [
                {
                    "name": f"{c.first_name} {c.last_name or ''}".strip(),
                    "orders_count": c.orders_count,
                    "total_spent": float(c.total_spent),
                }
                for c in top_customers
            ]
        }

async def export_statistics_to_text() -> str:
    """
    Экспортировать всю статистику в текстовый формат
    """
    total = await get_total_statistics()
    today = await get_period_statistics("today")
    week = await get_period_statistics("week")
    month = await get_period_statistics("month")
    popular = await get_popular_products(5)
    categories = await get_category_statistics()
    loyalty = await get_loyalty_statistics()
    users = await get_user_activity_statistics()
    
    # Получаем текущее московское время
    now_msk = datetime.now(MSK_TZ)
    timestamp = now_msk.strftime("%d.%m.%Y %H:%M")
    
    text = f"📊 <b>ПОЛНЫЙ ОТЧЁТ</b>\n"
    text += f"🕐 Сформирован: {timestamp} (МСК)\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    text += "🔹 <b>ОБЩАЯ СТАТИСТИКА</b>\n"
    text += f"📦 Всего заказов: {total['total_orders']}\n"
    text += f"💰 Общая выручка: {total['total_revenue']:.2f} ₽\n"
    text += f"💳 Средний чек: {total['average_check']:.2f} ₽\n"
    text += f"👥 Всего пользователей: {total['total_users']}\n"
    text += f"📋 Активных товаров: {total['active_products']}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    text += "🔹 <b>ЗА СЕГОДНЯ</b>\n"
    text += f"📦 Заказов: {today['orders_count']}\n"
    text += f"💰 Выручка: {today['revenue']:.2f} ₽\n"
    text += f"💳 Средний чек: {today['average_check']:.2f} ₽\n"
    text += f"👥 Активных клиентов: {today['active_users']}\n\n"
    
    text += "🔹 <b>ЗА НЕДЕЛЮ</b>\n"
    text += f"📦 Заказов: {week['orders_count']}\n"
    text += f"💰 Выручка: {week['revenue']:.2f} ₽\n"
    text += f"💳 Средний чек: {week['average_check']:.2f} ₽\n\n"
    
    text += "🔹 <b>ЗА МЕСЯЦ</b>\n"
    text += f"📦 Заказов: {month['orders_count']}\n"
    text += f"💰 Выручка: {month['revenue']:.2f} ₽\n"
    text += f"💳 Средний чек: {month['average_check']:.2f} ₽\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if popular:
        text += "🔹 <b>ТОП-5 ТОВАРОВ</b>\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, p in enumerate(popular):
            text += f"{medals[i]} {p['name']}\n"
            text += f"   📦 Продано: {p['total_sold']} шт\n"
            text += f"   💰 Выручка: {p['total_revenue']:.2f} ₽\n"
        text += "\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if categories:
        text += "🔹 <b>ПО КАТЕГОРИЯМ</b>\n"
        for c in categories:
            text += f"{c['category']}\n"
            text += f"   📦 Позиций: {c['items_sold']}\n"
            text += f"   💰 Выручка: {c['revenue']:.2f} ₽\n"
        text += "\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    text += "🔹 <b>ПРОГРАММА ЛОЯЛЬНОСТИ</b>\n"
    text += f"💎 Всего выдано бонусов: {loyalty['total_bonus_issued']}\n"
    text += f"💳 Баланс бонусов: {loyalty['total_bonus_balance']}\n"
    text += f"👥 Пользователей с бонусами: {loyalty['users_with_bonus']}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    text += "🔹 <b>АКТИВНОСТЬ ПОЛЬЗОВАТЕЛЕЙ</b>\n"
    text += f"👥 Всего: {users['total_users']}\n"
    text += f"🛒 С заказами: {users['users_with_orders']}\n"
    text += f"🔥 Активных за неделю: {users['active_last_week']}\n"
    
    if 'roles_distribution' in users:
        text += f"\n📊 По ролям:\n"
        text += f"   👤 Клиентов: {users['roles_distribution']['buyer']}\n"
        text += f"   ☕ Бариста: {users['roles_distribution']['seller']}\n"
        text += f"   👑 Админов: {users['roles_distribution']['owner']}\n"
    
    return text