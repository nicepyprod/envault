"""Group vault keys by prefix or custom label and operate on groups."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import lock, unlock


class GroupError(Exception):
    """Raised when a group operation fails."""


@dataclass
class KeyGroup:
    name: str
    keys: List[str] = field(default_factory=list)


def _groups_path(vault_path: Path) -> Path:
    return vault_path.with_suffix(".groups.json")


def load_groups(vault_path: Path) -> Dict[str, List[str]]:
    """Return saved groups for *vault_path*; empty dict when none exist."""
    p = _groups_path(vault_path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise GroupError(f"Corrupt groups file: {exc}") from exc
    if not isinstance(data, dict):
        raise GroupError("Groups file must contain a JSON object.")
    return data


def save_groups(vault_path: Path, groups: Dict[str, List[str]]) -> None:
    p = _groups_path(vault_path)
    p.write_text(json.dumps(groups, indent=2))


def add_group(vault_path: Path, name: str, keys: List[str]) -> None:
    """Create or overwrite group *name* with *keys*."""
    if not name.strip():
        raise GroupError("Group name must not be empty.")
    groups = load_groups(vault_path)
    groups[name] = list(keys)
    save_groups(vault_path, groups)


def remove_group(vault_path: Path, name: str) -> None:
    groups = load_groups(vault_path)
    if name not in groups:
        raise GroupError(f"Group '{name}' does not exist.")
    del groups[name]
    save_groups(vault_path, groups)


def extract_group(
    vault_path: Path,
    group_name: str,
    passphrase: str,
    output_path: Optional[Path] = None,
) -> Path:
    """Decrypt vault, keep only keys in *group_name*, write to *output_path*."""
    groups = load_groups(vault_path)
    if group_name not in groups:
        raise GroupError(f"Group '{group_name}' not found.")
    wanted = set(groups[group_name])
    env_text = unlock(vault_path, passphrase)
    filtered_lines = []
    for line in env_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            filtered_lines.append(line)
            continue
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in wanted:
                filtered_lines.append(line)
    result = "\n".join(filtered_lines)
    out = output_path or vault_path.with_stem(vault_path.stem + f"_{group_name}")
    lock(out, result, passphrase)
    return out
