import asyncio
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import plotly.graph_objects as go
import streamlit as st

from database import DatabaseManager
from risk_engine import RiskEngine
from automation import BillingAutomationEngine
from services import PresentationDataService
from utils import construct_aging_buckets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BillingEngine")

def initialize_application_state() -> None:
    if "db_manager" not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
            st.session_state.risk_engine = RiskEngine()
            st.session_state.automation = BillingAutomationEngine(st.session_state.db_manager, st.session_state.risk_engine)
            st.session_state.data_service = PresentationDataService(st.session_state.db_manager)
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            loop.run_until_complete(st.session_state.db_manager.initialize_database())
            loop.run_until_complete(st.session_state.db_manager.seed_mock_data())
            loop.run_until_complete(st.session_state.automation.execute_daily_billing_sweep())
            
            def run_billing_sweep_sync():
                new_loop = asyncio.new_event_loop()
                try:
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(st.session_state.automation.execute_daily_billing_sweep())
                finally:
                    new_loop.close()

            scheduler = BackgroundScheduler()
            scheduler.add_job(run_billing_sweep_sync, "interval", minutes=5)
            scheduler.start()
            st.session_state.scheduler = scheduler

def render_dashboard() -> None:
    st.set_page_config(page_title="Accounts Receivable Management", layout="wide")

    initialize_application_state()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    invoice_df = loop.run_until_complete(st.session_state.data_service.fetch_invoice_metrics())
    logs_df = loop.run_until_complete(st.session_state.data_service.fetch_communication_logs())

    with st.sidebar:
        st.title("Billing System")
        st.caption("System Status")
        st.status("Service Active", state="complete")
        st.write("**Database:** Connected")
        st.write("**Sweep Frequency:** 5 min")

    st.title("Accounts Receivable & Debt Collection Management")
    st.divider()

    overdue_mask = invoice_df["status"] == "OVERDUE"
    total_outstanding = invoice_df[overdue_mask]["amount"].sum() + invoice_df[overdue_mask]["accumulated_fees"].sum()
    active_delinquent_counts = invoice_df[overdue_mask]["customer_id"].nunique()
    mock_accuracy = 94.2

    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    with kpi_col1:
        st.metric(label="Total Overdue Amount", value=f"${total_outstanding:,.2f}")
    with kpi_col2:
        st.metric(label="Delinquent Customers", value=active_delinquent_counts)
    with kpi_col3:
        st.metric(label="Model Accuracy", value=f"{mock_accuracy}%")

    st.divider()
    
    st.subheader("Aging Analysis")
    aging_data = construct_aging_buckets(invoice_df)
    
    if not aging_data.empty:
        fig = go.Figure(data=[go.Bar(
            x=aging_data["Aging Bucket"],
            y=aging_data["Outstanding Balance"],
            marker_color="#2563eb",
            text=[f"${val:,.2f}" for val in aging_data["Outstanding Balance"]],
            textposition="auto"
        )])
        fig.update_layout(
            template="plotly_white",
            xaxis=dict(title="Aging Bracket"),
            yaxis=dict(title="Total Amount ($)"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No records found for the period.")

    st.divider()
    st.subheader("Notification History")
    
    if not logs_df.empty:
        logs_df["Risk Level"] = logs_df["action_taken"].apply(
            lambda x: "High" if "Critical" in x else "Low"
        )
        logs_df["Timestamp"] = logs_df["dispatched_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
        
        display_df = logs_df[["Timestamp", "Risk Level", "action_taken"]].rename(
            columns={"action_taken": "Action Executed"}
        )
        
        st.dataframe(
            display_df,
            column_config={
                "Risk Level": st.column_config.SelectboxColumn(
                    "Risk Level",
                    options=["Low", "High"],
                    required=True,
                )
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No notifications logged so far.")

if __name__ == "__main__":
    render_dashboard()