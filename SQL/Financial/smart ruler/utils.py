from datetime import date
import numpy as np
import pandas as pd

def construct_aging_buckets(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return pd.DataFrame(columns=["Aging Bucket", "Outstanding Balance"])
    
    today = date.today()
    dataframe["due_date"] = pd.to_datetime(dataframe["due_date"]).dt.date
    overdue_df = dataframe[dataframe["status"] == "OVERDUE"].copy()
    
    if overdue_df.empty:
        return pd.DataFrame(columns=["Aging Bucket", "Outstanding Balance"])

    overdue_df["days_past"] = overdue_df["due_date"].apply(lambda x: (today - x).days)
    overdue_df["total_debt"] = overdue_df["amount"] + overdue_df["accumulated_fees"]

    conditions = [
        (overdue_df["days_past"] <= 30),
        (overdue_df["days_past"] > 30) & (overdue_df["days_past"] <= 60),
        (overdue_df["days_past"] > 60)
    ]
    choices = ["1-30 Days", "31-60 Days", "60+ Days"]
    overdue_df["Aging Bucket"] = np.select(conditions, choices, default="Unknown")
    
    grouped = overdue_df.groupby("Aging Bucket", observed=False)["total_debt"].sum().reset_index()
    grouped.columns = ["Aging Bucket", "Outstanding Balance"]
    
    bucket_order = {bucket: i for i, bucket in enumerate(choices)}
    grouped["order"] = grouped["Aging Bucket"].map(bucket_order)
    return grouped.sort_values("order").drop(columns=["order"])