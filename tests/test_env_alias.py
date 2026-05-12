"""Tests for envault.env_alias."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.env_alias import (
    AliasError,
    add_alias,
    load_aliases,
    remove_alias,
    resolve_alias,
    save_aliases,
)


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_aliases_missing_file_returns_empty(base_dir: Path) -> None:
    assert load_aliases(base_dir) == {}


def test_load_aliases_corrupt_file_raises(base_dir: Path) -> None:
    (base_dir / ".envault_aliases.json").write_text("not json")
    with pytest.raises(AliasError, match="Corrupt"):
        load_aliases(base_dir)


def test_load_aliases_wrong_type_raises(base_dir: Path) -> None:
    (base_dir / ".envault_aliases.json").write_text(json.dumps(["a", "b"]))
    with pytest.raises(AliasError, match="JSON object"):
        load_aliases(base_dir)


def test_save_and_load_roundtrip(base_dir: Path) -> None:
    data = {"db": "DATABASE_URL", "s3": "AWS_S3_BUCKET"}
    save_aliases(base_dir, data)
    assert load_aliases(base_dir) == data


def test_add_alias_creates_entry(base_dir: Path) -> None:
    add_alias(base_dir, "db", "DATABASE_URL")
    aliases = load_aliases(base_dir)
    assert aliases["db"] == "DATABASE_URL"


def test_add_alias_duplicate_raises(base_dir: Path) -> None:
    add_alias(base_dir, "db", "DATABASE_URL")
    with pytest.raises(AliasError, match="already exists"):
        add_alias(base_dir, "db", "OTHER_KEY")


def test_remove_alias_deletes_entry(base_dir: Path) -> None:
    add_alias(base_dir, "db", "DATABASE_URL")
    remove_alias(base_dir, "db")
    assert "db" not in load_aliases(base_dir)


def test_remove_alias_missing_raises(base_dir: Path) -> None:
    with pytest.raises(AliasError, match="not found"):
        remove_alias(base_dir, "ghost")


def test_resolve_alias_returns_key(base_dir: Path) -> None:
    add_alias(base_dir, "cache", "REDIS_URL")
    assert resolve_alias(base_dir, "cache") == "REDIS_URL"


def test_resolve_alias_missing_raises(base_dir: Path) -> None:
    with pytest.raises(AliasError, match="not found"):
        resolve_alias(base_dir, "missing")
