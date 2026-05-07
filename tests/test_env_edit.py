"""Tests for envault.env_edit — set_key, delete_key, get_key."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.env_edit import EditError, set_key, delete_key, get_key


PASSPHRASE = "test-passphrase-42"
_INITIAL_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET=abc123\n"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / "secrets.env"
    vault = tmp_path / "secrets.vault"
    env.write_text(_INITIAL_ENV)
    lock(env, vault, PASSPHRASE)
    env.unlink()
    return vault


# ---------------------------------------------------------------------------
# set_key
# ---------------------------------------------------------------------------

def test_set_key_adds_new_key(vault_file: Path) -> None:
    set_key(vault_file, PASSPHRASE, "NEW_KEY", "new_value")
    result = get_key(vault_file, PASSPHRASE, "NEW_KEY")
    assert result == "new_value"


def test_set_key_overwrites_existing_key(vault_file: Path) -> None:
    set_key(vault_file, PASSPHRASE, "DB_HOST", "remotehost")
    result = get_key(vault_file, PASSPHRASE, "DB_HOST")
    assert result == "remotehost"


def test_set_key_preserves_other_keys(vault_file: Path) -> None:
    set_key(vault_file, PASSPHRASE, "DB_PORT", "9999")
    assert get_key(vault_file, PASSPHRASE, "SECRET") == "abc123"
    assert get_key(vault_file, PASSPHRASE, "DB_HOST") == "localhost"


def test_set_key_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(EditError, match="Vault not found"):
        set_key(tmp_path / "no.vault", PASSPHRASE, "K", "V")


def test_set_key_empty_key_raises(vault_file: Path) -> None:
    with pytest.raises(EditError, match="Key must not be empty"):
        set_key(vault_file, PASSPHRASE, "", "value")


def test_set_key_no_leftover_env_file(vault_file: Path) -> None:
    set_key(vault_file, PASSPHRASE, "X", "1")
    assert not vault_file.with_suffix(".env").exists()


# ---------------------------------------------------------------------------
# delete_key
# ---------------------------------------------------------------------------

def test_delete_key_removes_existing_key(vault_file: Path) -> None:
    existed = delete_key(vault_file, PASSPHRASE, "SECRET")
    assert existed is True
    assert get_key(vault_file, PASSPHRASE, "SECRET") is None


def test_delete_key_returns_false_for_missing_key(vault_file: Path) -> None:
    existed = delete_key(vault_file, PASSPHRASE, "DOES_NOT_EXIST")
    assert existed is False


def test_delete_key_preserves_other_keys(vault_file: Path) -> None:
    delete_key(vault_file, PASSPHRASE, "DB_PORT")
    assert get_key(vault_file, PASSPHRASE, "DB_HOST") == "localhost"
    assert get_key(vault_file, PASSPHRASE, "SECRET") == "abc123"


def test_delete_key_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(EditError, match="Vault not found"):
        delete_key(tmp_path / "no.vault", PASSPHRASE, "K")


# ---------------------------------------------------------------------------
# get_key
# ---------------------------------------------------------------------------

def test_get_key_returns_value(vault_file: Path) -> None:
    assert get_key(vault_file, PASSPHRASE, "DB_HOST") == "localhost"


def test_get_key_returns_none_for_absent_key(vault_file: Path) -> None:
    assert get_key(vault_file, PASSPHRASE, "NOPE") is None


def test_get_key_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(EditError, match="Vault not found"):
        get_key(tmp_path / "no.vault", PASSPHRASE, "K")
