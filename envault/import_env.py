"""Import secrets from an external source (JSON or dotenv) into a vault file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from envault.vault import lock


class ImportError(Exception):
    """Raised when an import operation fails."""


def _parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a dotenv-formatted string into a key/value dict."""
    result: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def _parse_json(text: str) -> Dict[str, str]:
    """Parse a JSON object string into a key/value dict (values coerced to str)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object.")
    return {str(k): str(v) for k, v in data.items()}


def import_into_vault(
    source_path: Path,
    vault_path: Path,
    passphrase: str,
    fmt: str = "dotenv",
    merge: bool = False,
) -> int:
    """Import key/value pairs from *source_path* and write an encrypted vault.

    Parameters
    ----------
    source_path:
        Path to the plaintext source file (.env or .json).
    vault_path:
        Destination vault file (will be created or overwritten).
    passphrase:
        Encryption passphrase.
    fmt:
        ``"dotenv"`` (default) or ``"json"``.
    merge:
        If *True* and *vault_path* already exists, merge new keys on top of
        existing ones (existing keys not present in source are preserved).

    Returns
    -------
    int
        Number of key/value pairs written.
    """
    if not source_path.exists():
        raise ImportError(f"Source file not found: {source_path}")

    text = source_path.read_text(encoding="utf-8")

    if fmt == "dotenv":
        incoming = _parse_dotenv(text)
    elif fmt == "json":
        incoming = _parse_json(text)
    else:
        raise ImportError(f"Unknown format: {fmt!r}. Use 'dotenv' or 'json'.")

    if not incoming:
        raise ImportError("No key/value pairs found in source file.")

    if merge and vault_path.exists():
        from envault.vault import unlock
        existing_text = unlock(vault_path, passphrase)
        existing = _parse_dotenv(existing_text)
        existing.update(incoming)
        final = existing
    else:
        final = incoming

    env_lines = "\n".join(f"{k}={v}" for k, v in final.items()) + "\n"
    lock(env_lines, vault_path, passphrase)
    return len(final)
