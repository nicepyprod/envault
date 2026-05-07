"""Watch a .env file for changes and report when keys are added, removed, or modified."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable problem."""


@dataclass
class WatchEvent:
    kind: str          # 'added' | 'removed' | 'changed' | 'unchanged'
    key: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None


def _parse_env(path: Path) -> Dict[str, str]:
    """Parse a plain .env file into a dict (no crypto — for local dev watching)."""
    result: Dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip('"\'')
    return result


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_changes(
    old: Dict[str, str], new: Dict[str, str]
) -> list[WatchEvent]:
    """Return a list of WatchEvents describing what changed between two env snapshots."""
    events: list[WatchEvent] = []
    all_keys = set(old) | set(new)
    for key in sorted(all_keys):
        if key in old and key not in new:
            events.append(WatchEvent("removed", key, old_value=old[key]))
        elif key not in old and key in new:
            events.append(WatchEvent("added", key, new_value=new[key]))
        elif old[key] != new[key]:
            events.append(WatchEvent("changed", key, old_value=old[key], new_value=new[key]))
    return events


def watch(
    env_path: Path,
    callback: Callable[[list[WatchEvent]], None],
    interval: float = 1.0,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *env_path* every *interval* seconds and invoke *callback* on changes.

    Raises WatchError if the file disappears after the first read.
    Stops after *max_iterations* polls when set (useful for testing).
    """
    if not env_path.exists():
        raise WatchError(f"File not found: {env_path}")

    current_hash = _file_hash(env_path)
    current_env = _parse_env(env_path)
    iterations = 0

    while True:
        time.sleep(interval)
        iterations += 1

        if not env_path.exists():
            raise WatchError(f"Watched file disappeared: {env_path}")

        new_hash = _file_hash(env_path)
        if new_hash != current_hash:
            new_env = _parse_env(env_path)
            events = compute_changes(current_env, new_env)
            if events:
                callback(events)
            current_hash = new_hash
            current_env = new_env

        if max_iterations is not None and iterations >= max_iterations:
            break
