from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
from typing import Any

import jwt
from pydantic import ValidationError

from config import logger
from schemas import JWTPayloadSchema


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