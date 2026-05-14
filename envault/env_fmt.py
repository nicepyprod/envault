"""Format (pretty-print / normalize) a vault's env contents in-place."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from envault.crypto import decrypt, encrypt


class FmtError(Exception):
    """Raised when formatting fails."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_env_pairs(text: str) -> List[Tuple[str, str]]:
    """Return (key, value) pairs preserving order; skip comments and blanks."""
    pairs: List[Tuple[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            pairs.append((key, value))
    return pairs


def _pairs_to_env(pairs: List[Tuple[str, str]], *, quote_values: bool = False) -> str:
    """Serialise key/value pairs back to .env text."""
    lines: List[str] = []
    for key, value in pairs:
        if quote_values or " " in value or not value:
            lines.append(f'{key}="{value}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def format_vault(
    vault_path: Path,
    passphrase: str,
    *,
    sort_keys: bool = False,
    quote_values: bool = False,
) -> int:
    """Decrypt *vault_path*, normalise formatting, re-encrypt in-place.

    Returns the number of key/value pairs written.

    Raises:
        FmtError: if the vault file is missing or the passphrase is wrong.
    """
    if not vault_path.exists():
        raise FmtError(f"Vault not found: {vault_path}")

    try:
        plaintext = decrypt(vault_path.read_bytes(), passphrase)
    except Exception as exc:
        raise FmtError(f"Failed to decrypt vault: {exc}") from exc

    pairs = _parse_env_pairs(plaintext)

    if sort_keys:
        pairs.sort(key=lambda kv: kv[0].lower())

    formatted = _pairs_to_env(pairs, quote_values=quote_values)

    try:
        vault_path.write_bytes(encrypt(formatted, passphrase))
    except Exception as exc:
        raise FmtError(f"Failed to re-encrypt vault: {exc}") from exc

    return len(pairs)
