"""Tests for envault.env_history."""

from __future__ import annotations

import json
import time
import pytest
from pathlib import Path

from envault.env_history import (
    HistoryError,
    _history_path,
    load_history,
    record_change,
    clear_history,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy-vault-content")
    return p


# ---------------------------------------------------------------------------
# load_history
# ---------------------------------------------------------------------------

def test_load_history_missing_file_returns_empty(vault_file: Path) -> None:
    assert load_history(vault_file) == []


def test_load_history_corrupt_file_raises(vault_file: Path) -> None:
    _history_path(vault_file).write_text("not json", encoding="utf-8")
    with pytest.raises(HistoryError, match="Corrupt"):
        load_history(vault_file)


def test_load_history_wrong_type_raises(vault_file: Path) -> None:
    _history_path(vault_file).write_text(json.dumps({"a": 1}), encoding="utf-8")
    with pytest.raises(HistoryError, match="JSON array"):
        load_history(vault_file)


# ---------------------------------------------------------------------------
# record_change
# ---------------------------------------------------------------------------

def test_record_change_creates_history_file(vault_file: Path) -> None:
    record_change(vault_file, "set", "API_KEY")
    assert _history_path(vault_file).exists()


def test_record_change_entry_fields(vault_file: Path) -> None:
    before = time.time()
    entry = record_change(vault_file, "set", "DB_PASS", actor="ci-bot")
    after = time.time()
    assert entry["operation"] == "set"
    assert entry["key"] == "DB_PASS"
    assert entry["actor"] == "ci-bot"
    assert before <= entry["timestamp"] <= after


def test_record_change_appends_multiple(vault_file: Path) -> None:
    record_change(vault_file, "set", "KEY_A")
    record_change(vault_file, "delete", "KEY_B")
    record_change(vault_file, "rotate", "KEY_A")
    history = load_history(vault_file)
    assert len(history) == 3
    assert [e["operation"] for e in history] == ["set", "delete", "rotate"]


def test_record_change_invalid_operation_raises(vault_file: Path) -> None:
    with pytest.raises(HistoryError, match="Invalid operation"):
        record_change(vault_file, "explode", "KEY")


def test_record_change_missing_vault_raises(tmp_path: Path) -> None:
    missing = tmp_path / "ghost.vault"
    with pytest.raises(HistoryError, match="not found"):
        record_change(missing, "set", "KEY")


# ---------------------------------------------------------------------------
# clear_history
# ---------------------------------------------------------------------------

def test_clear_history_removes_file(vault_file: Path) -> None:
    record_change(vault_file, "set", "X")
    assert _history_path(vault_file).exists()
    clear_history(vault_file)
    assert not _history_path(vault_file).exists()


def test_clear_history_no_file_is_noop(vault_file: Path) -> None:
    # Should not raise even when no history file exists
    clear_history(vault_file)
