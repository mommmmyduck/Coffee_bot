# bot/handlers/menu_handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from services.menu_service import get_products_by_category, get_product_by_id
from services.order_service import add_to_cart, get_user_cart
from database.models.product import ProductCategory
from bot.keyboards.menu_keyboards import (
    get_categories_keyboard,
    get_products_keyboard,
    get_product_detail_keyboard
)
from bot.keyboards.order_keyboards import get_cart_keyboard

router = Router()


# -----------------------
# Меню и категории
# -----------------------

@router.message(Command("menu"))
@router.message(F.text == "📋 Меню")
async def cmd_menu(message: Message):
    await message.answer(
        "Выберите категорию:",
        reply_markup=get_categories_keyboard()
    )


@router.callback_query(F.data.startswith("category:"))
async def show_category_products(callback: CallbackQuery):
    category_name = callback.data.split(":")[1]
    category = ProductCategory[category_name]

    products = await get_products_by_category(category, active_only=False)
    
    if not products:
        await callback.message.edit_text(
            f"В категории '{category.value}' пока нет товаров."
        )
        return
    
    await callback.message.edit_text(
        f"Категория: {category.value}\n\nВыберите товар:",
        reply_markup=get_products_keyboard(products)
    )
    await callback.answer()


# -----------------------
# Детали товара
# -----------------------

@router.callback_query(F.data.startswith("product:"))
async def show_product_detail(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    text = f"<b>{product.name}</b>\n\n"
    if product.description:
        text += f"{product.description}\n\n"
    if product.volume:
        text += f"📏 Объём: {product.volume} мл\n"
    if product.weight:
        text += f"⚖️ Вес: {product.weight} г\n"
    text += f"\n💰 Цена: <b>{product.price} ₽</b>"

    if product.is_active:
        text += f"\n✅ Статус: <b>В наличии</b>"
    else:
        text += f"\n❌ Статус: <b>Нет в наличии</b>"

    # Фото или текст
    if product.image_url:
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=product.image_url,
            caption=text,
            reply_markup=get_product_detail_keyboard(product),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text,
            reply_markup=get_product_detail_keyboard(product),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.callback_query(F.data == "product_unavailable")
async def product_unavailable_handler(callback: CallbackQuery):
    await callback.answer(
        "❌ Этот товар временно недоступен",
        show_alert=True
    )


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    # Удаляем сообщение с товаром (где было фото)
    await callback.message.delete()
    
    # Отправляем новое сообщение с выбором категорий
    await callback.message.answer(
        text="Выберите категорию меню:",
        reply_markup=get_categories_keyboard() # Твоя функция клавиатуры категорий
    )
    await callback.answer()