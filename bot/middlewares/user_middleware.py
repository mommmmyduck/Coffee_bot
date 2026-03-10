from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from services.user_service import get_or_create_user

class AttachUserMiddleware(BaseMiddleware):
    """
    Подгружает пользователя из БД и прикрепляет к event.from_user._user
    Работает и для сообщений, и для callback_query
    """
    async def __call__(self, handler, event, data: dict):
        if isinstance(event, (Message, CallbackQuery)):
            telegram_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name
            last_name = event.from_user.last_name

            user = await get_or_create_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )

            # Прикрепляем пользователя к from_user
            event.from_user._user = user

        return await handler(event, data)