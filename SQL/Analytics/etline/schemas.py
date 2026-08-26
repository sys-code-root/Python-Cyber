from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

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