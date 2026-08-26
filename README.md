# Python Tools for Data Engineering & Security

A collection of practical Python and SQL scripts for data analysis, system defense, and privacy.

---

## Overview

This repository contains ready-to-use tools for handling data pipelines, database structures, security audits, and privacy compliance (LGPD/GDPR).

It is designed to keep code simple, organized, and effective for everyday tasks like file encryption, log analysis, and data masking.

---

## Features

- **Database Engineering & SQL:** Table structures and queries for Analytics, Sales, Finance, and Logistics.
- **Data Anonymization:** Scripts to mask sensitive fields before processing or storing data.
- **Encryption & Integrity:** AES encryption tools and hash verification for file safety.
- **Log Analysis:** Automated scripts to read system logs and flag potential issues.
- **Key & Password Storage:** A local encrypted vault for API keys, passwords, and backups.

---

## Repository Structure

```text
├── SQL/           # Database schemas and queries
├── sanitizer/     # Data masking and compliance scripts (LGPD/GDPR)
├── sec/           # Audit logs, security checks, and password vault
└── setup_toolkit/ # Environment configuration and CLI utilities
```

How to Install and Run
Clone the repository:
```bash
git clone https://github.com/sys-code-root/Python-Cyber.git
cd Python-Cyber
```

Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS

venv\Scripts\activate   # Windows
```

Install dependencies:
```bash
pip install -r requirements.txt