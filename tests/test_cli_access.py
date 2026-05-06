"""Tests for envault.cli_access CLI commands."""

from __future__ import annotations

import argparse
import getpass
import socket
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_access import (
    cmd_access_add,
    cmd_access_remove,
    cmd_access_list,
    cmd_access_check,
)
from envault.access import add_user, add_host, load_rules


def _ns(base_dir: Path, **kwargs) -> argparse.Namespace:
    defaults = {"dir": str(base_dir)}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_cmd_access_add_user_success(base_dir: Path) -> None:
    ns = _ns(base_dir, kind="user", name="alice")
    assert cmd_access_add(ns) == 0
    assert "alice" in load_rules(base_dir)["allowed_users"]


def test_cmd_access_add_host_success(base_dir: Path) -> None:
    ns = _ns(base_dir, kind="host", name="myserver")
    assert cmd_access_add(ns) == 0
    assert "myserver" in load_rules(base_dir)["allowed_hosts"]


def test_cmd_access_add_duplicate_returns_1(base_dir: Path) -> None:
    add_user(base_dir, "alice")
    ns = _ns(base_dir, kind="user", name="alice")
    assert cmd_access_add(ns) == 1


def test_cmd_access_remove_user_success(base_dir: Path) -> None:
    add_user(base_dir, "bob")
    ns = _ns(base_dir, kind="user", name="bob")
    assert cmd_access_remove(ns) == 0
    assert "bob" not in load_rules(base_dir)["allowed_users"]


def test_cmd_access_remove_missing_returns_1(base_dir: Path) -> None:
    ns = _ns(base_dir, kind="user", name="ghost")
    assert cmd_access_remove(ns) == 1


def test_cmd_access_list_prints_rules(base_dir: Path, capsys) -> None:
    add_user(base_dir, "carol")
    add_host(base_dir, "laptop")
    ns = _ns(base_dir)
    assert cmd_access_list(ns) == 0
    out = capsys.readouterr().out
    assert "carol" in out
    assert "laptop" in out


def test_cmd_access_list_empty_shows_any(base_dir: Path, capsys) -> None:
    ns = _ns(base_dir)
    assert cmd_access_list(ns) == 0
    out = capsys.readouterr().out
    assert "(any)" in out


def test_cmd_access_check_unrestricted(base_dir: Path) -> None:
    ns = _ns(base_dir)
    assert cmd_access_check(ns) == 0


def test_cmd_access_check_allowed_user(base_dir: Path) -> None:
    add_user(base_dir, getpass.getuser())
    ns = _ns(base_dir)
    assert cmd_access_check(ns) == 0


def test_cmd_access_check_denied_returns_1(base_dir: Path) -> None:
    add_user(base_dir, "__nobody__")
    ns = _ns(base_dir)
    assert cmd_access_check(ns) == 1
