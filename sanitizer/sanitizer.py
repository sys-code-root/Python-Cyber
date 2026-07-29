import argparse
import csv
import hashlib
import io
import json
import os
import random
import re
import sys
import time
from typing import Any, Generator, Iterator, Optional, Union

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

SENSITIVE_KEYWORDS = {
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


class SanitizerEngine:
    """Core engine responsible for masking, hashing, encrypting, and decrypting data."""

    def __init__(
        self,
        mode: str = "mask",
        key: Optional[str] = None,
        salt: bytes = b"sanitizer_salt_2026",
    ) -> None:
        self.mode = mode.lower()
        self.salt = salt
        self.fernet: Optional[Any] = None

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
                sys.stderr.write("[!] Error: 'decrypt' mode requires a key provided via -k/--key.\n")
                sys.exit(1)

            if not key and self.mode == "encrypt":
                key = Fernet.generate_key().decode()
                sys.stderr.write(f"[*] No key provided. Auto-generated Fernet Key:\n---> {key}\n\n")

            try:
                self.fernet = Fernet(key.encode() if isinstance(key, str) else key)
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
        """Transforms a single raw value based on the selected mode."""
        if not text:
            return text

        if self.mode == "mask":
            return self._mask_value(text)

        if self.mode == "hash":
            digest = hashlib.sha256(self.salt + text.encode("utf-8", errors="ignore")).hexdigest()
            return digest[:16]

        if self.mode == "encrypt" and self.fernet:
            encrypted_bytes = self.fernet.encrypt(text.encode("utf-8", errors="ignore"))
            return f"ENC({encrypted_bytes.decode('utf-8')})"

        return text

    def decrypt_text_block(self, text: str) -> str:
        """Scans for ENC(...) patterns and decrypts their contents."""
        def replace_encrypted(match: re.Match) -> str:
            token = match.group(1)
            try:
                return self.fernet.decrypt(token.encode("utf-8")).decode("utf-8")
            except Exception:
                return match.group(0)

        return REGEX_ENC_PATTERN.sub(replace_encrypted, text)

    def sanitize_text_block(self, text: str) -> str:
        """Sanitizes sensitive patterns and key-value pairs within a raw string block."""
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

        return text


def process_csv_stream(
    reader: Iterator[str], engine: SanitizerEngine
) -> Generator[str, None, None]:
    """Processes CSV content line-by-line using streaming buffers."""
    for line in reader:
        if not line.strip():
            yield line
            continue
        try:
            f_in = io.StringIO(line)
            f_out = io.StringIO()
            csv_reader = csv.reader(f_in)
            csv_writer = csv.writer(f_out, quoting=csv.QUOTE_MINIMAL)

            for row in csv_reader:
                sanitized_row = [engine.sanitize_text_block(cell) for cell in row]
                csv_writer.writerow(sanitized_row)

            yield f_out.getvalue()
        except Exception:
            yield engine.sanitize_text_block(line)


def process_sql_stream(
    reader: Iterator[str], engine: SanitizerEngine
) -> Generator[str, None, None]:
    """Processes SQL dumps with column-aware targeted transformation."""
    for line in reader:
        if not line.strip() or engine.mode == "decrypt":
            yield engine.sanitize_text_block(line)
            continue

        match = REGEX_SQL_INSERT.search(line)
        if match:
            cols_raw = match.group("cols")
            vals_raw = match.group("vals")

            cols = [c.strip(' `"') for c in cols_raw.split(",")]
            sensitive_indices = {
                idx for idx, col in enumerate(cols)
                if any(kw in col.lower() for kw in SENSITIVE_KEYWORDS)
            }

            def process_values_group(val_group_str: str) -> str:
                elements = re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", val_group_str)
                new_elements = []

                for idx, elem in enumerate(elements):
                    clean_elem = elem.strip()
                    if idx in sensitive_indices:
                        if clean_elem.startswith("'") and clean_elem.endswith("'"):
                            raw_val = clean_elem[1:-1]
                            new_elements.append(f"'{engine.transform(raw_val)}'")
                        else:
                            new_elements.append(engine.transform(clean_elem))
                    else:
                        new_elements.append(engine.sanitize_text_block(elem))

                return ",".join(new_elements)

            new_vals = re.sub(
                r"\(([^)]+)\)",
                lambda m: f"({process_values_group(m.group(1))})",
                vals_raw,
            )
            table = match.group("table")
            yield f"INSERT INTO `{table}` ({cols_raw}) VALUES {new_vals};\n"
        else:
            yield engine.sanitize_text_block(line)


def process_json_stream(
    reader: Iterator[str], engine: SanitizerEngine
) -> Generator[str, None, None]:
    """Processes both standard JSON files and NDJSON stream lines."""
    preview_lines = []
    for line in reader:
        preview_lines.append(line)
        if len(preview_lines) >= 5:
            break

    is_ndjson = False
    if preview_lines:
        try:
            json.loads(preview_lines[0])
            is_ndjson = True
        except Exception:
            is_ndjson = False

    def sanitize_obj(obj: Any) -> Any:
        if isinstance(obj, dict):
            new_dict = {}
            for key, val in obj.items():
                is_sensitive_key = engine.mode != "decrypt" and any(
                    kw in key.lower() for kw in SENSITIVE_KEYWORDS
                )
                if is_sensitive_key:
                    new_dict[key] = (
                        engine.transform(val) if isinstance(val, str) else sanitize_obj(val)
                    )
                else:
                    new_dict[key] = sanitize_obj(val)
            return new_dict

        if isinstance(obj, list):
            return [sanitize_obj(item) for item in obj]

        if isinstance(obj, str):
            return engine.sanitize_text_block(obj)

        return obj

    def full_stream() -> Generator[str, None, None]:
        yield from preview_lines
        yield from reader

    if is_ndjson:
        for line in full_stream():
            if not line.strip():
                yield line
                continue
            try:
                data = json.loads(line)
                sanitized_data = sanitize_obj(data)
                yield json.dumps(sanitized_data, ensure_ascii=False) + "\n"
            except Exception:
                yield engine.sanitize_text_block(line)
    else:
        full_content = "".join(full_stream())
        try:
            data = json.loads(full_content)
            sanitized_data = sanitize_obj(data)
            yield json.dumps(sanitized_data, indent=2, ensure_ascii=False) + "\n"
        except Exception:
            yield engine.sanitize_text_block(full_content)


def process_generic_stream(
    reader: Iterator[str], engine: SanitizerEngine
) -> Generator[str, None, None]:
    """Fallback stream handler for unstructured text files (e.g., log files)."""
    for line in reader:
        yield engine.sanitize_text_block(line)


def generate_benchmark_file(output_path: str, target_size_mb: int) -> None:
    """Generates synthetic log/SQL datasets for performance benchmarking."""
    print(f"[*] Generating benchmark dataset (~{target_size_mb} MB) at: {output_path}...")

    cpfs = ["123.456.789-00", "987.654.321-11", "111.222.333-44"]
    emails = ["user.test@company.com", "admin.sec@domain.org", "dev_python@cyber.io"]
    cards = ["4532117890123456", "5500881122334455", "378282246310005"]
    tokens = [
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        "sk_live_99887766554433221100",
    ]

    bytes_target = target_size_mb * 1024 * 1024
    bytes_written = 0
    lines_count = 0
    start_time = time.time()

    with open(output_path, "w", encoding="utf-8") as file:
        while bytes_written < bytes_target:
            line_type = random.randint(1, 3)
            if line_type == 1:
                line = (
                    f"2026-07-28 10:15:{random.randint(10, 59)} [INFO] User login success. "
                    f"Email: {random.choice(emails)}, CPF: {random.choice(cpfs)}\n"
                )
            elif line_type == 2:
                line = (
                    f"2026-07-28 10:16:{random.randint(10, 59)} [DEBUG] Processing card "
                    f"{random.choice(cards)} with api_key=\"{random.choice(tokens)}\"\n"
                )
            else:
                line = (
                    f"INSERT INTO users (id, name, email, pass, cpf) VALUES "
                    f"({lines_count}, 'Test User', '{random.choice(emails)}', "
                    f"'SuperSecretPass{lines_count}!', '{random.choice(cpfs)}');\n"
                )

            file.write(line)
            bytes_written += len(line.encode("utf-8"))
            lines_count += 1

    elapsed = time.time() - start_time
    print(
        f"[✓] File generated successfully! {lines_count:,} lines "
        f"({bytes_written / (1024 * 1024):.2f} MB) in {elapsed:.2f}s.\n"
    )

def read_file_by_line(filepath: str) -> Generator[str, None, None]:
    """Reads a file lazily line-by-line to minimize memory footprint."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as file:
        yield from file


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="High-performance stream sanitizer, encryptor, decrypter, and benchmarking tool."
    )
    parser.add_argument("-i", "--input", help="Path to the input file.")
    parser.add_argument("-o", "--output", help="Path to the output file.")
    parser.add_argument(
        "-m",
        "--mode",
        choices=["mask", "hash", "encrypt", "decrypt"],
        default="mask",
        help="Operation mode (default: mask).",
    )
    parser.add_argument(
        "-k",
        "--key",
        nargs="?",
        const="",
        default=None,
        help="Fernet key for encryption/decryption (Required for 'decrypt').",
    )
    parser.add_argument(
        "--generate-bench",
        type=int,
        metavar="SIZE_MB",
        help="Generates a synthetic benchmark dataset of SIZE_MB at the --output location.",
    )

    args = parser.parse_args()

    if args.generate_bench:
        if not args.output:
            sys.stderr.write(
                "[!] Error: Please specify an output path using -o/--output when using --generate-bench.\n"
            )
            sys.exit(1)
        generate_benchmark_file(args.output, args.generate_bench)
        sys.exit(0)

    if not args.input or not args.output:
        parser.print_help()
        sys.exit(1)

    if not os.path.isfile(args.input):
        sys.stderr.write(f"[!] Error: Input file '{args.input}' was not found.\n")
        sys.exit(1)

    ext = os.path.splitext(args.input)[1].lower()
    engine = SanitizerEngine(mode=args.mode, key=args.key)
    reader = read_file_by_line(args.input)

    print(f"[*] Starting processing: {args.input}")
    print(f"[*] Mode: {args.mode.upper()}")

    start_time = time.time()

    if ext == ".csv":
        processor = process_csv_stream(reader, engine)
    elif ext == ".json":
        processor = process_json_stream(reader, engine)
    elif ext == ".sql":
        processor = process_sql_stream(reader, engine)
    else:
        processor = process_generic_stream(reader, engine)

    try:
        lines_processed = 0
        with open(args.output, "w", encoding="utf-8", errors="replace") as out_file:
            for chunk in processor:
                out_file.write(chunk)
                lines_processed += 1

        elapsed = time.time() - start_time
        file_size_mb = os.path.getsize(args.output) / (1024 * 1024)
        lines_per_sec = lines_processed / (elapsed or 0.001)

        print("[✓] Processing completed successfully!")
        print(f"[✓] Total records/lines: {lines_processed:,}")
        print(f"[✓] Time elapsed: {elapsed:.2f}s ({lines_per_sec:,.0f} lines/s)")
        print(f"[✓] Output file: {args.output} ({file_size_mb:.2f} MB)")

    except Exception as exc:
        sys.stderr.write(f"[!] Processing error: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()