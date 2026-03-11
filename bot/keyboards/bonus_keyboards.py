# bot/keyboards/bonus_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_bonus_keyboard(order_id: int, user_bonus: int, order_total: float, payment_method: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора использования бонусов при оплате
    Можно списать любую сумму от 1 рубля до доступных бонусов
    """
    buttons = []
    
    # Доступно для списания (не больше суммы заказа и не больше бонусов)
    available = min(user_bonus, int(order_total))
    
    if available >= 1:
        # Быстрый выбор: 50, 100, 200, 500
        quick_options = []
        for amount in [50, 100, 200, 500]:
            if amount <= available:
                quick_options.append(amount)
        
        # Добавляем кнопки быстрого выбора (по две в ряд)
        quick_buttons = []
        for i, amount in enumerate(quick_options):
            quick_buttons.append(
                InlineKeyboardButton(
                    text=f"{amount}₽",
                    callback_data=f"use_bonus:{order_id}:{amount}:{payment_method}"
                )
            )
        
        # Группируем по 2 кнопки в ряд
        for i in range(0, len(quick_buttons), 2):
            buttons.append(quick_buttons[i:i+2])
        
        # Кнопка для ввода своей суммы
        buttons.append([
            InlineKeyboardButton(
                text="✏️ Ввести свою сумму",
                callback_data=f"custom_bonus:{order_id}:{payment_method}"
            )
        ])
        
        # Кнопка "Списать всё"
        if available > 0:
            buttons.append([
                InlineKeyboardButton(
                    text=f"💰 Списать всё ({available}₽)",
                    callback_data=f"use_bonus:{order_id}:{available}:{payment_method}"
                )
            ])
    
    # Кнопка "Не использовать бонусы"
    buttons.append([
        InlineKeyboardButton(
            text="⏭ Продолжить без бонусов",
            callback_data=f"skip_bonus:{order_id}:{payment_method}"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_custom_bonus_keyboard(order_id: int, payment_method: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для отмены ввода своей суммы
    """
    buttons = [
        [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=f"back_to_bonus:{order_id}:{payment_method}"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)