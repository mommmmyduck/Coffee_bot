#bot/handlers/history_handlers.py
from aiogram import Router, F
from aiogram.types import Message
from services.order_service import get_user_order_history_today

router = Router()

@router.message(F.text == "📦 История заказов")
async def show_order_history(message: Message):
    """
    Показать историю заказов пользователя за сегодня
    """
    user = message.from_user._user
    orders = await get_user_order_history_today(user.id)
    
    if not orders:
        await message.answer("📦 У вас пока нет выполненных заказов сегодня")
        return
    
    text = "📦 <b>История заказов за сегодня:</b>\n\n"
    
    for order in orders:
        text += f"🆔 Заказ №{order.id}\n"
        text += f"📅 {order.created_at.strftime('%H:%M')}\n"
        text += f"💰 Сумма: {order.total_price} ₽\n"
        text += f"✅ Статус: Выполнен\n"
        
        # Товары в заказе
        text += "📋 Товары:\n"
        for item in order.items:
            text += f"  • {item.product.name} x{item.quantity}\n"
        
        text += "\n" + "─" * 30 + "\n\n"
    
    await message.answer(text, parse_mode="HTML")