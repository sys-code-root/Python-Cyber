import asyncio
import pandas as pd
import plotly.express as px
import streamlit as st

from config import logger
from database import db_manager
from schemas import validate_and_transform_data
from engine import AttributionEngine

st.set_page_config(
    page_title="Attribution Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def startup_pipeline_executor():
    async def _init_db():
        await db_manager.initialize_schemas()
        await db_manager.seed_data_if_empty()

    asyncio.run(_init_db())
    logger.info("Database initialization completed.")
    return True

startup_pipeline_executor()

@st.cache_data(ttl=600)
def load_and_cache_dataset():
    async def _fetch():
        return await db_manager.fetch_analytics_dataset()

    raw_j, raw_c = asyncio.run(_fetch())
    return validate_and_transform_data(raw_j, raw_c)

validated_journeys, validated_costs = load_and_cache_dataset()
engine = AttributionEngine(validated_journeys, validated_costs)

st.title("Multi-Touch Marketing Attribution")
st.caption("Tracking revenue, spend, and ROI by acquisition channel.")
st.divider()

with st.sidebar:
    st.header("Settings")
    
    models_map = {
        "First Click": engine.compute_first_click,
        "Last Click": engine.compute_last_click,
        "Linear": engine.compute_linear,
        "Time Decay (7d Half-Life)": engine.compute_time_decay,
        "Data-Driven (Markov Chain)": engine.compute_data_driven_markov
    }
    
    selected_model_name = st.selectbox(
        "Attribution Model:",
        options=list(models_map.keys())
    )
    
    st.divider()
    st.caption("System Status")
    st.status("Database Connected", state="complete")

channel_revenues = models_map[selected_model_name]()

total_revenue = sum(channel_revenues.values())
total_spend = sum(validated_costs.values())
overall_roi = ((total_revenue - total_spend) / total_spend) * 100 if total_spend > 0 else 0.0

top_channel = max(channel_revenues, key=channel_revenues.get, default="N/A")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Attributed Revenue", f"${total_revenue:,.2f}")
col2.metric("Total Spend", f"${total_spend:,.2f}")
col3.metric("Overall ROI", f"{overall_roi:.1f}%")
col4.metric("Top Channel", top_channel)

st.divider()

data = [
    {
        "Channel": ch,
        "Revenue": rev := channel_revenues.get(ch, 0.0),
        "Spend": cost,
        "ROI (%)": ((rev - cost) / cost) * 100 if cost > 0 else 0.0
    }
    for ch, cost in validated_costs.items()
]

df_metrics = pd.DataFrame(data)

st.subheader("Channel Performance Analysis")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_bar = px.bar(
        df_metrics, 
        x="Channel", 
        y=["Revenue", "Spend"],
        barmode="group",
        title=f"Revenue vs. Spend ({selected_model_name})",
        color_discrete_sequence=["#2563eb", "#94a3b8"],
        template="plotly_white"
    )
    fig_bar.update_layout(
        xaxis_title="Channel",
        yaxis_title="Amount ($)",
        legend_title_text="Metric",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="bar_chart")

with chart_col2:
    fig_pie = px.pie(
        df_metrics, 
        names="Channel", 
        values="Revenue",
        hole=0.4,
        title="Revenue Share",
        color_discrete_sequence=px.colors.qualitative.Set2,
        template="plotly_white"
    )
    fig_pie.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_pie, use_container_width=True, key="pie_chart")

st.divider()

st.subheader("Channel Breakdown")
st.dataframe(
    df_metrics,
    column_config={
        "Revenue": st.column_config.NumberColumn("Revenue", format="$ %.2f"),
        "Spend": st.column_config.NumberColumn("Spend", format="$ %.2f"),
        "ROI (%)": st.column_config.NumberColumn("ROI", format="%.2f %%"),
    },
    use_container_width=True,
    hide_index=True
)