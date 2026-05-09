"""Validate that a .env file or vault contains required keys."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.vault import unlock


class ValidateError(Exception):
    """Raised when validation cannot be performed."""


@dataclass
class ValidationResult:
    missing: List[str] = field(default_factory=list)
    invalid_format: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.missing and not self.invalid_format

    def __str__(self) -> str:
        lines = []
        for k in self.missing:
            lines.append(f"  MISSING       {k}")
        for k in self.invalid_format:
            lines.append(f"  INVALID_FMT   {k}")
        return "\n".join(lines) if lines else "  All checks passed."


_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _parse_env_dict(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        result[key.strip()] = value.strip().strip('"\'')
    return result


def validate_vault(
    vault_path: Path,
    passphrase: str,
    required_keys: List[str],
    pattern: Optional[str] = None,
) -> ValidationResult:
    """Decrypt *vault_path* and check that *required_keys* are present.

    If *pattern* is given (a regex string), each value for the required keys
    must also match that pattern.
    """
    if not vault_path.exists():
        raise ValidateError(f"Vault not found: {vault_path}")

    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:
        raise ValidateError(f"Failed to decrypt vault: {exc}") from exc

    env = _parse_env_dict(plaintext)
    result = ValidationResult()

    compiled = re.compile(pattern) if pattern else None

    for key in required_keys:
        if key not in env:
            result.missing.append(key)
        elif compiled and not compiled.search(env[key]):
            result.invalid_format.append(key)

    return result
