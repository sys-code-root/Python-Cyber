import io
from decimal import Decimal
from typing import List, Tuple, Dict, Any

import pandas as pd
from ofxparse import OfxParser
from rapidfuzz import fuzz, process
from sklearn.ensemble import IsolationForest
import numpy as np

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models import GatewayTransaction, BankTransaction


class ReconciliationService:
    """Provides business logic and data engineering capabilities for transaction reconciliation."""

    @staticmethod
    def parse_ofx(file_content: bytes) -> List[Dict[str, Any]]:
        """Parses bank transaction data from standard OFX files."""
        ofx_buffer = io.BytesIO(file_content)
        ofx = OfxParser.parse(ofx_buffer)
        parsed_transactions = []
        
        for account in ofx.accounts:
            for tx in account.statement.transactions:
                parsed_transactions.append({
                    "id": str(tx.id),
                    "date": tx.date.date(),
                    "amount": Decimal(str(tx.amount)),
                    "description": str(tx.memo or tx.payee).strip()
                })
        return parsed_transactions

    @staticmethod
    def parse_gateway_csv(file_content: bytes) -> List[Dict[str, Any]]:
        """Parses gateway transaction records from standard CSV exports."""
        csv_buffer = io.BytesIO(file_content)
        dataframe = pd.read_csv(csv_buffer, dtype={"id": str, "description": str})
        
        dataframe["amount"] = dataframe["amount"].astype(str).apply(Decimal)
        dataframe["fee"] = dataframe["fee"].astype(str).apply(Decimal)
        dataframe["date"] = pd.to_datetime(dataframe["date"]).dt.date
        
        return dataframe.to_dict(orient="records")

    @staticmethod
    async def execute_exact_match(db: AsyncSession) -> List[Tuple[GatewayTransaction, BankTransaction]]:
        """Performs optimized batch-matching over primary indices and financial parameters via IN queries."""
        bank_stmt = select(BankTransaction).where(BankTransaction.status == "PENDING")
        bank_result = await db.execute(bank_stmt)
        bank_transactions = bank_result.scalars().all()

        if not bank_transactions:
            return []

        bank_ids = [tx.id for tx in bank_transactions]

        gateway_stmt = select(GatewayTransaction).where(
            and_(
                GatewayTransaction.id.in_(bank_ids),
                GatewayTransaction.status == "PENDING"
            )
        )
        gateway_result = await db.execute(gateway_stmt)
        gateway_transactions = gateway_result.scalars().all()

        gateway_map = {tx.id: tx for tx in gateway_transactions}
        matches = []

        for bank_tx in bank_transactions:
            if bank_tx.id in gateway_map:
                gateway_tx = gateway_map[bank_tx.id]
                if gateway_tx.amount == bank_tx.amount:
                    matches.append((gateway_tx, bank_tx))

        return matches

    @staticmethod
    async def execute_fuzzy_match(db: AsyncSession, threshold: float = 75.0) -> List[Dict[str, Any]]:
        """Executes secondary text similarity processing on unmatched pending entries."""
        gateway_stmt = select(GatewayTransaction).where(GatewayTransaction.status == "PENDING")
        bank_stmt = select(BankTransaction).where(BankTransaction.status == "PENDING")
        
        gateway_transactions = (await db.execute(gateway_stmt)).scalars().all()
        bank_transactions = (await db.execute(bank_stmt)).scalars().all()
        
        matches = []
        if not gateway_transactions or not bank_transactions:
            return matches

        bank_description_map = {tx.description: tx for tx in bank_transactions}
        bank_descriptions = list(bank_description_map.keys())

        for gateway_tx in gateway_transactions:
            extraction_result = process.extractOne(
                gateway_tx.description, 
                bank_descriptions, 
                scorer=fuzz.token_set_ratio
            )
            
            if extraction_result:
                best_match_description, score, _ = extraction_result
                if score >= threshold:
                    matched_bank_transaction = bank_description_map[best_match_description]
                    
                    if gateway_tx.amount == matched_bank_transaction.amount:
                        matches.append({
                            "gateway": gateway_tx,
                            "bank": matched_bank_transaction,
                            "score": Decimal(str(score))
                        })
                        bank_descriptions.remove(best_match_description)
                        
        return matches

    @staticmethod
    def detect_fee_anomalies(gateway_records: List[Dict[str, Any]], contamination: float = 0.05) -> List[bool]:
        """Utilizes an Isolation Forest estimator to identify irregular operational fees."""
        if not gateway_records:
            return []
            
        features = np.array([
            [float(tx["amount"]), float(tx["fee"])] 
            for tx in gateway_records
        ])
        
        isolation_forest = IsolationForest(contamination=contamination, random_state=42)
        predictions = isolation_forest.fit_predict(features)
        
        return [prediction == -1 for prediction in predictions]