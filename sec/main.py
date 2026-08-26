import os
import time

from pydantic import ValidationError
from rich import box
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from auditor import AIAuditor
from config import console, logger
from schemas import HMACPayloadSchema
from sec_guard import SecGuard
from vault import VaultBackup


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