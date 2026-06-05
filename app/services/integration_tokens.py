"""Encrypt/decrypt per-workspace integration tokens at rest."""
from __future__ import annotations

import base64
import hashlib
import os


def _derive_key() -> bytes:
    secret = (os.getenv("SECRET_KEY") or os.getenv("R4R_API_KEY_PEPPER") or "ready-for-robots-dev").encode()
    return hashlib.sha256(secret).digest()


def encrypt_token(token: str) -> str:
    key = _derive_key()
    raw = token.encode("utf-8")
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
    return base64.urlsafe_b64encode(xored).decode("ascii")


def decrypt_token(ciphertext: str) -> str:
    key = _derive_key()
    raw = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
    plain = bytes(b ^ key[i % len(key)] for i, b in enumerate(raw))
    return plain.decode("utf-8")
