"""Tests for envault.env_pin and envault.cli_pin."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envault.env_pin import (
    PinError,
    apply_pins,
    list_pins,
    load_pins,
    pin_key,
    save_pins,
    unpin_key,
)
from envault.cli_pin import cmd_pin_set, cmd_pin_remove, cmd_pin_list


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "secrets.vault"
    p.write_bytes(b"dummy")
    return p


def _ns(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


# --- load_pins ---

def test_load_pins_missing_file_returns_empty(vault_file):
    assert load_pins(vault_file) == {}


def test_load_pins_corrupt_file_raises(vault_file, tmp_path):
    pin_path = vault_file.with_suffix(".pins.json")
    pin_path.write_text("{bad json")
    with pytest.raises(PinError, match="Corrupt"):
        load_pins(vault_file)


def test_load_pins_wrong_type_raises(vault_file):
    pin_path = vault_file.with_suffix(".pins.json")
    pin_path.write_text(json.dumps(["not", "a", "dict"]))
    with pytest.raises(PinError, match="JSON object"):
        load_pins(vault_file)


# --- pin_key / unpin_key ---

def test_pin_key_stores_value(vault_file):
    pin_key(vault_file, "API_KEY", "secret123")
    assert load_pins(vault_file)["API_KEY"] == "secret123"


def test_pin_key_empty_key_raises(vault_file):
    with pytest.raises(PinError, match="empty"):
        pin_key(vault_file, "", "value")


def test_pin_key_overwrites_existing(vault_file):
    pin_key(vault_file, "X", "old")
    pin_key(vault_file, "X", "new")
    assert load_pins(vault_file)["X"] == "new"


def test_unpin_key_removes_entry(vault_file):
    pin_key(vault_file, "DB_URL", "postgres://")
    unpin_key(vault_file, "DB_URL")
    assert "DB_URL" not in load_pins(vault_file)


def test_unpin_key_not_pinned_raises(vault_file):
    with pytest.raises(PinError, match="not pinned"):
        unpin_key(vault_file, "MISSING")


def test_list_pins_returns_sorted(vault_file):
    pin_key(vault_file, "Z_KEY", "1")
    pin_key(vault_file, "A_KEY", "2")
    assert list_pins(vault_file) == ["A_KEY", "Z_KEY"]


# --- apply_pins ---

def test_apply_pins_enforces_pinned_value(vault_file):
    pin_key(vault_file, "FORCED", "pinned_val")
    result = apply_pins(vault_file, {"FORCED": "other", "FREE": "ok"})
    assert result["FORCED"] == "pinned_val"
    assert result["FREE"] == "ok"


def test_apply_pins_adds_missing_pinned_key(vault_file):
    pin_key(vault_file, "NEW_KEY", "injected")
    result = apply_pins(vault_file, {})
    assert result["NEW_KEY"] == "injected"


# --- CLI ---

def test_cmd_pin_set_success(vault_file):
    rc = cmd_pin_set(_ns(vault=str(vault_file), key="TOKEN", value="abc"))
    assert rc == 0
    assert load_pins(vault_file)["TOKEN"] == "abc"


def test_cmd_pin_remove_success(vault_file):
    pin_key(vault_file, "TOKEN", "abc")
    rc = cmd_pin_remove(_ns(vault=str(vault_file), key="TOKEN"))
    assert rc == 0
    assert "TOKEN" not in load_pins(vault_file)


def test_cmd_pin_remove_missing_returns_1(vault_file):
    rc = cmd_pin_remove(_ns(vault=str(vault_file), key="GHOST"))
    assert rc == 1


def test_cmd_pin_list_empty(vault_file, capsys):
    rc = cmd_pin_list(_ns(vault=str(vault_file)))
    assert rc == 0
    assert "No pinned" in capsys.readouterr().out


def test_cmd_pin_list_shows_entries(vault_file, capsys):
    pin_key(vault_file, "FOO", "bar")
    rc = cmd_pin_list(_ns(vault=str(vault_file)))
    assert rc == 0
    assert "FOO=bar" in capsys.readouterr().out
