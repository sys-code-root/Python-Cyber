import asyncio
from schemas import CleanedAdMetrics, AIAnomalyResponse

class AIAnomalyEngine:
    @staticmethod
    async def inspect_metrics_with_ai(metrics: CleanedAdMetrics) -> AIAnomalyResponse:
        await asyncio.sleep(0.05)
        
        if metrics.spend > 0.0 and metrics.clicks == 0:
            return AIAnomalyResponse(is_anomaly=True, reason="AI_DETECTED: Ad spending high budget but generating zero conversion intent.", confidence_score=0.99)
        
        if metrics.impressions > 0 and (metrics.clicks / metrics.impressions) > 0.65:
            return AIAnomalyResponse(is_anomaly=True, reason="AI_DETECTED: Click-Through Rate pattern highly correlates with automated click-fraud botnets.", confidence_score=0.94)
            
        return AIAnomalyResponse(is_anomaly=False, confidence_score=1.0)