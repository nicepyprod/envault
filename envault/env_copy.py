"""Copy or rename keys within a vault."""

from __future__ import annotations

from pathlib import Path

from envault.vault import lock, unlock


class CopyError(Exception):
    """Raised when a copy/rename operation fails."""


def _parse_env_dict(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def _dict_to_env(data: dict[str, str]) -> str:
    return "\n".join(f"{k}={v}" for k, v in data.items()) + "\n"


def _load_vault_data(vault_path: Path, passphrase: str) -> dict[str, str]:
    """Unlock the vault and return its contents as a key/value dict."""
    plaintext = unlock(vault_path, passphrase)
    return _parse_env_dict(plaintext)


def copy_key(
    vault_path: Path,
    passphrase: str,
    src_key: str,
    dst_key: str,
    overwrite: bool = False,
) -> None:
    """Copy *src_key* to *dst_key* inside the vault (both keys will exist)."""
    if not vault_path.exists():
        raise CopyError(f"Vault not found: {vault_path}")
    if src_key == dst_key:
        raise CopyError("Source and destination keys must differ.")

    data = _load_vault_data(vault_path, passphrase)

    if src_key not in data:
        raise CopyError(f"Key not found in vault: {src_key!r}")
    if dst_key in data and not overwrite:
        raise CopyError(
            f"Destination key {dst_key!r} already exists. Use overwrite=True to replace it."
        )

    data[dst_key] = data[src_key]
    lock(vault_path, _dict_to_env(data), passphrase)


def rename_key(
    vault_path: Path,
    passphrase: str,
    src_key: str,
    dst_key: str,
    overwrite: bool = False,
) -> None:
    """Rename *src_key* to *dst_key* inside the vault (src_key is removed)."""
    copy_key(vault_path, passphrase, src_key, dst_key, overwrite=overwrite)

    data = _load_vault_data(vault_path, passphrase)
    del data[src_key]
    lock(vault_path, _dict_to_env(data), passphrase)
