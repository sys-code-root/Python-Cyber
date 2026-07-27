# Python Cybersecurity & Defense Toolkit

A modular Python toolkit for defensive security, data privacy, and audit automation.

---

## Overview

This repository brings together a set of Python tools designed to solve practical challenges in defensive security, sensitive data protection, and system log analysis.

The project focuses on providing clean, modular, and straightforward code solutions for essential tasks in privacy, data integrity, and secure credential management.

---

## Key Features

- **Applied Cryptography & Integrity:** Utilities for file encryption/decryption using AES algorithms, alongside cryptographic hash verification.
- **Privacy & Sanitization:** Automated tools for removing file metadata and masking sensitive data fields prior to storage or transmission.
- **Log Forensics & Auditing:** Structured reading and automated analysis of system logs for pattern and failure detection.
- **Network & Application Security:** Scripts for inspecting security headers, checking SSL certificate validity, and basic traffic analysis.
- **Secure Secrets Management:** Implementation of an encrypted local vault for safely storing API keys, passwords, and backups.

---

## Tech Stack

- **Language:** Python 3.10+
- **Cryptography & Security:** `cryptography`, `hashlib`, `secrets`
- **Data & Processing:** `pandas`, `re`
- **Network:** `requests`, `socket`
- **Environment:** Linux / Bash / Git

---

## Quickstart

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sys-code-root/Python-Cyber.git
   cd Python-Cyber

2.  Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

3. Install dependencies:
pip install -r requirements.txt