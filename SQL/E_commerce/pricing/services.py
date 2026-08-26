from decimal import Decimal

from config import logger, AI_SAFETY_FLOOR
from enums import CouponType
from models import ProductModel, CouponModel
from schemas import PricingRequest, AppliedCouponSchema

class PricingEngineService:
    
    @staticmethod
    async def analyze_market_with_ai(product: ProductModel) -> Decimal:
        try:
            base = Decimal(str(product.base_price))
            competitor = Decimal(str(product.competitor_price))
            stock = product.stock_volume

            if stock < 5 and competitor > base:
                ai_modifier = Decimal("1.18")
            elif stock > 120 and competitor < base:
                ai_modifier = Decimal("0.88")
            else:
                ai_modifier = (competitor * Decimal("0.98")) / base
                
            calculated_price = base * ai_modifier
            
        except Exception as e:
            logger.error(f"AI Pricing Engine Inference anomaly: {str(e)}. Falling back to baseline price.")
            calculated_price = product.base_price
            
        safety_floor = product.base_price * AI_SAFETY_FLOOR
        return max(calculated_price, safety_floor).quantize(Decimal("0.00"))

    @classmethod
    def process_coupons(
        cls, 
        current_price: Decimal, 
        category: str, 
        request: PricingRequest, 
        coupons: list[CouponModel]
    ) -> tuple[list[AppliedCouponSchema], Decimal]:
        applied_coupons: list[AppliedCouponSchema] = []
        running_price = current_price

        sorted_coupons = sorted(coupons, key=lambda c: 0 if c.type == CouponType.PERCENTAGE else 1)

        for coupon in sorted_coupons:
            if running_price < coupon.min_purchase_value:
                continue

            if coupon.target_region and coupon.target_region != request.user_region:
                continue

            if coupon.first_purchase_only and not request.is_first_purchase:
                continue

            if coupon.excluded_categories:
                if category.lower() in [c.strip().lower() for c in coupon.excluded_categories.split(",")]:
                    continue

            if coupon.type == CouponType.PERCENTAGE:
                discount = running_price * (coupon.value / Decimal("100"))
            else:
                discount = coupon.value

            discount = min(discount, running_price)
            running_price -= discount

            applied_coupons.append(
                AppliedCouponSchema(
                    code=coupon.code, 
                    discount_applied=discount.quantize(Decimal("0.00"))
                )
            )

        return applied_coupons, running_price