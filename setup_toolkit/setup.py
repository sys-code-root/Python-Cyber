import os
import sys
import subprocess
from pathlib import Path

FILES = {
    "pyproject.toml": """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "applied-cryptography-toolkit"
version = "0.2.0"
description = "High-security CLI toolkit for file encryption, hashing, key vault management, and local AI security auditing."
authors = [{ name = "Principal DevSecOps Engineer", email = "sec@dev.local" }]
dependencies = [
    "typer[all]>=0.9.0",
    "cryptography>=42.0.0",
    "argon2-cffi>=23.1.0",
    "rich>=13.0.0",
    "requests>=2.31.0"
]
requires-python = ">=3.10"

[project.scripts]
crypto-cli = "crypto_cli.main:app"

[tool.setuptools.packages.find]
where = ["."]
include = ["crypto_cli*"]
""",

    "crypto_cli/__init__.py": '__version__ = "0.2.0"\n',

    "crypto_cli/crypto/__init__.py": '\n',

    "crypto_cli/crypto/aes_gcm.py": """import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32

def derive_key_argon2(passphrase: str, salt: bytes) -> bytes:
    kdf = Argon2id(
        salt=salt,
        length=KEY_SIZE,
        iterations=3,
        lanes=4,
        memory_cost=64 * 1024,
    )
    return kdf.derive(passphrase.encode("utf-8"))

def encrypt_file(file_path: Path, output_path: Path, passphrase: str) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key_argon2(passphrase, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = file_path.read_bytes()
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data=None)
        output_path.write_bytes(salt + nonce + ciphertext)
    finally:
        del key

def decrypt_file(file_path: Path, output_path: Path, passphrase: str) -> None:
    if not file_path.exists():
        raise FileNotFoundError(f"Encrypted file not found: {file_path}")

    file_data = file_path.read_bytes()
    min_length = SALT_SIZE + NONCE_SIZE + 16
    if len(file_data) < min_length:
        raise ValueError("Invalid encrypted file structure or corrupted header.")

    salt = file_data[:SALT_SIZE]
    nonce = file_data[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = file_data[SALT_SIZE + NONCE_SIZE:]

    key = derive_key_argon2(passphrase, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
        output_path.write_bytes(plaintext)
    except Exception as err:
        raise ValueError("Decryption failed. Invalid passphrase or corrupted data.") from err
    finally:
        del key
""",

    "crypto_cli/crypto/hashing.py": """import hashlib
from pathlib import Path
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16
)

def hash_file_sha3(file_path: Path, algorithm: str = "sha3-256") -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm == "sha3-256":
        hasher = hashlib.sha3_256()
    elif algorithm == "sha3-512":
        hasher = hashlib.sha3_512()
    else:
        raise ValueError(f"Unsupported hashing algorithm: {algorithm}")

    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)

    return hasher.hexdigest()

def hash_password_argon2(password: str) -> str:
    return _ph.hash(password)

def verify_password_argon2(hash_str: str, password: str) -> bool:
    try:
        return _ph.verify(hash_str, password)
    except VerifyMismatchError:
        return False
""",

    "crypto_cli/crypto/key_manager.py": """import os
import json
import secrets
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from crypto_cli.crypto.aes_gcm import derive_key_argon2, SALT_SIZE, NONCE_SIZE

VAULT_DIR = Path.home() / ".crypto_cli_vault"
VAULT_FILE = VAULT_DIR / "keys.json"

def ensure_vault_permissions() -> bool:
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    if os.name == "posix":
        os.chmod(VAULT_DIR, 0o700)
        if VAULT_FILE.exists():
            os.chmod(VAULT_FILE, 0o600)
        return True
    elif os.name == "nt":
        try:
            username = os.getlogin()
            cmd_dir = f'icacls "{VAULT_DIR}" /inheritance:r /grant:r "{username}":(OI)(CI)F'
            subprocess.run(cmd_dir, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if VAULT_FILE.exists():
                cmd_file = f'icacls "{VAULT_FILE}" /inheritance:r /grant:r "{username}":F'
                subprocess.run(cmd_file, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False
    return False

def generate_key_bytes(length: int = 32) -> bytes:
    return secrets.token_bytes(length)

def _load_vault_container() -> dict:
    if not VAULT_FILE.exists():
        return {"metadata": {}, "payload": None}
    with open(VAULT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_vault_container(container: dict) -> None:
    ensure_vault_permissions()
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(container, f, indent=2)
    ensure_vault_permissions()

def decrypt_vault_payload(master_passphrase: str) -> dict[str, list[dict]]:
    container = _load_vault_container()
    payload = container.get("payload")
    if not payload:
        return {}

    salt = bytes.fromhex(payload["salt_hex"])
    nonce = bytes.fromhex(payload["nonce_hex"])
    ciphertext = bytes.fromhex(payload["ciphertext_hex"])

    key = derive_key_argon2(master_passphrase, salt)
    aesgcm = AESGCM(key)
    try:
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
        return json.loads(decrypted_bytes.decode("utf-8"))
    except Exception as err:
        raise ValueError("Master Passphrase verification failed or corrupted vault.") from err
    finally:
        del key

def store_key(key_alias: str, key_bytes: bytes, master_passphrase: str) -> int:
    ensure_vault_permissions()
    
    try:
        vault_data = decrypt_vault_payload(master_passphrase)
    except ValueError:
        container = _load_vault_container()
        if container.get("payload") is not None:
            raise
        vault_data = {}

    history = vault_data.get(key_alias, [])
    new_version = len(history) + 1

    history.append({
        "version": new_version,
        "key_hex": key_bytes.hex(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    vault_data[key_alias] = history

    metadata: dict[str, list[dict]] = {}
    for alias, versions in vault_data.items():
        metadata[alias] = [
            {
                "version": v["version"],
                "created_at": v["created_at"],
                "length_bits": len(bytes.fromhex(v["key_hex"])) * 8
            }
            for v in versions
        ]

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key_argon2(master_passphrase, salt)
    aesgcm = AESGCM(key)

    plaintext_bytes = json.dumps(vault_data).encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, associated_data=None)
    del key

    container = {
        "metadata": metadata,
        "payload": {
            "salt_hex": salt.hex(),
            "nonce_hex": nonce.hex(),
            "ciphertext_hex": ciphertext.hex()
        }
    }
    _save_vault_container(container)
    return new_version

def get_key_metadata() -> dict[str, list[dict]]:
    container = _load_vault_container()
    return container.get("metadata", {})
""",

    "crypto_cli/ai/__init__.py": '\n',

    "crypto_cli/ai/advisor.py": r"""import os
import json
import requests
from crypto_cli.crypto.key_manager import VAULT_DIR, get_key_metadata, ensure_vault_permissions

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def audit_security_hygiene() -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if not ensure_vault_permissions():
        findings.append({
            "severity": "HIGH",
            "issue": "Insecure vault permissions detected.",
            "recommendation": "Restrict directory permissions to current user SID/UID."
        })

    if VAULT_DIR.exists() and os.name == "posix":
        permissions = oct(VAULT_DIR.stat().st_mode)[-3:]
        if permissions != "700":
            findings.append({
                "severity": "HIGH",
                "issue": f"Insecure POSIX vault directory permissions: {permissions}",
                "recommendation": "Execute: `chmod 700 ~/.crypto_cli_vault`"
            })

    metadata = get_key_metadata()
    if not metadata:
        findings.append({
            "severity": "INFO",
            "issue": "No cryptographic keys registered in the vault.",
            "recommendation": "Generate new keys using `crypto-cli keygen generate`."
        })
    else:
        for alias, versions in metadata.items():
            if len(versions) == 1:
                findings.append({
                    "severity": "MEDIUM",
                    "issue": f"Key '{alias}' has never been rotated.",
                    "recommendation": f"Execute: `crypto-cli keygen rotate --alias {alias}`"
                })

    return findings

def generate_ai_audit_report(model: str = DEFAULT_MODEL) -> str:
    findings = audit_security_hygiene()
    metadata = get_key_metadata()

    sanitized_context = {
        "vault_permission_status": "SECURE" if ensure_vault_permissions() else "INSECURE",
        "findings": findings,
        "key_metadata_summary": metadata
    }

    system_prompt = (
        "You are an expert DevSecOps and Cryptography Auditor. "
        "Analyze the static system findings and non-sensitive key vault metadata provided. "
        "Generate a concise, professional Security Audit Report in markdown format summarizing overall risk, "
        "identifying critical key rotation or configuration issues, and providing remediation advice."
    )

    prompt = f"SANITIZED CONTEXT:\n{json.dumps(sanitized_context, indent=2)}"

    try:
        response = requests.post(
            OLLAMA_ENDPOINT,
            json={
                "model": model,
                "system": system_prompt,
                "prompt": prompt,
                "stream": False
            },
            timeout=30.0
        )
        if response.status_code == 200:
            return response.json().get("response", "AI response empty.")
        return f"[Fallback Local Report] Ollama returned status code {response.status_code}. Static Findings: {len(findings)} issue(s) detected."
    except Exception:
        fallback = "### Static DevSecOps Security Audit Report (Local Fallback)\n\n"
        fallback += "*Note: Local Ollama LLM endpoint unreachable. Generated static findings report.*\n\n"
        for idx, f in enumerate(findings, 1):
            fallback += f"**{idx}. [{f['severity']}] {f['issue']}**\n"
            fallback += f"   - *Recommendation:* {f['recommendation']}\n\n"
        return fallback
""",

    "crypto_cli/main.py": r"""import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from pathlib import Path

from crypto_cli.crypto import aes_gcm, hashing, key_manager
from crypto_cli.ai import advisor

app = typer.Typer(
    name="crypto-cli",
    help="Applied Cryptography Toolkit: High-security CLI for file encryption, hashing, and auditing.",
    add_completion=False
)
console = Console()

encrypt_app = typer.Typer(help="File encryption and decryption using AES-256-GCM.")
app.add_typer(encrypt_app, name="encrypt")

@encrypt_app.command("encrypt-file")
def encrypt_file_cmd(
    input_file: Path = typer.Option(..., "--in", "-i", help="Path to input plaintext file."),
    output_file: Path = typer.Option(..., "--out", "-o", help="Path to save encrypted output."),
    passphrase: str = typer.Option(..., "--passphrase", "-p", prompt=True, hide_input=True, help="Key derivation passphrase.")
) -> None:
    try:
        aes_gcm.encrypt_file(input_file, output_file, passphrase)
        console.print(f"[bold green]✓[/bold green] File successfully encrypted: [cyan]{output_file}[/cyan]")
    except Exception as err:
        console.print(f"[bold red]Encryption error:[/bold red] {err}")
        raise typer.Exit(code=1)

@encrypt_app.command("decrypt-file")
def decrypt_file_cmd(
    input_file: Path = typer.Option(..., "--in", "-i", help="Path to input encrypted file."),
    output_file: Path = typer.Option(..., "--out", "-o", help="Path to save decrypted output."),
    passphrase: str = typer.Option(..., "--passphrase", "-p", prompt=True, hide_input=True, help="Decryption passphrase.")
) -> None:
    try:
        aes_gcm.decrypt_file(input_file, output_file, passphrase)
        console.print(f"[bold green]✓[/bold green] File successfully decrypted: [cyan]{output_file}[/cyan]")
    except Exception as err:
        console.print(f"[bold red]Decryption error:[/bold red] {err}")
        raise typer.Exit(code=1)

hash_app = typer.Typer(help="Cryptographic hashing and password verification.")
app.add_typer(hash_app, name="hash")

@hash_app.command("file")
def hash_file_cmd(
    file_path: Path = typer.Argument(..., help="Path to the target file."),
    algo: str = typer.Option("sha3-256", "--algo", "-a", help="Hashing algorithm: sha3-256 or sha3-512."),
    verify: str | None = typer.Option(None, "--check", "-c", help="Expected hash digest for integrity check.")
) -> None:
    try:
        calculated = hashing.hash_file_sha3(file_path, algorithm=algo)
        if verify:
            if calculated.lower() == verify.lower():
                console.print("[bold green]✓ MATCH![/bold green] File integrity verified successfully.")
            else:
                console.print("[bold red]✗ INTEGRITY ERROR![/bold red] Computed hash does not match expected digest.")
                console.print(f"Calculated Digest: [cyan]{calculated}[/cyan]")
                raise typer.Exit(code=1)
        else:
            console.print(f"File Hash ([bold cyan]{algo}[/bold cyan]): [cyan]{calculated}[/cyan]")
    except Exception as err:
        console.print(f"[bold red]Hashing error:[/bold red] {err}")
        raise typer.Exit(code=1)

@hash_app.command("password")
def hash_password_cmd(
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Password string to hash.")
) -> None:
    res = hashing.hash_password_argon2(password)
    console.print(f"Argon2id Hash: [cyan]{res}[/cyan]")

key_app = typer.Typer(help="Encrypted key vault management and key rotation operations.")
app.add_typer(key_app, name="keygen")

@key_app.command("generate")
def keygen_generate_cmd(
    alias: str = typer.Option(..., "--alias", "-a", help="Unique key identifier alias."),
    master_passphrase: str = typer.Option(..., "--master-pass", prompt="Master Vault Passphrase", hide_input=True, help="Master passphrase to encrypt vault.")
) -> None:
    try:
        raw_key = key_manager.generate_key_bytes(32)
        version = key_manager.store_key(alias, raw_key, master_passphrase)
        console.print(f"[bold green]✓[/bold green] Key '[cyan]{alias}[/cyan]' (v{version}) encrypted and stored in vault.")
    except Exception as err:
        console.print(f"[bold red]Vault error:[/bold red] {err}")
        raise typer.Exit(code=1)

@key_app.command("rotate")
def keygen_rotate_cmd(
    alias: str = typer.Option(..., "--alias", "-a", help="Key identifier alias to rotate."),
    master_passphrase: str = typer.Option(..., "--master-pass", prompt="Master Vault Passphrase", hide_input=True, help="Master passphrase to encrypt vault.")
) -> None:
    try:
        raw_key = key_manager.generate_key_bytes(32)
        version = key_manager.store_key(alias, raw_key, master_passphrase)
        console.print(f"[bold green]✓[/bold green] Key '[cyan]{alias}[/cyan]' rotated to version [cyan]v{version}[/cyan].")
    except Exception as err:
        console.print(f"[bold red]Vault error:[/bold red] {err}")
        raise typer.Exit(code=1)

@app.command("inspect")
def inspect_cmd(
    ai: bool = typer.Option(False, "--ai", help="Query local Ollama instance for AI-generated audit findings analysis.")
) -> None:
    console.print("[bold blue]🔎 Running Security Hygiene Auditor...[/bold blue]\n")
    findings = advisor.audit_security_hygiene()

    table = Table("Severity", "Detected Issue", "Remediation Recommendation")
    for f in findings:
        color = "red" if f["severity"] == "HIGH" else "yellow" if f["severity"] == "MEDIUM" else "blue"
        table.add_row(f"[{color}]{f['severity']}[/{color}]", f["issue"], f["recommendation"])

    console.print(table)

    if ai:
        console.print("\n[bold magenta]🤖 Generating AI Security Advisor Report (Ollama)...[/bold magenta]\n")
        report_md = advisor.generate_ai_audit_report()
        console.print(Panel(Markdown(report_md), title="AI Security Advisory", border_style="magenta"))

if __name__ == "__main__":
    app()
"""
}

