"""Compare two vault files and report key-level differences."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import unlock


class CompareError(Exception):
    """Raised when vault comparison fails."""


@dataclass
class CompareResult:
    only_in_a: List[str]
    only_in_b: List[str]
    changed: List[str]          # key exists in both but value differs
    unchanged: List[str]        # key exists in both with same value

    @property
    def is_identical(self) -> bool:
        return not (self.only_in_a or self.only_in_b or self.changed)

    def summary(self) -> str:
        lines = []
        for k in sorted(self.only_in_a):
            lines.append(f"  only-in-A : {k}")
        for k in sorted(self.only_in_b):
            lines.append(f"  only-in-B : {k}")
        for k in sorted(self.changed):
            lines.append(f"  changed   : {k}")
        for k in sorted(self.unchanged):
            lines.append(f"  unchanged : {k}")
        return "\n".join(lines) if lines else "  (identical)"


def _load(vault_path: Path, passphrase: str) -> Dict[str, str]:
    """Decrypt a vault and return its key/value pairs."""
    try:
        plaintext = unlock(vault_path, passphrase)
    except Exception as exc:
        raise CompareError(f"Cannot decrypt {vault_path}: {exc}") from exc
    result: Dict[str, str] = {}
    for line in plaintext.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip()
    return result


def compare_vaults(
    vault_a: Path,
    vault_b: Path,
    passphrase_a: str,
    passphrase_b: Optional[str] = None,
) -> CompareResult:
    """Compare two encrypted vaults and return a CompareResult."""
    if passphrase_b is None:
        passphrase_b = passphrase_a

    dict_a = _load(vault_a, passphrase_a)
    dict_b = _load(vault_b, passphrase_b)

    keys_a = set(dict_a)
    keys_b = set(dict_b)

    only_in_a = sorted(keys_a - keys_b)
    only_in_b = sorted(keys_b - keys_a)
    common = keys_a & keys_b
    changed = sorted(k for k in common if dict_a[k] != dict_b[k])
    unchanged = sorted(k for k in common if dict_a[k] == dict_b[k])

    return CompareResult(
        only_in_a=only_in_a,
        only_in_b=only_in_b,
        changed=changed,
        unchanged=unchanged,
    )
