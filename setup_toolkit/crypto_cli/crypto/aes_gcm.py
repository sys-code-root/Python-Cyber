import os
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