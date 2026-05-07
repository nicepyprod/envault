"""Interactive in-place editing of a decrypted vault's key-value pairs."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from envault.vault import lock, unlock


class EditError(Exception):
    """Raised when an edit operation fails."""


def _parse_env_dict(text: str) -> Dict[str, str]:
    """Parse decrypted env text into an ordered dict."""
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def _dict_to_env(data: Dict[str, str]) -> str:
    """Serialize a dict back to .env format."""
    return "\n".join(f"{k}={v}" for k, v in data.items()) + "\n"


def set_key(
    vault_path: Path,
    passphrase: str,
    key: str,
    value: str,
) -> None:
    """Decrypt the vault, set *key* to *value*, then re-encrypt in place."""
    if not vault_path.exists():
        raise EditError(f"Vault not found: {vault_path}")
    if not key:
        raise EditError("Key must not be empty.")

    env_path = vault_path.with_suffix(".env")
    unlock(vault_path, env_path, passphrase)
    try:
        data = _parse_env_dict(env_path.read_text())
        data[key] = value
        env_path.write_text(_dict_to_env(data))
        lock(env_path, vault_path, passphrase)
    finally:
        if env_path.exists():
            env_path.unlink()


def delete_key(
    vault_path: Path,
    passphrase: str,
    key: str,
) -> bool:
    """Remove *key* from the vault.  Returns True if the key existed."""
    if not vault_path.exists():
        raise EditError(f"Vault not found: {vault_path}")
    if not key:
        raise EditError("Key must not be empty.")

    env_path = vault_path.with_suffix(".env")
    unlock(vault_path, env_path, passphrase)
    try:
        data = _parse_env_dict(env_path.read_text())
        existed = key in data
        data.pop(key, None)
        env_path.write_text(_dict_to_env(data))
        lock(env_path, vault_path, passphrase)
    finally:
        if env_path.exists():
            env_path.unlink()
    return existed


def get_key(
    vault_path: Path,
    passphrase: str,
    key: str,
) -> Optional[str]:
    """Return the value of *key* from the vault, or None if absent."""
    if not vault_path.exists():
        raise EditError(f"Vault not found: {vault_path}")

    env_path = vault_path.with_suffix(".env")
    unlock(vault_path, env_path, passphrase)
    try:
        data = _parse_env_dict(env_path.read_text())
        return data.get(key)
    finally:
        if env_path.exists():
            env_path.unlink()
