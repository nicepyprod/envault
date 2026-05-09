"""Filter vault keys by prefix, pattern, or tag membership."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import unlock
from envault.tags import load_tags


class FilterError(Exception):
    """Raised when filtering fails."""


def _parse_env_dict(text: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def filter_vault(
    vault_path: Path,
    passphrase: str,
    *,
    prefix: Optional[str] = None,
    pattern: Optional[str] = None,
    tag: Optional[str] = None,
    invert: bool = False,
) -> Dict[str, str]:
    """Return a filtered subset of key/value pairs from a vault.

    At least one of *prefix*, *pattern*, or *tag* must be supplied.
    If *invert* is True the matching logic is negated.
    """
    if prefix is None and pattern is None and tag is None:
        raise FilterError("At least one of prefix, pattern, or tag must be specified.")

    if not vault_path.exists():
        raise FilterError(f"Vault not found: {vault_path}")

    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:
        raise FilterError(f"Failed to decrypt vault: {exc}") from exc

    env = _parse_env_dict(plaintext)

    tagged_keys: Optional[set] = None
    if tag is not None:
        tags_map = load_tags(vault_path)
        tagged_keys = set(tags_map.get(tag, []))

    def _matches(key: str) -> bool:
        if prefix is not None and not key.startswith(prefix):
            return False
        if pattern is not None and not fnmatch.fnmatch(key, pattern):
            return False
        if tagged_keys is not None and key not in tagged_keys:
            return False
        return True

    return {
        k: v for k, v in env.items() if _matches(k) != invert
    }
