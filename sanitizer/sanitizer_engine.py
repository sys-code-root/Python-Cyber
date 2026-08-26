import hashlib
import re
import sys
from typing import Any, Optional

from ai_service import AIService
from config import REGEX_ENC_PATTERN, REGEX_KEY_VALUE_SECRET, REGEX_PATTERNS


class SanitizerEngine:

    def __init__(
        self,
        mode: str = "mask",
        key: Optional[str] = None,
        salt: bytes = b"sanitizer_salt_2026",
        use_ai: bool = False,
        ai_model: str = "pt_core_news_sm",
    ) -> None:
        self.mode = mode.lower()
        self.salt = salt
        self.fernet: Optional[Any] = None
        self.use_ai = use_ai
        self.ai_engine: Optional[AIService] = None

        if self.use_ai:
            print("[*] Initializing Lazy AI Engine (spaCy NER)...")
            self.ai_engine = AIService(model_name=ai_model)

        if self.mode in ("encrypt", "decrypt"):
            try:
                from cryptography.fernet import Fernet
            except ImportError:
                sys.stderr.write(
                    "[!] Error: 'cryptography' library is required for 'encrypt' and 'decrypt' modes.\n"
                    "[!] Install it via: pip install cryptography\n"
                )
                sys.exit(1)

            if self.mode == "decrypt" and not key:
                sys.stderr.write(
                    "[!] Error: 'decrypt' mode requires a key provided via -k/--key.\n"
                )
                sys.exit(1)

            if not key and self.mode == "encrypt":
                key = Fernet.generate_key().decode()
                sys.stderr.write(
                    f"[*] No key provided. Auto-generated Fernet Key:\n---> {key}\n\n"
                )

            try:
                key_bytes = key.encode() if isinstance(key, str) else key
                self.fernet = Fernet(key_bytes)
            except Exception as exc:
                sys.stderr.write(f"[!] Error initializing Fernet key: {exc}\n")
                sys.exit(1)

    def _mask_value(self, val: str) -> str:
        if "@" in val:
            user, domain = val.split("@", 1)
            masked_user = user[0] + "****" if len(user) > 1 else "*"
            return f"{masked_user}@{domain}"

        digits = re.sub(r"\D", "", val)
        if len(digits) == 11:
            return f"{digits[:3]}.***.***-{digits[-2:]}"
        if len(digits) == 14:
            return f"{digits[:2]}.***.***/****-{digits[-2:]}"
        if 13 <= len(digits) <= 16:
            return f"****-****-****-{digits[-4:]}"

        if len(val) <= 4:
            return "*****"
        return f"{val[:2]}{'*' * (len(val) - 4)}{val[-2:]}"

    def transform(self, text: str) -> str:
        if not text:
            return text

        if self.mode == "mask":
            return self._mask_value(text)

        if self.mode == "hash":
            digest = hashlib.sha256(
                self.salt + text.encode("utf-8", errors="ignore")
            ).hexdigest()
            return digest[:16]

        if self.mode == "encrypt" and self.fernet:
            encrypted_bytes = self.fernet.encrypt(
                text.encode("utf-8", errors="ignore")
            )
            return f"ENC({encrypted_bytes.decode('utf-8')})"

        return text

    def decrypt_text_block(self, text: str) -> str:

        def replace_encrypted(match: re.Match) -> str:
            token = match.group(1)
            try:
                if self.fernet:
                    return self.fernet.decrypt(token.encode("utf-8")).decode(
                        "utf-8"
                    )
            except Exception:
                pass
            return match.group(0)

        return REGEX_ENC_PATTERN.sub(replace_encrypted, text)

    def sanitize_text_block(self, text: str) -> str:
        if self.mode == "decrypt":
            return self.decrypt_text_block(text)

        def replace_secret(match: re.Match) -> str:
            key_part = match.group("key")
            val_part = match.group("val")
            quote = ""
            raw_val = val_part

            if (val_part.startswith('"') and val_part.endswith('"')) or (
                val_part.startswith("'") and val_part.endswith("'")
            ):
                quote = val_part[0]
                raw_val = val_part[1:-1]

            return f"{key_part}{quote}{self.transform(raw_val)}{quote}"

        text = REGEX_KEY_VALUE_SECRET.sub(replace_secret, text)

        for pattern in REGEX_PATTERNS.values():
            text = pattern.sub(lambda m: self.transform(m.group(0)), text)

        if self.use_ai and self.ai_engine:
            pii_entities = self.ai_engine.extract_unstructured_pii(text)
            for entity in pii_entities:
                if len(entity.strip()) > 2:
                    text = text.replace(entity, self.transform(entity))

        return text