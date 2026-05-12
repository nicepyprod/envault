"""Type-casting utilities for vault key values."""
from __future__ import annotations

import json
from typing import Any

from envault.vault import unlock

SUPPORTED_TYPES = ("str", "int", "float", "bool", "json")


class CastError(Exception):
    """Raised when a cast operation fails."""


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


def cast_value(value: str, to_type: str) -> Any:
    """Cast *value* to *to_type*. Raises CastError on failure."""
    if to_type not in SUPPORTED_TYPES:
        raise CastError(
            f"Unsupported type '{to_type}'. Choose from: {', '.join(SUPPORTED_TYPES)}"
        )
    try:
        if to_type == "str":
            return value
        if to_type == "int":
            return int(value)
        if to_type == "float":
            return float(value)
        if to_type == "bool":
            if value.lower() in ("1", "true", "yes", "on"):
                return True
            if value.lower() in ("0", "false", "no", "off"):
                return False
            raise ValueError(f"Cannot interpret '{value}' as bool")
        if to_type == "json":
            return json.loads(value)
    except (ValueError, json.JSONDecodeError) as exc:
        raise CastError(f"Cannot cast '{value}' to {to_type}: {exc}") from exc


def cast_key(vault_path: str, passphrase: str, key: str, to_type: str) -> Any:
    """Decrypt *vault_path* and return the value of *key* cast to *to_type*."""
    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:
        raise CastError(f"Failed to unlock vault: {exc}") from exc

    env = _parse_env_dict(plaintext)
    if key not in env:
        raise CastError(f"Key '{key}' not found in vault")

    return cast_value(env[key], to_type)
