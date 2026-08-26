from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import DATABASE_URL, logger

class Base(DeclarativeBase):
    pass

class JourneyRecord(Base):
    __tablename__ = "customer_journeys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    touchpoints: Mapped[str] = mapped_column(Text, nullable=False)
    timestamps: Mapped[str] = mapped_column(Text, nullable=False)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    converted: Mapped[int] = mapped_column(Integer, default=0)

class ChannelCostRecord(Base):
    __tablename__ = "channel_costs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)

class DatabaseManager:
    def __init__(self, url: str):
        self.engine = create_async_engine(url, echo=False, poolclass=NullPool)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def initialize_schemas(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas initialized.")

    async def seed_data_if_empty(self):
        async with self.session_factory() as session:
            from sqlalchemy import select, func
            result = await session.execute(select(func.count(JourneyRecord.id)))
            count = result.scalar()
            if count and count > 0:
                return

            logger.info("Database is empty. Initiating mock generation engine...")
            
            costs = {
                "Google Ads": 12000.0,
                "Facebook Ads": 9500.0,
                "Instagram": 7000.0,
                "TikTok": 8500.0,
                "Email": 1500.0,
                "Direct": 0.0,
                "Referral": 1200.0
            }
            for ch, cost in costs.items():
                session.add(ChannelCostRecord(channel=ch, cost=cost))

            np.random.seed(42)
            base_time = datetime.now() - timedelta(days=30)
            channels_pool = list(costs.keys())
            
            for i in range(1, 1201):
                user_id = f"USR-{i:05d}"
                rand_val = np.random.rand()
                if rand_val < 0.25:
                    tps = ["Google Ads", "Instagram", "Email"]
                    revenue = float(np.random.normal(600, 150))
                    converted = 1
                elif rand_val < 0.45:
                    tps = ["TikTok", "Instagram"]
                    revenue = float(np.random.normal(200, 50))
                    converted = 1
                elif rand_val < 0.65:
                    tps = ["Facebook Ads", "Google Ads", "Direct", "Email"]
                    revenue = float(np.random.normal(1100, 250))
                    converted = 1
                elif rand_val < 0.85:
                    tps = [np.random.choice(["Direct", "Referral"]), "Email"]
                    revenue = float(np.random.normal(120, 30))
                    converted = 1
                else:
                    path_len = np.random.randint(1, 4)
                    tps = list(np.random.choice(channels_pool, size=path_len))
                    revenue = 0.0
                    converted = 0
                
                revenue = max(0.0, round(revenue, 2)) if converted == 1 else 0.0
                
                times = []
                current_tp_time = base_time + timedelta(days=np.random.uniform(0, 28))
                for _ in tps:
                    times.append(str(int(current_tp_time.timestamp())))
                    current_tp_time += timedelta(hours=np.random.uniform(2, 48))

                session.add(JourneyRecord(
                    user_id=user_id,
                    touchpoints=";".join(tps),
                    timestamps=";".join(times),
                    revenue=revenue,
                    converted=converted
                ))
            
            await session.commit()
            logger.info("Database successfully loaded with comprehensive mock validation sequences.")

    async def fetch_analytics_dataset(self):
        async with self.session_factory() as session:
            from sqlalchemy import select
            journey_stmt = select(JourneyRecord)
            cost_stmt = select(ChannelCostRecord)
            
            j_res = await session.execute(journey_stmt)
            c_res = await session.execute(cost_stmt)
            
            journeys = j_res.scalars().all()
            costs = c_res.scalars().all()
            
            return journeys, costs

db_manager = DatabaseManager(DATABASE_URL)