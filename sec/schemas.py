from pydantic import BaseModel, Field


class JWTPayloadSchema(BaseModel):
    user_id: int = Field(..., description="Unique numerical user identifier")
    role: str = Field(..., min_length=1, description="Assigned role for access control")


class HMACPayloadSchema(BaseModel):
    user_id: int
    action: str
    amount: float = Field(..., ge=0.0)