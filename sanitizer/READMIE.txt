# Stream Sanitizer & Data Masker

A high-performance CLI tool that streams and sanitizes sensitive data (PII, credentials, tokens) across various file formats using regex matching and structured parsing. It supports masking, hashing, Fernet symmetric encryption/decryption, and includes a built-in benchmark dataset generator.

---

## What it is

This Python script is a memory-efficient stream processor that strips or obfuscates sensitive information from structured and unstructured files. It handles CSV, JSON/NDJSON, SQL dumps, and plain text logs line-by-line without loading entire datasets into RAM. You can mask, hash, or encrypt values using simple command-line flags.

---

## Problem it solves

Sharing database dumps, production logs, or API payloads with local environments, third-party developers, or testing pipelines often exposes real user PII (CPFs, credit cards, emails) and secrets (JWTs, API keys). Manually scrubbing these files is slow and prone to human error, while standard search-and-replace scripts often break valid CSV or JSON syntaxes. This tool safely sanitizes data while maintaining structural file integrity and low memory consumption.

---

## Requirements

*   **Python 3.8+** (uses standard library modules like `argparse`, `csv`, `json`, `re`, `hashlib`).
*   **`cryptography` library** (optional — only required if you use `--mode encrypt` or `--mode decrypt`).

Install the optional dependency:

```bash
pip install cryptography

. Basic Masking (Default Mode)
Mask sensitive data (CPFs, emails, credit cards, JWTs) in a file:

python sanitizer.py -i raw_logs.txt -o sanitized_logs.txt

2. Hash Sensitive Fields
Replace matched sensitive strings with deterministic SHA-256 hashes (truncated to 16 chars):

python sanitizer.py -i dump.sql -o anonymized_dump.sql -m hash

3. Symmetric Encryption & Decryption
Encrypt sensitive fields in-place using a generated or custom Fernet key:

# Encrypt (Auto-generates a key if -k is omitted)
python sanitizer.py -i database.csv -o encrypted_data.csv -m encrypt

# Decrypt using a specific key
python sanitizer.py -i encrypted_data.csv -o decrypted_data.csv -m decrypt -k "YOUR_FERNET_KEY_HERE"

4. Generate Benchmark Files
Create synthetic dummy datasets (logs, SQL inserts, tokens) to test processing speed and memory handling:

python sanitizer.py --generate-bench 100 -o benchmark_100mb.log
