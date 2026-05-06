"""Tests for envault.audit module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.audit import AuditError, clear_log, read_log, record, _audit_path


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_record_creates_log_file(base_dir: Path) -> None:
    record("lock", ".env", success=True, base_dir=base_dir)
    log_path = _audit_path(base_dir)
    assert log_path.exists()


def test_record_appends_valid_json(base_dir: Path) -> None:
    record("lock", ".env", success=True, detail="ok", base_dir=base_dir)
    record("unlock", ".env", success=False, detail="bad pass", base_dir=base_dir)
    lines = _audit_path(base_dir).read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        obj = json.loads(line)
        assert "ts" in obj
        assert "action" in obj
        assert "success" in obj


def test_record_entry_fields(base_dir: Path) -> None:
    record("push", "vault.enc", success=True, detail="synced", base_dir=base_dir)
    entries = read_log(base_dir)
    assert len(entries) == 1
    e = entries[0]
    assert e["action"] == "push"
    assert e["target"] == "vault.enc"
    assert e["success"] is True
    assert e["detail"] == "synced"
    assert "user" in e


def test_read_log_empty_when_no_file(base_dir: Path) -> None:
    entries = read_log(base_dir)
    assert entries == []


def test_read_log_returns_all_entries(base_dir: Path) -> None:
    actions = ["lock", "unlock", "rotate", "pull"]
    for action in actions:
        record(action, ".env", success=True, base_dir=base_dir)
    entries = read_log(base_dir)
    assert len(entries) == len(actions)
    assert [e["action"] for e in entries] == actions


def test_clear_log_removes_file(base_dir: Path) -> None:
    record("lock", ".env", success=True, base_dir=base_dir)
    assert _audit_path(base_dir).exists()
    clear_log(base_dir)
    assert not _audit_path(base_dir).exists()


def test_clear_log_no_error_when_missing(base_dir: Path) -> None:
    # Should not raise even if file does not exist
    clear_log(base_dir)


def test_read_log_raises_on_corrupt_file(base_dir: Path) -> None:
    log_path = _audit_path(base_dir)
    log_path.write_text("not json\n", encoding="utf-8")
    with pytest.raises(AuditError):
        read_log(base_dir)


def test_record_raises_on_unwritable_path(tmp_path: Path) -> None:
    read_only = tmp_path / "ro_dir"
    read_only.mkdir()
    read_only.chmod(0o444)
    with pytest.raises(AuditError):
        record("lock", ".env", success=True, base_dir=read_only)
