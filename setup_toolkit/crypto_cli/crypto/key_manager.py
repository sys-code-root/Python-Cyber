import os
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
