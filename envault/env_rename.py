"""Bulk rename (prefix add/strip) of keys inside an encrypted vault."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from .vault import lock, unlock


class RenameError(Exception):
    """Raised when a bulk-rename operation fails."""


def _parse_env_dict(text: str) -> Dict[str, str]:
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


def _dict_to_env(d: Dict[str, str]) -> str:
    return "\n".join(f"{k}={v}" for k, v in sorted(d.items())) + "\n"


def add_prefix(
    vault_path: Path, passphrase: str, prefix: str
) -> List[Tuple[str, str]]:
    """Add *prefix* to every key in the vault. Returns list of (old, new) pairs."""
    if not vault_path.exists():
        raise RenameError(f"Vault not found: {vault_path}")
    if not prefix:
        raise RenameError("Prefix must not be empty.")
    env_text = unlock(vault_path, passphrase)
    data = _parse_env_dict(env_text)
    renamed: List[Tuple[str, str]] = []
    new_data: Dict[str, str] = {}
    for key, value in data.items():
        new_key = f"{prefix}{key}" if not key.startswith(prefix) else key
        new_data[new_key] = value
        renamed.append((key, new_key))
    lock(vault_path, _dict_to_env(new_data), passphrase)
    return renamed


def strip_prefix(
    vault_path: Path, passphrase: str, prefix: str
) -> List[Tuple[str, str]]:
    """Remove *prefix* from every key that starts with it. Returns (old, new) pairs."""
    if not vault_path.exists():
        raise RenameError(f"Vault not found: {vault_path}")
    if not prefix:
        raise RenameError("Prefix must not be empty.")
    env_text = unlock(vault_path, passphrase)
    data = _parse_env_dict(env_text)
    renamed: List[Tuple[str, str]] = []
    new_data: Dict[str, str] = {}
    for key, value in data.items():
        new_key = key[len(prefix):] if key.startswith(prefix) else key
        if not new_key:
            raise RenameError(
                f"Stripping prefix '{prefix}' from key '{key}' would produce an empty key."
            )
        new_data[new_key] = value
        renamed.append((key, new_key))
    lock(vault_path, _dict_to_env(new_data), passphrase)
    return renamed
