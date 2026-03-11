# main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.database import init_db
from bot.handlers.users_handlers import router as users_router
from bot.handlers.menu_handlers import router as menu_router
from bot.middlewares.user_middleware import AttachUserMiddleware  
from bot.handlers import admin_handlers, analytics_handlers, customization_handlers, menu_management_handlers, user_orders_handlers
from bot.handlers import order_handlers
from bot.handlers import history_handlers  
from bot.handlers import staff_handlers
from bot.handlers import analytics_handlers 
from bot.handlers.profile_handlers import router as profile_router  
from bot.handlers.admin_user_handlers import router as admin_user_router 
from bot.handlers import menu_admin_handlers 

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
    dp.include_router(history_handlers.router) 
    dp.include_router(staff_handlers.router)  
    dp.include_router(customization_handlers.router) 
    dp.include_router(profile_router)  
    dp.include_router(admin_user_router)
    dp.include_router(menu_management_handlers.router)
    dp.include_router(user_orders_handlers.router)
    dp.include_router(menu_admin_handlers.router)
    dp.include_router(analytics_handlers.router)
    
    # 5️⃣ Запуск бота
    print("Бот запущен")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())