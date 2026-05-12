"""Alias management: map short alias names to vault keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class AliasError(Exception):
    pass


def _alias_path(base_dir: Path) -> Path:
    return base_dir / ".envault_aliases.json"


def load_aliases(base_dir: Path) -> Dict[str, str]:
    """Return mapping of alias -> vault key."""
    path = _alias_path(base_dir)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise AliasError(f"Corrupt alias file: {exc}") from exc
    if not isinstance(data, dict):
        raise AliasError("Alias file must contain a JSON object.")
    return data


def save_aliases(base_dir: Path, aliases: Dict[str, str]) -> None:
    path = _alias_path(base_dir)
    path.write_text(json.dumps(aliases, indent=2))


def add_alias(base_dir: Path, alias: str, key: str) -> None:
    """Register *alias* pointing to vault *key*."""
    aliases = load_aliases(base_dir)
    if alias in aliases:
        raise AliasError(f"Alias '{alias}' already exists (points to '{aliases[alias]}').")
    aliases[alias] = key
    save_aliases(base_dir, aliases)


def remove_alias(base_dir: Path, alias: str) -> None:
    aliases = load_aliases(base_dir)
    if alias not in aliases:
        raise AliasError(f"Alias '{alias}' not found.")
    del aliases[alias]
    save_aliases(base_dir, aliases)


def resolve_alias(base_dir: Path, alias: str) -> str:
    """Return the vault key that *alias* maps to."""
    aliases = load_aliases(base_dir)
    if alias not in aliases:
        raise AliasError(f"Alias '{alias}' not found.")
    return aliases[alias]
