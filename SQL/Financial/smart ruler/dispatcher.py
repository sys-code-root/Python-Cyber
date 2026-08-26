import asyncio
from decimal import Decimal

class CommunicationDispatcher:
    @staticmethod
    async def dispatch_soft_reminder(invoice_id: int, customer_id: str, amount: Decimal) -> str:
        await asyncio.sleep(0.01)
        return f"Email Reminder Sent to {customer_id} for Invoice #{invoice_id} [Amount: ${amount}]"

    @staticmethod
    async def dispatch_critical_alert(invoice_id: int, customer_id: str, amount: Decimal) -> str:
        await asyncio.sleep(0.01)
        return f"Webhook Critical Escalation Triggered for {customer_id} [Total Debt: ${amount}]"