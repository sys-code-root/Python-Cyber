import argparse
import os
import sys
import time

from processors import (
    process_csv_stream,
    process_generic_stream,
    process_json_stream,
    process_sql_stream,
)
from sanitizer_engine import SanitizerEngine
from utils import generate_benchmark_file, read_file_by_line


def main() -> None:
    parser = argparse.ArgumentParser(
        description="High-performance stream sanitizer, encryptor, decrypter, and AI benchmarking tool."
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
        default=None,
        help="Fernet key for encryption/decryption (Required for 'decrypt').",
    )
    parser.add_argument(
        "--use-ai",
        action="store_true",
        help="Enable AI-based (spaCy NER) detection for unstructured PII (e.g. names and locations).",
    )
    parser.add_argument(
        "--ai-model",
        default="pt_core_news_sm",
        help="spaCy model name for NER (default: pt_core_news_sm).",
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
    engine = SanitizerEngine(
        mode=args.mode,
        key=args.key,
        use_ai=args.use_ai,
        ai_model=args.ai_model,
    )
    reader = read_file_by_line(args.input)

    print(f"[*] Starting processing: {args.input}")
    print(f"[*] Mode: {args.mode.upper()}")
    print(f"[*] AI Engine Enabled: {args.use_ai}")

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