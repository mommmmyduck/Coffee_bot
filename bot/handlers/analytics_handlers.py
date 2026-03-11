#bot/handlers/analytics_handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.decorators import admin_required
from services.analytics_service import (
    get_total_statistics,
    get_period_statistics,
    get_popular_products,
    get_category_statistics,
    get_loyalty_statistics,
    get_user_activity_statistics,
    export_statistics_to_text,
)

router = Router()

# -----------------------
# Главное меню статистики
# -----------------------

@router.message(F.text == "📈 Статистика")
@admin_required
async def show_statistics_menu(message: Message):
    """Главное меню статистики"""
    text = "📈 <b>Статистика и аналитика</b>\n\n"
    text += "Выберите раздел:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📊 Общая статистика",
            callback_data="stats_total"
        )],
        [InlineKeyboardButton(
            text="📅 Статистика за период",
            callback_data="stats_period"
        )],
        [InlineKeyboardButton(
            text="🏆 Популярные товары",
            callback_data="stats_popular"
        )],
        [InlineKeyboardButton(
            text="📂 Статистика по категориям",
            callback_data="stats_categories"
        )],
        [InlineKeyboardButton(
            text="👥 Активность пользователей",
            callback_data="stats_users"
        )],
        [InlineKeyboardButton(
            text="💎 Программа лояльности",
            callback_data="stats_loyalty"
        )],
        # ✅ НОВОЕ: Кнопка экспорта
        [InlineKeyboardButton(
            text="📤 Экспорт полного отчёта",
            callback_data="stats_export"
        )],
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
# -----------------------
# Общая статистика
# -----------------------

@router.callback_query(F.data == "stats_total")
@admin_required
async def show_total_statistics(callback: CallbackQuery):
    """Показать общую статистику за всё время"""
    stats = await get_total_statistics()
    
    text = "📊 <b>Общая статистика</b>\n\n"
    text += f"📦 Всего заказов: {stats['total_orders']}\n"
    text += f"💰 Общая выручка: {stats['total_revenue']:.2f} ₽\n"
    text += f"💳 Средний чек: {stats['average_check']:.2f} ₽\n\n"
    text += f"👥 Всего пользователей: {stats['total_users']}\n"
    text += f"📋 Активных товаров: {stats['active_products']}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="stats_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# -----------------------
# Статистика за период
# -----------------------

@router.callback_query(F.data == "stats_period")
@admin_required
async def show_period_menu(callback: CallbackQuery):
    """Выбор периода"""
    text = "📅 <b>Статистика за период</b>\n\n"
    text += "Выберите период:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📅 Сегодня",
            callback_data="stats_period:today"
        )],
        [InlineKeyboardButton(
            text="📅 За неделю",
            callback_data="stats_period:week"
        )],
        [InlineKeyboardButton(
            text="📅 За месяц",
            callback_data="stats_period:month"
        )],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="stats_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("stats_period:"))
@admin_required
async def show_period_statistics(callback: CallbackQuery):
    """Показать статистику за выбранный период"""
    period = callback.data.split(":")[1]
    stats = await get_period_statistics(period)
    
    text = f"📅 <b>Статистика {stats['period']}</b>\n\n"
    text += f"📦 Заказов: {stats['orders_count']}\n"
    text += f"💰 Выручка: {stats['revenue']:.2f} ₽\n"
    text += f"💳 Средний чек: {stats['average_check']:.2f} ₽\n"
    text += f"👥 Активных пользователей: {stats['active_users']}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="stats_period")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# -----------------------
# Популярные товары
# -----------------------

@router.callback_query(F.data == "stats_popular")
@admin_required
async def show_popular_products(callback: CallbackQuery):
    """Показать топ популярных товаров"""
    products = await get_popular_products(limit=5)
    
    if not products:
        await callback.answer("📊 Нет данных о продажах", show_alert=True)
        return
    
    text = "🏆 <b>Топ-5 популярных товаров</b>\n\n"
    
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    
    for i, product in enumerate(products):
        text += f"{medals[i]} <b>{product['name']}</b>\n"
        text += f"   📦 Продано: {product['total_sold']} шт\n"
        text += f"   💰 Выручка: {product['total_revenue']:.2f} ₽\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="stats_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# -----------------------
# Статистика по категориям
# -----------------------

@router.callback_query(F.data == "stats_categories")
@admin_required
async def show_category_statistics(callback: CallbackQuery):
    """Показать статистику по категориям"""
    categories = await get_category_statistics()
    
    if not categories:
        await callback.answer("📂 Нет данных по категориям", show_alert=True)
        return
    
    text = "📂 <b>Статистика по категориям</b>\n\n"
    
    for cat in categories:
        text += f"{cat['category']}\n"
        text += f"   📦 Продано позиций: {cat['items_sold']}\n"
        text += f"   💰 Выручка: {cat['revenue']:.2f} ₽\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="stats_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# -----------------------
# Активность пользователей
# -----------------------

@router.callback_query(F.data == "stats_users")
@admin_required
async def show_user_statistics(callback: CallbackQuery):
    """Показать статистику пользователей"""
    stats = await get_user_activity_statistics()
    
    text = "👥 <b>Активность пользователей</b>\n\n"
    text += f"📊 Всего пользователей: {stats['total_users']}\n"
    text += f"🛒 С заказами: {stats['users_with_orders']}\n"
    text += f"🔥 Активных за неделю: {stats['active_last_week']}\n\n"
    
    # ✅ НОВОЕ: Распределение по ролям
    if 'roles_distribution' in stats:
        text += "📊 <b>По ролям:</b>\n"
        text += f"👤 Клиентов: {stats['roles_distribution']['buyer']}\n"
        text += f"☕ Бариста: {stats['roles_distribution']['seller']}\n"
        text += f"👑 Админов: {stats['roles_distribution']['owner']}\n\n"
    
    if stats['top_customers']:
        text += "🏆 <b>Топ-5 клиентов:</b>\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        
        for i, customer in enumerate(stats['top_customers']):
            text += f"{medals[i]} {customer['name']}\n"
            text += f"   📦 Заказов: {customer['orders_count']}\n"
            text += f"   💰 Потрачено: {customer['total_spent']:.2f} ₽\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="stats_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# -----------------------
# Программа лояльности
# -----------------------

@router.callback_query(F.data == "stats_loyalty")
@admin_required
async def show_loyalty_statistics(callback: CallbackQuery):
    """Показать статистику программы лояльности"""
    stats = await get_loyalty_statistics()
    
    text = "💎 <b>Программа лояльности</b>\n\n"
    text += f"💰 Всего выдано бонусов: {stats['total_bonus_issued']}\n"
    text += f"💳 Общий баланс бонусов: {stats['total_bonus_balance']}\n"
    text += f"👥 Пользователей с бонусами: {stats['users_with_bonus']}\n\n"
    
    if stats['top_users']:
        text += "🏆 <b>Топ-5 по бонусам:</b>\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        
        for i, user in enumerate(stats['top_users']):
            text += f"{medals[i]} {user['name']}\n"
            text += f"   💎 Бонусов: {user['bonus_points']}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="stats_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# -----------------------
# Навигация
# -----------------------

@router.callback_query(F.data == "stats_back")
@admin_required
async def stats_back(callback: CallbackQuery):
    """Вернуться в главное меню статистики"""
    # 👇 НЕ используем callback.message, а создаем новое сообщение
    text = "📈 <b>Статистика и аналитика</b>\n\n"
    text += "Выберите раздел:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Общая статистика", callback_data="stats_total")],
        [InlineKeyboardButton(text="📅 Статистика за период", callback_data="stats_period")],
        [InlineKeyboardButton(text="🏆 Популярные товары", callback_data="stats_popular")],
        [InlineKeyboardButton(text="📂 По категориям", callback_data="stats_categories")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="stats_users")],
        [InlineKeyboardButton(text="💎 Лояльность", callback_data="stats_loyalty")],
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
    
@router.callback_query(F.data == "stats_export")
@admin_required
async def export_statistics(callback: CallbackQuery):
    """Экспортировать всю статистику"""
    await callback.answer("📊 Формирую отчёт...")
    
    text = await export_statistics_to_text()
    
    # Разбиваем, если слишком длинное сообщение (лимит Telegram 4096 символов)
    if len(text) > 4096:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for i, part in enumerate(parts):
            if i == 0:
                await callback.message.answer(part, parse_mode="HTML")
            else:
                await callback.message.answer(part, parse_mode="HTML")
    else:
        await callback.message.answer(text, parse_mode="HTML")
    
    await callback.answer()