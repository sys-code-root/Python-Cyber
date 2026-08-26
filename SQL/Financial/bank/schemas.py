import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class TransactionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    date: datetime.date
    amount: Decimal = Field(..., max_digits=18, decimal_places=4)
    description: str
    status: str


class ReconciliationSummary(BaseModel):
    exact_matches: int
    fuzzy_matches: int
    anomalies_detected: int
    execution_status: str