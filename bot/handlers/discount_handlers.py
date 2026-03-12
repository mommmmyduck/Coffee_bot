from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.utils.decorators import admin_required
from services.discount_service import set_category_discount, remove_all_discounts
from database.models.product import ProductCategory

router = Router()

class DiscountStates(StatesGroup):
    """Состояния для установки скидки"""
    enter_percent = State()


# -----------------------
# Главное меню скидок
# -----------------------

@router.message(F.text == "🏷️ Скидки")
@admin_required
async def show_discount_menu(message: Message):
    """Меню управления скидками"""
    text = "🏷️ <b>Управление скидками</b>\n\n"
    text += "Установите скидку на целую категорию товаров:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="☕ Скидка на кофе",
            callback_data="discount:coffee"
        )],
        [InlineKeyboardButton(
            text="🍵 Скидка на напитки",
            callback_data="discount:non_coffee"
        )],
        [InlineKeyboardButton(
            text="🥐 Скидка на выпечку",
            callback_data="discount:bakery"
        )],
        [InlineKeyboardButton(
            text="🍰 Скидка на десерты",
            callback_data="discount:desserts"
        )],
        [InlineKeyboardButton(
            text="🗑 Убрать все скидки",
            callback_data="discount:remove_all"
        )],
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("discount:"))
@admin_required
async def discount_choose_category(callback: CallbackQuery, state: FSMContext):
    """Выбрать категорию для скидки"""
    action = callback.data.split(":")[1]
    
    if action == "remove_all":
        await remove_all_discounts()
        await callback.message.edit_text("✅ Все скидки убраны!")
        await callback.answer()
        return
    
    # Сохраняем категорию
    category = ProductCategory[action]
    await state.update_data(discount_category=category)
    await state.set_state(DiscountStates.enter_percent)
    
    category_names = {
        ProductCategory.coffee: "☕ Кофе",
        ProductCategory.non_coffee: "🍵 Напитки",
        ProductCategory.bakery: "🥐 Выпечку",
        ProductCategory.desserts: "🍰 Десерты",
    }
    
    text = f"🏷️ <b>Скидка на {category_names[category]}</b>\n\n"
    text += "Введите процент скидки (от 1 до 100):\n\n"
    text += "Например: 20"
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(DiscountStates.enter_percent)
@admin_required
async def discount_set_percent(message: Message, state: FSMContext):
    """Установить процент скидки"""
    try:
        percent = int(message.text.strip())
        
        if not (1 <= percent <= 100):
            await message.answer("❌ Процент должен быть от 1 до 100. Попробуйте снова:")
            return
    except ValueError:
        await message.answer("❌ Введите число от 1 до 100:")
        return
    
    data = await state.get_data()
    category = data['discount_category']
    
    # Устанавливаем скидку
    updated_count = await set_category_discount(category, percent)
    
    category_names = {
        ProductCategory.coffee: "кофе",
        ProductCategory.non_coffee: "напитки",
        ProductCategory.bakery: "выпечку",
        ProductCategory.desserts: "десерты",
    }
    
    text = f"✅ <b>Скидка установлена!</b>\n\n"
    text += f"🏷️ Категория: {category_names[category]}\n"
    text += f"💰 Скидка: {percent}%\n"
    text += f"📦 Обновлено товаров: {updated_count}"
    
    await message.answer(text, parse_mode="HTML")
    await state.clear()