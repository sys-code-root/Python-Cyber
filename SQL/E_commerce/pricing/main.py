from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import GLOBAL_PRICE_FLOOR
from database import engine, Base, get_db
from models import ProductModel
from schemas import PricingRequest, PricingResponse
from services import PricingEngineService

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title="Pricing & Coupon API",
    version="2.5.0",
    lifespan=lifespan
)

@app.post(
    "/api/v1/pricing/calculate", 
    response_model=PricingResponse, 
    status_code=status.HTTP_200_OK,
    summary="Calculates final product price with coupon application"
)
async def calculate_pricing(request: PricingRequest, db: AsyncSession = Depends(get_db)):
    product = await db.get(ProductModel, request.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Product ID {request.product_id} not found."
        )

    # Coupon validation logic encapsulated inside the service layer
    valid_coupons, invalid_codes = await PricingEngineService.validate_coupons(
        db, request.coupon_codes
    )

    dynamic_price = await PricingEngineService.analyze_market_with_ai(product)

    processed_coupons, computed_final_price = PricingEngineService.process_coupons(
        current_price=dynamic_price,
        category=product.category,
        request=request,
        coupons=valid_coupons
    )
    
    price_floor = product.base_price * GLOBAL_PRICE_FLOOR
    final_price = max(computed_final_price, price_floor)

    return PricingResponse(
        product_id=product.id,
        base_price=product.base_price,
        dynamic_price=dynamic_price,
        applied_coupons=processed_coupons,
        invalid_or_expired_coupons=invalid_codes,
        final_price=final_price.quantize(Decimal("0.00"))
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)