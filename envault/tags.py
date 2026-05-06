"""Tag management for vault entries — assign, remove, and filter keys by tag."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set


class TagError(Exception):
    """Raised when a tag operation fails."""


def _tags_path(vault_file: Path) -> Path:
    """Return the sidecar .tags.json path for a given vault file."""
    return vault_file.with_suffix(".tags.json")


def load_tags(vault_file: Path) -> Dict[str, List[str]]:
    """Load tag mapping {key: [tag, ...]} from the sidecar file.

    Returns an empty dict if the file does not exist.
    """
    path = _tags_path(vault_file)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TagError(f"Corrupt tags file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise TagError(f"Tags file {path} must contain a JSON object")
    return {k: list(v) for k, v in data.items()}


def save_tags(vault_file: Path, mapping: Dict[str, List[str]]) -> None:
    """Persist tag mapping to the sidecar file."""
    path = _tags_path(vault_file)
    path.write_text(json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8")


def add_tag(vault_file: Path, key: str, tag: str) -> None:
    """Add *tag* to *key*.  Idempotent."""
    mapping = load_tags(vault_file)
    tags: Set[str] = set(mapping.get(key, []))
    tags.add(tag)
    mapping[key] = sorted(tags)
    save_tags(vault_file, mapping)


def remove_tag(vault_file: Path, key: str, tag: str) -> None:
    """Remove *tag* from *key*.  Raises TagError if tag not present."""
    mapping = load_tags(vault_file)
    tags: Set[str] = set(mapping.get(key, []))
    if tag not in tags:
        raise TagError(f"Key '{key}' does not have tag '{tag}'")
    tags.discard(tag)
    if tags:
        mapping[key] = sorted(tags)
    else:
        mapping.pop(key, None)
    save_tags(vault_file, mapping)


def keys_for_tag(vault_file: Path, tag: str) -> List[str]:
    """Return sorted list of keys that carry *tag*."""
    mapping = load_tags(vault_file)
    return sorted(k for k, tags in mapping.items() if tag in tags)


def tags_for_key(vault_file: Path, key: str) -> List[str]:
    """Return sorted list of tags assigned to *key*."""
    mapping = load_tags(vault_file)
    return sorted(mapping.get(key, []))
