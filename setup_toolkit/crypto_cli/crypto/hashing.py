import hashlib
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
