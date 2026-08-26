from pydantic import BaseModel, Field
from config import logger

class ValidatedJourney(BaseModel):
    user_id: str = Field(..., min_length=3)
    touchpoints: list[str] = Field(..., min_length=1)
    timestamps: list[int] = Field(..., min_length=1)
    revenue: float = Field(..., ge=0.0)
    converted: int = Field(..., ge=0, le=1)

class ValidatedCost(BaseModel):
    channel: str
    cost: float = Field(..., ge=0.0)

def validate_and_transform_data(raw_journeys, raw_costs) -> tuple[list[ValidatedJourney], dict[str, float]]:
    clean_journeys = []
    for r in raw_journeys:
        try:
            v = ValidatedJourney(
                user_id=r.user_id,
                touchpoints=r.touchpoints.split(";"),
                timestamps=[int(x) for x in r.timestamps.split(";")],
                revenue=r.revenue,
                converted=r.converted
            )
            clean_journeys.append(v)
        except Exception as e:
            logger.error(f"Pydantic parsing isolation alert on record {r.id}: {e}")
            continue

    cost_map = {}
    for c in raw_costs:
        try:
            v = ValidatedCost(channel=c.channel, cost=c.cost)
            cost_map[v.channel] = v.cost
        except Exception as e:
            logger.error(f"Pydantic parsing isolation alert on cost mapping table structural segment: {e}")
            continue
            
    return clean_journeys, cost_map