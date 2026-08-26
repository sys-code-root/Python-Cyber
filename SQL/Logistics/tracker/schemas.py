from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

class CarrierCheckpointEvent(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    tracking_code: str
    location_hub: str
    status_timestamp: datetime
    status_description: str

class DelayAlertPayload(BaseModel):
    shipment_id: str
    tracking_code: str
    carrier: str
    risk_score: float
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status_description: str