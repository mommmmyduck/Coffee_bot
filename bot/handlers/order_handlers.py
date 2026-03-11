# bot/handlers/order_handlers.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from bot.keyboards.order_keyboards import get_cart_keyboard, get_payment_method_keyboard
from config import PROVIDER_TOKEN
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.notification_service import notify_staff_new_order, notify_staff_order_cancelled

from database.models.product import ProductCategory
from services.menu_service import get_product_by_id
from services.order_service import (
    get_user_cart,
    add_to_cart,
    remove_from_cart,
    confirm_order,
    cancel_order,
    finalize_order,
    spend_bonus_points,
    get_order_by_id,
    get_awaiting_payment_order,
    format_cart_text,  # 👈 ДОБАВЛЯЕМ ИМПОРТ
    format_cart_text_short  # 👈 ОПЦИОНАЛЬНО
)
from database.database import SessionLocal
from database.models.order import Order
from sqlalchemy import select

router = Router()

# Состояние для ввода суммы бонусов
class BonusState(StatesGroup):
    waiting_for_amount = State()


# -----------------------
# Добавление товара в корзину
# -----------------------
@router.callback_query(F.data.startswith("add_to_cart:"))
async def start_customization(callback: CallbackQuery, state: FSMContext):
    """
    Начать процесс кастомизации напитка
    """
    from bot.states.customization_states import CustomizationStates
    from bot.keyboards.customization_keyboards import get_milk_keyboard
    
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    # Проверяем что это кофе (только кофе можно кастомизировать)
    if product.category == ProductCategory.coffee:
        # Сохраняем product_id в FSM
        await state.update_data(product_id=product_id)
        await state.set_state(CustomizationStates.choose_milk)
        
        await callback.message.answer(
            f"☕ Настройка напитка: <b>{product.name}</b>\n\n"
            f"Шаг 1/4: Выберите тип молока:",
            reply_markup=get_milk_keyboard(product_id),
            parse_mode="HTML"
        )
        
        try:
            await callback.message.delete()
        except:
            pass
    else:
        user = callback.from_user._user
        await add_to_cart(user.id, product_id, quantity=1)
        await callback.answer("✅ Товар добавлен в корзину!")
        
        await callback.message.answer(
            f"✅ <b>{product.name}</b> добавлен в корзину!\n"
            f"💰 Цена: {product.price} ₽\n\n"
            f"🛒 Чтобы посмотреть корзину, нажми /cart",
            parse_mode="HTML"
        )
    
    await callback.answer()
    

