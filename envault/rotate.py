"""Passphrase rotation: re-encrypt vault files under a new passphrase."""

from pathlib import Path
from typing import Optional

from .vault import lock, unlock


class RotateError(Exception):
    """Raised when passphrase rotation fails."""


def rotate(
    env_path: Path,
    vault_path: Path,
    old_passphrase: str,
    new_passphrase: str,
    profile: Optional[str] = None,
) -> None:
    """Re-encrypt *vault_path* from *old_passphrase* to *new_passphrase*.

    Steps
    -----
    1. Decrypt the existing vault file with the old passphrase.
    2. Re-encrypt the recovered plaintext with the new passphrase.
    3. Overwrite the vault file in place.

    Raises
    ------
    RotateError
        If decryption with the old passphrase fails or the vault file does
        not exist.
    """
    if not vault_path.exists():
        raise RotateError(f"Vault file not found: {vault_path}")

    # --- decrypt with old passphrase ---
    try:
        unlock(vault_path=vault_path, env_path=env_path, passphrase=old_passphrase)
    except Exception as exc:  # pragma: no cover – propagate as RotateError
        raise RotateError(f"Failed to decrypt vault with old passphrase: {exc}") from exc

    # --- re-encrypt with new passphrase ---
    try:
        lock(env_path=env_path, vault_path=vault_path, passphrase=new_passphrase)
    except Exception as exc:
        raise RotateError(f"Failed to re-encrypt vault with new passphrase: {exc}") from exc

    # Clean up the temporary plaintext file produced by unlock
    if env_path.exists():
        env_path.unlink()
