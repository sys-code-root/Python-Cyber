import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import numpy as np
from sklearn.linear_model import LinearRegression

from database import conn, cursor
from alerts import send_email_alert

st.set_page_config(page_title="Smart Inventory Management", layout="wide")
st.title("📦 Inventory Monitoring & Prediction System")

st.sidebar.header("📧 Alert Settings")
SENDER_EMAIL = st.sidebar.text_input("Sender Email", value="your_email@gmail.com")
SENDER_PASSWORD = st.sidebar.text_input("App Password (Google)", type="password", value="your_app_password")
RECEIVER_EMAIL = st.sidebar.text_input("Receiver Email", value="receiver_alert@gmail.com")

dashboard_tab, registration_tab, status_tab, simulator_tab = st.tabs([
    "📊 General Dashboard & Prediction", 
    "🆕 Register Products", 
    "⚙️ Manage Product Line",
    "🛒 Simulate New Sales"
])

with dashboard_tab:
    st.header("Automated Risk and Trend Analysis")
    
    traditional_col, ai_col = st.columns(2)
    
    with traditional_col:
        st.subheader("Traditional Statistical Analysis")
        st.caption("Calculates depletion strictly based on the average sales of the last 3 days.")
        
        if st.button("🔄 Run Simple Average Analysis", type="primary"):
            three_days_ago = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
            
            query = """
                SELECT 
                    p.id, p.name, p.current_stock, 
                    (IFNULL(SUM(s.quantity), 0) / 3.0) AS daily_average
                FROM products p
                LEFT JOIN sales s ON p.id = s.product_id AND s.sale_date >= ?
                WHERE p.status = 'Active'
                GROUP BY p.id
            """
            df = pd.read_sql_query(query, conn, params=(three_days_ago,))

            for index, row in df.iterrows():
                average = row['daily_average']
                stock = row['current_stock']
                name = row['name']
                
                if average > 0:
                    remaining_days = int(stock / average)
                    depletion_date = (datetime.now() + timedelta(days=remaining_days)).strftime('%Y-%m-%d')

                    if remaining_days <= 5:
                        st.error(f"⚠️ **TRADITIONAL:** The product **{name}** (ID: {row['id']}) will run out in **{remaining_days} days** ({depletion_date}).")
                        status_email = send_email_alert(name, remaining_days, depletion_date, stock, SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL)
                        st.info(status_email)
                    else:
                        st.success(f"✅ **{name}**: Safe stock. {remaining_days} more days.")
                else:
                    st.warning(f"ℹ️ **{name}**: No recent sales to calculate average.")

    with ai_col:
        st.subheader("Advanced AI Prediction")
        st.caption("Uses Machine Learning (Linear Regression) to map acceleration or drop in demand over time.")
        
        if st.button("🧠 Run Predictive AI Forecast", type="secondary"):
            sales_query = "SELECT product_id, quantity, sale_date FROM sales"
            df_sales = pd.read_sql_query(sales_query, conn)
            
            products_query = "SELECT id, name, current_stock FROM products WHERE status = 'Active'"
            df_products = pd.read_sql_query(products_query, conn)

            for index, product in df_products.iterrows():
                p_id = product['id']
                name = product['name']
                stock = product['current_stock']
                
                product_sales = df_sales[df_sales['product_id'] == p_id].copy()
                
                if len(product_sales) >= 3:
                    product_sales['day_num'] = range(1, len(product_sales) + 1)
                    X = product_sales[['day_num']].values
                    y = product_sales['quantity'].values
                    
                    ai_model = LinearRegression()
                    ai_model.fit(X, y)
                    
                    next_day = np.array([[len(product_sales) + 1]])
                    tomorrow_sales_forecast = ai_model.predict(next_day)[0]
                    tomorrow_sales_forecast = max(0.1, tomorrow_sales_forecast)
                    
                    remaining_days = int(stock / tomorrow_sales_forecast)
                    depletion_date = (datetime.now() + timedelta(days=remaining_days)).strftime('%Y-%m-%d')
                    
                    if remaining_days <= 5:
                        st.error(f"🚨 **CRITICAL AI ALERT:** **{name}** detected in strong trend! Runs out in **{remaining_days} days** ({depletion_date}).")
                        status_email = send_email_alert(name, remaining_days, depletion_date, stock, SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL)
                        st.info(status_email)
                    else:
                        st.success(f"🧠 **AI ANALYSIS:** **{name}** calculated with commercial stability. {remaining_days} days remaining.")
                else:
                    st.warning(f"ℹ️ **{name}**: Insufficient history for predictive intelligence (Minimum of 3 records).")

with registration_tab:
    st.header("New Item Entry in Database")
    with st.form("form_registration", clear_on_submit=True):
        product_id = st.number_input("Unique ID Code", min_value=1, step=1)
        product_name = st.text_input("Commercial Product Name")
        initial_stock = st.number_input("Initial Stock Quantity", min_value=0, step=1)
        save_button = st.form_submit_button("Save to SQL Database")
        
        if save_button:
            if product_name:
                try:
                    cursor.execute("INSERT INTO products (id, name, current_stock, status) VALUES (?, ?, ?, 'Active')", (product_id, product_name, initial_stock))
                    conn.commit()
                    st.success(f"Product '{product_name}' successfully added to SQL!")
                except sqlite3.IntegrityError:
                    st.error("Error: A product with this ID is already registered.")
            else:
                st.error("Product name cannot be blank.")

with status_tab:
    st.header("Commercialization Status")
    st.caption("Products marked as 'Discontinued' are ignored by the email alert robot.")
    
    products_df = pd.read_sql_query("SELECT id, name, current_stock, status FROM products", conn)
    
    for idx, row in products_df.iterrows():
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.write(f"**{row['name']}** (ID: {row['id']}) - Stock: {row['current_stock']}")
        with col2:
            st.write(f"Status: `{row['status']}`")
        with col3:
            if row['status'] == 'Active':
                if st.button("Change to Discontinued", key=f"del_{row['id']}"):
                    cursor.execute("UPDATE products SET status = 'Discontinued' WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()
            else:
                if st.button("Reactivate Product", key=f"act_{row['id']}"):
                    cursor.execute("UPDATE products SET status = 'Active' WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.rerun()

with simulator_tab:
    st.header("Register Stock Outflow (Sale)")
    active_products_df = pd.read_sql_query("SELECT id, name FROM products WHERE status='Active'", conn)
    product_options = [f"{row['id']} - {row['name']}" for index, row in active_products_df.iterrows()]
    sold_product = st.selectbox("Choose Product", product_options)
    sold_quantity = st.number_input("Quantity Sold", min_value=1, step=1)
    
    if st.button("Confirm Sale"):
        if sold_product:
            p_id = int(sold_product.split(" - ")[0])
            cursor.execute("UPDATE products SET current_stock = current_stock - ? WHERE id = ?", (sold_quantity, p_id))
            cursor.execute("INSERT INTO sales VALUES (?, ?, ?)", (p_id, sold_quantity, datetime.now().strftime('%Y-%m-%d')))
            conn.commit()
            st.success("Sale processed! Stock updated in SQL.")
            st.rerun()
        else:
            st.error("Error: No active products available. Please register a product first.")