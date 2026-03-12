# bot/keyboards/menu_keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models.product import ProductCategory


def get_categories_keyboard() -> InlineKeyboardMarkup:
    """
    Inline-клавиатура с категориями товаров
    """
    # Словарь для красивого отображения категорий
    category_names = {
        ProductCategory.coffee: "☕ Кофе",
        ProductCategory.non_coffee: "🍵 Не кофе",
        ProductCategory.bakery: "🥐 Выпечка",
        ProductCategory.desserts: "🍰 Десерты",
    }
    
    buttons = [
        [InlineKeyboardButton(
            text=category_names[cat], 
            callback_data=f"category:{cat.name}"
        )]
        for cat in ProductCategory
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_products_keyboard(products) -> InlineKeyboardMarkup:
    """
    Inline-клавиатура с товарами внутри категории с отображением скидок
    """
    buttons = []
    for product in products:
        status = "✅" if product.is_active else "❌"
        
        # Формируем цену с учётом скидки
        if hasattr(product, 'discount') and product.discount and product.discount > 0:
            discounted = product.get_discounted_price()
            price_text = f"{product.price}→{discounted:.0f}₽ (-{product.discount}%)"
        else:
            price_text = f"{product.price} ₽"
        
        buttons.append([
            InlineKeyboardButton(
                text=f"{product.name} {status} — {price_text}",
                callback_data=f"product:{product.id}"
            )
        ])

    # Возвращаем кнопку "Назад"
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад к категориям",
            callback_data="back_to_categories"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_product_detail_keyboard(product) -> InlineKeyboardMarkup:
    """
    Inline-клавиатура для деталей товара:
    - кнопка добавления в корзину, если товар активен
    - кнопка "Нет в наличии", если товар не активен
    - кнопка возврата к категориям
    """
    buttons = []

    if product.is_active:
        buttons.append([
            InlineKeyboardButton(
                text="➕ В корзину",
                callback_data=f"add_to_cart:{product.id}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="❌ Нет в наличии",
                callback_data="product_unavailable"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="back_to_categories"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)