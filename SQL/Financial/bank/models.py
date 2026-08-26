import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import Numeric, String, Date, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class GatewayTransaction(Base):
    __tablename__ = "gateway_transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="PENDING")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="PENDING")


class ReconciliationLog(Base):
    __tablename__ = "reconciliation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gateway_transaction_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    bank_transaction_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    match_type: Mapped[str] = mapped_column(String, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    anomaly_flag: Mapped[bool] = mapped_column(Boolean, default=False)