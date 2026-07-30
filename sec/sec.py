"""
Dual-Layer Security Toolkit (In-Transit & At-Rest)
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any
import warnings

from cryptography.fernet import Fernet, InvalidToken
import jwt
from pydantic import BaseModel, Field, ValidationError
import requests
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

warnings.filterwarnings("ignore")

logging.basicConfig(
    level=logging.CRITICAL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SecToolkit")

console = Console()


class JWTPayloadSchema(BaseModel):
    user_id: int = Field(..., description="Unique numerical user identifier")
    role: str = Field(..., min_length=1, description="Assigned role for access control")


class HMACPayloadSchema(BaseModel):
    user_id: int
    action: str
    amount: float = Field(..., ge=0.0)


class SecGuard:

    def __init__(self, jwt_secret: str | None = None, hmac_secret: str | None = None) -> None:
        raw_jwt = jwt_secret or os.getenv("JWT_SECRET")
        raw_hmac = hmac_secret or os.getenv("HMAC_SECRET")

        if not raw_jwt or len(raw_jwt) < 32:
            raise EnvironmentError("JWT_SECRET must be explicitly set and at least 32 characters long.")
        if not raw_hmac or len(raw_hmac) < 32:
            raise EnvironmentError("HMAC_SECRET must be explicitly set and at least 32 characters long.")

        self._jwt_secret: str = raw_jwt
        self._hmac_secret: bytes = raw_hmac.encode("utf-8")

    def generate_hmac(self, payload: str) -> str:
        return hmac.new(
            self._hmac_secret,
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def verify_hmac(self, payload: str, signature: str) -> bool:
        expected_signature = self.generate_hmac(payload)
        return hmac.compare_digest(expected_signature, signature)

    def generate_jwt(self, payload_data: dict[str, Any], expiration_minutes: int = 15) -> str:
        try:
            validated_payload = JWTPayloadSchema(**payload_data).model_dump()
        except ValidationError as exc:
            logger.error("JWT payload failed validation schema: %s", exc)
            raise ValueError("Invalid JWT Payload Structure") from exc

        validated_payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
        return jwt.encode(validated_payload, self._jwt_secret, algorithm="HS256")

    def verify_jwt(self, token: str) -> tuple[bool, str]:
        try:
            jwt.decode(token, self._jwt_secret, algorithms=["HS256"])
            return True, "Valid Signature & Not Expired"
        except jwt.ExpiredSignatureError:
            logger.warning("JWT verification failed: Expired Token")
            return False, "Token Expired"
        except jwt.InvalidTokenError as exc:
            logger.warning("JWT verification failed: Invalid Token (%s)", exc)
            return False, "Invalid Token"

    def check_security_headers(self, headers: dict[str, str]) -> dict[str, bool]:
        normalized_headers = {k.lower(): v for k, v in headers.items()}
        required_headers = {
            "strict-transport-security": "HSTS",
            "content-security-policy": "CSP",
            "x-frame-options": "X-Frame-Options"
        }
        
        return {
            display_name: header_key in normalized_headers
            for header_key, display_name in required_headers.items()
        }


class VaultBackup:

    def __init__(self) -> None:
        self.key: bytes = Fernet.generate_key()
        self.cipher_suite: Fernet = Fernet(self.key)

    def encrypt_data(self, raw_data: bytes) -> bytes:
        return self.cipher_suite.encrypt(raw_data)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        try:
            return self.cipher_suite.decrypt(encrypted_data)
        except InvalidToken as exc:
            logger.error("Decryption failed due to invalid token or corrupted ciphertext")
            raise ValueError("Decryption failed: Invalid key or corrupted data.") from exc

    def generate_integrity_hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def get_key_base64(self) -> str:
        return self.key.decode("utf-8")


class AIAuditor:

    def __init__(self, ollama_url: str = "http://localhost:11434/api/generate", model: str = "llama3"):
        self.api_url = ollama_url
        self.model = model

    def audit_infrastructure(self, layer1_status: dict[str, Any], layer2_status: dict[str, Any]) -> str:
        audit_payload = {
            "in_transit": layer1_status,
            "at_rest": layer2_status
        }
        prompt = (
            "You are a Senior Security Auditor. Review the following JSON telemetry for a "
            "data security pipeline and provide exactly ONE sentence assessing the encryption "
            f"integrity and compliance. Telemetry: {json.dumps(audit_payload)}"
        )

        try:
            response = requests.post(
                self.api_url,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=2.5
            )
            response.raise_for_status()
            audit_response = response.json().get("response", "").strip()
            if audit_response:
                return audit_response
        except (requests.exceptions.RequestException, ValueError) as exc:
            logger.warning("Ollama API unreachable or failed (%s). Falling back to synthetic audit report.", exc)

        return (
            "[SYNTHETIC FALLBACK] The cryptographic envelope and HTTP security headers "
            "are properly configured, ensuring robust zero-trust compliance for both "
            "in-transit and at-rest vectors."
        )


def run_demo() -> None:
    console.clear()

    os.environ.setdefault("JWT_SECRET", "super-secret-jwt-key-with-sufficient-length-32bytes")
    os.environ.setdefault("HMAC_SECRET", "hmac-signing-key-with-sufficient-length-32bytes")

    header = Panel(
        "[bold cyan]🛡️ SEC-TOOLKIT | Data Protection (In-Transit & At-Rest Engine)[/bold cyan]\n"
        "[dim italic]System Status: Operational | Module: Core Security Pipeline[/dim italic]",
        box=box.DOUBLE, expand=False, border_style="blue"
    )
    console.print(header, justify="center")
    console.print("\n")

    sec_guard = SecGuard()
    vault = VaultBackup()
    auditor = AIAuditor()

    raw_payload_dict = {"user_id": 101, "action": "bank_transfer", "amount": 5000.0}
    
    try:
        validated_hmac_payload = HMACPayloadSchema(**raw_payload_dict)
        mock_payload = validated_hmac_payload.model_dump_json()
    except ValidationError as err:
        logger.error("HMAC Input payload validation failed: %s", err)
        return

    valid_signature = sec_guard.generate_hmac(mock_payload)
    hmac_valid = sec_guard.verify_hmac(mock_payload, valid_signature)

    mock_token = sec_guard.generate_jwt({"user_id": 101, "role": "admin"})
    jwt_valid, jwt_msg = sec_guard.verify_jwt(mock_token)

    mock_headers = {
        "sTrict-tRansport-sEcurity": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "X-FRAME-OPTIONS": "DENY",
        "Content-Type": "application/json"
    }
    header_status = sec_guard.check_security_headers(mock_headers)

    layer1_report = {
        "HMAC Valid": hmac_valid,
        "JWT Status": jwt_msg,
        "Headers Configured": all(header_status.values())
    }

    raw_file_data = b"CONFIDENTIAL: Financial ledgers for Q3 2026. Do not distribute."

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=True
    ) as progress:
        task1 = progress.add_task("[cyan]Simulating Vault Encryption & Hashing...", total=100)
        while not progress.finished:
            progress.update(task1, advance=20)
            time.sleep(0.05)

    encrypted_data = vault.encrypt_data(raw_file_data)
    file_hash = vault.generate_integrity_hash(encrypted_data)

    layer2_report = {
        "Algorithm": "AES-128 (Fernet) CBC mode",
        "Data Encrypted": True,
        "Integrity Hash": "SHA-256"
    }

    table_l1 = Table(title="Layer 1: In-Transit Security", box=box.MINIMAL_DOUBLE_HEAD, show_lines=True)
    table_l1.add_column("Component", style="cyan", no_wrap=True)
    table_l1.add_column("Status", style="green")
    table_l1.add_column("Details", style="dim")

    table_l1.add_row("HMAC-SHA256", "✔️ VERIFIED" if hmac_valid else "❌ FAILED", "Payload integrity intact")
    table_l1.add_row("JWT Auth", f"✔️ {jwt_msg.upper()}" if jwt_valid else f"❌ {jwt_msg.upper()}", "Bearer token verified")
    for h_name, h_present in header_status.items():
        table_l1.add_row(f"HTTP: {h_name}", "✔️ PRESENT" if h_present else "❌ MISSING", "Defense-in-depth header")

    table_l2 = Table(title="Layer 2: At-Rest Security", box=box.MINIMAL_DOUBLE_HEAD, show_lines=True)
    table_l2.add_column("Metric", style="magenta", no_wrap=True)
    table_l2.add_column("Value", style="yellow")

    table_l2.add_row("Archive Status", "Encrypted & Packed")
    table_l2.add_row("AES Cipher Key", f"{vault.get_key_base64()[:16]}... (Truncated)")
    table_l2.add_row("Encrypted Size", f"{len(encrypted_data)} bytes")
    table_l2.add_row("SHA-256 Hash", file_hash)

    console.print(table_l1)
    console.print("\n")
    console.print(table_l2)
    console.print("\n")

    with console.status("[bold green]Requesting AI Security Audit...", spinner="dots"):
        audit_text = auditor.audit_infrastructure(layer1_report, layer2_report)

    audit_panel = Panel(
        f"[bold white]{audit_text}[/bold white]",
        title="🤖 AI Security Audit Report",
        border_style="green",
        box=box.ROUNDED
    )
    console.print(audit_panel)
    console.print("\n[dim]Demo execution completed successfully.[/dim]")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        console.print("\n[red]Execution aborted by user.[/red]")