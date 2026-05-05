"""Tests for envault.rotate (passphrase rotation)."""

import pytest
from pathlib import Path

from envault.vault import lock
from envault.rotate import RotateError, rotate


PLAINTEXT = b"SECRET=hunter2\nAPI_KEY=abc123\n"
OLD_PASS = "old-secret"
NEW_PASS = "new-secret"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_bytes(PLAINTEXT)
    return p


@pytest.fixture()
def vault_file(tmp_path: Path, env_file: Path) -> Path:
    v = tmp_path / ".env.vault"
    lock(env_path=env_file, vault_path=v, passphrase=OLD_PASS)
    return v


def test_rotate_produces_new_vault(vault_file: Path, tmp_path: Path) -> None:
    """After rotation the vault should be decryptable with the new passphrase."""
    env_path = tmp_path / ".env"
    rotate(
        env_path=env_path,
        vault_path=vault_file,
        old_passphrase=OLD_PASS,
        new_passphrase=NEW_PASS,
    )
    # Vault file must still exist
    assert vault_file.exists()


def test_rotate_new_vault_decryptable(vault_file: Path, tmp_path: Path) -> None:
    """Content recovered after rotation must match the original plaintext."""
    from envault.vault import unlock

    env_path = tmp_path / ".env"
    rotate(
        env_path=env_path,
        vault_path=vault_file,
        old_passphrase=OLD_PASS,
        new_passphrase=NEW_PASS,
    )
    out = tmp_path / ".env.out"
    unlock(vault_path=vault_file, env_path=out, passphrase=NEW_PASS)
    assert out.read_bytes() == PLAINTEXT


def test_rotate_old_passphrase_no_longer_works(vault_file: Path, tmp_path: Path) -> None:
    """After rotation the old passphrase must NOT decrypt the vault."""
    from envault.crypto import DecryptionError  # type: ignore[attr-defined]
    from envault.vault import unlock

    env_path = tmp_path / ".env"
    rotate(
        env_path=env_path,
        vault_path=vault_file,
        old_passphrase=OLD_PASS,
        new_passphrase=NEW_PASS,
    )
    out = tmp_path / ".env.out"
    with pytest.raises(Exception):
        unlock(vault_path=vault_file, env_path=out, passphrase=OLD_PASS)


def test_rotate_missing_vault_raises(tmp_path: Path) -> None:
    """RotateError raised when vault file does not exist."""
    with pytest.raises(RotateError, match="Vault file not found"):
        rotate(
            env_path=tmp_path / ".env",
            vault_path=tmp_path / "nonexistent.vault",
            old_passphrase=OLD_PASS,
            new_passphrase=NEW_PASS,
        )


def test_rotate_wrong_old_passphrase_raises(vault_file: Path, tmp_path: Path) -> None:
    """RotateError raised when old passphrase is incorrect."""
    with pytest.raises(Exception):
        rotate(
            env_path=tmp_path / ".env",
            vault_path=vault_file,
            old_passphrase="wrong-pass",
            new_passphrase=NEW_PASS,
        )
