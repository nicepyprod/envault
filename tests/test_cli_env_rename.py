"""Tests for envault.cli_env_rename (cmd_add_prefix / cmd_strip_prefix)."""
from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.vault import lock, unlock
from envault.cli_env_rename import cmd_add_prefix, cmd_strip_prefix

PASSPHRASE = "cli-test-secret"


def _ns(**kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


@pytest.fixture()
def prepared_vault(tmp_path: Path) -> Path:
    path = tmp_path / "env.vault"
    lock(path, "DB_HOST=localhost\nDB_PORT=5432\n", PASSPHRASE)
    return path


def _keys(vault_path: Path) -> list[str]:
    text = unlock(vault_path, PASSPHRASE)
    return sorted(
        line.split("=", 1)[0]
        for line in text.splitlines()
        if line.strip() and "=" in line
    )


# --- cmd_add_prefix ---

def test_cmd_add_prefix_success(prepared_vault: Path, capsys: pytest.CaptureFixture) -> None:
    args = _ns(vault=str(prepared_vault), prefix="PROD_")
    with patch("envault.cli_env_rename._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_add_prefix(args)
    assert rc == 0
    assert "PROD_DB_HOST" in _keys(prepared_vault)
    out = capsys.readouterr().out
    assert "->" in out
    assert "2 key(s) renamed" in out


def test_cmd_add_prefix_missing_vault_returns_1(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    args = _ns(vault=str(tmp_path / "no.vault"), prefix="X_")
    with patch("envault.cli_env_rename._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_add_prefix(args)
    assert rc == 1
    assert "error" in capsys.readouterr().err


# --- cmd_strip_prefix ---

def test_cmd_strip_prefix_success(prepared_vault: Path, capsys: pytest.CaptureFixture) -> None:
    # First add a prefix so we can strip it
    with patch("envault.cli_env_rename._read_passphrase", return_value=PASSPHRASE):
        cmd_add_prefix(_ns(vault=str(prepared_vault), prefix="PROD_"))

    args = _ns(vault=str(prepared_vault), prefix="PROD_")
    with patch("envault.cli_env_rename._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_strip_prefix(args)
    assert rc == 0
    keys = _keys(prepared_vault)
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    out = capsys.readouterr().out
    assert "2 key(s) renamed" in out


def test_cmd_strip_prefix_missing_vault_returns_1(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    args = _ns(vault=str(tmp_path / "no.vault"), prefix="X_")
    with patch("envault.cli_env_rename._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_strip_prefix(args)
    assert rc == 1
    assert "error" in capsys.readouterr().err
