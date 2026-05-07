"""Track a change history log per vault file (key-level changes)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Dict, Any


class HistoryError(Exception):
    """Raised when history operations fail."""


def _history_path(vault_path: Path) -> Path:
    """Return the history file path alongside the vault file."""
    return vault_path.with_suffix(".history.json")


def load_history(vault_path: Path) -> List[Dict[str, Any]]:
    """Load the history log for a vault. Returns empty list if none exists."""
    path = _history_path(vault_path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HistoryError(f"Corrupt history file: {exc}") from exc
    if not isinstance(data, list):
        raise HistoryError("History file must contain a JSON array.")
    return data


def record_change(
    vault_path: Path,
    operation: str,
    key: str,
    actor: str = "local",
) -> Dict[str, Any]:
    """Append a change entry to the history log.

    Parameters
    ----------
    vault_path: path to the .vault file
    operation:  one of 'set', 'delete', 'rotate', 'import'
    key:        the env key that was affected
    actor:      free-form identifier for who made the change
    """
    valid_ops = {"set", "delete", "rotate", "import"}
    if operation not in valid_ops:
        raise HistoryError(
            f"Invalid operation '{operation}'. Must be one of {valid_ops}."
        )
    if not vault_path.exists():
        raise HistoryError(f"Vault file not found: {vault_path}")

    entry: Dict[str, Any] = {
        "timestamp": time.time(),
        "operation": operation,
        "key": key,
        "actor": actor,
    }
    history = load_history(vault_path)
    history.append(entry)
    _history_path(vault_path).write_text(
        json.dumps(history, indent=2), encoding="utf-8"
    )
    return entry


def clear_history(vault_path: Path) -> None:
    """Delete the history log for a vault."""
    path = _history_path(vault_path)
    if path.exists():
        path.unlink()
