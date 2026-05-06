"""TTL (time-to-live) support for vault secrets.

Allows setting an expiry timestamp on a vault file so that
unlock/export operations warn or fail when the vault has expired.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

TTL_SUFFIX = ".ttl"


class TTLError(Exception):
    """Raised for TTL-related failures."""


def _ttl_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(vault_path.suffix + TTL_SUFFIX)


def set_ttl(vault_path: Path, seconds: int) -> float:
    """Record an expiry time *seconds* from now next to *vault_path*.

    Returns the absolute expiry timestamp (Unix epoch).
    """
    if seconds <= 0:
        raise TTLError("TTL must be a positive integer number of seconds.")
    expires_at = time.time() + seconds
    ttl_file = _ttl_path(vault_path)
    ttl_file.write_text(json.dumps({"expires_at": expires_at}), encoding="utf-8")
    return expires_at


def get_ttl(vault_path: Path) -> Optional[float]:
    """Return the expiry timestamp for *vault_path*, or None if not set."""
    ttl_file = _ttl_path(vault_path)
    if not ttl_file.exists():
        return None
    try:
        data = json.loads(ttl_file.read_text(encoding="utf-8"))
        return float(data["expires_at"])
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        raise TTLError(f"Corrupt TTL file: {ttl_file}") from exc


def clear_ttl(vault_path: Path) -> bool:
    """Remove the TTL file for *vault_path*. Returns True if one existed."""
    ttl_file = _ttl_path(vault_path)
    if ttl_file.exists():
        ttl_file.unlink()
        return True
    return False


def check_ttl(vault_path: Path) -> None:
    """Raise *TTLError* if the vault has an expired TTL.

    Does nothing if no TTL is set or if the vault is still within its
    valid window.
    """
    expires_at = get_ttl(vault_path)
    if expires_at is None:
        return
    remaining = expires_at - time.time()
    if remaining <= 0:
        raise TTLError(
            f"Vault '{vault_path}' has expired "
            f"({abs(remaining):.0f}s ago). Re-lock to refresh."
        )


def remaining_seconds(vault_path: Path) -> Optional[float]:
    """Return seconds until expiry, or None if no TTL is set.

    Returns a negative value if already expired.
    """
    expires_at = get_ttl(vault_path)
    if expires_at is None:
        return None
    return expires_at - time.time()
