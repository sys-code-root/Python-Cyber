from datetime import date
from decimal import Decimal
from sqlalchemy import select

from models import Invoice, CommunicationLog
from database import DatabaseManager
from risk_engine import RiskEngine
from dispatcher import CommunicationDispatcher

class BillingAutomationEngine:
    def __init__(self, db_manager: DatabaseManager, risk_engine: RiskEngine):
        self.db_manager = db_manager
        self.risk_engine = risk_engine
        self.fine_rate = Decimal("0.02")
        self.daily_interest_rate = Decimal("0.00033")

    async def execute_daily_billing_sweep(self) -> None:
        today = date.today()
        async with self.db_manager.session_factory() as session:
            async with session.begin():
                query = select(Invoice).where(Invoice.status == "OVERDUE")
                result = await session.execute(query)
                overdue_invoices = result.scalars().all()

                for invoice in overdue_invoices:
                    days_past_due = (today - invoice.due_date).days
                    if days_past_due <= 0:
                        continue

                    base_fine = invoice.amount * self.fine_rate
                    compounded = invoice.amount * ((Decimal("1.0") + self.daily_interest_rate) ** days_past_due)
                    calculated_fees = base_fine + (compounded - invoice.amount)
                    invoice.accumulated_fees = calculated_fees.quantize(Decimal("0.01"))

                    recovery_probability = self.risk_engine.predict_probability(
                        days_overdue=days_past_due,
                        amount=invoice.amount,
                        historical_delays=2
                    )

                    total_due = invoice.amount + invoice.accumulated_fees
                    if recovery_probability >= 0.5:
                        action = await CommunicationDispatcher.dispatch_soft_reminder(invoice.id, invoice.customer_id, total_due)
                    else:
                        action = await CommunicationDispatcher.dispatch_critical_alert(invoice.id, invoice.customer_id, total_due)

                    log_entry = CommunicationLog(invoice_id=invoice.id, action_taken=action)
                    session.add(log_entry)