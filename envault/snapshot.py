"""Snapshot support: save and restore point-in-time copies of a vault."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional

SNAPSHOT_DIR = ".envault_snapshots"


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshot_dir(vault_file: Path) -> Path:
    return vault_file.parent / SNAPSHOT_DIR


def save_snapshot(vault_file: Path, label: Optional[str] = None) -> Path:
    """Copy the current vault file into the snapshot directory.

    Returns the path of the created snapshot file.
    """
    if not vault_file.exists():
        raise SnapshotError(f"Vault file not found: {vault_file}")

    snap_dir = _snapshot_dir(vault_file)
    snap_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())
    suffix = f"_{label}" if label else ""
    snap_name = f"{vault_file.stem}_{timestamp}{suffix}.vault"
    snap_path = snap_dir / snap_name

    snap_path.write_bytes(vault_file.read_bytes())
    return snap_path


def list_snapshots(vault_file: Path) -> List[Path]:
    """Return snapshot paths sorted oldest-first."""
    snap_dir = _snapshot_dir(vault_file)
    if not snap_dir.exists():
        return []
    return sorted(snap_dir.glob("*.vault"))


def restore_snapshot(snapshot_path: Path, vault_file: Path) -> None:
    """Overwrite vault_file with the contents of snapshot_path."""
    if not snapshot_path.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot_path}")
    vault_file.parent.mkdir(parents=True, exist_ok=True)
    vault_file.write_bytes(snapshot_path.read_bytes())


def delete_snapshot(snapshot_path: Path) -> None:
    """Delete a single snapshot file."""
    if not snapshot_path.exists():
        raise SnapshotError(f"Snapshot not found: {snapshot_path}")
    snapshot_path.unlink()
