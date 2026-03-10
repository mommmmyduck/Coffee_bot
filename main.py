# main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.database import init_db
from bot.handlers.users_handlers import router as users_router
from bot.handlers.menu_handlers import router as menu_router
from bot.middlewares.user_middleware import AttachUserMiddleware  
from bot.handlers import admin_handlers
from bot.handlers import order_handlers

async def main():
    # 1️⃣ Инициализация базы данных
    await init_db()
    print("✅ База данных подключена и таблицы созданы")
    
    # 2️⃣ Инициализация бота
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # 3️⃣ Подключаем middleware для сообщений и callback_query
    dp.message.middleware(AttachUserMiddleware())
    dp.callback_query.middleware(AttachUserMiddleware())
    
    # 4️⃣ Подключаем роутеры
    dp.include_router(users_router)
    dp.include_router(menu_router)
    dp.include_router(admin_handlers.router)
    dp.include_router(order_handlers.router)
    
    # 5️⃣ Запуск бота
    print("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())