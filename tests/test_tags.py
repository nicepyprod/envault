"""Tests for envault.tags."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.tags import (
    TagError,
    add_tag,
    keys_for_tag,
    load_tags,
    remove_tag,
    save_tags,
    tags_for_key,
)


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    """Return a dummy vault path (file need not exist for tag tests)."""
    return tmp_path / "secrets.vault"


# ---------------------------------------------------------------------------
# load / save
# ---------------------------------------------------------------------------

def test_load_tags_missing_file(vault_file: Path) -> None:
    assert load_tags(vault_file) == {}


def test_load_tags_corrupt_file(vault_file: Path) -> None:
    sidecar = vault_file.with_suffix(".tags.json")
    sidecar.write_text("not-json", encoding="utf-8")
    with pytest.raises(TagError, match="Corrupt"):
        load_tags(vault_file)


def test_load_tags_wrong_type(vault_file: Path) -> None:
    sidecar = vault_file.with_suffix(".tags.json")
    sidecar.write_text(json.dumps(["a", "b"]), encoding="utf-8")
    with pytest.raises(TagError, match="JSON object"):
        load_tags(vault_file)


def test_save_and_load_roundtrip(vault_file: Path) -> None:
    mapping = {"DB_PASS": ["db", "secret"], "API_KEY": ["api"]}
    save_tags(vault_file, mapping)
    loaded = load_tags(vault_file)
    assert loaded == mapping


# ---------------------------------------------------------------------------
# add_tag
# ---------------------------------------------------------------------------

def test_add_tag_creates_entry(vault_file: Path) -> None:
    add_tag(vault_file, "DB_PASS", "database")
    assert "database" in load_tags(vault_file)["DB_PASS"]


def test_add_tag_idempotent(vault_file: Path) -> None:
    add_tag(vault_file, "DB_PASS", "database")
    add_tag(vault_file, "DB_PASS", "database")
    assert load_tags(vault_file)["DB_PASS"].count("database") == 1


def test_add_multiple_tags(vault_file: Path) -> None:
    add_tag(vault_file, "DB_PASS", "database")
    add_tag(vault_file, "DB_PASS", "secret")
    assert sorted(load_tags(vault_file)["DB_PASS"]) == ["database", "secret"]


# ---------------------------------------------------------------------------
# remove_tag
# ---------------------------------------------------------------------------

def test_remove_tag_success(vault_file: Path) -> None:
    add_tag(vault_file, "DB_PASS", "database")
    remove_tag(vault_file, "DB_PASS", "database")
    assert "DB_PASS" not in load_tags(vault_file)


def test_remove_tag_not_present_raises(vault_file: Path) -> None:
    with pytest.raises(TagError, match="does not have tag"):
        remove_tag(vault_file, "DB_PASS", "nonexistent")


def test_remove_one_tag_keeps_others(vault_file: Path) -> None:
    add_tag(vault_file, "DB_PASS", "database")
    add_tag(vault_file, "DB_PASS", "secret")
    remove_tag(vault_file, "DB_PASS", "database")
    assert load_tags(vault_file)["DB_PASS"] == ["secret"]


# ---------------------------------------------------------------------------
# query helpers
# ---------------------------------------------------------------------------

def test_keys_for_tag(vault_file: Path) -> None:
    add_tag(vault_file, "DB_PASS", "secret")
    add_tag(vault_file, "API_KEY", "secret")
    add_tag(vault_file, "LOG_LEVEL", "config")
    assert keys_for_tag(vault_file, "secret") == ["API_KEY", "DB_PASS"]


def test_keys_for_tag_empty(vault_file: Path) -> None:
    assert keys_for_tag(vault_file, "nonexistent") == []


def test_tags_for_key(vault_file: Path) -> None:
    add_tag(vault_file, "DB_PASS", "secret")
    add_tag(vault_file, "DB_PASS", "database")
    assert tags_for_key(vault_file, "DB_PASS") == ["database", "secret"]


def test_tags_for_key_missing(vault_file: Path) -> None:
    assert tags_for_key(vault_file, "MISSING") == []
