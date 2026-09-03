#!/usr/bin/env python3
"""Decrypt .dta files from the outgoing folder using Fernet and place them in incoming.

Usage: uv run python scripts/decrypt_file.py
"""

import getpass
import sys
import uuid
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = PROJECT_ROOT / "incoming"
OUTGOING_DIR = PROJECT_ROOT / "outgoing"


def main():
    files = [f for f in OUTGOING_DIR.iterdir() if f.is_file() and f.suffix == ".dta"]
    if not files:
        print("No .dta files found in outgoing/")
        sys.exit(0)

    print(f"Found {len(files)} .dta file(s) in outgoing/")

    key = getpass.getpass("Enter Fernet key: ").encode()
    fernet = Fernet(key)

    for source in files:
        ciphertext = source.read_bytes()
        try:
            data = fernet.decrypt(ciphertext)
        except InvalidToken:
            print(f"Error: decryption failed for {source.name} — wrong key or corrupted file", file=sys.stderr)
            continue

        name_len = int.from_bytes(data[:2], "big")
        original_name = data[2 : 2 + name_len].decode()
        plaintext = data[2 + name_len :]

        expected_uuid = str(uuid.uuid5(NAMESPACE, original_name))
        if source.stem != expected_uuid:
            print(f"Warning: UUID mismatch for {source.name} (expected {expected_uuid})", file=sys.stderr)

        output_path = INCOMING_DIR / original_name
        output_path.write_bytes(plaintext)
        print(f"Decrypted: {source.name} -> {output_path.name}")

    print("Done.")


if __name__ == "__main__":
    main()
