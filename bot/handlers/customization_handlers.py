from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.customization_states import CustomizationStates
from bot.keyboards.customization_keyboards import (
    get_sugar_keyboard,
    get_temperature_keyboard,
    get_toppings_keyboard
)
from services.order_service import add_to_cart_with_customization

router = Router()

# -----------------------
# Шаг 1: Выбор молока
# -----------------------
@router.callback_query(F.data.startswith("milk:"))
async def choose_milk(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора молока"""
    _, milk_type, product_id = callback.data.split(":")
    product_id = int(product_id)
    
    # Сохраняем выбор
    if milk_type != "skip":
        await state.update_data(milk_type=milk_type)
    
    # Переход к следующему шагу
    await state.set_state(CustomizationStates.choose_sugar)
    
    milk_names = {
        "regular": "Обычное молоко",
        "almond": "Миндальное молоко",
        "coconut": "Кокосовое молоко",
        "soy": "Соевое молоко",
        "lactose_free": "Безлактозное молоко",
        "skip": "Пропущено"
    }
    
    await callback.message.edit_text(
        f"✅ Молоко: {milk_names.get(milk_type, 'Обычное')}\n\n"
        f"Шаг 2/4: Сколько сахара?",
        reply_markup=get_sugar_keyboard(product_id),
        parse_mode="HTML"
    )
    await callback.answer()


# -----------------------
# Шаг 2: Количество сахара
# -----------------------
@router.callback_query(F.data.startswith("sugar:"))
async def choose_sugar(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора сахара"""
    _, sugar_count, product_id = callback.data.split(":")
    product_id = int(product_id)
    sugar_count = int(sugar_count)
    
    # Сохраняем выбор
    await state.update_data(sugar_count=sugar_count)
    
    # Переход к следующему шагу
    await state.set_state(CustomizationStates.choose_temperature)
    
    sugar_text = {
        0: "Без сахара",
        1: "1 ложка",
        2: "2 ложки",
        3: "3 ложки"
    }
    
    await callback.message.edit_text(
        f"✅ Сахар: {sugar_text[sugar_count]}\n\n"
        f"Шаг 3/4: Выберите температуру:",
        reply_markup=get_temperature_keyboard(product_id),
        parse_mode="HTML"
    )
    await callback.answer()


# -----------------------
# Шаг 3: Температура
# -----------------------
@router.callback_query(F.data.startswith("temp:"))
async def choose_temperature(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора температуры"""
    _, temperature, product_id = callback.data.split(":")
    product_id = int(product_id)
    
    # Сохраняем выбор
    await state.update_data(temperature=temperature)
    
    # Переход к следующему шагу
    await state.set_state(CustomizationStates.choose_toppings)
    
    temp_names = {
        "hot": "Горячий",
        "warm": "Тёплый",
        "cold": "Холодный (айс)"
    }
    
    # Инициализируем пустой словарь топпингов
    await state.update_data(toppings={})
    
    await callback.message.edit_text(
        f"✅ Температура: {temp_names[temperature]}\n\n"
        f"Шаг 4/4: Выберите добавки (можно несколько):",
        reply_markup=get_toppings_keyboard(product_id, {}),
        parse_mode="HTML"
    )
    await callback.answer()


# -----------------------
# Шаг 4: Топпинги (множественный выбор)
# -----------------------
@router.callback_query(F.data.startswith("topping:"))
async def toggle_topping(callback: CallbackQuery, state: FSMContext):
    """Переключение топпинга (вкл/выкл)"""
    _, topping_name, product_id = callback.data.split(":")
    product_id = int(product_id)
    
    # Получаем текущие выборы
    data = await state.get_data()
    toppings = data.get("toppings", {})
    
    # Переключаем топпинг
    toppings[topping_name] = not toppings.get(topping_name, False)
    
    # Сохраняем обновлённые топпинги
    await state.update_data(toppings=toppings)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_toppings_keyboard(product_id, toppings)
    )
    await callback.answer()


# -----------------------
# Завершение кастомизации
# -----------------------
@router.callback_query(F.data.startswith("toppings:done:"))
async def finish_customization(callback: CallbackQuery, state: FSMContext):
    """Завершить кастомизацию и добавить в корзину"""
    product_id = int(callback.data.split(":")[2])
    
    # Получаем все выборы
    data = await state.get_data()
    user = callback.from_user._user
    
    # Добавляем в корзину с кастомизацией
    await add_to_cart_with_customization(
        user_id=user.id,
        product_id=product_id,
        quantity=1,
        customization_data=data
    )
    
    # Очищаем состояние
    await state.clear()
    
    # Формируем итоговое сообщение
    summary = "✅ <b>Напиток добавлен в корзину!</b>\n\n"
    summary += "Ваши настройки:\n"
    
    if "milk_type" in data:
        milk_names = {
            "regular": "Обычное молоко",
            "almond": "Миндальное",
            "coconut": "Кокосовое",
            "soy": "Соевое",
            "lactose_free": "Безлактозное"
        }
        summary += f"🥛 Молоко: {milk_names.get(data['milk_type'], 'Обычное')}\n"
    
    if "sugar_count" in data:
        sugar_text = {0: "Без сахара", 1: "1 ложка", 2: "2 ложки", 3: "3 ложки"}
        summary += f"🍬 Сахар: {sugar_text[data['sugar_count']]}\n"
    
    if "temperature" in data:
        temp_names = {"hot": "Горячий", "warm": "Тёплый", "cold": "Холодный"}
        summary += f"🌡 Температура: {temp_names[data['temperature']]}\n"
    
    toppings = data.get("toppings", {})
    selected_toppings = [k for k, v in toppings.items() if v]
    if selected_toppings:
        topping_names = {
            "whipped_cream": "Взбитые сливки",
            "cinnamon": "Корица",
            "cocoa": "Какао",
            "caramel_syrup": "Карамельный сироп",
            "vanilla_syrup": "Ванильный сироп"
        }
        summary += "✨ Добавки: " + ", ".join([topping_names[t] for t in selected_toppings])
    
    await callback.message.edit_text(summary, parse_mode="HTML")
    await callback.answer()