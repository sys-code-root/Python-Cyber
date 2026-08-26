# Dynamic Pricing and AI Coupon Engine API

This project is a backend API that calculates real-time product prices using an automated pricing service and validates multiple checkout coupons simultaneously. 

## What This Project Solves

* Dynamic Margin Adjustment: The pricing service automatically changes product prices based on stock volume and competitor prices to balance profit margins and inventory turnover.
* Coupon Sequencing: It automatically sorts coupons so that percentage discounts apply before fixed-value discounts, ensuring consistent calculation behavior.
* Loss Prevention: It implements a strict global price floor to stop stacked discounts from dropping the final product price below a safe threshold.
* Lifecycle Tracking: It checks coupon activation status, start dates, and end dates, filtering out expired or incorrect codes while returning them in the API response for debugging.

## Technical Choices and Stack

* Python: Written with typed data models, standard enums, and native decimal math for accurate financial operations.
* FastAPI: Handles the HTTP routing and uses the modern lifespan pattern to set up and tear down database connections.
* Pydantic: Cleans and validates incoming payloads, automatically normalizing region strings and coupon codes to uppercase format.
* SQLAlchemy: Handles asynchronous database interactions using modern mapping types and identity-map lookups.
* SQLite and AioSQLite: Runs an asynchronous relational database completely in memory for fast testing, automatically seeding mock products and coupons on startup.

## Core Code Parameters

* Global Price Floor: Fixed at 0.70. No combination of dynamic adjustments and coupons can lower the final price below 70 percent of the original base price.
* AI Safety Floor: Fixed at 0.85. The automated market pricing method cannot drop the raw adjusted price below 85 percent of the base price.

## How to Install and Run

1. Open your terminal in the project directory with your virtual environment active.

2. Install the required packages:
```bash
pip install fastapi pydantic sqlalchemy aiosqlite uvicorn

## 📊 How to Test the API
## Use 
uvicorn pricing:app --reload

After starting the server, open your preferred browser and access the automated interactive documentation (Swagger UI):

👉 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)