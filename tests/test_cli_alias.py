"""Tests for envault.cli_alias."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.env_alias import add_alias, load_aliases
from envault.cli_alias import (
    cmd_alias_add,
    cmd_alias_list,
    cmd_alias_remove,
    cmd_alias_resolve,
)


def _ns(base_dir: Path, **kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(dir=str(base_dir), **kwargs)


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_cmd_alias_add_success(base_dir: Path) -> None:
    ns = _ns(base_dir, alias="db", key="DATABASE_URL")
    assert cmd_alias_add(ns) == 0
    assert load_aliases(base_dir)["db"] == "DATABASE_URL"


def test_cmd_alias_add_duplicate_returns_1(base_dir: Path) -> None:
    add_alias(base_dir, "db", "DATABASE_URL")
    ns = _ns(base_dir, alias="db", key="OTHER")
    assert cmd_alias_add(ns) == 1


def test_cmd_alias_remove_success(base_dir: Path) -> None:
    add_alias(base_dir, "db", "DATABASE_URL")
    ns = _ns(base_dir, alias="db")
    assert cmd_alias_remove(ns) == 0
    assert "db" not in load_aliases(base_dir)


def test_cmd_alias_remove_missing_returns_1(base_dir: Path) -> None:
    ns = _ns(base_dir, alias="ghost")
    assert cmd_alias_remove(ns) == 1


def test_cmd_alias_list_empty(base_dir: Path, capsys: pytest.CaptureFixture) -> None:
    ns = _ns(base_dir)
    assert cmd_alias_list(ns) == 0
    out = capsys.readouterr().out
    assert "No aliases" in out


def test_cmd_alias_list_shows_entries(base_dir: Path, capsys: pytest.CaptureFixture) -> None:
    add_alias(base_dir, "db", "DATABASE_URL")
    add_alias(base_dir, "s3", "AWS_S3_BUCKET")
    ns = _ns(base_dir)
    assert cmd_alias_list(ns) == 0
    out = capsys.readouterr().out
    assert "db -> DATABASE_URL" in out
    assert "s3 -> AWS_S3_BUCKET" in out


def test_cmd_alias_resolve_success(base_dir: Path, capsys: pytest.CaptureFixture) -> None:
    add_alias(base_dir, "cache", "REDIS_URL")
    ns = _ns(base_dir, alias="cache")
    assert cmd_alias_resolve(ns) == 0
    assert "REDIS_URL" in capsys.readouterr().out


def test_cmd_alias_resolve_missing_returns_1(base_dir: Path) -> None:
    ns = _ns(base_dir, alias="nope")
    assert cmd_alias_resolve(ns) == 1
