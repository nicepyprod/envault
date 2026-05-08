"""Merge two vault files, with configurable conflict resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal

from envault.vault import lock, unlock


class MergeError(Exception):
    """Raised when a merge operation fails."""


ConflictStrategy = Literal["ours", "theirs", "error"]


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)


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


def _dict_to_env(d: Dict[str, str]) -> str:
    return "\n".join(f"{k}={v}" for k, v in sorted(d.items())) + "\n"


def merge_vaults(
    base_vault: Path,
    base_passphrase: str,
    other_vault: Path,
    other_passphrase: str,
    output_vault: Path,
    output_passphrase: str,
    strategy: ConflictStrategy = "error",
) -> MergeResult:
    """Merge *other_vault* into *base_vault* and write to *output_vault*."""
    if not base_vault.exists():
        raise MergeError(f"Base vault not found: {base_vault}")
    if not other_vault.exists():
        raise MergeError(f"Other vault not found: {other_vault}")

    base_text = unlock(base_vault, base_passphrase)
    other_text = unlock(other_vault, other_passphrase)

    base_dict = _parse_env_dict(base_text)
    other_dict = _parse_env_dict(other_text)

    result = MergeResult(merged=dict(base_dict))

    for key, value in other_dict.items():
        if key not in base_dict:
            result.merged[key] = value
            result.added.append(key)
        elif base_dict[key] != value:
            result.conflicts.append(key)
            if strategy == "error":
                raise MergeError(
                    f"Conflict on key '{key}': base={base_dict[key]!r}, "
                    f"other={value!r}. Use --strategy ours|theirs to resolve."
                )
            elif strategy == "theirs":
                result.merged[key] = value
                result.overwritten.append(key)
            # strategy == "ours": keep base value, already present

    env_text = _dict_to_env(result.merged)
    lock(output_vault, env_text, output_passphrase)
    return result
