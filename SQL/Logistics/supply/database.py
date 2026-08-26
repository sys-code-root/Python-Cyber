from datetime import date, timedelta
import numpy as np
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from models import Base, Product, SalesHistory

class DatabaseManager:
    def __init__(self, connection_string: str = "sqlite+aiosqlite:///:memory:"):
        self.engine = create_async_engine(connection_string, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def initialize_database(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def seed_mock_data(self) -> None:
        async with self.session_factory() as session:
            async with session.begin():
                today = date.today()
                
                p1 = Product(sku="SKU-CHIP-X1", name="Quantum Processing Unit v1", current_stock=45, lead_time_days=5)
                p2 = Product(sku="SKU-NEURAL-LINK", name="Neural Interface Node", current_stock=12, lead_time_days=7)
                p3 = Product(sku="SKU-CYBER-CORE", name="Fusion Core Cell Block", current_stock=120, lead_time_days=3)
                session.add_all([p1, p2, p3])
                await session.flush()

                sales = []
                for i in range(30, 0, -1):
                    sale_date = today - timedelta(days=i)
                    sales.append(SalesHistory(product_id=p1.id, sale_date=sale_date, quantity_sold=np.random.randint(2, 6)))
                    sales.append(SalesHistory(product_id=p2.id, sale_date=sale_date, quantity_sold=np.random.randint(3, 8)))
                    sales.append(SalesHistory(product_id=p3.id, sale_date=sale_date, quantity_sold=np.random.randint(1, 4)))
                session.add_all(sales)