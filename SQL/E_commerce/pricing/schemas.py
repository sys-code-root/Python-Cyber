from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

class PricingRequest(BaseModel):
    product_id: int
    user_region: str = Field(..., min_length=2, max_length=2, description="State/Region ISO code")
    is_first_purchase: bool = False
    coupon_codes: list[str] = Field(default_factory=list)

    @field_validator("user_region", mode="before")
    @classmethod
    def normalize_region(cls, v: str) -> str:
        return str(v).strip().upper() if v else v

    @field_validator("coupon_codes", mode="before")
    @classmethod
    def clean_coupon_codes(cls, v: list) -> list[str]:
        if isinstance(v, list):
            return [str(code).strip().upper() for code in v if code]
        return v

class AppliedCouponSchema(BaseModel):
    code: str
    discount_applied: Decimal

class PricingResponse(BaseModel):
    product_id: int
    base_price: Decimal
    dynamic_price: Decimal
    applied_coupons: list[AppliedCouponSchema]
    invalid_or_expired_coupons: list[str] = Field(default_factory=list)
    final_price: Decimal