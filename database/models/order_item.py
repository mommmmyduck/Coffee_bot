from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # ⚡ Строки в relationship, чтобы не было циклического импорта
    order: Mapped["Order"] = relationship("Order", back_populates="items")

    # Product можно оставить импортом, но лучше тоже через строку
    product: Mapped["Product"] = relationship("Product")