from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.order_service import get_user_active_orders, get_order_by_id, cancel_order
from database.models.order import get_status_display, get_status_emoji, OrderStatus
from bot.utils.time_utils import format_order_time
from services.notification_service import notify_staff_order_cancelled

router = Router()

# Константы для пагинации
ORDERS_PER_PAGE = 5  # Показывать по 5 заказов на странице


# -----------------------
# Активные заказы клиента с пагинацией
# -----------------------
@router.message(F.text == "📦 Мои заказы")
async def show_user_active_orders(message: Message):
    """
    Показать активные заказы пользователя (первая страница)
    """
    await show_orders_page(message, page=0)


async def show_orders_page(message: Message, page: int = 0):
    """
    Показать страницу с заказами
    """
    user = message.from_user._user
    all_orders = await get_user_active_orders(user.id)
    
    if not all_orders:
        await message.answer(
            "📦 У вас нет активных заказов\n\n"
            "Когда вы оформите заказ, он появится здесь, "
            "и вы сможете отслеживать его статус в реальном времени! 📍"
        )
        return
    
    # Рассчитываем пагинацию
    total_orders = len(all_orders)
    total_pages = (total_orders + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE
    start_idx = page * ORDERS_PER_PAGE
    end_idx = min(start_idx + ORDERS_PER_PAGE, total_orders)
    
    # Заказы для текущей страницы
    orders = all_orders[start_idx:end_idx]
    
    text = f"📦 <b>Ваши активные заказы</b> (страница {page + 1}/{total_pages}):\n\n"
    
    buttons = []
    
    for order in orders:
        status_emoji = get_status_emoji(order.status)
        status_text = get_status_display(order.status)
        
        text += f"{status_emoji} <b>Заказ №{order.id}</b>\n"
        text += f"📅 Время: {format_order_time(order.created_at)}\n"
        text += f"📊 Статус: {status_text}\n"
        text += f"💰 Сумма: {order.total_price} ₽\n\n"
        
        # Кнопка для детального просмотра
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_emoji} Заказ №{order.id} — {status_text}",
                callback_data=f"view_order:{order.id}"
            )
        ])
    
    # Кнопки пагинации
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Предыдущая",
                callback_data=f"orders_page:{page - 1}"
            )
        )
    
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Следующая ▶️",
                callback_data=f"orders_page:{page + 1}"
            )
        )
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Кнопка обновить список
    buttons.append([
        InlineKeyboardButton(
            text="🔄 Обновить список",
            callback_data=f"orders_page:{page}"
        )
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    # Если это callback (обновление страницы), редактируем сообщение
    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await message.answer()
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("orders_page:"))
async def handle_orders_page(callback: CallbackQuery):
    """
    Обработчик переключения страниц
    """
    page = int(callback.data.split(":")[1])
    await show_orders_page(callback, page)


@router.callback_query(F.data == "back_to_orders")
async def back_to_orders_list(callback: CallbackQuery):
    """
    Вернуться к списку заказов (на первую страницу)
    """
    await show_orders_page(callback, page=0)


# -----------------------
# Детальный просмотр заказа
# -----------------------
@router.callback_query(F.data.startswith("view_order:"))
async def view_order_detail(callback: CallbackQuery):
    """
    Детальный просмотр заказа с обновлением статуса
    """
    order_id = int(callback.data.split(":")[1])
    order = await get_order_by_id(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    status_emoji = get_status_emoji(order.status)
    status_text = get_status_display(order.status)
    
    text = f"{status_emoji} <b>Заказ №{order.id}</b>\n\n"
    
    # Прогресс-бар статуса
    text += "📊 <b>Статус заказа:</b>\n"
    text += get_order_progress_bar(order.status) + "\n\n"
    
    text += f"📅 Оформлен: {format_order_time(order.created_at)}\n"
    text += f"💰 Сумма: {order.total_price} ₽\n\n"
    
    text += "📋 <b>Состав заказа:</b>\n"
    for item in order.items:
        text += f"  • {item.product.name} x{item.quantity}\n"
        
        # Показываем кастомизацию
        if item.customization:
            c = item.customization
            custom_text = []
            
            if c.milk_type and c.milk_type != "regular":
                milk_map = {
                    "almond": "миндальное",
                    "coconut": "кокосовое",
                    "soy": "соевое",
                    "lactose_free": "безлактозное"
                }
                custom_text.append(milk_map.get(c.milk_type, c.milk_type))
            
            if c.sugar_count > 0:
                custom_text.append(f"{c.sugar_count} л. сахара")
            
            if c.temperature == "cold":
                custom_text.append("айс")
            elif c.temperature == "warm":
                custom_text.append("тёплый")
            
            toppings = []
            if c.whipped_cream:
                toppings.append("сливки")
            if c.cinnamon:
                toppings.append("корица")
            if c.cocoa:
                toppings.append("какао")
            if c.caramel_syrup:
                toppings.append("карамель")
            if c.vanilla_syrup:
                toppings.append("ваниль")
            
            if toppings:
                custom_text.append("+ " + ", ".join(toppings))
            
            if custom_text:
                text += f"    <i>({', '.join(custom_text)})</i>\n"
    
    # Информация в зависимости от статуса
    text += "\n" + get_status_message(order.status)
    
    # Кнопки
    buttons = []
    
    # Кнопка обновить статус
    buttons.append([
        InlineKeyboardButton(
            text="🔄 Обновить статус",
            callback_data=f"refresh_order:{order.id}"
        )
    ])
    
    # Кнопка отменить (только если заказ ещё готовится)
    if order.status == OrderStatus.processing:
        buttons.append([
            InlineKeyboardButton(
                text="❌ Отменить заказ",
                callback_data=f"cancel_my_order:{order.id}"
            )
        ])
    
    # Кнопка к списку заказов
    buttons.append([
        InlineKeyboardButton(
            text="◀️ К списку заказов",
            callback_data="back_to_orders"
        )
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await callback.answer("✅ Статус актуален", show_alert=False)
        return
    
    await callback.answer()


@router.callback_query(F.data.startswith("refresh_order:"))
async def refresh_order_status(callback: CallbackQuery):
    """
    Обновить статус заказа
    """
    await view_order_detail(callback)


@router.callback_query(F.data.startswith("cancel_my_order:"))
async def cancel_my_order(callback: CallbackQuery):
    """
    Отменить свой заказ (только на этапе готовки)
    """
    order_id = int(callback.data.split(":")[1])
    
    # Получаем заказ для проверки статуса
    order = await get_order_by_id(order_id)
    
    if not order:
        await callback.answer("❌ Заказ не найден", show_alert=True)
        return
    
    # Проверяем, можно ли отменить
    if order.status != OrderStatus.processing:
        await callback.answer("❌ Этот заказ уже нельзя отменить", show_alert=True)
        return
    
    # Отменяем
    cancelled_order = await cancel_order(order_id)
    
    if cancelled_order:
        await notify_staff_order_cancelled(cancelled_order, cancelled_by_user=True)
        
        await callback.message.edit_text(
            "❌ <b>Заказ отменён</b>\n\n"
            f"Заказ №{order_id} успешно отменён.\n"
            "Бариста получили уведомление."
        )
    else:
        await callback.answer("❌ Не удалось отменить заказ", show_alert=True)
    
    await callback.answer()


# -----------------------
# Вспомогательные функции
# -----------------------
def get_order_progress_bar(status) -> str:
    """
    Прогресс-бар статуса заказа
    """
    if status == OrderStatus.pending:
        return "🛒━━━━━━━━━━ Оформление"
    elif status == OrderStatus.awaiting_payment:
        return "🛒▓⏳━━━━━━━━ Ожидание оплаты"
    elif status == OrderStatus.processing:
        return "🛒▓⏳▓👨‍🍳━━━━━━ Готовится"
    elif status == OrderStatus.completed:
        return "🛒▓⏳▓👨‍🍳▓✅━━━ Готов!"
    elif status == OrderStatus.cancelled:
        return "❌━━━━━━━━━━ Отменён"
    
    return "❓ Неизвестный статус"


def get_status_message(status) -> str:
    """
    Дополнительное сообщение в зависимости от статуса
    """
    messages = {
        OrderStatus.pending: "⏳ Заказ ещё не подтверждён. Завершите оформление в корзине.",
        OrderStatus.awaiting_payment: "💳 Ожидаем оплату. Пожалуйста, завершите платёж.",
        OrderStatus.processing: "👨‍🍳 Бариста уже готовит ваш заказ! Скоро будет готов.",
        OrderStatus.completed: "✅ Ваш заказ готов! Можете забрать на стойке.",
        OrderStatus.cancelled: "❌ Заказ был отменён.",
    }
    
    return messages.get(status, "")