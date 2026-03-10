#bot/utils/decorators.py
from functools import wraps
from aiogram.types import Message

def admin_required(func):
    """Декоратор для проверки прав администратора"""
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        user = message.from_user._user
        
        if user.role not in ("owner",):
            await message.answer("❌ Доступ запрещён. Требуются права администратора.")
            return
        
        return await func(message, *args, **kwargs)
    
    return wrapper


def staff_required(func):
    """Декоратор для проверки прав сотрудника (seller или owner)"""
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        user = message.from_user._user
        
        if user.role not in ("seller", "owner"):
            await message.answer("❌ Доступ запрещён. Требуются права сотрудника.")
            return
        
        return await func(message, *args, **kwargs)
    
    return wrapper