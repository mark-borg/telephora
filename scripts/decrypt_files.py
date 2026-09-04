#!/usr/bin/env python3
"""Decrypt .dta files from the outgoing folder using Fernet and place them in incoming.

Usage: uv run python scripts/decrypt_files.py
"""

import sys
import uuid
from pathlib import Path

import pwinput
from cryptography.fernet import Fernet, InvalidToken
from rich.console import Console

NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = PROJECT_ROOT / "incoming"
OUTGOING_DIR = PROJECT_ROOT / "outgoing"

console = Console()


def main():
    files = [f for f in OUTGOING_DIR.iterdir() if f.is_file() and f.suffix == ".dta"]
    if not files:
        console.print("No .dta files found in outgoing/")
        sys.exit(0)

    console.print(f"Found [bold]{len(files)}[/bold] .dta file(s) in outgoing/")

    key = pwinput.pwinput(prompt="Enter Fernet key: ", mask="*").encode()
    fernet = Fernet(key)

    for source in files:
        ciphertext = source.read_bytes()
        try:
            data = fernet.decrypt(ciphertext)
        except InvalidToken:
            console.print(
                f"  [bold red]Error:[/bold red] decryption failed for {source.name}"
                " — wrong key or corrupted file"
            )
            continue

        name_len = int.from_bytes(data[:2], "big")
        original_name = data[2 : 2 + name_len].decode()
        plaintext = data[2 + name_len :]

        expected_uuid = str(uuid.uuid5(NAMESPACE, original_name))
        if source.stem != expected_uuid:
            console.print(
                f"  [bold yellow]Warning:[/bold yellow] UUID mismatch for {source.name}"
                f" (expected {expected_uuid})"
            )

        output_path = INCOMING_DIR / original_name
        output_path.write_bytes(plaintext)
        console.print(f"  {source.name}  [dim]->[/dim]  {output_path.name}")

    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    main()
