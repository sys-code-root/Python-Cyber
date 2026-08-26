# Marketing Data ETL Pipeline and Anomaly Detector

This project is an asynchronous ETL pipeline that extracts marketing data from Google Ads, Facebook Ads, and TikTok Ads. It transforms different API response formats into a unified schema, checks metrics for click-fraud or anomalies using simple validation rules, and saves everything into a star-schema data warehouse.

## What It Solves

* **Data Discrepancy:** It handles different date formats and metric names across multiple ad networks and merges them into one place.
* **API Flakiness:** It implements automatic backoff retries when external APIs fail or time out.
* **Fraud Tracking:** It catches unusual metrics like high spending with zero clicks or impossibly high click-through rates.

## Core Technical Choices

* **Asyncio:** Used to fetch data from all ad networks concurrently to save time.
* **SQLAlchemy (Async):** Manages the database schema and writes to the data warehouse asynchronously.
* **Pydantic:** Validates data incoming from APIs before any database ingestion happens.
* **Loguru:** Handles structured terminal logging with built-in formats.

## Database Schema (Star Schema)

* **DimCampaign (Dimension):** Stores campaign names, IDs, and ad networks.
* **DimDate (Dimension):** Keeps dates broken down by day, month, year, and quarter.
* **FactAdPerformance (Fact Table):** Links campaigns and dates with performance numbers like cost, impressions, clicks, CTR, CPC, and anomaly flags.

## Prerequisites

You need Python 3.10+ and the following packages installed:

* SQLAlchemy
* aiosqlite
* pydantic
* loguru

## How to Run

1. Clone this repository or copy the script file.

2. Install the required dependencies:
   ```bash
   pip install sqlalchemy aiosqlite pydantic loguru

python etline.py