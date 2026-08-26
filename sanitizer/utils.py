import random
import time
from typing import Generator


def generate_benchmark_file(output_path: str, target_size_mb: int) -> None:
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
                    f"Email: {random.choice(emails)}, CPF: {random.choice(cpfs)}, Name: Carlos Silva\n"
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
    with open(filepath, "r", encoding="utf-8", errors="replace") as file:
        yield from file