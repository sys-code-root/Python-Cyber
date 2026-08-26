# Reorder Matrix

An asynchronous inventory dashboard that tracking product stock levels and uses linear regression to predict when stock will run out. The application highlights items that need an immediate resupply based on daily sales trends and lead times.

## Problem it Resolves

Managing stock manually makes it easy to miss when an item is running low, especially when considering supplier lead times. This project solves that by automatically calculating daily consumption speed. It tells you exactly how many days of stock you have left, flags critical items, and calculates how many units you need to buy to cover the next 30 days.

## Technical Choices and Frameworks

* **Streamlit**: Used to build the web user interface and render real-time charts.
* **SQLAlchemy (Async)**: Handles database persistence using asynchronous sessions to avoid blocking the main thread during data loading.
* **SQLite (aiosqlite)**: An in-memory relational database configuration used to store and query products and sales histories.
* **scikit-learn (Linear Regression)**: Fits historical sales timelines to forecast the average daily demand and detect depletion velocity.
* **Plotly**: Renders interactive trend lines comparing historical ledger volume with predicted future decay.
* **Pandas & NumPy**: Structures the sales data arrays and handles grouping and indexing calculations.

## Core Features and Calculations

* **Linear Regression Forecast**: Groups past sales by date and uses a linear model to project the future zero-stock date.
* **Reorder Point Trigger**: Checks if current stock volume is less than or equal to average daily demand multiplied by supplier lead time days.
* **Status Badges**: Categorizes products into HOLD, WARNING, or CRITICAL REORDER states based on remaining days.
* **Purchase Suggestion**: Generates an exact ordering metric aiming to restore a 30-day stock buffer.

## Project Structure

* **Product & SalesHistory**: Database tables linked via foreign keys.
* **DatabaseManager**: Initializes tables and inserts initial mock data into the database instance.
* **DemandPredictor**: Contains the scikit-learn logic to calculate stock lifetime.
* **PresentationDataService**: Formats database results into clean dictionaries for UI consumption.

## Setup and Execution

1. Install the required dependencies:
   ```bash
   pip install streamlit sqlalchemy aiosqlite numpy pandas plotly scikit-learn

## Save the code into a python file named:
supply.py

Start the dashboard from your terminal:

## Bash
streamlit run supply.py