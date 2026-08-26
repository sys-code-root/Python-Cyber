# Automated Billing and Debt Recovery Engine

This project is an automated system designed to manage overdue invoices, calculate dynamic interest fees, predict payment recovery probabilities, and trigger custom communication actions. It includes an asynchronous backend worker and a web dashboard to monitor the status of delinquent accounts in real-time.

## What it Does

* Scans a SQLite database periodically for overdue invoices.
* Calculates late fees using a base fine plus compound daily interest.
* Scores the recovery probability of each debt using a Machine Learning model.
* Routes notifications automatically: higher probability debts receive soft email reminders, while high-risk debts trigger critical webhooks.
* Displays live operational statistics, debt aging windows, and historical dispatch logs on a central user interface.

## Problem it Resolves

When invoices go unpaid, calculating interest manually over different time windows is error-prone and scales poorly. Deciding how aggressively to pursue a customer or when to escalate an account usually requires manual evaluation. 

This project solves that inefficiency by coupling the data layer directly to an automated scheduling pipeline. It automatically computes precision fees, classifies risk profiles on the fly, and fires off the appropriate notification systems without human intervention.

## Requirements

To run this project, you need Python 3.10 or higher and the following libraries installed:

* apscheduler
* asyncio
* numpy
* pandas
* plotly
* scikit-learn
* sqlalchemy
* streamlit

## Getting Started
# Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install all required dependencies:

pip install streamlit sqlalchemy aiosqlite scikit-learn numpy pandas plotly apscheduler

# Run the application to initialize the database, seed mock data, and launch the interface:

streamlit run ruler.py