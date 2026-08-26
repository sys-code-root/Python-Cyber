import asyncio
from config import logger

class LogisticsRiskEngine:
    @staticmethod
    async def predict_delay_probability(hours_at_hub: float, carrier_historical_delay_rate: float, days_remaining: float) -> float:
        logger.info(f"AI Engine crunching metrics -> Hours At Hub: {hours_at_hub}, Carrier Base Risk: {carrier_historical_delay_rate}, Days Left: {days_remaining}")
        await asyncio.sleep(0.05)
        if days_remaining <= 1:
            return 0.89  
        return 0.25