#!/usr/bin/env python3
"""Encrypt files from the incoming folder using Fernet and place them in outgoing."""

import getpass
import sys
import uuid
from pathlib import Path

from cryptography.fernet import Fernet

NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INCOMING_DIR = PROJECT_ROOT / "incoming"
OUTGOING_DIR = PROJECT_ROOT / "outgoing"


def main():
    files = [f for f in INCOMING_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    if not files:
        print("No files found in incoming/")
        sys.exit(0)

    print(f"Found {len(files)} file(s) in incoming/")

    key_input = getpass.getpass("Enter Fernet key (leave empty to generate a new one): ")
    if key_input:
        key = key_input.encode()
    else:
        key = Fernet.generate_key()
        print(f"Generated new key: {key.decode()}")

    fernet = Fernet(key)

    for source in files:
        plaintext = source.read_bytes()
        ciphertext = fernet.encrypt(plaintext)

        name_uuid = uuid.uuid5(NAMESPACE, source.name)
        output_path = OUTGOING_DIR / f"{name_uuid}.dta"
        output_path.write_bytes(ciphertext)

        source.unlink()
        print(f"Encrypted: {source.name} -> {output_path.name}")

    print("Done.")


if __name__ == "__main__":
    main()
