"""Tests for envault.snapshot."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from envault.snapshot import (
    SnapshotError,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
    save_snapshot,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / ".env.vault"
    vf.write_bytes(b"encrypted-payload-v1")
    return vf


def test_save_snapshot_creates_file(vault_file: Path) -> None:
    snap = save_snapshot(vault_file)
    assert snap.exists()
    assert snap.suffix == ".vault"


def test_save_snapshot_content_matches(vault_file: Path) -> None:
    snap = save_snapshot(vault_file)
    assert snap.read_bytes() == vault_file.read_bytes()


def test_save_snapshot_with_label(vault_file: Path) -> None:
    snap = save_snapshot(vault_file, label="before-deploy")
    assert "before-deploy" in snap.name


def test_save_snapshot_missing_vault(tmp_path: Path) -> None:
    with pytest.raises(SnapshotError, match="not found"):
        save_snapshot(tmp_path / "missing.vault")


def test_list_snapshots_empty(vault_file: Path) -> None:
    assert list_snapshots(vault_file) == []


def test_list_snapshots_returns_all(vault_file: Path) -> None:
    save_snapshot(vault_file, label="a")
    time.sleep(0.01)
    save_snapshot(vault_file, label="b")
    snaps = list_snapshots(vault_file)
    assert len(snaps) == 2


def test_list_snapshots_sorted_oldest_first(vault_file: Path) -> None:
    s1 = save_snapshot(vault_file, label="first")
    time.sleep(0.01)
    s2 = save_snapshot(vault_file, label="second")
    snaps = list_snapshots(vault_file)
    assert snaps[0].name == s1.name
    assert snaps[1].name == s2.name


def test_restore_snapshot_overwrites_vault(vault_file: Path) -> None:
    snap = save_snapshot(vault_file)
    vault_file.write_bytes(b"new-payload")
    restore_snapshot(snap, vault_file)
    assert vault_file.read_bytes() == b"encrypted-payload-v1"


def test_restore_snapshot_missing_raises(tmp_path: Path, vault_file: Path) -> None:
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(tmp_path / "ghost.vault", vault_file)


def test_delete_snapshot_removes_file(vault_file: Path) -> None:
    snap = save_snapshot(vault_file)
    assert snap.exists()
    delete_snapshot(snap)
    assert not snap.exists()


def test_delete_snapshot_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(SnapshotError, match="not found"):
        delete_snapshot(tmp_path / "no_such.vault")
