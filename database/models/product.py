#database/models/product.py
from sqlalchemy import String, Numeric, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
import enum

class ProductCategory(enum.Enum):
    """Категории товаров"""
    coffee = "coffee"
    non_coffee = "non_coffee"
    bakery = "bakery"
    desserts = "desserts"

class Product(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    price: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    
    category: Mapped[ProductCategory] = mapped_column(
        SQLEnum(ProductCategory),
        nullable=False
    )
    
    volume: Mapped[str | None] = mapped_column(String(10))  # "200", "300", "500"
    image_url: Mapped[str | None] = mapped_column(String)
    weight: Mapped[int | None] = mapped_column(Integer)  # в граммах
    
    # ✅ НОВОЕ: калорийность
    calories: Mapped[int | None] = mapped_column(Integer)  # ккал
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"