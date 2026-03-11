# database/models/order.py
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
import enum
import pytz

class OrderStatus(enum.Enum):
    pending = "pending"
    awaiting_payment = "awaiting_payment"
    processing = "processing"
    completed = "completed"
    cancelled = "cancelled"

def get_moscow_time():
    """Возвращает текущее московское время"""
    tz = pytz.timezone('Europe/Moscow')
    return datetime.now(tz)

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=get_moscow_time  # 👈 используем функцию, а не datetime.now()
    )
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus), default=OrderStatus.pending)
    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    bonus_points: Mapped[int] = mapped_column(Integer, default=0)
    payment_method: Mapped[str | None] = mapped_column(String(20), default=None)

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )