"""Search vault entries by value pattern (grep-style)."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from envault.vault import unlock


class GrepError(Exception):
    """Raised when grep operation fails."""


@dataclass
class GrepMatch:
    key: str
    value: str
    pattern: str

    def __str__(self) -> str:
        return f"{self.key}={self.value}"


def _parse_env_dict(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def grep_vault(
    vault_path: Path,
    passphrase: str,
    pattern: str,
    *,
    search_keys: bool = False,
    case_sensitive: bool = True,
    use_regex: bool = False,
) -> List[GrepMatch]:
    """Return all entries whose value (or key) matches *pattern*.

    Args:
        vault_path: Path to the encrypted vault file.
        passphrase: Decryption passphrase.
        pattern: Glob or regex pattern to match against.
        search_keys: If True, match against keys instead of values.
        case_sensitive: Whether matching is case-sensitive.
        use_regex: Treat *pattern* as a regular expression instead of a glob.

    Returns:
        List of :class:`GrepMatch` objects for every matching entry.

    Raises:
        GrepError: If the vault cannot be read or decrypted.
    """
    if not vault_path.exists():
        raise GrepError(f"Vault not found: {vault_path}")

    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:
        raise GrepError(f"Failed to decrypt vault: {exc}") from exc

    env = _parse_env_dict(plaintext)

    flags = 0 if case_sensitive else re.IGNORECASE

    def _matches(text: str) -> bool:
        if use_regex:
            try:
                return bool(re.search(pattern if case_sensitive else pattern, text, flags))
            except re.error as exc:
                raise GrepError(f"Invalid regex pattern '{pattern}': {exc}") from exc
        needle = pattern if case_sensitive else pattern.lower()
        haystack = text if case_sensitive else text.lower()
        return fnmatch.fnmatch(haystack, needle)

    matches: List[GrepMatch] = []
    for key, value in env.items():
        target = key if search_keys else value
        if _matches(target):
            matches.append(GrepMatch(key=key, value=value, pattern=pattern))

    return matches
