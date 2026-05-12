"""Tests for envault.env_group."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock, unlock
from envault.env_group import (
    GroupError,
    add_group,
    extract_group,
    load_groups,
    remove_group,
    save_groups,
)

PASSPHRASE = "s3cret"

ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\nAPP_ENV=prod\n"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.vault"
    lock(p, ENV_CONTENT, PASSPHRASE)
    return p


def test_load_groups_missing_file(vault_file: Path) -> None:
    groups = load_groups(vault_file)
    assert groups == {}


def test_load_groups_corrupt_file(vault_file: Path) -> None:
    groups_path = vault_file.with_suffix(".groups.json")
    groups_path.write_text("not json")
    with pytest.raises(GroupError, match="Corrupt"):
        load_groups(vault_file)


def test_load_groups_wrong_type(vault_file: Path) -> None:
    groups_path = vault_file.with_suffix(".groups.json")
    groups_path.write_text("[1,2,3]")
    with pytest.raises(GroupError, match="JSON object"):
        load_groups(vault_file)


def test_add_group_creates_entry(vault_file: Path) -> None:
    add_group(vault_file, "db", ["DB_HOST", "DB_PORT"])
    groups = load_groups(vault_file)
    assert "db" in groups
    assert groups["db"] == ["DB_HOST", "DB_PORT"]


def test_add_group_empty_name_raises(vault_file: Path) -> None:
    with pytest.raises(GroupError, match="empty"):
        add_group(vault_file, "  ", ["DB_HOST"])


def test_add_group_overwrites_existing(vault_file: Path) -> None:
    add_group(vault_file, "db", ["DB_HOST"])
    add_group(vault_file, "db", ["DB_PORT"])
    groups = load_groups(vault_file)
    assert groups["db"] == ["DB_PORT"]


def test_remove_group_success(vault_file: Path) -> None:
    add_group(vault_file, "db", ["DB_HOST"])
    remove_group(vault_file, "db")
    assert "db" not in load_groups(vault_file)


def test_remove_group_missing_raises(vault_file: Path) -> None:
    with pytest.raises(GroupError, match="does not exist"):
        remove_group(vault_file, "nonexistent")


def test_extract_group_creates_vault(vault_file: Path, tmp_path: Path) -> None:
    add_group(vault_file, "app", ["APP_NAME", "APP_ENV"])
    out = tmp_path / "app.vault"
    result = extract_group(vault_file, "app", PASSPHRASE, out)
    assert result == out
    assert out.exists()


def test_extract_group_contains_only_group_keys(vault_file: Path, tmp_path: Path) -> None:
    add_group(vault_file, "db", ["DB_HOST", "DB_PORT"])
    out = tmp_path / "db.vault"
    extract_group(vault_file, "db", PASSPHRASE, out)
    decrypted = unlock(out, PASSPHRASE)
    keys = [ln.split("=", 1)[0] for ln in decrypted.splitlines() if "=" in ln]
    assert set(keys) == {"DB_HOST", "DB_PORT"}


def test_extract_group_missing_group_raises(vault_file: Path) -> None:
    with pytest.raises(GroupError, match="not found"):
        extract_group(vault_file, "ghost", PASSPHRASE)
