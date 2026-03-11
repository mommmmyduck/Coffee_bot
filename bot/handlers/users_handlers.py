from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from services.user_service import get_or_create_user, list_staff, set_user_role
from bot.utils.decorators import admin_required
from bot.keyboards.user_keyboards import get_main_keyboard, get_admin_keyboard, get_staff_keyboard 

router = Router()

# -----------------------
# Helpers
# -----------------------
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


# -----------------------
# Handlers
# -----------------------

@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Приветствие и регистрация пользователя
    """
    user = message.from_user._user
    
    # Формируем приветствие
    text = f"Привет, {user.first_name}! 👋\n\n"
    
    # Информация о роли
    role_names = {
        "buyer": "Клиент",
        "seller": "Бариста",
        "owner": "Администратор",
    }
    role_name = role_names.get(user.role, user.role)
    text += f"Ваша роль: {role_name}\n\n"
    
    # Инструкция
    text += "Выберите действие из меню ниже:"
    
    # Отправляем с клавиатурой
    await message.answer(
        text,
        reply_markup=get_keyboard_for_user(user)
    )


@router.message(Command("staff"))
@admin_required
async def cmd_list_staff(message: Message):
    """
    Список сотрудников (только для админов)
    """
    staff = await list_staff()
    if not staff:
        await message.answer("Сотрудники не найдены")
        return

    text = "👥 Список сотрудников:\n\n"
    for s in staff:
        role_emoji = "👑" if s.role == "owner" else "☕"
        text += f"{role_emoji} {s.first_name} {s.last_name} — {s.role}\n"

    await message.answer(text)


@router.message(F.text.startswith("/setrole"))
@admin_required
async def cmd_set_role(message: Message):
    """
    Назначение роли сотруднику
    Формат команды: /setrole <telegram_id> <role>
    """
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /setrole <telegram_id> <role>")
        return

    target_id, role = parts[1], parts[2]
    try:
        target_id = int(target_id)
    except ValueError:
        await message.answer("❌ Telegram ID должен быть числом")
        return

    if role not in ("buyer", "seller", "owner"):
        await message.answer("❌ Неверная роль. Используйте: buyer, seller, owner")
        return

    target_user = await set_user_role(target_id, role)
    if not target_user:
        await message.answer("❌ Пользователь не найден")
        return

    await message.answer(f"✅ Роль пользователя {target_user.first_name} установлена на {role}")



    __all__ = ['router', 'get_keyboard_for_user']