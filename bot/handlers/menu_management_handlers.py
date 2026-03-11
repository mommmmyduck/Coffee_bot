from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.decorators import staff_required
from services.menu_service import (
    get_all_products,
    toggle_product_active,
    get_products_by_category
)
from database.models.product import ProductCategory

router = Router()

# -----------------------
# Главное меню управления
# -----------------------
@router.message(F.text == "⚙️ Управление меню")
@staff_required
async def menu_management(message: Message):
    """Главное меню управления товарами"""
    user = message.from_user._user
    
    text = "⚙️ <b>Управление меню</b>\n\n"
    text += "Выберите действие:"
    
    buttons = [
        [InlineKeyboardButton(
            text="🔄 Изменить доступность товара",
            callback_data="menu_toggle_product"
        )],
        [InlineKeyboardButton(
            text="📋 Список всех товаров",
            callback_data="menu_list_all"
        )],
    ]
    
    # Для админа добавляем полный функционал
    if user.role == "owner":
        buttons.insert(0, [InlineKeyboardButton(
            text="⚙️ Полное управление (Админ)",
            callback_data="admin_menu_management"
        )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# -----------------------
# Показать все товары
# -----------------------
@router.callback_query(F.data == "menu_list_all")
@staff_required
async def menu_list_all_products(callback: CallbackQuery):
    """Показать все товары со статусом"""
    products = await get_all_products(active_only=False)
    
    if not products:
        await callback.message.edit_text("📋 Товары не найдены")
        return
    
    text = "📋 <b>Все товары:</b>\n\n"
    
    for product in products:
        status = "✅" if product.is_active else "❌"
        text += f"{status} <b>{product.name}</b>\n"
        text += f"   🆔 ID: {product.id}\n"
        text += f"   💰 Цена: {product.price} ₽\n"
        text += f"   📂 Категория: {product.category.value}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_back")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# -----------------------
# Изменить доступность
# -----------------------
@router.callback_query(F.data == "menu_toggle_product")
@staff_required
async def menu_toggle_choose_category(callback: CallbackQuery):
    """Выбрать категорию для toggle"""
    text = "🔄 <b>Изменение доступности</b>\n\n"
    text += "Выберите категорию товара:"
    
    buttons = []
    category_names = {
        ProductCategory.coffee: "☕ Кофе",
        ProductCategory.non_coffee: "🍵 Напитки",
        ProductCategory.bakery: "🥐 Выпечка",
        ProductCategory.desserts: "🍰 Десерты",
    }
    
    for category, name in category_names.items():
        buttons.append([
            InlineKeyboardButton(
                text=name,
                callback_data=f"toggle_category:{category.name}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu_back")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_category:"))
@staff_required
async def menu_toggle_show_products(callback: CallbackQuery):
    """Показать товары категории для toggle"""
    category_name = callback.data.split(":")[1]
    category = ProductCategory[category_name]
    
    products = await get_products_by_category(category, active_only=False)
    
    if not products:
        await callback.answer("В этой категории нет товаров", show_alert=True)
        return
    
    category_display = {
        ProductCategory.coffee: "☕ Кофе",
        ProductCategory.non_coffee: "🍵 Напитки",
        ProductCategory.bakery: "🥐 Выпечка",
        ProductCategory.desserts: "🍰 Десерты",
    }
    
    text = f"🔄 <b>Категория: {category_display[category]}</b>\n\n"
    text += "Выберите товар для изменения доступности:\n\n"
    
    buttons = []
    for product in products:
        status_emoji = "✅" if product.is_active else "❌"
        status_text = "В наличии" if product.is_active else "Нет в наличии"
        
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} {product.name} ({status_text})",
                callback_data=f"toggle_product:{product.id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu_toggle_product")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_product:"))
@staff_required
async def menu_toggle_execute(callback: CallbackQuery):
    """Переключить доступность товара"""
    product_id = int(callback.data.split(":")[1])
    
    product = await toggle_product_active(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    status = "✅ В наличии" if product.is_active else "❌ Нет в наличии"
    
    await callback.answer(
        f"Товар: {product.name}\nСтатус: {status}",
        show_alert=True
    )
    
    # Возвращаемся к списку товаров в категории
    await menu_toggle_show_products(callback)


@router.callback_query(F.data == "menu_back")
@staff_required
async def menu_back(callback: CallbackQuery):
    """Вернуться в главное меню управления"""
    await menu_management(callback.message)
    await callback.answer()