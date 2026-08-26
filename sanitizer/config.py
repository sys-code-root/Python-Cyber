import re
from typing import Set

REGEX_PATTERNS = {
    "CPF": re.compile(r"\b\d{3}[\.-]?\d{3}[\.-]?\d{3}[\.-]?\d{2}\b"),
    "CNPJ": re.compile(r"\b\d{2}[\.-]?\d{3}[\.-]?\d{3}[\./-]?\d{4}[\.-]?\d{2}\b"),
    "CREDIT_CARD": re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b"
    ),
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "PHONE": re.compile(r"\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?(?:9?\d{4}[-\s]?\d{4})\b"),
    "BEARER_JWT": re.compile(
        r"(?:Bearer\s+)?\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*\b",
        re.IGNORECASE,
    ),
}

REGEX_KEY_VALUE_SECRET = re.compile(
    r'(?P<key>["\']?(?:api[_-]?key|password|passwd|secret|access[_-]?token|auth[_-]?token)["\']?\s*[:=]\s*)(?P<val>["\']?[^"\'\s,;{}]+["\']?)',
    re.IGNORECASE,
)

REGEX_ENC_PATTERN = re.compile(r"ENC\((gAAAAAB[A-Za-z0-9_=-]+)\)")

REGEX_SQL_INSERT = re.compile(
    r'INSERT\s+INTO\s+[`"]?(?P<table>\w+)[`"]?\s*\((?P<cols>[^)]+)\)\s*VALUES\s*(?P<vals>.*);?',
    re.IGNORECASE | re.DOTALL,
)

SENSITIVE_KEYWORDS: Set[str] = {
    "pass",
    "password",
    "token",
    "secret",
    "cpf",
    "cnpj",
    "email",
    "phone",
    "card",
    "credit_card",
    "auth",
    "key",
}