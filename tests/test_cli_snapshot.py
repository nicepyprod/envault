"""Tests for envault.cli_snapshot."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.cli_snapshot import (
    cmd_snapshot_delete,
    cmd_snapshot_list,
    cmd_snapshot_restore,
    cmd_snapshot_save,
)
from envault.snapshot import save_snapshot


def _ns(**kwargs) -> argparse.Namespace:  # type: ignore[return]
    defaults = {"vault": "", "label": "", "snapshot": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    vf = tmp_path / ".env.vault"
    vf.write_bytes(b"secret-blob")
    return vf


def test_cmd_snapshot_save_success(vault_file: Path, capsys) -> None:
    ns = _ns(vault=str(vault_file), label="")
    rc = cmd_snapshot_save(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Snapshot saved" in out


def test_cmd_snapshot_save_with_label(vault_file: Path, capsys) -> None:
    ns = _ns(vault=str(vault_file), label="release")
    rc = cmd_snapshot_save(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "release" in out


def test_cmd_snapshot_save_missing_vault(tmp_path: Path, capsys) -> None:
    ns = _ns(vault=str(tmp_path / "nope.vault"), label="")
    rc = cmd_snapshot_save(ns)
    assert rc == 1
    assert "error" in capsys.readouterr().err


def test_cmd_snapshot_list_empty(vault_file: Path, capsys) -> None:
    ns = _ns(vault=str(vault_file))
    rc = cmd_snapshot_list(ns)
    assert rc == 0
    assert "No snapshots" in capsys.readouterr().out


def test_cmd_snapshot_list_shows_entries(vault_file: Path, capsys) -> None:
    save_snapshot(vault_file, label="x")
    ns = _ns(vault=str(vault_file))
    rc = cmd_snapshot_list(ns)
    assert rc == 0
    assert ".vault" in capsys.readouterr().out


def test_cmd_snapshot_restore_success(vault_file: Path, capsys) -> None:
    snap = save_snapshot(vault_file)
    vault_file.write_bytes(b"changed")
    ns = _ns(vault=str(vault_file), snapshot=str(snap))
    rc = cmd_snapshot_restore(ns)
    assert rc == 0
    assert vault_file.read_bytes() == b"secret-blob"


def test_cmd_snapshot_restore_missing(tmp_path: Path, vault_file: Path, capsys) -> None:
    ns = _ns(vault=str(vault_file), snapshot=str(tmp_path / "ghost.vault"))
    rc = cmd_snapshot_restore(ns)
    assert rc == 1
    assert "error" in capsys.readouterr().err


def test_cmd_snapshot_delete_success(vault_file: Path, capsys) -> None:
    snap = save_snapshot(vault_file)
    ns = _ns(snapshot=str(snap))
    rc = cmd_snapshot_delete(ns)
    assert rc == 0
    assert not snap.exists()


def test_cmd_snapshot_delete_missing(tmp_path: Path, capsys) -> None:
    ns = _ns(snapshot=str(tmp_path / "gone.vault"))
    rc = cmd_snapshot_delete(ns)
    assert rc == 1
    assert "error" in capsys.readouterr().err
