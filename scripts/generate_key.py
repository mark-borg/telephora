#!/usr/bin/env python3
"""Generate a random Fernet key and display it."""

from cryptography.fernet import Fernet

print(Fernet.generate_key().decode())
