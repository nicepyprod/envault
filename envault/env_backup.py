"""Backup and restore vault files with timestamped copies."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import List


class BackupError(Exception):
    pass


def _backup_dir(vault_path: Path) -> Path:
    return vault_path.parent / ".envault_backups"


def create_backup(vault_path: Path) -> Path:
    """Copy vault_path into the backup directory with a timestamp suffix."""
    vault_path = Path(vault_path)
    if not vault_path.exists():
        raise BackupError(f"Vault not found: {vault_path}")

    backup_dir = _backup_dir(vault_path)
    backup_dir.mkdir(parents=True, exist_ok=True)

    ts = int(time.time())
    stem = vault_path.stem
    suffix = vault_path.suffix or ".vault"
    dest = backup_dir / f"{stem}.{ts}{suffix}"
    shutil.copy2(vault_path, dest)
    return dest


def list_backups(vault_path: Path) -> List[Path]:
    """Return all backups for *vault_path*, sorted oldest-first."""
    vault_path = Path(vault_path)
    backup_dir = _backup_dir(vault_path)
    if not backup_dir.exists():
        return []
    stem = vault_path.stem
    suffix = vault_path.suffix or ".vault"
    pattern = f"{stem}.*{suffix}"
    return sorted(backup_dir.glob(pattern))


def restore_backup(backup_path: Path, vault_path: Path) -> None:
    """Overwrite *vault_path* with the contents of *backup_path*."""
    backup_path = Path(backup_path)
    vault_path = Path(vault_path)
    if not backup_path.exists():
        raise BackupError(f"Backup not found: {backup_path}")
    shutil.copy2(backup_path, vault_path)


def delete_backup(backup_path: Path) -> None:
    """Delete a single backup file."""
    backup_path = Path(backup_path)
    if not backup_path.exists():
        raise BackupError(f"Backup not found: {backup_path}")
    backup_path.unlink()
