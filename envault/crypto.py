"""AES-256-GCM encryption/decryption for .env files using a passphrase-derived key."""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # 256 bits
ITERATIONS = 200_000


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a passphrase using PBKDF2-HMAC-SHA256."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        salt,
        ITERATIONS,
        dklen=KEY_SIZE,
    )


def encrypt(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext and return a base64-encoded ciphertext blob.

    Format: base64(salt || nonce || ciphertext_with_tag)
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    blob = salt + nonce + ciphertext
    return base64.b64encode(blob).decode("utf-8")


def decrypt(encoded: str, passphrase: str) -> str:
    """Decrypt a base64-encoded ciphertext blob and return the plaintext."""
    blob = base64.b64decode(encoded.encode("utf-8"))
    salt = blob[:SALT_SIZE]
    nonce = blob[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = blob[SALT_SIZE + NONCE_SIZE:]
    key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
