"""Tests for envault crypto and vault modules."""

import pytest
from pathlib import Path
from envault.crypto import encrypt, decrypt
from envault.vault import lock, unlock


PASSPHRASE = "super-secret-passphrase-123"
SAMPLE_ENV = "DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc123\n"


# ---------------------------------------------------------------------------
# crypto.py unit tests
# ---------------------------------------------------------------------------

class TestEncryptDecrypt:
    def test_roundtrip(self):
        ciphertext = encrypt(SAMPLE_ENV, PASSPHRASE)
        assert decrypt(ciphertext, PASSPHRASE) == SAMPLE_ENV

    def test_ciphertext_differs_from_plaintext(self):
        ciphertext = encrypt(SAMPLE_ENV, PASSPHRASE)
        assert ciphertext != SAMPLE_ENV

    def test_two_encryptions_differ(self):
        """Random salt/nonce means two calls produce different output."""
        c1 = encrypt(SAMPLE_ENV, PASSPHRASE)
        c2 = encrypt(SAMPLE_ENV, PASSPHRASE)
        assert c1 != c2

    def test_wrong_passphrase_raises(self):
        from cryptography.exceptions import InvalidTag
        ciphertext = encrypt(SAMPLE_ENV, PASSPHRASE)
        with pytest.raises(InvalidTag):
            decrypt(ciphertext, "wrong-passphrase")

    def test_empty_passphrase_still_encrypts(self):
        """crypto layer allows empty passphrase; vault layer rejects it."""
        ciphertext = encrypt(SAMPLE_ENV, "")
        assert decrypt(ciphertext, "") == SAMPLE_ENV


# ---------------------------------------------------------------------------
# vault.py integration tests
# ---------------------------------------------------------------------------

class TestVault:
    def test_lock_creates_vault_file(self, tmp_path):
        env_file = tmp_path / ".env"
        vault_file = tmp_path / ".env.vault"
        env_file.write_text(SAMPLE_ENV)
        lock(env_file, vault_file, PASSPHRASE)
        assert vault_file.exists()

    def test_unlock_restores_plaintext(self, tmp_path):
        env_file = tmp_path / ".env"
        vault_file = tmp_path / ".env.vault"
        env_file.write_text(SAMPLE_ENV)
        lock(env_file, vault_file, PASSPHRASE)
        env_file.unlink()  # remove original
        unlock(vault_file, env_file, PASSPHRASE)
        assert env_file.read_text() == SAMPLE_ENV

    def test_lock_raises_on_missing_env(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            lock(tmp_path / "missing.env", tmp_path / ".env.vault", PASSPHRASE)

    def test_lock_raises_on_empty_passphrase(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(SAMPLE_ENV)
        with pytest.raises(ValueError):
            lock(env_file, tmp_path / ".env.vault", "")

    def test_unlock_raises_on_missing_vault(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            unlock(tmp_path / "missing.vault", tmp_path / ".env", PASSPHRASE)
