from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_cart_keyboard(order, is_staff: bool = False) -> InlineKeyboardMarkup:
    """
    Создаёт inline-клавиатуру для корзины.
    - order: объект Order с items
    - is_staff: True для сотрудников/админа (добавляем кнопку завершения заказа)
    """
    buttons = []

    # -----------------------
    # Список товаров
    # -----------------------
    for item in order.items:
        buttons.append([
            InlineKeyboardButton(
                text=f"❌ {item.product.name} ({item.quantity} шт)",
                callback_data=f"remove_item:{item.id}"
            )
        ])

    # -----------------------
    # Кнопки действий
    # -----------------------
    action_buttons = [
        InlineKeyboardButton(
            text="✅ Подтвердить заказ",
            callback_data=f"confirm_order:{order.id}"
        ),
        InlineKeyboardButton(
            text="❌ Отменить заказ",
            callback_data=f"cancel_order:{order.id}"
        )
    ]

    # -----------------------
    # Для сотрудников/админа
    # -----------------------
    if is_staff:
        action_buttons.append(
            InlineKeyboardButton(
                text="⚡ Отметить как выполненный",
                callback_data=f"complete_order:{order.id}"
            )
        )

    buttons.append(action_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# -----------------------
# оплата заказа
# -----------------------


def get_payment_method_keyboard(order_id: int) -> InlineKeyboardMarkup:
    buttons = [
        # Добавляем ID заказа в callback_data
        [InlineKeyboardButton(text="💳 Картой в боте", callback_data=f"pay_card:{order_id}")],
        [InlineKeyboardButton(text="💵 При получении", callback_data=f"pay_cash:{order_id}")],
        [InlineKeyboardButton(text="◀️ Назад в корзину", callback_data="/cart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)