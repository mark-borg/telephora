#!/usr/bin/env python3
"""Generate a random Fernet key and display it.

Usage: uv run python scripts/generate_key.py
"""

from cryptography.fernet import Fernet

print(Fernet.generate_key().decode())
