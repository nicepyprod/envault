"""High-level vault operations: lock (encrypt) and unlock (decrypt) .env files."""

from pathlib import Path
from envault.crypto import encrypt, decrypt


DEFAULT_ENV_FILE = ".env"
DEFAULT_VAULT_FILE = ".env.vault"


def lock(env_path: str | Path = DEFAULT_ENV_FILE,
         vault_path: str | Path = DEFAULT_VAULT_FILE,
         passphrase: str = "") -> Path:
    """Encrypt *env_path* and write the ciphertext to *vault_path*.

    Returns the resolved vault path.
    """
    env_path = Path(env_path)
    vault_path = Path(vault_path)

    if not env_path.exists():
        raise FileNotFoundError(f"Source file not found: {env_path}")
    if not passphrase:
        raise ValueError("Passphrase must not be empty.")

    plaintext = env_path.read_text(encoding="utf-8")
    ciphertext = encrypt(plaintext, passphrase)
    vault_path.write_text(ciphertext, encoding="utf-8")
    return vault_path.resolve()


def unlock(vault_path: str | Path = DEFAULT_VAULT_FILE,
           env_path: str | Path = DEFAULT_ENV_FILE,
           passphrase: str = "") -> Path:
    """Decrypt *vault_path* and write the plaintext to *env_path*.

    Returns the resolved env path.
    """
    vault_path = Path(vault_path)
    env_path = Path(env_path)

    if not vault_path.exists():
        raise FileNotFoundError(f"Vault file not found: {vault_path}")
    if not passphrase:
        raise ValueError("Passphrase must not be empty.")

    ciphertext = vault_path.read_text(encoding="utf-8")
    plaintext = decrypt(ciphertext, passphrase)
    env_path.write_text(plaintext, encoding="utf-8")
    return env_path.resolve()
