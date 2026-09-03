#!/usr/bin/env python3
"""Decrypt .dta files from the outgoing folder using Fernet and place them in incoming."""

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

    original_name = input("Enter original filename (e.g. my_code.zip) to verify UUID and use as output name: ")
    expected_uuid = str(uuid.uuid5(NAMESPACE, original_name))

    matched = [f for f in files if f.stem == expected_uuid]
    if not matched:
        print(f"Error: no file matching UUID {expected_uuid} for '{original_name}'", file=sys.stderr)
        sys.exit(1)

    key = getpass.getpass("Enter Fernet key: ").encode()
    fernet = Fernet(key)

    for source in matched:
        ciphertext = source.read_bytes()
        try:
            plaintext = fernet.decrypt(ciphertext)
        except InvalidToken:
            print(f"Error: decryption failed for {source.name} — wrong key or corrupted file", file=sys.stderr)
            continue

        output_path = INCOMING_DIR / original_name
        output_path.write_bytes(plaintext)
        print(f"Decrypted: {source.name} -> {output_path.name}")

    print("Done.")


if __name__ == "__main__":
    main()
