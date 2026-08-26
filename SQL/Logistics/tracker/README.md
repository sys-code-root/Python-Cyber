# Logistics Tracker and Delay Alert System

This is an asynchronous service that processes carrier tracking events, stores checkpoint history in a database, calculates delivery delay risks, and publishes alerts if a package is going to miss its deadline.

## What It Does

* Receives and validates incoming package location updates from carriers.
* Links checkpoints to existing shipments in the database.
* Stores a full history of checkpoints along with the raw payload for tracking.
* Evaluates the package data to estimate if a delay is likely.
* Sends a notification to an alert queue if the calculation flags the shipment as high-risk.

## Technical Stack

* FastStream: Handles message routing and asynchronous event processing.
* TestRabbitBroker: Runs a full RabbitMQ broker simulation in memory for testing without external dependencies.
* SQLAlchemy and aiosqlite: Manages async database storage using an in-memory SQLite database.
* Pydantic: Enforces data validation schemas for both incoming events and outgoing alerts.
* Loguru: Provides formatted logs to track exactly how events flow through the system.

## Data Structures

### Database Models

* Shipment: Contains tracking codes, carrier names, original delivery deadlines, and overall statuses.
* CheckpointLedger: Stores each specific hub arrival timestamp, location details, and raw message logs linked back to a shipment.

### Message Payloads

* Carrier Checkpoint: Expects a tracking code, location hub, timestamp, and status description.
* Delay Alert: Outputs the shipment ID, tracking code, carrier name, calculated risk score, and current status description.

## Installation

Install the required packages directly using pip:

pip install faststream sqlalchemy aiosqlite pydantic loguru

## How to Run

Run the script directly from your terminal:

python tracker.py

The script includes a built-in simulation context. When you run it, the code automatically:

* Creates the database tables in memory.
* Seeds a sample shipment (AEGIS-QUANTUM-99).
* Publishes a mock carrier event to trigger the validation, database logging, risk evaluation, and alert dispatch processes.