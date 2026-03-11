##database/models/customization.py
from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class OrderItemCustomization(Base):
    """
    Кастомизация позиции заказа (молоко, сахар, добавки и т.д.)
    """
    __tablename__ = "order_item_customizations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("order_items.id"))
    
    # Выбор молока
    milk_type: Mapped[str | None] = mapped_column(String(50))  # "regular", "almond", "coconut", "soy", "lactose_free"
    
    # Количество сахара
    sugar_count: Mapped[int | None] = mapped_column(Integer, default=0)  # 0, 1, 2, 3
    
    # Температура
    temperature: Mapped[str | None] = mapped_column(String(20))  # "hot", "warm", "cold"
    
    # Топпинги (булевы флаги)
    whipped_cream: Mapped[bool] = mapped_column(Boolean, default=False)  # Взбитые сливки
    cinnamon: Mapped[bool] = mapped_column(Boolean, default=False)       # Корица
    cocoa: Mapped[bool] = mapped_column(Boolean, default=False)          # Какао
    caramel_syrup: Mapped[bool] = mapped_column(Boolean, default=False)  # Карамельный сироп
    vanilla_syrup: Mapped[bool] = mapped_column(Boolean, default=False)  # Ванильный сироп
    
    # Связь с позицией заказа
    order_item: Mapped["OrderItem"] = relationship("OrderItem", back_populates="customization")
    
    def __repr__(self):
        return f"<Customization(milk={self.milk_type}, sugar={self.sugar_count})>"