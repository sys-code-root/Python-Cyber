from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from models import Base, Invoice

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
                invoices = [
                    Invoice(customer_id="CUST-101", due_date=today - timedelta(days=15), amount=Decimal("1500.00"), status="OVERDUE"),
                    Invoice(customer_id="CUST-102", due_date=today - timedelta(days=45), amount=Decimal("2800.00"), status="OVERDUE"),
                    Invoice(customer_id="CUST-103", due_date=today - timedelta(days=75), amount=Decimal("5000.00"), status="OVERDUE"),
                    Invoice(customer_id="CUST-104", due_date=today + timedelta(days=5), amount=Decimal("1200.00"), status="PENDING"),
                    Invoice(customer_id="CUST-105", due_date=today - timedelta(days=5), amount=Decimal("950.00"), status="OVERDUE"),
                    Invoice(customer_id="CUST-106", due_date=today - timedelta(days=32), amount=Decimal("4300.00"), status="OVERDUE"),
                    Invoice(customer_id="CUST-107", due_date=today - timedelta(days=12), amount=Decimal("600.00"), status="PAID")
                ]
                session.add_all(invoices)