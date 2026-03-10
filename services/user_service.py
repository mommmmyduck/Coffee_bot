#services/user_service.py
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select
from database.database import SessionLocal
from database.models.user import User


async def get_or_create_user(
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    """
    Получить пользователя по telegram_id или создать нового.
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user:
            return user

        # Создаём нового пользователя
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user


async def set_user_role(telegram_id: int, role: str) -> User | None:
    """
    Назначить роль пользователю по telegram_id.
    Возвращает пользователя или None, если не найден.
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            return None

        user.role = role
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def list_staff() -> list[User]:
    """
    Получить список всех сотрудников (role='seller' или 'owner').
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.role.in_(["seller", "owner"]))
        result = await session.execute(stmt)
        staff = result.scalars().all()
        return staff