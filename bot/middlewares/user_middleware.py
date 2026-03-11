#middlewares/user_middleware.py
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from services.user_service import get_or_create_user

class AttachUserMiddleware(BaseMiddleware):
    """
    Подгружает пользователя из БД и прикрепляет к event.from_user._user
    Работает для Message и CallbackQuery
    """
    async def __call__(self, handler, event: TelegramObject, data: dict):
        # Проверяем что у события есть from_user
        if hasattr(event, 'from_user') and event.from_user:
            telegram_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name or "Друг"  
            last_name = event.from_user.last_name

            user = await get_or_create_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )

            # Прикрепляем пользователя
            event.from_user._user = user

        return await handler(event, data)