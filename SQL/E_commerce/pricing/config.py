import logging
from decimal import Decimal

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PricingEngine")

DATABASE_URL = "sqlite+aiosqlite:///:memory:"
GLOBAL_PRICE_FLOOR = Decimal("0.70")
AI_SAFETY_FLOOR = Decimal("0.85")