import pandas as pd
from sqlalchemy import select

from models import Invoice, CommunicationLog
from database import DatabaseManager

class PresentationDataService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def fetch_invoice_metrics(self) -> pd.DataFrame:
        async with self.db_manager.session_factory() as session:
            result = await session.execute(select(Invoice))
            invoices = result.scalars().all()
            return pd.DataFrame([{
                "id": i.id, "customer_id": i.customer_id, "due_date": i.due_date,
                "amount": float(i.amount), "accumulated_fees": float(i.accumulated_fees), "status": i.status
            } for i in invoices])

    async def fetch_communication_logs(self) -> pd.DataFrame:
        async with self.db_manager.session_factory() as session:
            result = await session.execute(select(CommunicationLog).order_by(CommunicationLog.dispatched_at.desc()))
            logs = result.scalars().all()
            return pd.DataFrame([{
                "id": l.id, "invoice_id": l.invoice_id, "action_taken": l.action_taken, "dispatched_at": l.dispatched_at
            } for l in logs])