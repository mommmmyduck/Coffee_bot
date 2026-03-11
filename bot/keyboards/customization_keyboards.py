#bot/keyboards/customization_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_milk_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора молока"""
    buttons = [
        [InlineKeyboardButton(text="🥛 Обычное молоко", callback_data=f"milk:regular:{product_id}")],
        [InlineKeyboardButton(text="🌰 Миндальное молоко", callback_data=f"milk:almond:{product_id}")],
        [InlineKeyboardButton(text="🥥 Кокосовое молоко", callback_data=f"milk:coconut:{product_id}")],
        [InlineKeyboardButton(text="🌾 Соевое молоко", callback_data=f"milk:soy:{product_id}")],
        [InlineKeyboardButton(text="💚 Безлактозное молоко", callback_data=f"milk:lactose_free:{product_id}")],
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"milk:skip:{product_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_sugar_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора количества сахара"""
    buttons = [
        [InlineKeyboardButton(text="🚫 Без сахара", callback_data=f"sugar:0:{product_id}")],
        [InlineKeyboardButton(text="1️⃣ Одна ложка", callback_data=f"sugar:1:{product_id}")],
        [InlineKeyboardButton(text="2️⃣ Две ложки", callback_data=f"sugar:2:{product_id}")],
        [InlineKeyboardButton(text="3️⃣ Три ложки", callback_data=f"sugar:3:{product_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_temperature_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора температуры"""
    buttons = [
        [InlineKeyboardButton(text="🔥 Горячий", callback_data=f"temp:hot:{product_id}")],
        [InlineKeyboardButton(text="🌡 Тёплый", callback_data=f"temp:warm:{product_id}")],
        [InlineKeyboardButton(text="🧊 Холодный (айс)", callback_data=f"temp:cold:{product_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_toppings_keyboard(product_id: int, selected_toppings: dict) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора топпингов (множественный выбор)
    selected_toppings: {"whipped_cream": True, "cinnamon": False, ...}
    """
    # Эмодзи для выбранных/невыбранных
    def get_emoji(selected: bool) -> str:
        return "✅" if selected else "⬜"
    
    buttons = [
        [InlineKeyboardButton(
            text=f"{get_emoji(selected_toppings.get('whipped_cream', False))} Взбитые сливки",
            callback_data=f"topping:whipped_cream:{product_id}"
        )],
        [InlineKeyboardButton(
            text=f"{get_emoji(selected_toppings.get('cinnamon', False))} Корица",
            callback_data=f"topping:cinnamon:{product_id}"
        )],
        [InlineKeyboardButton(
            text=f"{get_emoji(selected_toppings.get('cocoa', False))} Какао",
            callback_data=f"topping:cocoa:{product_id}"
        )],
        [InlineKeyboardButton(
            text=f"{get_emoji(selected_toppings.get('caramel_syrup', False))} Карамельный сироп",
            callback_data=f"topping:caramel_syrup:{product_id}"
        )],
        [InlineKeyboardButton(
            text=f"{get_emoji(selected_toppings.get('vanilla_syrup', False))} Ванильный сироп",
            callback_data=f"topping:vanilla_syrup:{product_id}"
        )],
        [InlineKeyboardButton(
            text="➡️ Готово",
            callback_data=f"toppings:done:{product_id}"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)