def build_project() -> None:
    print("🚀 [1/3] Assembling modern project file structure...")
    for rel_path, content in FILES.items():
        file_path = Path(rel_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        print(f"   └─ Created: {rel_path}")

def install_package() -> None:
    print("\n📦 [2/3] Installing dependencies and 'crypto-cli' package...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])

def run_tests() -> None:
    print("\n🧪 [3/3] Running end-to-end integration test suite...\n")

    master_pass = "MasterVaultSecretPassphrase2026!"

    print("🔐 Testing encrypted key vault storage...")
    subprocess.run(["crypto-cli", "keygen", "generate", "--alias", "db-secret", "--master-pass", master_pass], check=True)
    subprocess.run(["crypto-cli", "keygen", "rotate", "--alias", "db-secret", "--master-pass", master_pass], check=True)

    print("\n🔎 Testing security inspection & AI advisor...")
    subprocess.run(["crypto-cli", "inspect", "--ai"], check=True)

    test_file = Path("payload.txt")
    enc_file = Path("payload.enc")
    dec_file = Path("payload_dec.txt")

    test_file.write_text("Top secret message encrypted successfully!", encoding="utf-8")

    print("\n🔒 Encrypting file with AES-256-GCM...")
    subprocess.run(["crypto-cli", "encrypt", "encrypt-file", "-i", str(test_file), "-o", str(enc_file), "-p", "UltraSecurePassphrase123"], check=True)

    print("🔓 Decrypting file with AES-256-GCM...")
    subprocess.run(["crypto-cli", "encrypt", "decrypt-file", "-i", str(enc_file), "-o", str(dec_file), "-p", "UltraSecurePassphrase123"], check=True)

    print(f"📄 Decrypted Payload Verification: {dec_file.read_text(encoding='utf-8')}")

    print("\n⚡ Computing SHA-3 Digest...")
    subprocess.run(["crypto-cli", "hash", "file", str(test_file)], check=True)

    test_file.unlink(missing_ok=True)
    enc_file.unlink(missing_ok=True)
    dec_file.unlink(missing_ok=True)

if __name__ == "__main__":
    build_project()
    install_package()
    run_tests()
    print("\n✨ Installation, modernization, and verification complete! The 'crypto-cli' binary is ready.")
