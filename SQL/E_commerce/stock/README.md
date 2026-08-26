# Smart Inventory Management and Prediction System

This web application tracks product stock levels, logs sales data, registers new inventory items, and forecasts stock depletion dates. It solves the need to monitor supply levels in real time and automatically predicts when items will run out using both simple averages and trend-based machine learning lines.

## What It Solves

* Database Tracking: Creates a local SQLite database to store product status information and chronological sales volumes.
* Dual Forecast Calculations: Provides a traditional 3-day average consumption check alongside an AI-driven trend line to catch rapid demand spikes.
* Automatic Alerts: Generates and logs email purchase triggers via an SMTP channel if an item is projected to empty within 5 days or less.
* Interactive Operations: Provides a clean web view divided into tabs to handle general dashboards, item registration, baseline product line adjustments, and live sales simulations.

## Technical Choices

* Written in Python 3 for straight integration with data processing libraries.
* Uses the Streamlit framework to compile an interactive multi-tab layout directly accessible from any browser.
* Uses SQLite3 to handle local relational storage without needing external database server deployments.
* Uses Pandas and NumPy to pull data from SQL tables, organize indices, and pass coordinates into data loops.
* Uses Scikit-Learn to apply a Linear Regression model that tracks shifts in consumer purchase speeds over time.
* Uses built-in email modules (smtplib, email.mime) to establish secure TLS connections to Google SMTP relays on port 587.

## Prerequisites

You need Python 3 installed on your system along with the required web, data, and machine learning packages.

Install all dependencies using pip:

```bash
pip install streamlit pandas scikit-learn numpy

# Smart Inventory Management and Prediction System

## 🔗 Live Demo
Access the live application here: [Aegis Inventory Monitor](https://aegis-quantum-u8goky85x5bkwnxjqudcsb.streamlit.app)