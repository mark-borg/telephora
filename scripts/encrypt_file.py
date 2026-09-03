#!/usr/bin/env python3
"""Encrypt a file using Fernet and save it with a deterministic UUID5-based filename."""

import argparse
import getpass
import sys
import uuid
from pathlib import Path

from cryptography.fernet import Fernet

NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def main():
    parser = argparse.ArgumentParser(description="Encrypt a file using Fernet encryption.")
    parser.add_argument("file", help="Path to the file to encrypt")
    args = parser.parse_args()

    source = Path(args.file)
    if not source.is_file():
        print(f"Error: {source} not found", file=sys.stderr)
        sys.exit(1)

    key_input = getpass.getpass("Enter Fernet key (leave empty to generate a new one): ")
    if key_input:
        key = key_input.encode()
    else:
        key = Fernet.generate_key()
        print(f"Generated new key: {key.decode()}")

    fernet = Fernet(key)

    plaintext = source.read_bytes()
    ciphertext = fernet.encrypt(plaintext)

    name_uuid = uuid.uuid5(NAMESPACE, source.name)
    output_path = source.parent / f"{name_uuid}.dta"
    output_path.write_bytes(ciphertext)

    print(f"Encrypted: {source} -> {output_path}")


if __name__ == "__main__":
    main()
