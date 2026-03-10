from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
import enum

class OrderStatus(enum.Enum):
    pending = "pending"       # только создан
    processing = "processing" # в работе (бариста)
    completed = "completed"   # выполнен
    cancelled = "cancelled"   # отменён

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus), default=OrderStatus.pending)
    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    bonus_points: Mapped[int] = mapped_column(Integer, default=0)

    # ⚡ Здесь используем строку, чтобы не импортировать OrderItem
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )