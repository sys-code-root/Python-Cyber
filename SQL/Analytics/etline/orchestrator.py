import asyncio
from datetime import datetime
from typing import Any, Dict, List
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import DatabaseManager
from models import DimCampaign, DimDate, FactAdPerformance
from schemas import CleanedAdMetrics
from ai_engine import AIAnomalyEngine
from api_simulator import AdPlatformAPISimulator

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