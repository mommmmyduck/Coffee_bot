#bot/handlers/order_handlers.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from bot.keyboards.order_keyboards import get_cart_keyboard, get_payment_method_keyboard
from config import PROVIDER_TOKEN

from services.order_service import (
    get_user_cart,
    add_to_cart,
    remove_from_cart,
    confirm_order,
    cancel_order,
    finalize_order
)
from bot.keyboards.order_keyboards import get_cart_keyboard

router = Router()


# -----------------------
# Добавление товара в корзину
# -----------------------
@router.callback_query(F.data.startswith("add_to_cart:"))
@router.callback_query(F.data.startswith("add_to_cart:"))
async def add_to_cart_handler(callback: CallbackQuery):
    product_id = int(callback.data.split(":")[1])
    user = callback.from_user._user

    order = await add_to_cart(user.id, product_id, quantity=1)
    
    # Просто уведомляем пользователя всплывашкой (не ломает сообщение)
    await callback.answer("✅ Товар добавлен в корзину!")

# -----------------------
# Просмотр корзины
# -----------------------
@router.message(F.text == "🛒 Корзина")
@router.message(F.text == "/cart")
async def show_cart(message: Message):
    user = message.from_user._user
    order = await get_user_cart(user.id)

    if order and order.items:
        is_staff = user.role in ("seller", "owner")
        await message.answer("Ваша корзина:", reply_markup=get_cart_keyboard(order, is_staff=is_staff))
    else:
        await message.answer("Корзина пуста")


# -----------------------
# Удаление товара из корзины
# -----------------------
@router.callback_query(F.data.startswith("remove_item:"))
async def remove_item_handler(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[1])
    user = callback.from_user._user

    await remove_from_cart(item_id)
    order = await get_user_cart(user.id)

    if order and order.items:
        is_staff = user.role in ("seller", "owner")
        keyboard = get_cart_keyboard(order, is_staff=is_staff)
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await callback.message.edit_text("Корзина пуста")

    await callback.answer()


# -----------------------
# Подтверждение и отмена заказа
# -----------------------
@router.callback_query(F.data.startswith("confirm_order:"))
async def confirm_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await confirm_order(order_id) # Здесь статус меняется на confirmed

    if order:
        await callback.message.edit_text(
            f"Заказ №{order.id} сформирован.\nСумма: {order.total_price} ₽\nВыберите способ оплаты:",
            # Передаем ID сюда
            reply_markup=get_payment_method_keyboard(order.id) 
        )
    else:
        await callback.message.edit_text("Заказ не найден.")
    await callback.answer()

@router.callback_query(F.data.startswith("cancel_order:"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await cancel_order(order_id)

    if order:
        await callback.message.edit_text("❌ Заказ отменён")
    else:
        await callback.message.edit_text("Ошибка при отмене заказа")

    await callback.answer()


# -----------------------
# Завершение заказа для сотрудников/админа
# -----------------------
@router.callback_query(F.data.startswith("complete_order:"))
async def complete_order_handler(callback: CallbackQuery):
    user = callback.from_user._user
    if user.role not in ("seller", "owner"):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    order = await get_user_cart(user.id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    await finalize_order(order)

    await callback.message.edit_text(
        f"✅ Заказ выполнен!\n💰 Итог: {order.total_price} ₽\n💎 Бонусы: {order.bonus_points}"
    )
    await callback.answer()

# -----------------------
# Оплата заказа
# -----------------------

@router.callback_query(F.data == "checkout")
async def checkout_handler(callback: CallbackQuery):
    """Этап 1: Выбор способа оплаты"""
    user = callback.from_user._user
    order = await get_user_cart(user.id)
    
    if not order or not order.items:
        await callback.answer("Ваша корзина пуста!", show_alert=True)
        return

    await callback.message.edit_text(
        f"Сумма к оплате: {order.total_price} ₽\nВыберите способ оплаты:",
        reply_markup=get_payment_method_keyboard()
    )

@router.callback_query(F.data.startswith("pay_cash:"))
async def process_pay_cash(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    # Нам больше не нужно искать 'pending' заказ, у нас есть ID
    await callback.message.edit_text(
        f"✅ Заказ №{order_id} принят!\nОплата при получении. Ждем вас!"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("pay_card:"))
async def process_pay_card(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    
    # Здесь можно добавить получение заказа по ID из сервиса, чтобы узнать цену
    # Например: order = await get_order_by_id(order_id)
    
    # Для теста оставим фиксированную или динамическую цену, если есть объект order
    prices = [LabeledPrice(label=f"Заказ №{order_id}", amount=25000)] 

    await callback.message.answer_invoice(
        title=f"Оплата заказа №{order_id}",
        description="Кофе и десерты",
        payload=f"order_{order_id}",
        provider_token=PROVIDER_TOKEN, 
        currency="rub",
        prices=prices,
        start_parameter=f"order_{order_id}"
    )
    await callback.answer()