import csv
import io
import json
import re
from typing import Any, Generator, Iterator

from config import REGEX_SQL_INSERT, SENSITIVE_KEYWORDS
from sanitizer_engine import SanitizerEngine


def process_csv_stream(
    reader: Iterator[str], engine: SanitizerEngine
) -> Generator[str, None, None]:
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
                idx
                for idx, col in enumerate(cols)
                if any(kw in col.lower() for kw in SENSITIVE_KEYWORDS)
            }

            def process_values_group(val_group_str: str) -> str:
                elements = re.split(
                    r",(?=(?:[^']*'[^']*')*[^']*$)", val_group_str
                )
                new_elements = []

                for idx, elem in enumerate(elements):
                    clean_elem = elem.strip()
                    if idx in sensitive_indices:
                        if clean_elem.startswith("'") and clean_elem.endswith("'"):
                            raw_val = clean_elem[1:-1]
                            new_elements.append(
                                f"'{engine.transform(raw_val)}'"
                            )
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
                        engine.transform(val)
                        if isinstance(val, str)
                        else sanitize_obj(val)
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
    for line in reader:
        yield engine.sanitize_text_block(line)