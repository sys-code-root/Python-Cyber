from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric as SQLDecimal, Integer, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from enums import CouponType

class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    base_price: Mapped[Decimal] = mapped_column(SQLDecimal(10, 2), nullable=False)
    stock_volume: Mapped[int] = mapped_column(Integer, default=0)
    competitor_price: Mapped[Decimal] = mapped_column(SQLDecimal(10, 2), nullable=False)

class CouponModel(Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    type: Mapped[CouponType] = mapped_column(SAEnum(CouponType, native_enum=False), nullable=False)
    value: Mapped[Decimal] = mapped_column(SQLDecimal(10, 2), nullable=False)
    min_purchase_value: Mapped[Decimal] = mapped_column(SQLDecimal(10, 2), default=Decimal("0.00"))
    target_region: Mapped[str | None] = mapped_column(String(2), nullable=True)
    first_purchase_only: Mapped[bool] = mapped_column(Boolean, default=False)
    excluded_categories: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)