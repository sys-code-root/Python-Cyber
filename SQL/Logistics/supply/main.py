import asyncio
from datetime import date, timedelta
import logging
import numpy as np
import plotly.graph_objects as go
import streamlit as st

from database import DatabaseManager
from services import PresentationDataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupplyEngine")

def initialize_application_state() -> None:
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
        st.session_state.data_service = PresentationDataService(st.session_state.db_manager)
        
        async def _init_db():
            await st.session_state.db_manager.initialize_database()
            await st.session_state.db_manager.seed_mock_data()
            
        asyncio.run(_init_db())

def render_dashboard() -> None:
    st.set_page_config(page_title="Inventory Planning & Reorder Dashboard", layout="wide")

    initialize_application_state()
    
    async def _fetch_reports():
        return await st.session_state.data_service.fetch_inventory_status()
        
    reports = asyncio.run(_fetch_reports())

    with st.sidebar:
        st.title("Inventory System")
        st.caption("System Status")
        st.status("Database Connected", state="complete")
        st.write("**Forecast Engine:** Active")

    st.title("Inventory Planning & Reorder Dashboard")
    st.caption("Monitor stock depletion rates, reorder thresholds, and purchase recommendations.")
    st.divider()

    critical_alerts = [r for r in reports if r["action_required"] == "CRITICAL REORDER"]
    for alert in critical_alerts:
        st.error(
            f"**Critical Action Required:** Reorder **{alert['name']}** ({alert['sku']}). "
            f"Stock will be exhausted in **{alert['days_until_zero']} days**."
        )

   
    cols = st.columns(len(reports))
    for idx, report in enumerate(reports):
        with cols[idx]:
            status_label = report["action_required"].title()
            st.metric(
                label=f"{report['name']} ({report['sku']})",
                value=f"{report['current_stock']} units",
                delta=f"{report['days_until_zero']} Days Left",
                delta_color="inverse" if report["action_required"] == "CRITICAL REORDER" else "normal"
            )

    st.divider()
    st.subheader("Stock Depletion & Forecast")

    product_names = [r["name"] for r in reports]
    selected_product_name = st.selectbox("Select Product for Analysis:", product_names)
    selected_report = next(r for r in reports if r["name"] == selected_product_name)
    
    sales_df = selected_report["sales_data"]
    
    if not sales_df.empty:
        sales_df = sales_df.sort_values("sale_date").reset_index(drop=True)
        
        historical_stock = []
        stock_tracker = selected_report["current_stock"] + sales_df["quantity_sold"].sum()
        
        for qty in sales_df["quantity_sold"]:
            stock_tracker -= qty
            historical_stock.append(stock_tracker)
            
        sales_df["computed_stock"] = historical_stock

        future_days = list(range(1, selected_report["days_until_zero"] + 5))
        future_dates = [date.today() + timedelta(days=d) for d in future_days]
        future_stock = [
            max(selected_report["current_stock"] - int(np.ceil(selected_report["avg_demand"] * d)), 0) 
            for d in future_days
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sales_df["sale_date"], 
            y=sales_df["computed_stock"],
            name="Historical Stock", 
            line=dict(color="#2563eb", width=2)
        ))
        fig.add_trace(go.Scatter(
            x=future_dates, 
            y=future_stock,
            name="Projected Stock", 
            line=dict(color="#dc2626", width=2, dash="dash")
        ))
        fig.add_trace(go.Scatter(
            x=[date.today() + timedelta(days=selected_report["days_until_zero"])], 
            y=[0],
            mode="markers", 
            name="Exhaustion Date", 
            marker=dict(color="#d97706", size=10, symbol="x")
        ))

        fig.update_layout(
            template="plotly_white",
            xaxis=dict(title="Date"),
            yaxis=dict(title="Stock Volume (Units)"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=380
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Purchase Orders & Inventory Recommendations")
    
    table_data = []
    for r in reports:
        table_data.append({
            "SKU": r["sku"],
            "Product Name": r["name"],
            "Current Stock": r["current_stock"],
            "Reorder Point": r["reorder_point"],
            "Days to Zero": f"{r['days_until_zero']} Days",
            "Suggested Order": f"+{r['suggested_purchase']} units",
            "Status": r["action_required"].title()
        })

    display_df = pd.DataFrame(table_data)

    st.dataframe(
        display_df,
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Hold", "Warning", "Critical Reorder"],
                required=True
            )
        },
        use_container_width=True,
        hide_index=True
    )

if __name__ == "__main__":
    render_dashboard()