# bot/handlers/admin_user_handlers.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.decorators import admin_required
from services.user_service import search_users, set_user_role_by_username, list_staff
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

class AdminUserStates(StatesGroup):
    waiting_for_search = State()
    waiting_for_role_change = State()


# -----------------------
# Вспомогательная функция для отображения меню
# -----------------------
async def show_admin_users_menu(chat_id: int, bot, user):
    """Показать меню управления пользователями"""
    text = "👥 <b>Управление пользователями</b>\n\n"
    text += "Выберите действие:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_search_user")],
        [InlineKeyboardButton(text="📋 Список сотрудников", callback_data="admin_list_staff")],
        [InlineKeyboardButton(text="➕ Назначить бариста", callback_data="admin_add_staff")],
    ])
    
    await bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode="HTML")


# -----------------------
# Основные обработчики
# -----------------------
@router.message(F.text == "👥 Пользователи")
@admin_required
async def admin_users_menu(message: Message):
    """Меню управления пользователями"""
    await show_admin_users_menu(message.chat.id, message.bot, message.from_user._user)


@router.callback_query(F.data == "admin_list_staff")
@admin_required
async def admin_list_staff(callback: CallbackQuery):
    """Показать список сотрудников"""
    staff = await list_staff()
    
    if not staff:
        await callback.message.edit_text(
            "👥 Сотрудники не найдены",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back_to_users")]
            ])
        )
        await callback.answer()
        return
    
    text = "👥 <b>Список сотрудников:</b>\n\n"
    for s in staff:
        role_emoji = "👑" if s.role == "owner" else "☕"
        text += f"{role_emoji} {s.first_name or '—'} {s.last_name or '—'}\n"
        text += f"   📧 @{s.username or '—'}\n"
        text += f"   🆔 {s.telegram_id}\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back_to_users")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_search_user")
@admin_required
async def admin_search_user_start(callback: CallbackQuery, state: FSMContext):
    """Начать поиск пользователя"""
    await state.set_state(AdminUserStates.waiting_for_search)
    await callback.message.edit_text(
        "🔍 Введите имя, фамилию или username для поиска:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_back_to_users")]
        ])
    )
    await callback.answer()


@router.message(AdminUserStates.waiting_for_search)
@admin_required
async def admin_search_user_process(message: Message, state: FSMContext):
    """Обработать поиск пользователя"""
    query = message.text.strip()
    users = await search_users(query)
    
    if not users:
        await message.answer(
            f"❌ Пользователи по запросу '{query}' не найдены",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back_to_users")]
            ])
        )
        await state.clear()
        return
    
    text = f"🔍 <b>Результаты поиска по запросу '{query}':</b>\n\n"
    
    for user in users:
        text += f"👤 {user.first_name or '—'} {user.last_name or '—'}\n"
        text += f"   📧 @{user.username or '—'}\n"
        text += f"   🆔 {user.telegram_id}\n"
        text += f"   🎭 Роль: {user.role}\n\n"
    
    await message.answer(text, parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data == "admin_add_staff")
@admin_required
async def admin_add_staff_start(callback: CallbackQuery, state: FSMContext):
    """Начать добавление сотрудника"""
    text = "➕ <b>Назначение бариста</b>\n\n"
    text += "Введите username пользователя (с @ или без):\n\n"
    text += "Пример: @username или просто username"
    
    await state.set_state(AdminUserStates.waiting_for_role_change)
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="admin_back_to_users")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminUserStates.waiting_for_role_change)
@admin_required
async def admin_add_staff_process(message: Message, state: FSMContext):
    """Обработать назначение бариста"""
    username = message.text.strip()
    
    user = await set_user_role_by_username(username, "seller")
    
    if user:
        await message.answer(
            f"✅ Пользователь @{username} успешно назначен бариста!\n\n"
            f"Имя: {user.first_name or '—'} {user.last_name or '—'}\n"
            f"Telegram ID: {user.telegram_id}"
        )
    else:
        await message.answer(
            f"❌ Пользователь @{username} не найден",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="admin_add_staff")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back_to_users")]
            ])
        )
    
    await state.clear()


@router.callback_query(F.data == "admin_back_to_users")
@admin_required
async def admin_back_to_users(callback: CallbackQuery, state: FSMContext):
    """Вернуться в меню пользователей"""
    await state.clear()
    await show_admin_users_menu(callback.message.chat.id, callback.bot, callback.from_user._user)
    await callback.answer()