from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID, uuid4
from sqlalchemy import String, DateTime, ForeignKey, UUID as SQ_UUID, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[UUID] = mapped_column(SQ_UUID, primary_key=True, default=uuid4)
    tracking_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    carrier: Mapped[str] = mapped_column(String(50), nullable=False)
    promised_delivery_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="IN_TRANSIT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    checkpoints: Mapped[list["CheckpointLedger"]] = relationship("CheckpointLedger", back_populates="shipment", cascade="all, delete-orphan")

class CheckpointLedger(Base):
    __tablename__ = "checkpoint_ledger"

    id: Mapped[UUID] = mapped_column(SQ_UUID, primary_key=True, default=uuid4)
    shipment_id: Mapped[UUID] = mapped_column(SQ_UUID, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    location_hub: Mapped[str] = mapped_column(String(100), nullable=False)
    arrival_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status_description: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)

    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="checkpoints")