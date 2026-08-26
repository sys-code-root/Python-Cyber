import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID, uuid4
from loguru import logger
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import String, ForeignKey, select, Float, Integer, Date, Boolean, DateTime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

logger.add(
    sink=lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    enqueue=True
)

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

class DatabaseManager:
    def __init__(self, database_url: str) -> None:
        self._engine = create_async_engine(database_url, echo=False)
        self._session_factory = async_sessionmaker(bind=self._engine, class_=AsyncSession, expire_on_commit=False)

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"DW Transaction rollback due to error: {str(e)}")
                raise

    async def create_dw_schemas(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

class CleanedAdMetrics(BaseModel):
    model_config = ConfigDict(frozen=True)
    platform: str
    campaign_name: str
    date: datetime
    spend: float = Field(..., ge=0.0)
    impressions: int = Field(..., ge=0)
    clicks: int = Field(..., ge=0)

class AIAnomalyResponse(BaseModel):
    is_anomaly: bool
    reason: Optional[str] = None
    confidence_score: float

class AIAnomalyEngine:
    @staticmethod
    async def inspect_metrics_with_ai(metrics: CleanedAdMetrics) -> AIAnomalyResponse:
        await asyncio.sleep(0.05)
        
        if metrics.spend > 0.0 and metrics.clicks == 0:
            return AIAnomalyResponse(is_anomaly=True, reason="AI_DETECTED: Ad spending high budget but generating zero conversion intent.", confidence_score=0.99)
        
        if metrics.impressions > 0 and (metrics.clicks / metrics.impressions) > 0.65:
            return AIAnomalyResponse(is_anomaly=True, reason="AI_DETECTED: Click-Through Rate pattern highly correlates with automated click-fraud botnets.", confidence_score=0.94)
            
        return AIAnomalyResponse(is_anomaly=False, confidence_score=1.0)

class AdPlatformAPISimulator:
    def __init__(self) -> None:
        self.attempts_tracker: Dict[str, int] = {"Google": 0, "Facebook": 0, "TikTok": 0}

    async def fetch_google_ads(self) -> List[Dict[str, Any]]:
        self.attempts_tracker["Google"] += 1
        if self.attempts_tracker["Google"] < 2:
            logger.warning("Simulated HTTP 503 Service Unavailable on Google Ads API Endpoint.")
            raise ConnectionError("Google Ads Gateway Timeout")
        return [
            {"ad_date": "2026/07/11", "camp_name": "G_Search_Brand_Aegis", "cost": 150.75, "imps": 3500, "clicks": 180},
            {"ad_date": "2026/07/11", "camp_name": "G_PerformanceMax_Conversion", "cost": 420.00, "imps": 12000, "clicks": 950}
        ]

    async def fetch_facebook_ads(self) -> List[Dict[str, Any]]:
        return [
            {"date": "2026-07-11", "campaign": "FB_Prospecting_Lookalike_v2", "amount_spent": 310.50, "impressions": 8500, "clicks": 0},
            {"date": "2026-07-11", "campaign": "FB_Retargeting_Cart_Abandon", "amount_spent": 95.00, "impressions": 1200, "clicks": 890}
        ]

    async def fetch_tiktok_ads(self) -> List[Dict[str, Any]]:
        self.attempts_tracker["TikTok"] += 1
        if self.attempts_tracker["TikTok"] < 3:
            logger.warning("Simulated Connection Reset by Peer on TikTok Core Telemetry Cluster.")
            raise ConnectionError("TikTok Streams Interrupted")
        return [
            {"timestamp": "11-07-2026", "campaign_title": "TT_Video_Branding_Neon", "spend": 180.00, "views": 25000, "clicks": 120}
        ]

class EnterpriseETLOrchestrator:
    def __init__(self, db: DatabaseManager) -> None:
        self.db = db
        self.api = AdPlatformAPISimulator()

    async def execute_extract_with_retry(self, platform_name: str, api_coroutine) -> List[Dict[str, Any]]:
        max_retries = 3
        backoff_delay = 0.5
        for attempt in range(1, max_retries + 1):
            try:
                data = await api_coroutine()
                logger.info(f"Successfully extracted payloads from {platform_name} Ads on attempt {attempt}.")
                return data
            except ConnectionError as err:
                if attempt == max_retries:
                    logger.critical(f"Extraction Pipeline Failed permanently for {platform_name} after {max_retries} attempts.")
                    raise
                logger.warning(f"Retry hook triggered for {platform_name}. Attempt {attempt} failed: {str(err)}. Backoff: {backoff_delay}s")
                await asyncio.sleep(backoff_delay)
                backoff_delay *= 2
        return []

    def transform_payload(self, platform: str, raw_data: List[Dict[str, Any]]) -> List[CleanedAdMetrics]:
        cleaned_records = []
        for row in raw_data:
            try:
                if platform == "Google":
                    dt = datetime.strptime(row["ad_date"], "%Y/%m/%d")
                    metrics = CleanedAdMetrics(platform=platform, campaign_name=row["camp_name"], date=dt, spend=float(row["cost"]), impressions=int(row["imps"]), clicks=int(row["clicks"]))
                elif platform == "Facebook":
                    dt = datetime.strptime(row["date"], "%Y-%m-%d")
                    metrics = CleanedAdMetrics(platform=platform, campaign_name=row["campaign"], date=dt, spend=float(row["amount_spent"]), impressions=int(row["impressions"]), clicks=int(row["clicks"]))
                elif platform == "TikTok":
                    dt = datetime.strptime(row["timestamp"], "%d-%m-%Y")
                    metrics = CleanedAdMetrics(platform=platform, campaign_name=row["campaign_title"], date=dt, spend=float(row["spend"]), impressions=int(row["views"]), clicks=int(row["clicks"]))
                cleaned_records.append(metrics)
            except Exception as transform_err:
                logger.error(f"Data mapping corruption found in {platform} schema. Dropping record. Error: {str(transform_err)}")
        return cleaned_records

    async def load_into_dimensional_dw(self, session: AsyncSession, record: CleanedAdMetrics) -> None:
        campaign_stmt = await session.execute(select(DimCampaign).where(DimCampaign.campaign_name == record.campaign_name))
        campaign = campaign_stmt.scalar_one_or_none()
        if not campaign:
            campaign = DimCampaign(platform=record.platform, campaign_name=record.campaign_name)
            session.add(campaign)
            await session.flush()

        date_id = int(record.date.strftime("%Y%m%d"))
        date_stmt = await session.execute(select(DimDate).where(DimDate.date_key == date_id))
        date_dim = date_stmt.scalar_one_or_none()
        if not date_dim:
            date_dim = DimDate(
                date_key=date_id,
                full_date=record.date.date(),
                day=record.date.day,
                month=record.date.month,
                year=record.date.year,
                quarter=(record.date.month - 1) // 3 + 1
            )
            session.add(date_dim)
            await session.flush()

        ai_analysis = await AIAnomalyEngine.inspect_metrics_with_ai(record)
        if ai_analysis.is_anomaly:
            logger.error(f"💥 AI DETECTED ANOMALY [{ai_analysis.confidence_score * 100}% Confidence]: Platform={record.platform} | Campaign={record.campaign_name} | Reason={ai_analysis.reason}")

        ctr = (record.clicks / record.impressions) if record.impressions > 0 else 0.0
        cpc = (record.spend / record.clicks) if record.clicks > 0 else 0.0

        fact_entry = FactAdPerformance(
            date_key=date_dim.date_key,
            campaign_key=campaign.campaign_key,
            spend=record.spend,
            impressions=record.impressions,
            clicks=record.clicks,
            ctr=round(ctr, 4),
            cpc=round(cpc, 4),
            is_anomaly=ai_analysis.is_anomaly,
            anomaly_reason=ai_analysis.reason
        )
        session.add(fact_entry)

    async def run_pipeline(self) -> None:
        logger.info("Initializing Aegis Multi-Platform Marketing Analytics ETL Run...")
        await self.db.create_dw_schemas()

        fb_task = self.execute_extract_with_retry("Facebook", self.api.fetch_facebook_ads)
        google_task = self.execute_extract_with_retry("Google", self.api.fetch_google_ads)
        tt_task = self.execute_extract_with_retry("TikTok", self.api.fetch_tiktok_ads)
        
        raw_fb, raw_google, raw_tiktok = await asyncio.gather(fb_task, google_task, tt_task)

        cleaned_data: List[CleanedAdMetrics] = []
        cleaned_data.extend(self.transform_payload("Facebook", raw_fb))
        cleaned_data.extend(self.transform_payload("Google", raw_google))
        cleaned_data.extend(self.transform_payload("TikTok", raw_tiktok))

        logger.info(f"Transformation complete. {len(cleaned_data)} target records consolidated.")

        async with self._db_session_context() as session:
            for cleaned_record in cleaned_data:
                await self.load_into_dimensional_dw(session, cleaned_record)
        
        logger.info("ETL Pipeline Execution Completed Successfully.")

    def _db_session_context(self):
        class SessionContext:
            def __init__(self, manager): self.manager = manager
            async def __aenter__(self):
                self.gen = self.manager.get_session()
                return await self.gen.__anext__()
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                try: await self.gen.__anext__()
                except StopAsyncIteration: pass
        return SessionContext(self.db)

if __name__ == "__main__":
    dw_manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    orchestrator = EnterpriseETLOrchestrator(dw_manager)
    try:
        asyncio.run(orchestrator.run_pipeline())
    except KeyboardInterrupt:
        logger.warning("Pipeline process shutdown manually by engineer context.")