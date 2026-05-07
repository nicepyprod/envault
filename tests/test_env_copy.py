"""Tests for envault.env_copy (copy_key / rename_key)."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock, unlock
from envault.env_copy import CopyError, copy_key, rename_key

PASS = "s3cr3t"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / ".env.vault"
    lock(path, "API_KEY=abc123\nDB_PASS=hunter2\n", PASS)
    return path


def _read(vault: Path) -> dict[str, str]:
    text = unlock(vault, PASS)
    result: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


def test_copy_key_adds_destination(vault_file: Path) -> None:
    copy_key(vault_file, PASS, "API_KEY", "API_KEY_BACKUP")
    data = _read(vault_file)
    assert data["API_KEY"] == "abc123"
    assert data["API_KEY_BACKUP"] == "abc123"


def test_copy_key_preserves_other_keys(vault_file: Path) -> None:
    copy_key(vault_file, PASS, "API_KEY", "API_KEY_COPY")
    data = _read(vault_file)
    assert data["DB_PASS"] == "hunter2"


def test_copy_key_missing_src_raises(vault_file: Path) -> None:
    with pytest.raises(CopyError, match="Key not found"):
        copy_key(vault_file, PASS, "MISSING_KEY", "NEW_KEY")


def test_copy_key_same_src_dst_raises(vault_file: Path) -> None:
    with pytest.raises(CopyError, match="must differ"):
        copy_key(vault_file, PASS, "API_KEY", "API_KEY")


def test_copy_key_dst_exists_raises_without_overwrite(vault_file: Path) -> None:
    with pytest.raises(CopyError, match="already exists"):
        copy_key(vault_file, PASS, "API_KEY", "DB_PASS")


def test_copy_key_dst_exists_overwrite(vault_file: Path) -> None:
    copy_key(vault_file, PASS, "API_KEY", "DB_PASS", overwrite=True)
    data = _read(vault_file)
    assert data["DB_PASS"] == "abc123"


def test_copy_key_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(CopyError, match="Vault not found"):
        copy_key(tmp_path / "ghost.vault", PASS, "A", "B")


def test_rename_key_removes_src(vault_file: Path) -> None:
    rename_key(vault_file, PASS, "API_KEY", "API_KEY_NEW")
    data = _read(vault_file)
    assert "API_KEY" not in data
    assert data["API_KEY_NEW"] == "abc123"


def test_rename_key_preserves_other_keys(vault_file: Path) -> None:
    rename_key(vault_file, PASS, "API_KEY", "API_KEY_RENAMED")
    data = _read(vault_file)
    assert data["DB_PASS"] == "hunter2"
