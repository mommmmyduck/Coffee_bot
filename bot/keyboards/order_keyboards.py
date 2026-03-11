# bot/keyboards/orders_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_cart_keyboard(order, is_staff: bool = False) -> InlineKeyboardMarkup:
    """
    Создаёт inline-клавиатуру для корзины.
    - order: объект Order с items
    - is_staff: True для сотрудников/админа (добавляем кнопку завершения заказа)
    """
    buttons = []

    # -----------------------
    # Список товаров с кастомизацией
    # -----------------------
    for item in order.items:
        # Формируем текст кнопки с учетом кастомизации
        item_text = f"❌ {item.product.name} ({item.quantity} шт)"
        
        # Добавляем краткую информацию о кастомизации в текст кнопки, если есть
        if item.customization:
            c = item.customization
            custom_icons = []
            
            if c.milk_type and c.milk_type != "regular":
                milk_icons = {
                    "almond": "🌰",
                    "coconut": "🥥",
                    "soy": "🌱",
                    "lactose_free": "🚫🥛"
                }
                if c.milk_type in milk_icons:
                    custom_icons.append(milk_icons[c.milk_type])
            
            if c.sugar_count > 0:
                custom_icons.append(f"🍬{c.sugar_count}")
            
            if c.temperature == "cold":
                custom_icons.append("❄️")
            elif c.temperature == "warm":
                custom_icons.append("🔥")
            
            toppings = []
            if c.whipped_cream:
                toppings.append("🥛")
            if c.cinnamon:
                toppings.append("⚜️")
            if c.cocoa:
                toppings.append("🍫")
            if c.caramel_syrup:
                toppings.append("🍯")
            if c.vanilla_syrup:
                toppings.append("🌿")
            
            if toppings:
                custom_icons.extend(toppings[:2])  # Показываем только первые 2 иконки
            
            if custom_icons:
                item_text += f" [{''.join(custom_icons)}]"
        
        buttons.append([
            InlineKeyboardButton(
                text=item_text,
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


def get_payment_method_keyboard(order_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="💳 Картой в боте", callback_data=f"pay_card:{order_id}")],
        [InlineKeyboardButton(text="💵 При получении", callback_data=f"pay_cash:{order_id}")],
        [InlineKeyboardButton(text="◀️ Назад в корзину", callback_data="/cart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
