from typing import List
import numpy as np
import pandas as pd
from sqlalchemy import select

from models import Product, SalesHistory
from database import DatabaseManager
from predictor import DemandPredictor

class PresentationDataService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def fetch_inventory_status(self) -> List[dict]:
        async with self.db_manager.session_factory() as session:
            product_query = select(Product)
            product_result = await session.execute(product_query)
            products = product_result.scalars().all()
            
            inventory_reports = []
            for product in products:
                sales_query = select(SalesHistory).where(SalesHistory.product_id == product.id)
                sales_result = await session.execute(sales_query)
                sales = sales_result.scalars().all()
                
                sales_df = pd.DataFrame([{
                    "sale_date": s.sale_date, "quantity_sold": s.quantity_sold
                } for s in sales])
                
                days_left, avg_demand = DemandPredictor.forecast_zero_stock_date(sales_df, product.current_stock)
                
                reorder_point = int(np.ceil(avg_demand * product.lead_time_days))
                action_required = "HOLD"
                
                if days_left <= product.lead_time_days:
                    action_required = "CRITICAL REORDER"
                elif product.current_stock <= reorder_point:
                    action_required = "WARNING"
                    
                suggested_purchase = max(int(np.ceil(avg_demand * 30)) - product.current_stock, 0)

                inventory_reports.append({
                    "id": product.id,
                    "sku": product.sku,
                    "name": product.name,
                    "current_stock": product.current_stock,
                    "lead_time": product.lead_time_days,
                    "avg_demand": round(avg_demand, 2),
                    "days_until_zero": days_left,
                    "reorder_point": reorder_point,
                    "suggested_purchase": suggested_purchase,
                    "action_required": action_required,
                    "sales_data": sales_df
                })
            return inventory_reports