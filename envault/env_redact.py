"""env_redact.py – mask sensitive values in vault output."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import unlock

# Keys whose values should always be redacted (case-insensitive patterns)
_DEFAULT_PATTERNS: List[str] = [
    r".*secret.*",
    r".*password.*",
    r".*passwd.*",
    r".*token.*",
    r".*api[_-]?key.*",
    r".*private[_-]?key.*",
    r".*credentials.*",
]

REDACT_PLACEHOLDER = "***REDACTED***"


class RedactError(Exception):
    """Raised when redaction cannot be performed."""


@dataclass
class RedactResult:
    entries: Dict[str, str] = field(default_factory=dict)
    redacted_keys: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def redacted_count(self) -> int:
        return len(self.redacted_keys)


def _should_redact(key: str, patterns: List[str]) -> bool:
    key_lower = key.lower()
    return any(re.fullmatch(p, key_lower) for p in patterns)


def _parse_env_dict(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"\'')
        if k:
            result[k] = v
    return result


def redact_vault(
    vault_path: Path,
    passphrase: str,
    extra_patterns: Optional[List[str]] = None,
    show_keys: Optional[List[str]] = None,
) -> RedactResult:
    """Decrypt *vault_path* and return a RedactResult with sensitive values masked.

    Args:
        vault_path:      Path to the encrypted vault file.
        passphrase:      Passphrase used to decrypt the vault.
        extra_patterns:  Additional regex patterns (case-insensitive full-match)
                         for keys that should be redacted.
        show_keys:       Explicit list of keys to *never* redact, overriding patterns.
    """
    if not vault_path.exists():
        raise RedactError(f"Vault not found: {vault_path}")

    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:  # noqa: BLE001
        raise RedactError(f"Failed to decrypt vault: {exc}") from exc

    env = _parse_env_dict(plaintext)
    patterns = _DEFAULT_PATTERNS + (extra_patterns or [])
    show_set = set(show_keys or [])

    result = RedactResult()
    for key, value in env.items():
        if key not in show_set and _should_redact(key, patterns):
            result.entries[key] = REDACT_PLACEHOLDER
            result.redacted_keys.append(key)
        else:
            result.entries[key] = value

    return result
