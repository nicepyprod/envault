"""Tests for envault.env_sort."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock, unlock
from envault.env_sort import SortError, sort_vault

_PASSPHRASE = "test-sort-pass"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    plaintext = "ZEBRA=1\nAPPLE=2\nMANGO=3\nBANANA=4\n"
    lock(path, _PASSPHRASE, plaintext)
    return path


def _keys(vault_path: Path) -> list[str]:
    text = unlock(vault_path, _PASSPHRASE)
    return [line.split("=")[0] for line in text.splitlines() if "=" in line]


def test_sort_asc_default(vault_file: Path) -> None:
    count = sort_vault(vault_file, _PASSPHRASE)
    assert count == 4
    assert _keys(vault_file) == ["APPLE", "BANANA", "MANGO", "ZEBRA"]


def test_sort_desc(vault_file: Path) -> None:
    sort_vault(vault_file, _PASSPHRASE, order="desc")
    assert _keys(vault_file) == ["ZEBRA", "MANGO", "BANANA", "APPLE"]


def test_sort_preserves_values(vault_file: Path) -> None:
    sort_vault(vault_file, _PASSPHRASE)
    text = unlock(vault_file, _PASSPHRASE)
    env = dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
    assert env["APPLE"] == "2"
    assert env["ZEBRA"] == "1"


def test_sort_group_by_prefix(tmp_path: Path) -> None:
    path = tmp_path / "grouped.vault"
    plaintext = "DB_HOST=h\nAWS_KEY=k\nDB_PORT=5432\nAWS_SECRET=s\nAPP_NAME=x\n"
    lock(path, _PASSPHRASE, plaintext)
    sort_vault(path, _PASSPHRASE, group_by_prefix=True)
    keys = _keys(path)
    # APP_ group before AWS_ before DB_
    assert keys.index("APP_NAME") < keys.index("AWS_KEY")
    assert keys.index("AWS_KEY") < keys.index("DB_HOST")
    # Within DB_ group, HOST before PORT
    assert keys.index("DB_HOST") < keys.index("DB_PORT")


def test_sort_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(SortError, match="Vault not found"):
        sort_vault(tmp_path / "missing.vault", _PASSPHRASE)


def test_sort_wrong_passphrase_raises(vault_file: Path) -> None:
    with pytest.raises(Exception):
        sort_vault(vault_file, "wrong-passphrase")


def test_sort_empty_vault_returns_zero(tmp_path: Path) -> None:
    path = tmp_path / "empty.vault"
    lock(path, _PASSPHRASE, "")
    count = sort_vault(path, _PASSPHRASE)
    assert count == 0


def test_sort_single_key_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "single.vault"
    lock(path, _PASSPHRASE, "ONLY_KEY=value\n")
    count = sort_vault(path, _PASSPHRASE)
    assert count == 1
    assert _keys(path) == ["ONLY_KEY"]
