import os
import json
import requests
from crypto_cli.crypto.key_manager import VAULT_DIR, get_key_metadata, ensure_vault_permissions

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"

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

def generate_ai_audit_report(model: str = "llama3") -> str:
    findings = audit_security_hygiene()
    metadata = get_key_metadata()

    sanitized_context = {
        "vault_permission_status": "SECURE" if ensure_vault_permissions() else "INSECURE",
        "findings": findings,
        "key_metadata_summary": metadata
    }

    prompt = (
        "You are an expert DevSecOps and Cryptography Auditor. "
        "Analyze the following static system findings and non-sensitive key vault metadata. "
        "Generate a concise, professional Security Audit Report in markdown format summarizing overall risk, "
        "identifying critical key rotation or configuration issues, and providing remediation advice.\n\n"
        f"SANITIZED CONTEXT:\n{json.dumps(sanitized_context, indent=2)}"
    )

    try:
        response = requests.post(
            OLLAMA_ENDPOINT,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=5.0
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
