#!/usr/bin/env python3
"""Encrypt files from the incoming folder using Fernet and place them in outgoing.

Usage: uv run python scripts/encrypt_files.py
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import humanize
import pwinput
from cryptography.fernet import Fernet
from rich.console import Console

NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = PROJECT_ROOT / "incoming"
OUTGOING_DIR = PROJECT_ROOT / "outgoing"

console = Console()


def main():
    files = [f for f in INCOMING_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    if not files:
        console.print("No files found in incoming/")
        sys.exit(0)

    console.print(f"Found [bold]{len(files)}[/bold] file(s) in incoming/")

    key_input = pwinput.pwinput(prompt="Enter Fernet key (leave empty to generate a new one): ", mask="*")
    if key_input:
        key = key_input.encode()
    else:
        key = Fernet.generate_key()
        console.print(f"Generated new key: [bold]{key.decode()}[/bold]")

    fernet = Fernet(key)

    log_path = OUTGOING_DIR / ".log"

    for source in files:
        plaintext = source.read_bytes()
        name_bytes = source.name.encode()
        header = len(name_bytes).to_bytes(2, "big") + name_bytes
        ciphertext = fernet.encrypt(header + plaintext)

        name_uuid = uuid.uuid5(NAMESPACE, source.name)
        output_path = OUTGOING_DIR / f"{name_uuid}.dta"
        output_path.write_bytes(ciphertext)

        file_size = len(plaintext)
        source.unlink()

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a") as log:
            log.write(f"{timestamp}\t{output_path.name}\t{source.name}\n")

        console.print(
            f"  {timestamp}  {output_path.name}  [dim]{source.name}[/dim]"
            f"  [cyan]{humanize.naturalsize(file_size)}[/cyan]"
        )

    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    main()
