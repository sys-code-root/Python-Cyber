import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from uuid import uuid4
from sqlalchemy import select
from faststream import FastStream
from faststream.rabbit import RabbitBroker

from config import logger
from models import Shipment, CheckpointLedger
from schemas import CarrierCheckpointEvent, DelayAlertPayload
from database import DatabaseManager
from risk_engine import LogisticsRiskEngine

broker = RabbitBroker()
app = FastStream(broker)

db_manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
risk_engine = LogisticsRiskEngine()

@broker.subscriber("carrier.checkpoints")
async def handle_carrier_checkpoint(payload: Dict[str, Any]) -> None:
    logger.info("Event consumed from 'carrier.checkpoints' pipeline.")
    try:
        event_data = CarrierCheckpointEvent.model_validate(payload)
    except Exception as err:
        logger.error(f"Invalid payload schema. Aborting. Trace: {str(err)}")
        return

    try:
        async for session in db_manager.get_session():
            shipment_query = await session.execute(
                select(Shipment).where(Shipment.tracking_code == event_data.tracking_code)
            )
            shipment: Optional[Shipment] = shipment_query.scalar_one_or_none()

            if not shipment:
                logger.warning(f"Orphaned event: tracking code '{event_data.tracking_code}' not found in database.")
                return

            new_entry = CheckpointLedger(
                shipment_id=shipment.id,
                location_hub=event_data.location_hub,
                arrival_timestamp=event_data.status_timestamp,
                status_description=event_data.status_description,
                raw_payload=payload
            )
            session.add(new_entry)
            
            risk_score = await risk_engine.predict_delay_probability(
                hours_at_hub=12.5,
                carrier_historical_delay_rate=0.28,
                days_remaining=1.0
            )

            logger.info(f"Calculated SLA Risk Score for Package: {risk_score}")

            if risk_score >= 0.75:
                logger.warning(f"🚨 CRITICAL OVERWATCH ALERT: Risk score {risk_score} violates SLA for {shipment.tracking_code}")
                
                alert = DelayAlertPayload(
                    shipment_id=str(shipment.id),
                    tracking_code=shipment.tracking_code,
                    carrier=shipment.carrier,
                    risk_score=risk_score,
                    status_description=event_data.status_description
                )
                
                await broker.publish(alert.model_dump(mode="json"), queue="logistics.alerts.delay")
                logger.info("Downstream alert notification published successfully to 'logistics.alerts.delay'.")

    except Exception as system_fault:
        logger.error(f"Internal processing failure: {str(system_fault)}")

@broker.subscriber("logistics.alerts.delay")
async def handle_downstream_alert(payload: Dict[str, Any]) -> None:
    logger.info(f"🔔 ALERT CONSUMER ACTIVATED: Successfully received risk signal for {payload.get('tracking_code')} | Score: {payload.get('risk_score')}")

@app.after_startup
async def run_automated_simulation() -> None:
    logger.info("🚀 Starting Automated Simulation Environment...")
    await db_manager.create_tables()
    
    async with db_manager._session_factory() as session:
        mock_shipment = Shipment(
            id=uuid4(),
            tracking_code="AEGIS-QUANTUM-99",
            carrier="DHL_EXPRESS",
            promised_delivery_date=datetime.now(timezone.utc) + timedelta(days=1),
            status="IN_TRANSIT"
        )
        session.add(mock_shipment)
        await session.commit()
    logger.info("Database initialized with contract: 'AEGIS-QUANTUM-99'")

    await asyncio.sleep(1)
    logger.info("Simulating carrier transmission: incoming checkpoint radio alert...")
    
    mock_event = {
        "tracking_code": "AEGIS-QUANTUM-99",
        "location_hub": "BERLIN_LOGISTICS_HUB_A",
        "status_timestamp": datetime.now(timezone.utc).isoformat(),
        "status_description": "Package held for customs anomalies inspection"
    }
    await broker.publish(mock_event, queue="carrier.checkpoints")