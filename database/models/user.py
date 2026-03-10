#database/models/user.py
from datetime import date

from sqlalchemy import BigInteger, String, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="buyer"
    )

    username: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True
    )

    first_name: Mapped[str | None] = mapped_column(String(30))
    last_name: Mapped[str | None] = mapped_column(String(30))
    middle_name: Mapped[str | None] = mapped_column(String(30))

    birth_date: Mapped[date | None] = mapped_column(Date)

    bonus_points: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    total_cups: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    password: Mapped[str | None] = mapped_column(
        String(255)
    )

def __repr__(self):
    return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"