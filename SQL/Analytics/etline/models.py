from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4
from sqlalchemy import String, ForeignKey, Float, Integer, Date, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class DimCampaign(Base):
    __tablename__ = "dim_campaigns"

    campaign_key: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    campaign_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    extracted_status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    facts: Mapped[List["FactAdPerformance"]] = relationship("FactAdPerformance", back_populates="campaign")

class DimDate(Base):
    __tablename__ = "dim_dates"

    date_key: Mapped[int] = mapped_column(primary_key=True)
    full_date: Mapped[datetime] = mapped_column(Date, nullable=False, unique=True)
    day: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)

    facts: Mapped[List["FactAdPerformance"]] = relationship("FactAdPerformance", back_populates="date_dimension")

class FactAdPerformance(Base):
    __tablename__ = "fact_ad_performance"

    fact_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    date_key: Mapped[int] = mapped_column(ForeignKey("dim_dates.date_key"), nullable=False)
    campaign_key: Mapped[UUID] = mapped_column(ForeignKey("dim_campaigns.campaign_key"), nullable=False)
    
    spend: Mapped[float] = mapped_column(Float, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False)
    ctr: Mapped[float] = mapped_column(Float, nullable=False)
    cpc: Mapped[float] = mapped_column(Float, nullable=False)
    
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False)
    anomaly_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    campaign: Mapped["DimCampaign"] = relationship("DimCampaign", back_populates="facts")
    date_dimension: Mapped["DimDate"] = relationship("DimDate", back_populates="facts")