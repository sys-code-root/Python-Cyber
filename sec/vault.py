import hashlib

from cryptography.fernet import Fernet, InvalidToken

from config import logger


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