"""Sort keys in an encrypted vault file alphabetically or by custom order."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from envault.vault import lock, unlock


class SortError(Exception):
    """Raised when a sort operation fails."""


SortOrder = Literal["asc", "desc"]


def _parse_env_dict(text: str) -> dict[str, str]:
    """Parse decrypted env text into an ordered dict."""
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
    """Serialise a dict back to .env text."""
    return "\n".join(f"{k}={v}" for k, v in data.items()) + "\n"


def sort_vault(
    vault_path: Path,
    passphrase: str,
    order: SortOrder = "asc",
    group_by_prefix: bool = False,
) -> int:
    """Sort keys in *vault_path* and re-encrypt in place.

    Parameters
    ----------
    vault_path:
        Path to the encrypted vault file.
    passphrase:
        Passphrase used to decrypt/re-encrypt the vault.
    order:
        ``"asc"`` (default) or ``"desc"``.
    group_by_prefix:
        When *True*, keys that share the same ``PREFIX_`` are grouped
        together before sorting within each group.

    Returns
    -------
    int
        Number of keys sorted.
    """
    if not vault_path.exists():
        raise SortError(f"Vault not found: {vault_path}")

    plaintext = unlock(vault_path, passphrase)
    env_dict = _parse_env_dict(plaintext)

    if not env_dict:
        return 0

    reverse = order == "desc"

    if group_by_prefix:
        from itertools import groupby

        def _prefix(key: str) -> str:
            return key.split("_")[0] if "_" in key else key

        sorted_keys = sorted(env_dict.keys(), key=lambda k: (_prefix(k), k), reverse=reverse)
    else:
        sorted_keys = sorted(env_dict.keys(), reverse=reverse)

    sorted_dict = {k: env_dict[k] for k in sorted_keys}
    new_plaintext = _dict_to_env(sorted_dict)
    lock(vault_path, passphrase, new_plaintext)
    return len(sorted_dict)
