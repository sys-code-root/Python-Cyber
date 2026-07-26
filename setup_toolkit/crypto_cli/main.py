import typer
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
