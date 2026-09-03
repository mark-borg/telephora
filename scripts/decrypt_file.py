#!/usr/bin/env python3
"""Decrypt a .dta file back to its original filename using Fernet."""

import argparse
import getpass
import sys
import uuid
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def main():
    parser = argparse.ArgumentParser(description="Decrypt a Fernet-encrypted .dta file.")
    parser.add_argument("file", help="Path to the .dta file to decrypt")
    parser.add_argument("original_name", help="Original filename (e.g. my_code.zip) to verify UUID and use as output name")
    args = parser.parse_args()

    source = Path(args.file)
    if not source.is_file():
        print(f"Error: {source} not found", file=sys.stderr)
        sys.exit(1)

    expected_uuid = str(uuid.uuid5(NAMESPACE, args.original_name))
    if source.stem != expected_uuid:
        print(f"Error: UUID mismatch — {source.stem} does not match expected {expected_uuid} for '{args.original_name}'", file=sys.stderr)
        sys.exit(1)

    key = getpass.getpass("Enter Fernet key: ").encode()
    fernet = Fernet(key)

    ciphertext = source.read_bytes()
    try:
        plaintext = fernet.decrypt(ciphertext)
    except InvalidToken:
        print("Error: decryption failed — wrong key or corrupted file", file=sys.stderr)
        sys.exit(1)

    output_path = source.parent / args.original_name
    output_path.write_bytes(plaintext)
    print(f"Decrypted: {source} -> {output_path}")


if __name__ == "__main__":
    main()
