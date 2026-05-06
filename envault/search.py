"""Search for keys across a vault file."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .vault import unlock


class SearchError(Exception):
    """Raised when a search operation fails."""


@dataclass
class SearchResult:
    key: str
    value: str
    matched_by: str  # 'key', 'value', or 'both'


def search_vault(
    vault_path: Path,
    passphrase: str,
    pattern: str,
    search_keys: bool = True,
    search_values: bool = False,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Decrypt *vault_path* and return entries whose key/value match *pattern*.

    *pattern* supports Unix shell-style wildcards (fnmatch).
    """
    if not vault_path.exists():
        raise SearchError(f"Vault file not found: {vault_path}")

    if not search_keys and not search_values:
        raise SearchError("At least one of search_keys or search_values must be True.")

    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:
        raise SearchError(f"Failed to decrypt vault: {exc}") from exc

    def _match(text: str) -> bool:
        if not case_sensitive:
            return fnmatch.fnmatch(text.lower(), pattern.lower())
        return fnmatch.fnmatch(text, pattern)

    results: List[SearchResult] = []
    for line in plaintext.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        key_match = search_keys and _match(key)
        val_match = search_values and _match(value)

        if key_match and val_match:
            results.append(SearchResult(key=key, value=value, matched_by="both"))
        elif key_match:
            results.append(SearchResult(key=key, value=value, matched_by="key"))
        elif val_match:
            results.append(SearchResult(key=key, value=value, matched_by="value"))

    return results
