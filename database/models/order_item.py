##database/models/order_item.py
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Связи
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product")
    
    # ✅ НОВОЕ: связь с кастомизацией
    customization: Mapped["OrderItemCustomization"] = relationship(
        "OrderItemCustomization",
        back_populates="order_item",
        uselist=False,  # Один к одному
        cascade="all, delete-orphan"
    )