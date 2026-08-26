from typing import Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

class DemandPredictor:
    @staticmethod
    def forecast_zero_stock_date(sales_df: pd.DataFrame, current_stock: int) -> Tuple[int, float]:
        if sales_df.empty or len(sales_df) < 2:
            return 0, 0.0
            
        grouped_sales = sales_df.groupby("sale_date")["quantity_sold"].sum().reset_index()
        grouped_sales["day_index"] = np.arange(len(grouped_sales))
        
        X = grouped_sales[["day_index"]]
        y = grouped_sales["quantity_sold"]
        
        model = LinearRegression()
        model.fit(X, y)
        
        avg_daily_demand = max(float(model.predict([[len(grouped_sales)]])[0]), 0.1)
        days_until_zero = int(np.ceil(current_stock / avg_daily_demand))
        
        return days_until_zero, avg_daily_demand