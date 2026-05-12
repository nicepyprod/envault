"""Tests for envault.env_backup."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.env_backup import (
    BackupError,
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / "secrets.vault"
    vf.write_bytes(b"encrypted-content-abc")
    return vf


def test_create_backup_returns_path(vault_file: Path) -> None:
    dest = create_backup(vault_file)
    assert dest.exists()
    assert dest.suffix == ".vault"


def test_create_backup_content_matches(vault_file: Path) -> None:
    dest = create_backup(vault_file)
    assert dest.read_bytes() == vault_file.read_bytes()


def test_create_backup_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="Vault not found"):
        create_backup(tmp_path / "nonexistent.vault")


def test_list_backups_empty_when_none(vault_file: Path) -> None:
    assert list_backups(vault_file) == []


def test_list_backups_returns_created(vault_file: Path) -> None:
    create_backup(vault_file)
    backups = list_backups(vault_file)
    assert len(backups) == 1


def test_list_backups_sorted_oldest_first(vault_file: Path) -> None:
    b1 = create_backup(vault_file)
    time.sleep(0.01)
    b2 = create_backup(vault_file)
    backups = list_backups(vault_file)
    assert backups[0].name <= backups[1].name
    assert len(backups) == 2


def test_restore_backup_overwrites_vault(vault_file: Path) -> None:
    original = vault_file.read_bytes()
    backup = create_backup(vault_file)
    vault_file.write_bytes(b"modified-content")
    restore_backup(backup, vault_file)
    assert vault_file.read_bytes() == original


def test_restore_backup_missing_raises(tmp_path: Path, vault_file: Path) -> None:
    with pytest.raises(BackupError, match="Backup not found"):
        restore_backup(tmp_path / "ghost.vault", vault_file)


def test_delete_backup_removes_file(vault_file: Path) -> None:
    backup = create_backup(vault_file)
    assert backup.exists()
    delete_backup(backup)
    assert not backup.exists()


def test_delete_backup_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(BackupError, match="Backup not found"):
        delete_backup(tmp_path / "no_such_backup.vault")


def test_list_backups_only_matches_stem(tmp_path: Path) -> None:
    """Backups for a different vault should not appear."""
    vault_a = tmp_path / "alpha.vault"
    vault_b = tmp_path / "beta.vault"
    vault_a.write_bytes(b"aaa")
    vault_b.write_bytes(b"bbb")
    create_backup(vault_a)
    assert list_backups(vault_b) == []
