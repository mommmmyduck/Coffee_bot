#bot/keyboards/user_keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Главная клавиатура для пользователя
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
        resize_keyboard=True,  # Кнопки подстраиваются под размер экрана
        one_time_keyboard=False,  # Клавиатура не скрывается после нажатия
    )


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для администратора
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
            KeyboardButton(text="⚙️ Управление меню"),
            KeyboardButton(text="📊 Заказы"),
        ],
        [
            KeyboardButton(text="👥 Пользователи"),
            KeyboardButton(text="📈 Статистика"),
        ],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_staff_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для сотрудника (бариста)
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
            KeyboardButton(text="📊 Заказы"),
            KeyboardButton(text="⚙️ Управление меню"),
        ],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )