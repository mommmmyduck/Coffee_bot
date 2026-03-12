# staff_handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.decorators import staff_required
from services.notification_service import notify_customer_status_change
from services.order_service import get_active_orders, mark_order_as_completed, get_order_by_id
from services.user_service import get_user_by_id  # 👈 ДОБАВЛЯЕМ
from bot.utils.time_utils import format_order_time

router = Router()

def format_customization_text(item) -> str:
    """Форматирует кастомизацию товара в понятный текст"""
    if not hasattr(item, 'customization') or not item.customization:
        return ""
    
    c = item.customization
    parts = []
    
    # Молоко
    if c.milk_type and c.milk_type != "regular":
        milk_names = {
            "almond": "🌰 миндальное молоко",
            "coconut": "🥥 кокосовое молоко",
            "soy": "🌱 соевое молоко",
            "lactose_free": "🚫 безлактозное молоко"
        }
        if c.milk_type in milk_names:
            parts.append(milk_names[c.milk_type])
    
    # Сахар
    if c.sugar_count is not None:
        if c.sugar_count == 0:
            parts.append("🚫 без сахара")
        elif c.sugar_count == 1:
            parts.append("🍬 1 ложка сахара")
        elif c.sugar_count == 2:
            parts.append("🍬🍬 2 ложки сахара")
        elif c.sugar_count == 3:
            parts.append("🍬🍬🍬 3 ложки сахара")
    
    # Температура
    if c.temperature:
        temp_names = {
            "hot": "🔥 горячий",
            "warm": "🌡 тёплый",
            "cold": "❄️ холодный (айс)"
        }
        if c.temperature in temp_names:
            parts.append(temp_names[c.temperature])
    
    # Топпинги
    toppings = []
    if c.whipped_cream:
        toppings.append("🥛 взбитые сливки")
    if c.cinnamon:
        toppings.append("⚜️ корица")
    if c.cocoa:
        toppings.append("🍫 какао")
    if c.caramel_syrup:
        toppings.append("🍯 карамельный сироп")
    if c.vanilla_syrup:
        toppings.append("🌿 ванильный сироп")
    
    if toppings:
        parts.append("➕ " + ", ".join(toppings))
    
    if parts:
        return "    📝 " + "\n    📝 ".join(parts)
    return ""


@router.message(F.text == "📊 Активные заказы")
@staff_required
async def show_active_orders(message: Message):
    """
    Показать активные заказы (только для бариста/админа)
    """
    orders = await get_active_orders()
    
    if not orders:
        await message.answer("📊 Нет активных заказов")
        return
    
    text = "📊 <b>Активные заказы:</b>\n\n"
    
    buttons = []
    
    for order in orders:
        # ✅ НОВОЕ: Получаем информацию о клиенте
        user = await get_user_by_id(order.user_id)
        
        # Способ оплаты
        payment_emoji = "💵" if order.payment_method == "cash" else "💳"
        payment_text = "Наличными" if order.payment_method == "cash" else "Картой"
        
        text += f"🆔 <b>Заказ №{order.id}</b>\n"
        text += f"⏰ Время: {format_order_time(order.created_at)}\n"
        
        # ✅ НОВОЕ: Показываем телефон клиента
        if user and user.phone_number:
            text += f"📱 Телефон: {user.phone_number}\n"
        elif user:
            text += f"👤 Клиент: {user.first_name or 'Неизвестно'}\n"
        
        text += f"💰 Сумма: {order.total_price} ₽\n"
        text += f"{payment_emoji} Оплата: {payment_text}\n"
        
        # Товары в заказе
        text += "📋 <b>Состав заказа:</b>\n"
        for item in order.items:
            text += f"  • {item.product.name} x{item.quantity}\n"
            
            # Показываем кастомизацию если есть
            custom_text = format_customization_text(item)
            if custom_text:
                text += f"{custom_text}\n"
        
        text += "\n" + "─" * 40 + "\n\n"
        
        # Кнопка для завершения заказа
        buttons.append([
            InlineKeyboardButton(
                text=f"✅ Завершить заказ №{order.id}",
                callback_data=f"complete_order:{order.id}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("complete_order:"))
@staff_required
async def complete_order_callback(callback: CallbackQuery):
    """
    Завершить заказ (кнопка для бариста)
    """
    order_id = int(callback.data.split(":")[1])
    
    # 👇 Получаем заказ через правильную функцию
    from services.order_service import get_order_by_id, mark_order_as_completed
    order = await get_order_by_id(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    # Завершаем заказ
    completed_order = await mark_order_as_completed(order_id)
    
    if completed_order:
        # Уведомляем клиента
        await notify_customer_status_change(completed_order)
        
        await callback.answer(f"✅ Заказ №{order_id} завершён! Клиент уведомлён.", show_alert=True)
        
        # Обновляем список активных заказов
        orders = await get_active_orders()
        
        if not orders:
            await callback.message.edit_text("📊 Нет активных заказов")
            return
        
        # Перестраиваем сообщение
        text = "📊 <b>Активные заказы:</b>\n\n"
        buttons = []
        
        for o in orders:
            # ✅ НОВОЕ: Получаем информацию о клиенте
            user = await get_user_by_id(o.user_id)
            
            payment_emoji = "💵" if o.payment_method == "cash" else "💳"
            payment_text = "Наличными" if o.payment_method == "cash" else "Картой"
            
            text += f"🆔 <b>Заказ №{o.id}</b>\n"
            text += f"⏰ Время: {format_order_time(o.created_at)}\n"
            
            # ✅ НОВОЕ: Показываем телефон клиента
            if user and user.phone_number:
                text += f"📱 Телефон: {user.phone_number}\n"
            elif user:
                text += f"👤 Клиент: {user.first_name or 'Неизвестно'}\n"
            
            text += f"💰 Сумма: {o.total_price} ₽\n"
            text += f"{payment_emoji} Оплата: {payment_text}\n"
            text += "📋 <b>Состав заказа:</b>\n"
            
            for item in o.items:
                text += f"  • {item.product.name} x{item.quantity}\n"
                
                # Показываем кастомизацию
                custom_text = format_customization_text(item)
                if custom_text:
                    text += f"{custom_text}\n"
            
            text += "\n" + "─" * 40 + "\n\n"
            
            buttons.append([
                InlineKeyboardButton(
                    text=f"✅ Завершить заказ №{o.id}",
                    callback_data=f"complete_order:{o.id}"
                )
            ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await callback.answer("❌ Не удалось завершить заказ", show_alert=True)