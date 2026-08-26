from typing import Any, Dict, List
from loguru import logger

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