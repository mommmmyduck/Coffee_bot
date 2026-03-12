from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Главная клавиатура для клиента (buyer)
    """
    keyboard = [
        [
            KeyboardButton(text="📋 Меню"),
            KeyboardButton(text="🛒 Корзина"),
        ],
        [
            KeyboardButton(text="📦 Мои заказы"),
            KeyboardButton(text="👤 Профиль"),
        ],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_staff_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для бариста (seller)
    """
    keyboard = [
        [
            KeyboardButton(text="📋 Меню"),
            KeyboardButton(text="🛒 Корзина"),
        ],
        [
            KeyboardButton(text="📦 История заказов"),
            KeyboardButton(text="👤 Профиль"),
        ],
        [
            KeyboardButton(text="📊 Активные заказы"),  
            KeyboardButton(text="⚙️ Управление меню"),
        ],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для администратора (owner)
    """
    keyboard = [
        [
            KeyboardButton(text="📋 Меню"),
            KeyboardButton(text="🛒 Корзина"),
        ],
        [
            KeyboardButton(text="📦 Мои заказы"),
            KeyboardButton(text="👤 Профиль"),
        ],
        [
            KeyboardButton(text="📊 Активные заказы"),
            KeyboardButton(text="⚙️ Управление меню"),
        ],
        [
            KeyboardButton(text="👥 Пользователи"),
            KeyboardButton(text="📈 Статистика"),
        ],
        # ✅ НОВЫЕ КНОПКИ
        [
            KeyboardButton(text="📢 Рассылка"),
            KeyboardButton(text="🏷️ Скидки"),
        ],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )