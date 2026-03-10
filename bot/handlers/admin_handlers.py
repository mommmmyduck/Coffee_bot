#bot/handlers/admin_handlers.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.utils.decorators import admin_required
from services.menu_service import toggle_product_active, get_product_by_id

router = Router()

@router.message(Command("toggle"))
@admin_required
async def cmd_toggle_product(message: Message):
    """
    Переключить доступность товара
    Формат: /toggle <product_id>
    """
    parts = message.text.split()
    
    if len(parts) != 2:
        await message.answer("Использование: /toggle <product_id>")
        return
    
    try:
        product_id = int(parts[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return
    
    product = await toggle_product_active(product_id)
    
    if not product:
        await message.answer("❌ Товар не найден")
        return
    
    status = "✅ В наличии" if product.is_active else "❌ Нет в наличии"
    await message.answer(
        f"Товар: {product.name}\n"
        f"Новый статус: {status}"
    )