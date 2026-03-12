# services/user_service.py
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, or_
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
    Обновляем только username (он может меняться в Telegram).
    Имя и фамилию НЕ обновляем автоматически - они меняются только через профиль.
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user:
            # 👇 Обновляем ТОЛЬКО username, если он изменился
            if username and user.username != username:
                user.username = username
                await session.commit()
                await session.refresh(user)
            
            # 👇 НЕ обновляем имя и фамилию из Telegram!
            # Это позволяет сохранить ручные изменения
            
            return user

        # Создаём нового пользователя (только при первом входе)
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


async def update_user_profile(
    telegram_id: int,
    first_name: str | None = None,
    last_name: str | None = None
) -> User | None:
    """
    Обновить имя и фамилию пользователя
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if not user:
            return None

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name

        await session.commit()
        await session.refresh(user)
        return user


async def update_user_phone(telegram_id: int, phone_number: str) -> User | None:
    """
    Обновить номер телефона пользователя
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.phone_number = phone_number
            await session.commit()
            await session.refresh(user)
            return user
        
        return None


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


async def set_user_role_by_username(username: str, role: str) -> User | None:
    """
    Назначить роль пользователю по username (без @)
    """
    async with SessionLocal() as session:
        # Убираем @ если есть
        clean_username = username.lstrip('@')
        
        stmt = select(User).where(User.username == clean_username)
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


async def get_staff_users() -> list[User]:
    """
    Получить всех сотрудников (seller и owner) - алиас для list_staff
    """
    return await list_staff()


async def search_users(query: str) -> list[User]:
    """
    Поиск пользователей по имени, фамилии или username
    """
    async with SessionLocal() as session:
        # Убираем @ если есть
        clean_query = query.lstrip('@')
        
        stmt = select(User).where(
            or_(
                User.first_name.ilike(f"%{clean_query}%"),
                User.last_name.ilike(f"%{clean_query}%"),
                User.username.ilike(f"%{clean_query}%")
            )
        ).limit(20)
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    """
    Получить пользователя по telegram_id
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalars().first()


async def get_user_by_id(user_id: int) -> User | None:
    """
    Получить пользователя по ID (для заказов)
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()


async def get_user_by_username(username: str) -> User | None:
    """
    Получить пользователя по username (без @)
    """
    async with SessionLocal() as session:
        clean_username = username.lstrip('@')
        stmt = select(User).where(User.username == clean_username)
        result = await session.execute(stmt)
        return result.scalars().first()


async def get_all_users(limit: int = 100) -> list[User]:
    """
    Получить всех пользователей (с ограничением)
    """
    async with SessionLocal() as session:
        stmt = select(User).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()


# ========================
# 👇 ФУНКЦИИ ДЛЯ БЛОКИРОВКИ
# ========================

async def block_user_by_phone(phone_number: str) -> bool:
    """
    Заблокировать пользователя по номеру телефона
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.phone_number == phone_number)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.is_blocked = True
            await session.commit()
            return True
        
        return False


async def unblock_user_by_phone(phone_number: str) -> bool:
    """
    Разблокировать пользователя по номеру телефона
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.phone_number == phone_number)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.is_blocked = False
            await session.commit()
            return True
        
        return False


async def block_user_by_telegram_id(telegram_id: int) -> bool:
    """
    Заблокировать пользователя по telegram_id
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.is_blocked = True
            await session.commit()
            return True
        
        return False


async def unblock_user_by_telegram_id(telegram_id: int) -> bool:
    """
    Разблокировать пользователя по telegram_id
    """
    async with SessionLocal() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.is_blocked = False
            await session.commit()
            return True
        
        return False
    
async def block_user_by_phone(phone_number: str) -> bool:
    """Заблокировать пользователя по номеру телефона"""
    async with SessionLocal() as session:
        stmt = select(User).where(User.phone_number == phone_number)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.is_blocked = True
            await session.commit()
            return True
        
        return False


async def unblock_user_by_phone(phone_number: str) -> bool:
    """Разблокировать пользователя по номеру телефона"""
    async with SessionLocal() as session:
        stmt = select(User).where(User.phone_number == phone_number)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if user:
            user.is_blocked = False
            await session.commit()
            return True
        
        return False