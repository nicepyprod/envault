"""Diff two vault files (or a vault against a live .env) to show changed keys."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, NamedTuple

from envault.vault import unlock
from envault.export import _parse_env_lines


class DiffError(Exception):
    """Raised when diffing fails."""


class DiffEntry(NamedTuple):
    key: str
    status: str   # 'added' | 'removed' | 'changed' | 'unchanged'
    old_value: str | None
    new_value: str | None


def _load_vault_as_dict(vault_path: Path, passphrase: str) -> Dict[str, str]:
    """Decrypt a vault file and return its key/value pairs."""
    if not vault_path.exists():
        raise DiffError(f"Vault file not found: {vault_path}")
    plaintext = unlock(vault_path, passphrase)
    return _parse_env_lines(plaintext.splitlines())


def _load_env_as_dict(env_path: Path) -> Dict[str, str]:
    """Read a plain .env file and return its key/value pairs."""
    if not env_path.exists():
        raise DiffError(f".env file not found: {env_path}")
    lines = env_path.read_text(encoding="utf-8").splitlines()
    return _parse_env_lines(lines)


def diff_vaults(
    old_vault: Path,
    new_vault: Path,
    passphrase: str,
) -> List[DiffEntry]:
    """Compare two encrypted vault files using the same passphrase."""
    old = _load_vault_as_dict(old_vault, passphrase)
    new = _load_vault_as_dict(new_vault, passphrase)
    return _compute_diff(old, new)


def diff_vault_vs_env(
    vault_path: Path,
    env_path: Path,
    passphrase: str,
) -> List[DiffEntry]:
    """Compare an encrypted vault against a plain .env file."""
    old = _load_vault_as_dict(vault_path, passphrase)
    new = _load_env_as_dict(env_path)
    return _compute_diff(old, new)


def _compute_diff(old: Dict[str, str], new: Dict[str, str]) -> List[DiffEntry]:
    entries: List[DiffEntry] = []
    all_keys = sorted(set(old) | set(new))
    for key in all_keys:
        if key in old and key not in new:
            entries.append(DiffEntry(key, "removed", old[key], None))
        elif key not in old and key in new:
            entries.append(DiffEntry(key, "added", None, new[key]))
        elif old[key] != new[key]:
            entries.append(DiffEntry(key, "changed", old[key], new[key]))
        else:
            entries.append(DiffEntry(key, "unchanged", old[key], new[key]))
    return entries
