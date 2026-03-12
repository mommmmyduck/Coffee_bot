from aiogram import Bot
from config import BOT_TOKEN
from database.database import SessionLocal
from database.models.user import User
from sqlalchemy import select

async def get_all_buyers():
    """
    Получить всех покупателей (роль buyer)
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.role == "buyer")
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def broadcast_promotion(text: str, image_id: str | None = None):
    """
    Отправить рассылку всем покупателям
    
    Args:
        text: Текст акции
        image_id: file_id картинки (если есть)
    
    Returns:
        dict: Статистика рассылки (успешно, ошибок)
    """
    bot = Bot(token=BOT_TOKEN)
    buyers = await get_all_buyers()
    
    success_count = 0
    error_count = 0
    
    for buyer in buyers:
        try:
            if image_id:
                # Отправляем с картинкой
                await bot.send_photo(
                    chat_id=buyer.telegram_id,
                    photo=image_id,
                    caption=text,
                    parse_mode="HTML"
                )
            else:
                # Только текст
                await bot.send_message(
                    chat_id=buyer.telegram_id,
                    text=text,
                    parse_mode="HTML"
                )
            
            success_count += 1
            
        except Exception as e:
            print(f"Ошибка отправки {buyer.telegram_id}: {e}")
            error_count += 1
    
    await bot.session.close()
    
    return {
        "success": success_count,
        "errors": error_count,
        "total": len(buyers)
    }