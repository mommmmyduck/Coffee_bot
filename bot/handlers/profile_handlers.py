# bot/handlers/profile_handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.user_keyboards import get_main_keyboard, get_staff_keyboard, get_admin_keyboard
from services.user_service import update_user_profile

router = Router()

class ProfileEditStates(StatesGroup):
    waiting_for_first_name = State()
    waiting_for_last_name = State()

# Функция для получения клавиатуры по роли
def get_keyboard_for_user(user):
    """
    Вернуть клавиатуру в зависимости от роли пользователя
    """
    if user.role == "owner":
        return get_admin_keyboard()
    elif user.role == "seller":
        return get_staff_keyboard()
    else:  # buyer
        return get_main_keyboard()


def get_profile_text(user):
    """Сформировать текст профиля"""
    role_names = {
        "buyer": "Клиент",
        "seller": "Бариста",
        "owner": "Администратор",
    }
    
    text = f"👤 <b>Ваш профиль</b>\n\n"
    text += f"🆔 ID: {user.telegram_id}\n"
    text += f"👤 Имя: {user.first_name or '—'}\n"
    text += f"👤 Фамилия: {user.last_name or '—'}\n"
    
    if user.username:
        text += f"📧 Username: @{user.username}\n"
    
    text += f"\n🎭 Роль: {role_names.get(user.role, user.role)}\n"
    text += f"💰 Бонусы: {user.bonus_points}\n"
    text += f"☕ Чашек: {user.total_cups}"
    
    return text


@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    """
    Показать профиль пользователя с кнопками для редактирования
    """
    user = message.from_user._user
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    text = get_profile_text(user)
    
    # Кнопки для редактирования
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить имя", callback_data="edit_first_name")],
        [InlineKeyboardButton(text="✏️ Изменить фамилию", callback_data="edit_last_name")]
    ])
    
    # Сохраняем ID сообщения с профилем в данных пользователя для последующего обновления
    msg = await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    
    # Сохраняем ID сообщения в FSM (опционально)
    # await state.update_data(profile_message_id=msg.message_id)


@router.callback_query(F.data == "edit_first_name")
async def edit_first_name_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование имени"""
    # Сохраняем ID сообщения профиля, чтобы потом обновить его
    await state.update_data(profile_message_id=callback.message.message_id)
    await state.set_state(ProfileEditStates.waiting_for_first_name)
    
    await callback.message.edit_text(
        "✏️ Введите новое имя:",
        reply_markup=None
    )
    await callback.answer()


@router.callback_query(F.data == "edit_last_name")
async def edit_last_name_start(callback: CallbackQuery, state: FSMContext):
    """Начать редактирование фамилии"""
    await state.update_data(profile_message_id=callback.message.message_id)
    await state.set_state(ProfileEditStates.waiting_for_last_name)
    
    await callback.message.edit_text(
        "✏️ Введите новую фамилию:",
        reply_markup=None
    )
    await callback.answer()


@router.message(ProfileEditStates.waiting_for_first_name)
async def process_new_first_name(message: Message, state: FSMContext):
    """Обработать новое имя"""
    new_name = message.text.strip()
    
    if len(new_name) > 30:
        await message.answer("❌ Имя слишком длинное (максимум 30 символов). Попробуйте снова:")
        return
    
    user = message.from_user._user
    updated_user = await update_user_profile(user.telegram_id, first_name=new_name)
    
    if updated_user:
        # 👇 ВАЖНО: обновляем объект пользователя в событии
        message.from_user._user = updated_user
        
        data = await state.get_data()
        profile_message_id = data.get('profile_message_id')
        
        if profile_message_id:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Изменить имя", callback_data="edit_first_name")],
                [InlineKeyboardButton(text="✏️ Изменить фамилию", callback_data="edit_last_name")]
            ])
            
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=profile_message_id,
                text=get_profile_text(updated_user),  # используем обновленного
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await message.delete()
        else:
            await show_profile(message)
    else:
        await message.answer("❌ Ошибка при обновлении имени")
    
    await state.clear()


@router.message(ProfileEditStates.waiting_for_last_name)
async def process_new_last_name(message: Message, state: FSMContext):
    """Обработать новую фамилию"""
    new_name = message.text.strip()
    
    if len(new_name) > 30:
        await message.answer("❌ Фамилия слишком длинная (максимум 30 символов). Попробуйте снова:")
        return
    
    user = message.from_user._user
    updated_user = await update_user_profile(user.telegram_id, last_name=new_name)
    
    if updated_user:
        # 👇 ВАЖНО: обновляем объект пользователя в событии
        message.from_user._user = updated_user
        
        data = await state.get_data()
        profile_message_id = data.get('profile_message_id')
        
        if profile_message_id:
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Изменить имя", callback_data="edit_first_name")],
                [InlineKeyboardButton(text="✏️ Изменить фамилию", callback_data="edit_last_name")]
            ])
            
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=profile_message_id,
                text=get_profile_text(updated_user),
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            await message.delete()
        else:
            await show_profile(message)
    else:
        await message.answer("❌ Ошибка при обновлении фамилии")
    
    await state.clear()