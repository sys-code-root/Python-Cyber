# Applied Cryptography Toolkit

## Overview
A high-security CLI tool designed for authenticated file encryption, cryptographic hashing, local key vault management, and automated DevSecOps security auditing. It integrates standard cryptographic algorithms with optional local LLM analysis via Ollama.

## Problem Solved
Managing file encryption, secure key rotation, and file integrity often relies on fragmented scripts or insecure default permissions. This project unifies these tasks into a single tool, using Argon2id key derivation, AES-256-GCM authenticated encryption, and local permission hardening for file vaults without relying on external cloud services.

## Requirements
* Python >= 3.10
* typer[all] >= 0.9.0
* cryptography >= 42.0.0
* argon2-cffi >= 23.1.0
* rich >= 13.0.0
* requests >= 2.31.0
* Optional: Local Ollama instance running for AI audit analysis


## How to Test / Run

1. Clone or extract the repository files locally, then navigate to this tool's directory:
   cd setup_toolkit

2. Install the package in editable mode:
   pip install -e .

3. Run basic file encryption and decryption:
   # Encrypt a file
   crypto-cli encrypt encrypt-file -i secret.txt -o secret.enc -p "YourPassphrase"

   # Decrypt a file
   crypto-cli encrypt decrypt-file -i secret.enc -o secret.txt -p "YourPassphrase"

4. Manage keys in the secure vault:
   # Generate a key entry
   crypto-cli keygen generate --alias db-key --master-pass "MasterPassword"

   # Rotate an existing key
   crypto-cli keygen rotate --alias db-key --master-pass "MasterPassword"

5. Run a local security audit:
   # Static audit
   crypto-cli inspect

   # Static audit with Ollama AI report
   crypto-cli inspect --ai