# -----------------------
# Просмотр корзины
# -----------------------
@router.message(F.text == "🛒 Корзина")
@router.message(F.text == "/cart")
async def show_cart(message: Message):
    user = message.from_user._user
    
    # Проверяем, есть ли заказ, ожидающий оплаты
    awaiting_order = await get_awaiting_payment_order(user.id)
    
    if awaiting_order:
        cart_text = await format_cart_text(awaiting_order)  # 👈 ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
        await message.answer(
            f"⏳ <b>У вас есть заказ, ожидающий оплаты</b>\n\n"
            f"{cart_text}\n\n"
            f"Пожалуйста, завершите оплату или отмените заказ:",
            reply_markup=get_payment_method_keyboard(awaiting_order.id),
            parse_mode="HTML"
        )
        return
    
    # Обычная корзина
    order = await get_user_cart(user.id)
    if order and order.items:
        is_staff = user.role in ("seller", "owner")
        cart_text = await format_cart_text(order)  # 👈 ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ
        await message.answer(
            cart_text,
            reply_markup=get_cart_keyboard(order, is_staff=is_staff),
            parse_mode="HTML"
        )
    else:
        await message.answer("🛒 Корзина пуста")


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
        # 👇 ОБНОВЛЯЕМ ТЕКСТ ПРИ УДАЛЕНИИ
        cart_text = await format_cart_text(order)
        await callback.message.edit_text(
            cart_text,
            reply_markup=get_cart_keyboard(order, is_staff=is_staff),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("🛒 Корзина пуста")

    await callback.answer()


# -----------------------
# Подтверждение заказа
# -----------------------
@router.callback_query(F.data.startswith("confirm_order:"))
async def confirm_order_handler(callback: CallbackQuery):
    """Показать выбор способа оплаты"""
    order_id = int(callback.data.split(":")[1])
    
    # 👇 НЕ вызываем confirm_order здесь!
    # Просто получаем заказ для отображения
    from services.order_service import get_order_by_id
    order = await get_order_by_id(order_id)
    
    if not order:
        await callback.message.edit_text("❌ Заказ не найден.")
        await callback.answer()
        return
    
    # Показываем кнопки выбора способа оплаты
    await callback.message.edit_text(
        f"✅ Заказ №{order.id} сформирован!\n\n"
        f"💰 Сумма: {order.total_price} ₽\n\n"
        f"Теперь выберите способ оплаты:",
        reply_markup=get_payment_method_keyboard(order.id)
    )
    
    await callback.answer()
# -----------------------
# Отмена заказа
# -----------------------

@router.callback_query(F.data.startswith("cancel_order:"))
async def cancel_order_handler(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order = await cancel_order(order_id)

    if order:
        # ✅ НОВОЕ: Уведомляем баристов об отмене
        await notify_staff_order_cancelled(order, cancelled_by_user=True)
        
        await callback.message.edit_text("❌ Заказ отменён")
    else:
        await callback.message.edit_text("Ошибка при отмене заказа")

    await callback.answer()


# -----------------------
# Обработка оплаты наличными с бонусами
# -----------------------
@router.callback_query(F.data.startswith("pay_cash:"))
async def process_pay_cash(callback: CallbackQuery):
    """Обработка оплаты наличными - спрашиваем про бонусы"""
    order_id = int(callback.data.split(":")[1])
    
    from bot.keyboards.bonus_keyboards import get_bonus_keyboard
    
    order = await get_order_by_id(order_id)
    user = callback.from_user._user
    
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    # Показываем информацию о бонусах
    text = (
        f"💵 Оплата наличными\n\n"
        f"Заказ №{order.id}\n"
        f"💰 Сумма: {order.total_price} ₽\n"
        f"💎 Ваши бонусы: {user.bonus_points} (1 бонус = 1 рубль)\n\n"
        f"Хотите использовать бонусы для оплаты?"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_bonus_keyboard(order_id, user.bonus_points, order.total_price, "cash")
    )
    await callback.answer()


# -----------------------
# Обработка оплаты картой с бонусами
# -----------------------
@router.callback_query(F.data.startswith("pay_card:"))
async def process_pay_card(callback: CallbackQuery):
    """Обработка оплаты картой - спрашиваем про бонусы"""
    order_id = int(callback.data.split(":")[1])
    
    from bot.keyboards.bonus_keyboards import get_bonus_keyboard
    
    order = await get_order_by_id(order_id)
    user = callback.from_user._user
    
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    text = (
        f"💳 Оплата картой\n\n"
        f"Заказ №{order.id}\n"
        f"💰 Сумма: {order.total_price} ₽\n"
        f"💎 Ваши бонусы: {user.bonus_points} (1 бонус = 1 рубль)\n\n"
        f"Хотите использовать бонусы для оплаты?"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_bonus_keyboard(order_id, user.bonus_points, order.total_price, "card")
    )
    await callback.answer()


# -----------------------
# Использование бонусов
# -----------------------
@router.callback_query(F.data.startswith("use_bonus:"))
async def use_bonus_handler(callback: CallbackQuery, state: FSMContext):
    """Использовать бонусы для оплаты"""
    _, order_id_str, bonus_amount_str, payment_method = callback.data.split(":")
    order_id = int(order_id_str)
    bonus_amount = int(bonus_amount_str)
    
    order = await get_order_by_id(order_id)
    user = callback.from_user._user
    
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    # Списываем бонусы
    updated_user = await spend_bonus_points(user.id, bonus_amount)
    
    if not updated_user:
        await callback.answer("❌ Недостаточно бонусов", show_alert=True)
        return
    
    # Уменьшаем сумму заказа
    new_total = max(0, order.total_price - bonus_amount)
    
    # Обновляем сумму в заказе
    async with SessionLocal() as session:
        stmt = select(Order).where(Order.id == order_id)
        result = await session.execute(stmt)
        db_order = result.scalars().first()
        if db_order:
            db_order.total_price = new_total
            await session.commit()
    
    # Финальное подтверждение в зависимости от способа оплаты
    if payment_method == "cash":
        # Для наличных - сразу подтверждаем
        confirmed_order = await confirm_order(order_id, "cash")
        if confirmed_order:
            # 👇 УВЕДОМЛЯЕМ БАРИСТА
            await notify_staff_new_order(confirmed_order)
            
            await callback.message.edit_text(
                f"✅ Заказ №{order_id} принят!\n"
                f"💵 Оплата при получении.\n"
                f"💰 Списано бонусов: {bonus_amount}\n"
                f"💎 Осталось бонусов: {updated_user.bonus_points}\n"
                f"💳 К оплате: {new_total} ₽\n\n"
                f"Ждем вас! ☕"
            )
        else:
            await callback.message.edit_text("❌ Ошибка при оформлении заказа")
    
    else:  # card
        # Для карты - создаем инвойс с обновленной суммой
        prices = [LabeledPrice(
            label=f"Заказ №{order_id} (с учетом бонусов)",
            amount=int(new_total * 100)
        )]
        
        await callback.message.answer_invoice(
            title=f"Оплата заказа №{order_id}",
            description=f"Списано бонусов: {bonus_amount}",
            payload=f"order_{order_id}",
            provider_token=PROVIDER_TOKEN,
            currency="rub",
            prices=prices,
            start_parameter=f"order_{order_id}"
        )
        
        # Отправляем отдельное сообщение с информацией о бонусах
        await callback.message.answer(
            f"✅ Списано {bonus_amount} бонусов!\n"
            f"💎 Осталось бонусов: {updated_user.bonus_points}\n"
            f"💰 Сумма к оплате картой: {new_total} ₽"
        )
    
    await callback.answer()

# -----------------------
# Пропустить использование бонусов
# -----------------------
@router.callback_query(F.data.startswith("skip_bonus:"))
async def skip_bonus_handler(callback: CallbackQuery):
    """Пропустить использование бонусов"""
    _, order_id_str, payment_method = callback.data.split(":")
    order_id = int(order_id_str)
    
    order = await get_order_by_id(order_id)
    
    if payment_method == "cash":
        # Для наличных - сразу подтверждаем
        confirmed_order = await confirm_order(order_id, "cash")
        if confirmed_order:
            # 👇 УВЕДОМЛЯЕМ БАРИСТА
            await notify_staff_new_order(confirmed_order)
            
            await callback.message.edit_text(
                f"✅ Заказ №{order_id} принят!\n"
                f"💵 Оплата при получении.\n"
                f"💰 Сумма: {order.total_price} ₽\n\n"
                f"Ждем вас! ☕"
            )
        else:
            await callback.message.edit_text("❌ Ошибка при оформлении заказа")
    
    else:  # card
        # Для карты - создаем инвойс
        prices = [LabeledPrice(
            label=f"Заказ №{order_id}",
            amount=int(order.total_price * 100)
        )]
        
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


# -----------------------
# Своя сумма бонусов
# -----------------------
@router.callback_query(F.data.startswith("custom_bonus:"))
async def custom_bonus_handler(callback: CallbackQuery, state: FSMContext):
    """Запрос своей суммы для списания бонусов"""
    _, order_id_str, payment_method = callback.data.split(":")
    order_id = int(order_id_str)
    
    await state.set_state(BonusState.waiting_for_amount)
    await state.update_data(order_id=order_id, payment_method=payment_method)
    
    from bot.keyboards.bonus_keyboards import get_custom_bonus_keyboard
    await callback.message.edit_text(
        f"✏️ Введите сумму бонусов для списания (от 1 до {callback.from_user._user.bonus_points}):\n"
        f"❗️ Минимальная сумма: 1 рубль",
        reply_markup=get_custom_bonus_keyboard(order_id, payment_method)
    )
    await callback.answer()


@router.message(BonusState.waiting_for_amount)
async def process_custom_bonus(message: Message, state: FSMContext):
    """Обработка введенной суммы"""
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число")
        return
    
    data = await state.get_data()
    order_id = data['order_id']
    payment_method = data['payment_method']
    user = message.from_user._user
    
    if amount < 1:
        await message.answer("❌ Минимальная сумма списания - 1 рубль")
        return
    
    if amount > user.bonus_points:
        await message.answer(f"❌ У вас только {user.bonus_points} бонусов")
        return
    
    # Получаем заказ для проверки суммы
    order = await get_order_by_id(order_id)
    
    if not order:
        await message.answer("❌ Заказ не найден")
        await state.clear()
        return
    
    if amount > order.total_price:
        await message.answer(f"❌ Нельзя списать больше суммы заказа ({order.total_price} ₽)")
        return
    
    # Имитируем нажатие на кнопку use_bonus
    fake_callback_data = f"use_bonus:{order_id}:{amount}:{payment_method}"
    
    # Создаем объект callback
    from aiogram.types import CallbackQuery
    fake_callback = CallbackQuery(
        id="fake",
        from_user=message.from_user,
        chat_instance="fake",
        message=message,
        data=fake_callback_data
    )
    
    # Вызываем обработчик
    await use_bonus_handler(fake_callback, state)
    await state.clear()


@router.callback_query(F.data.startswith("back_to_bonus:"))
async def back_to_bonus_handler(callback: CallbackQuery, state: FSMContext):
    """Вернуться к выбору бонусов"""
    _, order_id_str, payment_method = callback.data.split(":")
    order_id = int(order_id_str)
    
    from bot.keyboards.bonus_keyboards import get_bonus_keyboard
    
    order = await get_order_by_id(order_id)
    user = callback.from_user._user
    
    await state.clear()
    
    text = (
        f"{'💵' if payment_method == 'cash' else '💳'} Оплата {'наличными' if payment_method == 'cash' else 'картой'}\n\n"
        f"Заказ №{order.id}\n"
        f"💰 Сумма: {order.total_price} ₽\n"
        f"💎 Ваши бонусы: {user.bonus_points}\n\n"
        f"Хотите использовать бонусы для оплаты?"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_bonus_keyboard(order_id, user.bonus_points, order.total_price, payment_method)
    )
    await callback.answer()


# -----------------------
# Отмена оплаты
# -----------------------
@router.callback_query(F.data.startswith("cancel_payment:"))
async def cancel_payment_handler(callback: CallbackQuery):
    """Отмена оплаты - возвращаем заказ в корзину"""
    order_id = int(callback.data.split(":")[1])
    
    from services.order_service import cancel_order_payment
    order = await cancel_order_payment(order_id)
    
    if order:
        await callback.message.delete()
        
        from bot.keyboards.user_keyboards import get_main_keyboard
        await callback.message.answer(
            f"❌ Оплата заказа №{order_id} отменена.\n\n"
            f"Заказ возвращен в корзину. Вы можете:\n"
            f"• Продолжить покупки\n"
            f"• Выбрать другой способ оплаты\n"
            f"• Удалить товары из корзины",
            reply_markup=get_main_keyboard()
        )
    else:
        await callback.answer("❌ Ошибка при отмене", show_alert=True)
    
    await callback.answer()



# -----------------------
# Завершение заказа для сотрудников
# -----------------------
@router.callback_query(F.data.startswith("complete_order:"))
async def complete_order_handler(callback: CallbackQuery):
    user = callback.from_user._user
    if user.role not in ("seller", "owner"):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])
    
    order = await get_order_by_id(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return

    await finalize_order(order)

    await callback.message.edit_text(
        f"✅ Заказ №{order_id} выполнен!\n💰 Итог: {order.total_price} ₽\n💎 Бонусы: {order.bonus_points}"
    )
    await callback.answer()


# -----------------------
# PreCheckout и успешная оплата
# -----------------------
@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """Подтверждение перед оплатой"""
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Обработка успешной оплаты"""
    payload = message.successful_payment.invoice_payload
    order_id = int(payload.split("_")[1])
    
    from services.order_service import confirm_payment
    order = await confirm_payment(order_id)
    
    if order:
        # 👇 УВЕДОМЛЯЕМ БАРИСТА
        await notify_staff_new_order(order)
        
        await message.answer(
            f"✅ Оплата прошла успешно!\n\n"
            f"Ваш заказ №{order_id} передан в работу.\n"
            f"Статус заказа можно отслеживать у бариста.\n\n"
            f"Спасибо за заказ! ☕"
        )
    else:
        await message.answer(
            f"❌ Ошибка при обработке заказа.\n"
            f"Пожалуйста, обратитесь к администратору."
        )