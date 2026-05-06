"""Tests for envault.access module."""

from __future__ import annotations

import json
import getpass
import socket
from pathlib import Path

import pytest

from envault.access import (
    AccessError,
    load_rules,
    save_rules,
    add_user,
    remove_user,
    add_host,
    remove_host,
    check_access,
    _access_path,
)


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_rules_missing_file_returns_defaults(base_dir: Path) -> None:
    rules = load_rules(base_dir)
    assert rules == {"allowed_users": [], "allowed_hosts": []}


def test_load_rules_corrupt_file_raises(base_dir: Path) -> None:
    _access_path(base_dir).write_text("not json")
    with pytest.raises(AccessError, match="Corrupt"):
        load_rules(base_dir)


def test_save_and_load_roundtrip(base_dir: Path) -> None:
    rules = {"allowed_users": ["alice"], "allowed_hosts": ["laptop"]}
    save_rules(base_dir, rules)
    loaded = load_rules(base_dir)
    assert loaded == rules


def test_add_user_creates_entry(base_dir: Path) -> None:
    add_user(base_dir, "bob")
    rules = load_rules(base_dir)
    assert "bob" in rules["allowed_users"]


def test_add_user_duplicate_raises(base_dir: Path) -> None:
    add_user(base_dir, "alice")
    with pytest.raises(AccessError, match="already in access list"):
        add_user(base_dir, "alice")


def test_remove_user_removes_entry(base_dir: Path) -> None:
    add_user(base_dir, "carol")
    remove_user(base_dir, "carol")
    rules = load_rules(base_dir)
    assert "carol" not in rules["allowed_users"]


def test_remove_user_missing_raises(base_dir: Path) -> None:
    with pytest.raises(AccessError, match="not in access list"):
        remove_user(base_dir, "nobody")


def test_add_host_creates_entry(base_dir: Path) -> None:
    add_host(base_dir, "server-01")
    rules = load_rules(base_dir)
    assert "server-01" in rules["allowed_hosts"]


def test_remove_host_removes_entry(base_dir: Path) -> None:
    add_host(base_dir, "server-01")
    remove_host(base_dir, "server-01")
    rules = load_rules(base_dir)
    assert "server-01" not in rules["allowed_hosts"]


def test_check_access_unrestricted(base_dir: Path) -> None:
    """Empty lists => no restriction."""
    check_access(base_dir)  # should not raise


def test_check_access_allowed_user(base_dir: Path) -> None:
    current = getpass.getuser()
    add_user(base_dir, current)
    check_access(base_dir)  # should not raise


def test_check_access_denied_user(base_dir: Path) -> None:
    add_user(base_dir, "__nonexistent_user__")
    with pytest.raises(AccessError, match="not allowed"):
        check_access(base_dir)


def test_check_access_allowed_host(base_dir: Path) -> None:
    current = socket.gethostname()
    add_host(base_dir, current)
    check_access(base_dir)  # should not raise


def test_check_access_denied_host(base_dir: Path) -> None:
    add_host(base_dir, "__nonexistent_host__")
    with pytest.raises(AccessError, match="not allowed"):
        check_access(base_dir)
