"""Tests for envault.env_rename (add_prefix / strip_prefix)."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.env_rename import RenameError, add_prefix, strip_prefix

PASSPHRASE = "test-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    env_text = "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\n"
    lock(path, env_text, PASSPHRASE)
    return path


def _decrypt_keys(vault_path: Path) -> list[str]:
    from envault.vault import unlock
    text = unlock(vault_path, PASSPHRASE)
    keys = []
    for line in text.splitlines():
        line = line.strip()
        if line and "=" in line:
            keys.append(line.split("=", 1)[0])
    return sorted(keys)


# --- add_prefix ---

def test_add_prefix_renames_all_keys(vault_file: Path) -> None:
    pairs = add_prefix(vault_file, PASSPHRASE, "PROD_")
    new_keys = _decrypt_keys(vault_file)
    assert "PROD_DB_HOST" in new_keys
    assert "PROD_DB_PORT" in new_keys
    assert "PROD_APP_NAME" in new_keys
    assert len(pairs) == 3


def test_add_prefix_skips_already_prefixed(vault_file: Path) -> None:
    add_prefix(vault_file, PASSPHRASE, "DB_")
    keys = _decrypt_keys(vault_file)
    # DB_HOST and DB_PORT already start with DB_ — should remain unchanged
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "DB_APP_NAME" in keys


def test_add_prefix_empty_raises(vault_file: Path) -> None:
    with pytest.raises(RenameError, match="empty"):
        add_prefix(vault_file, PASSPHRASE, "")


def test_add_prefix_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(RenameError, match="Vault not found"):
        add_prefix(tmp_path / "missing.vault", PASSPHRASE, "X_")


# --- strip_prefix ---

def test_strip_prefix_removes_matching(vault_file: Path) -> None:
    add_prefix(vault_file, PASSPHRASE, "PROD_")
    pairs = strip_prefix(vault_file, PASSPHRASE, "PROD_")
    keys = _decrypt_keys(vault_file)
    assert "DB_HOST" in keys
    assert "DB_PORT" in keys
    assert "APP_NAME" in keys
    assert all(not k.startswith("PROD_") for k in keys)
    assert len(pairs) == 3


def test_strip_prefix_ignores_non_matching(vault_file: Path) -> None:
    # Only DB_ keys should be stripped; APP_NAME stays
    pairs = strip_prefix(vault_file, PASSPHRASE, "DB_")
    keys = _decrypt_keys(vault_file)
    assert "HOST" in keys
    assert "PORT" in keys
    assert "APP_NAME" in keys


def test_strip_prefix_empty_raises(vault_file: Path) -> None:
    with pytest.raises(RenameError, match="empty"):
        strip_prefix(vault_file, PASSPHRASE, "")


def test_strip_prefix_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(RenameError, match="Vault not found"):
        strip_prefix(tmp_path / "missing.vault", PASSPHRASE, "X_")


def test_strip_prefix_would_produce_empty_key_raises(tmp_path: Path) -> None:
    path = tmp_path / "edge.vault"
    lock(path, "PREFIX=value\n", PASSPHRASE)
    with pytest.raises(RenameError, match="empty key"):
        strip_prefix(path, PASSPHRASE, "PREFIX")
