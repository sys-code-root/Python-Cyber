# Automated Bank Reconciliation System

This project is an asynchronous API built with FastAPI that automates the process of matching internal payment gateway records against bank statements. It processes uploaded bank statement files and gateway spreadsheets, runs matching logic, logs the results, and flags anomalies using machine learning.

---

## What This Project Solves

When running a business, financial transactions are recorded in two places: your payment gateway (like Stripe or Pagar.me) and your bank account. Manually checking if these two data sources match is slow and prone to errors. 

This system automates that work by:
* Parsing official bank statement files and gateway data exports.
* Running an exact match check based on transaction IDs and monetary amounts.
* Running a fuzzy text match check to pair transactions where the descriptions do not exactly line up.
* Analyzing transaction fees automatically to spot cases where the gateway charged an incorrect fee amount.

---

## Technical Choices and Libraries Used

* FastAPI: Used to handle file uploads and expose the async reconciliation endpoint.
* SQLAlchemy 2.0 and aiosqlite: Handles asynchronous database operations with an in-memory SQLite database.
* Pydantic v2: Validates data structures and enforces typing for requests and responses.
* OfxParser: Extracts raw transaction data from standard bank OFX files.
* Pandas: Parses and cleans data from gateway CSV reports.
* RapidFuzz: Measures string similarity between different transaction descriptions to catch partial text matches.
* Scikit-Learn: Uses the Isolation Forest model to detect outliers and potential fee overcharges.
* Decimal Type: All monetary fields use Python's Decimal type and SQL Numeric types. Floating-point numbers are completely avoided to ensure no binary rounding bugs occur.

---

## How the Matching Engine Works

### Ingestion
The system takes two raw binary streams via a POST request: an OFX file from the bank and a CSV file from the payment gateway. The service parses these files, maps them into Python dictionaries with strict Decimal casting, and inserts them into the database with a PENDING status.

### Exact Match
The system queries all pending bank transactions and finds their counterparts in the gateway table. It uses an optimized SQL statement with the `.in_()` operator to match records in batches by ID and transaction value. This design avoids executing individual queries for every single row, preventing N+1 database performance problems.

### Fuzzy Match
For transactions that remain unmatched, the engine pulls the remaining pending records into memory. It uses token-set ratio calculations to compare the text descriptions. If the text similarity score passes a given threshold (defaulting to 75%) and the financial amounts match exactly, the pair is marked as reconciled.

### Anomaly Detection
The gateway CSV includes both the transaction amount and the processed fee amount. The system feeds these two features into an Isolation Forest model. The algorithm learns the normal distribution of your processing fees relative to the transaction size and automatically flags statistical outliers as anomalies.

---

## Database Schema Summary

The application builds three main tables inside the database:

### Gateway Transactions Table
* id: String (Primary Key)
* date: Date
* amount: Numeric (18, 4)
* fee: Numeric (18, 4)
* description: String
* status: String (Defaults to PENDING)

### Bank Transactions Table
* id: String (Primary Key)
* date: Date
* amount: Numeric (18, 4)
* description: String
* status: String (Defaults to PENDING)

### Reconciliation Logs Table
* id: Integer (Primary Key, Autoincrement)
* gateway_transaction_id: String (Nullable)
* bank_transaction_id: String (Nullable)
* match_type: String (EXACT, FUZZY, or UNMATCHED)
* confidence_score: Numeric (5, 2)
* anomaly_flag: Boolean

---

## Installation and Setup

### Prerequisites
Make sure you have Python 3.11 or higher installed on your local machine.

### 1. Install Dependencies
Save the main application code as `bank.py`. Run the following command in your terminal to install all required packages:

```bash
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic pandas ofxparse rapidfuzz scikit-learn numpy python-multipart

## Use Test

[http://127.0.0.1:8000/docs]