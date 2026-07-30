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
## Installation Commands
# Basic cryptography dependencies
pip install cryptography

# Dependencies to enable targeted AI (spaCy)
pip install spacy

# Download the Portuguese spaCy model (automatically downloaded at runtime if omitted)
python -m spacy download pt_core_news_sm

## Usage Examples
⚡ Fast & Traditional Mode (Without AI)
# Generate test dataset
python script.py --generate-bench 50 -o dataset.log

# Mask deterministic PII (CPF, Credit Cards, Keys)
python script.py -i dataset.log -o output_masked.log -m mask

# Encrypt sensitive records
python script.py -i dataset.log -o output_encrypted.log -m encrypt -k "Your32ByteFernetKeyHere="

🧠 Advanced Hybrid AI Mode (--use-ai)
# Deep analysis using the AI flag and spaCy model
python script.py -i dataset.log -o output_ai_masked.log -m mask --use-ai

# Specifying an alternative spaCy model (e.g., English)
python script.py -i dataset.log -o output_ai_en.log -m mask --use-ai --ai-model en_core_web_sm


