#database/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from config import DB_URL
from database.base import Base

# подключение к PostgreSQL
engine = create_async_engine(
    DB_URL,
    echo=True
)

# фабрика сессий — даём правильное имя
SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# импорт моделей в самом конце, чтобы не было циклического импорта

from database.models import user, product, order_item, order, customization