from decimal import Decimal
from fastapi import Depends, HTTPException, status, APIRouter, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db_session
from models import GatewayTransaction, BankTransaction, ReconciliationLog
from schemas import ReconciliationSummary
from services import ReconciliationService

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


@router.post("/process", response_model=ReconciliationSummary, status_code=status.HTTP_200_OK)
async def process_reconciliation(
    ofx_file: UploadFile = File(...),
    csv_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        ofx_content = await ofx_file.read()
        csv_content = await csv_file.read()
        
        bank_data = ReconciliationService.parse_ofx(ofx_content)
        gateway_data = ReconciliationService.parse_gateway_csv(csv_content)
        
        for tx in bank_data:
            db.add(BankTransaction(id=tx["id"], date=tx["date"], amount=tx["amount"], description=tx["description"]))
        for tx in gateway_data:
            db.add(GatewayTransaction(id=tx["id"], date=tx["date"], amount=tx["amount"], fee=tx["fee"], description=tx["description"]))
        
        await db.flush()

        exact_matches = await ReconciliationService.execute_exact_match(db)
        for gateway, bank in exact_matches:
            gateway.status = "RECONCILED"
            bank.status = "RECONCILED"
            db.add(ReconciliationLog(
                gateway_transaction_id=gateway.id,
                bank_transaction_id=bank.id,
                match_type="EXACT",
                confidence_score=Decimal("100.00"),
                anomaly_flag=False
            ))
        
        await db.flush()

        fuzzy_matches = await ReconciliationService.execute_fuzzy_match(db)
        for match in fuzzy_matches:
            gateway = match["gateway"]
            bank = match["bank"]
            gateway.status = "RECONCILED"
            bank.status = "RECONCILED"
            db.add(ReconciliationLog(
                gateway_transaction_id=gateway.id,
                bank_transaction_id=bank.id,
                match_type="FUZZY",
                confidence_score=match["score"],
                anomaly_flag=False
            ))

        await db.flush()

        anomalies = ReconciliationService.detect_fee_anomalies(gateway_data)
        anomaly_count = 0
        for tx, is_anomaly in zip(gateway_data, anomalies):
            if is_anomaly:
                anomaly_count += 1
                db.add(ReconciliationLog(
                    gateway_transaction_id=tx["id"],
                    bank_transaction_id=None,
                    match_type="UNMATCHED",
                    confidence_score=Decimal("0.00"),
                    anomaly_flag=True
                ))

        return ReconciliationSummary(
            exact_matches=len(exact_matches),
            fuzzy_matches=len(fuzzy_matches),
            anomalies_detected=anomaly_count,
            execution_status="SUCCESS"
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal operational failure within the reconciliation engine: {str(error)}"
        )