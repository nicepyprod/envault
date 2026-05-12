"""Tests for envault.cli_group."""

from __future__ import annotations

import argparse
import pytest
from pathlib import Path
from unittest.mock import patch

from envault.vault import lock
from envault.env_group import add_group
from envault.cli_group import (
    cmd_group_add,
    cmd_group_extract,
    cmd_group_list,
    cmd_group_remove,
)

PASSPHRASE = "s3cret"
ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n"


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"vault": "", "name": "", "keys": "", "output": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    lock(p, ENV_CONTENT, PASSPHRASE)
    return p


def test_cmd_group_add_success(vault_file: Path) -> None:
    ns = _ns(vault=str(vault_file), name="db", keys="DB_HOST,DB_PORT")
    assert cmd_group_add(ns) == 0


def test_cmd_group_add_empty_keys_returns_1(vault_file: Path) -> None:
    ns = _ns(vault=str(vault_file), name="db", keys="  ,  ")
    assert cmd_group_add(ns) == 1


def test_cmd_group_remove_success(vault_file: Path) -> None:
    add_group(vault_file, "db", ["DB_HOST"])
    ns = _ns(vault=str(vault_file), name="db")
    assert cmd_group_remove(ns) == 0


def test_cmd_group_remove_missing_returns_1(vault_file: Path) -> None:
    ns = _ns(vault=str(vault_file), name="ghost")
    assert cmd_group_remove(ns) == 1


def test_cmd_group_list_empty(vault_file: Path, capsys) -> None:
    ns = _ns(vault=str(vault_file))
    rc = cmd_group_list(ns)
    assert rc == 0
    assert "No groups" in capsys.readouterr().out


def test_cmd_group_list_shows_groups(vault_file: Path, capsys) -> None:
    add_group(vault_file, "db", ["DB_HOST", "DB_PORT"])
    ns = _ns(vault=str(vault_file))
    rc = cmd_group_list(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "db" in out
    assert "DB_HOST" in out


def test_cmd_group_extract_success(vault_file: Path, tmp_path: Path) -> None:
    add_group(vault_file, "app", ["APP_NAME"])
    out = str(tmp_path / "app.vault")
    ns = _ns(vault=str(vault_file), name="app", output=out)
    with patch("envault.cli_group._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_group_extract(ns)
    assert rc == 0
    assert Path(out).exists()


def test_cmd_group_extract_missing_group_returns_1(vault_file: Path) -> None:
    ns = _ns(vault=str(vault_file), name="ghost", output=None)
    with patch("envault.cli_group._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_group_extract(ns)
    assert rc == 1
