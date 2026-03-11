#handler для управления меню (только для админов)
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.utils.decorators import admin_required
from bot.states.product_states import AddProductStates, EditProductStates
from services.menu_service import (
    get_all_products,
    get_products_by_category,
    get_product_by_id,
    create_product_full,
    update_product_field,
    delete_product,
)
from database.models.product import ProductCategory

router = Router()

# -----------------------
# Главное меню управления (для админа)
# -----------------------
@router.callback_query(F.data == "admin_menu_management")
@admin_required
async def admin_menu_management(callback: CallbackQuery):
    """Меню управления товарами для админа"""
    text = "⚙️ <b>Управление меню (Админ)</b>\n\n"
    text += "Выберите действие:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="➕ Добавить товар",
            callback_data="admin_add_product"
        )],
        [InlineKeyboardButton(
            text="✏️ Изменить товар",
            callback_data="admin_edit_product"
        )],
        [InlineKeyboardButton(
            text="🗑 Удалить товар",
            callback_data="admin_delete_product"
        )],
        [InlineKeyboardButton(
            text="📋 Список всех товаров",
            callback_data="menu_list_all"
        )],
        [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="admin_back"
        )],
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ======================
# ДОБАВЛЕНИЕ ТОВАРА
# ======================

@router.callback_query(F.data == "admin_add_product")
@admin_required
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление товара"""
    text = "➕ <b>Добавление нового товара</b>\n\n"
    text += "Шаг 1/7: Выберите категорию товара:"
    
    buttons = []
    category_names = {
        ProductCategory.coffee: "☕ Кофе",
        ProductCategory.non_coffee: "🍵 Напитки без кофе",
        ProductCategory.bakery: "🥐 Выпечка",
        ProductCategory.desserts: "🍰 Десерты",
    }
    
    for category, name in category_names.items():
        buttons.append([
            InlineKeyboardButton(
                text=name,
                callback_data=f"add_category:{category.name}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu_management")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await state.set_state(AddProductStates.choose_category)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("add_category:"))
@admin_required
async def admin_add_product_category(callback: CallbackQuery, state: FSMContext):
    """Сохранить категорию и запросить название"""
    category_name = callback.data.split(":")[1]
    category = ProductCategory[category_name]
    
    await state.update_data(category=category)
    await state.set_state(AddProductStates.enter_name)
    
    category_display = {
        ProductCategory.coffee: "☕ Кофе",
        ProductCategory.non_coffee: "🍵 Напитки",
        ProductCategory.bakery: "🥐 Выпечка",
        ProductCategory.desserts: "🍰 Десерты",
    }
    
    text = f"✅ Категория: {category_display[category]}\n\n"
    text += "Шаг 2/7: Введите название товара:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_add")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.message(AddProductStates.enter_name)
@admin_required
async def admin_add_product_name(message: Message, state: FSMContext):
    """Сохранить название и запросить описание"""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ Название слишком короткое. Попробуйте снова:")
        return
    
    await state.update_data(name=name)
    await state.set_state(AddProductStates.enter_description)
    
    text = f"✅ Название: {name}\n\n"
    text += "Шаг 3/7: Введите описание товара\n"
    text += "(или отправьте '—' чтобы пропустить):"
    
    await message.answer(text, parse_mode="HTML")


@router.message(AddProductStates.enter_description)
@admin_required
async def admin_add_product_description(message: Message, state: FSMContext):
    """Сохранить описание и запросить цену"""
    description = message.text.strip()
    
    if description == "—":
        description = None
    
    await state.update_data(description=description)
    await state.set_state(AddProductStates.enter_price)
    
    text = "Шаг 4/7: Введите цену товара в рублях\n"
    text += "(например: 150 или 199.50):"
    
    await message.answer(text, parse_mode="HTML")


@router.message(AddProductStates.enter_price)
@admin_required
async def admin_add_product_price(message: Message, state: FSMContext):
    """Сохранить цену и запросить объём/вес"""
    try:
        price = float(message.text.strip())
        
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверный формат цены. Введите число (например: 150 или 199.50):")
        return
    
    await state.update_data(price=price)
    
    # Проверяем категорию
    data = await state.get_data()
    category = data.get("category")
    
    if category in [ProductCategory.coffee, ProductCategory.non_coffee]:
        # Для напитков спрашиваем объём
        await state.set_state(AddProductStates.enter_volume)
        text = "Шаг 5/7: Введите объём в мл (например: 200, 300, 500)\n"
        text += "(или отправьте '—' чтобы пропустить):"
    else:
        # Для еды спрашиваем вес
        await state.set_state(AddProductStates.enter_weight)
        text = "Шаг 5/7: Введите вес в граммах (например: 80, 120)\n"
        text += "(или отправьте '—' чтобы пропустить):"
    
    await message.answer(text, parse_mode="HTML")


@router.message(AddProductStates.enter_volume)
@admin_required
async def admin_add_product_volume(message: Message, state: FSMContext):
    """Сохранить объём и запросить калорийность"""
    volume = message.text.strip()
    
    if volume == "—":
        volume = None
    
    await state.update_data(volume=volume)
    await state.set_state(AddProductStates.enter_calories)
    
    text = "Шаг 6/7: Введите калорийность в ккал\n"
    text += "(или отправьте '—' чтобы пропустить):"
    
    await message.answer(text, parse_mode="HTML")


@router.message(AddProductStates.enter_weight)
@admin_required
async def admin_add_product_weight(message: Message, state: FSMContext):
    """Сохранить вес и запросить калорийность"""
    weight_str = message.text.strip()
    
    if weight_str == "—":
        weight = None
    else:
        try:
            weight = int(weight_str)
        except ValueError:
            await message.answer("❌ Неверный формат. Введите число или '—' для пропуска:")
            return
    
    await state.update_data(weight=weight)
    await state.set_state(AddProductStates.enter_calories)
    
    text = "Шаг 6/7: Введите калорийность в ккал\n"
    text += "(или отправьте '—' чтобы пропустить):"
    
    await message.answer(text, parse_mode="HTML")


@router.message(AddProductStates.enter_calories)
@admin_required
async def admin_add_product_calories(message: Message, state: FSMContext):
    """Сохранить калорийность и запросить фото"""
    calories_str = message.text.strip()
    
    if calories_str == "—":
        calories = None
    else:
        try:
            calories = int(calories_str)
        except ValueError:
            await message.answer("❌ Неверный формат. Введите число или '—' для пропуска:")
            return
    
    await state.update_data(calories=calories)
    await state.set_state(AddProductStates.upload_photo)
    
    text = "Шаг 7/7: Отправьте фото товара\n"
    text += "(или отправьте '—' чтобы пропустить):"
    
    await message.answer(text, parse_mode="HTML")


@router.message(AddProductStates.upload_photo, F.photo)
@admin_required
async def admin_add_product_photo(message: Message, state: FSMContext):
    """Сохранить фото и создать товар"""
    # Получаем file_id самого большого фото
    photo_id = message.photo[-1].file_id
    
    await state.update_data(image_url=photo_id)
    
    # Создаём товар
    await create_product_from_state(message, state)


@router.message(AddProductStates.upload_photo, F.text)
@admin_required
async def admin_add_product_skip_photo(message: Message, state: FSMContext):
    """Пропустить фото и создать товар"""
    if message.text.strip() == "—":
        await state.update_data(image_url=None)
        await create_product_from_state(message, state)
    else:
        await message.answer("❌ Отправьте фото или '—' для пропуска:")


async def create_product_from_state(message: Message, state: FSMContext):
    """Создать товар из собранных данных"""
    data = await state.get_data()
    
    try:
        product = await create_product_full(
            name=data['name'],
            price=data['price'],
            category=data['category'],
            description=data.get('description'),
            volume=data.get('volume'),
            weight=data.get('weight'),
            calories=data.get('calories'),
            image_url=data.get('image_url'),
        )
        
        text = "✅ <b>Товар успешно добавлен!</b>\n\n"
        text += f"📦 {product.name}\n"
        text += f"💰 Цена: {product.price} ₽\n"
        text += f"📂 Категория: {product.category.value}\n"
        
        if product.description:
            text += f"📝 Описание: {product.description}\n"
        
        if product.volume:
            text += f"📏 Объём: {product.volume} мл\n"
        
        if product.weight:
            text += f"⚖️ Вес: {product.weight} г\n"
        
        if product.calories:
            text += f"🔥 Калорийность: {product.calories} ккал\n"
        
        await message.answer(text, parse_mode="HTML")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при создании товара: {e}")
    
    await state.clear()


@router.callback_query(F.data == "admin_cancel_add")
@admin_required
async def admin_cancel_add(callback: CallbackQuery, state: FSMContext):
    """Отменить добавление товара"""
    await state.clear()
    await admin_menu_management(callback)


# ======================
# РЕДАКТИРОВАНИЕ ТОВАРА
# ======================

@router.callback_query(F.data == "admin_edit_product")
@admin_required
async def admin_edit_product_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование товара"""
    products = await get_all_products(active_only=False)
    
    if not products:
        await callback.answer("❌ Товары не найдены", show_alert=True)
        return
    
    text = "✏️ <b>Редактирование товара</b>\n\n"
    text += "Выберите товар для редактирования:"
    
    buttons = []
    for product in products[:20]:  # Показываем первые 20
        buttons.append([
            InlineKeyboardButton(
                text=f"{product.name} ({product.price} ₽)",
                callback_data=f"edit_product:{product.id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu_management")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("edit_product:"))
@admin_required
async def admin_edit_product_choose_field(callback: CallbackQuery, state: FSMContext):
    """Выбрать что редактировать"""
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    await state.update_data(edit_product_id=product_id)
    
    text = f"✏️ <b>Редактирование: {product.name}</b>\n\n"
    text += "Выберите что изменить:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data="edit_field:name")],
        [InlineKeyboardButton(text="💰 Цену", callback_data="edit_field:price")],
        [InlineKeyboardButton(text="📄 Описание", callback_data="edit_field:description")],
        [InlineKeyboardButton(text="📏 Объём", callback_data="edit_field:volume")],
        [InlineKeyboardButton(text="⚖️ Вес", callback_data="edit_field:weight")],
        [InlineKeyboardButton(text="🔥 Калорийность", callback_data="edit_field:calories")],
        [InlineKeyboardButton(text="📸 Фото", callback_data="edit_field:image")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_edit_product")],
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"))
@admin_required
async def admin_edit_field_request(callback: CallbackQuery, state: FSMContext):
    """Запросить новое значение поля"""
    field = callback.data.split(":")[1]
    
    await state.update_data(edit_field=field)
    
    field_names = {
        "name": "название",
        "price": "цену (число)",
        "description": "описание",
        "volume": "объём (мл)",
        "weight": "вес (г)",
        "calories": "калорийность (ккал)",
    }
    
    if field == "image":
        await state.set_state(EditProductStates.upload_new_photo)
        text = "📸 Отправьте новое фото товара:"
    else:
        await state.set_state(EditProductStates.enter_new_value)
        text = f"✏️ Введите новое значение ({field_names.get(field, field)}):"
    
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(EditProductStates.enter_new_value)
@admin_required
async def admin_edit_save_value(message: Message, state: FSMContext):
    """Сохранить новое значение"""
    data = await state.get_data()
    product_id = data['edit_product_id']
    field = data['edit_field']
    new_value = message.text.strip()
    
    # Конвертация типов
    try:
        if field == "price":
            new_value = float(new_value)
        elif field in ["weight", "calories"]:
            new_value = int(new_value) if new_value else None
    except ValueError:
        await message.answer("❌ Неверный формат. Попробуйте снова:")
        return
    
    product = await update_product_field(product_id, field, new_value)
    
    if product:
        await message.answer(f"✅ Поле '{field}' успешно обновлено!")
    else:
        await message.answer("❌ Ошибка при обновлении")
    
    await state.clear()


@router.message(EditProductStates.upload_new_photo, F.photo)
@admin_required
async def admin_edit_save_photo(message: Message, state: FSMContext):
    """Сохранить новое фото"""
    data = await state.get_data()
    product_id = data['edit_product_id']
    
    photo_id = message.photo[-1].file_id
    
    product = await update_product_field(product_id, "image_url", photo_id)
    
    if product:
        await message.answer("✅ Фото успешно обновлено!")
    else:
        await message.answer("❌ Ошибка при обновлении фото")
    
    await state.clear()


# ======================
# УДАЛЕНИЕ ТОВАРА
# ======================

@router.callback_query(F.data == "admin_delete_product")
@admin_required
async def admin_delete_product_start(callback: CallbackQuery):
    """Начать удаление товара"""
    products = await get_all_products(active_only=False)
    
    if not products:
        await callback.answer("❌ Товары не найдены", show_alert=True)
        return
    
    text = "🗑 <b>Удаление товара</b>\n\n"
    text += "⚠️ Выберите товар для удаления:"
    
    buttons = []
    for product in products[:20]:
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {product.name}",
                callback_data=f"confirm_delete:{product.id}"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_menu_management")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete:"))
@admin_required
async def admin_delete_product_confirm(callback: CallbackQuery):
    """Подтвердить удаление"""
    product_id = int(callback.data.split(":")[1])
    product = await get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не найден", show_alert=True)
        return
    
    text = f"⚠️ <b>Подтвердите удаление</b>\n\n"
    text += f"Товар: {product.name}\n"
    text += f"Цена: {product.price} ₽\n\n"
    text += "❗ Это действие нельзя отменить!"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"delete_confirmed:{product_id}"
        )],
        [InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="admin_delete_product"
        )],
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("delete_confirmed:"))
@admin_required
async def admin_delete_product_execute(callback: CallbackQuery):
    """Выполнить удаление"""
    product_id = int(callback.data.split(":")[1])
    
    success = await delete_product(product_id)
    
    if success:
        await callback.message.edit_text("✅ Товар успешно удалён!")
    else:
        await callback.message.edit_text("❌ Ошибка при удалении товара")
    
    await callback.answer()


@router.callback_query(F.data == "admin_back")
@admin_required
async def admin_back(callback: CallbackQuery):
    """Назад в главное меню админа"""
    # Здесь можно вернуться в главное меню админки
    await callback.message.edit_text("◀️ Возврат в главное меню")
    await callback.answer()