"""Tests for envault.env_grep."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.env_grep import GrepError, GrepMatch, grep_vault

PASSPHRASE = "grep-test-secret"

ENV_CONTENT = """DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=s3cr3t
APP_ENV=production
APP_SECRET=topsecret
DEBUG=false
"""


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    vault = tmp_path / ".env.vault"
    env.write_text(ENV_CONTENT)
    lock(env, vault, PASSPHRASE)
    return vault


def test_grep_value_exact_glob(vault_file: Path) -> None:
    matches = grep_vault(vault_file, PASSPHRASE, "localhost")
    assert len(matches) == 1
    assert matches[0].key == "DB_HOST"


def test_grep_value_wildcard(vault_file: Path) -> None:
    matches = grep_vault(vault_file, PASSPHRASE, "*secret*")
    keys = {m.key for m in matches}
    assert "DB_PASSWORD" not in keys
    assert "APP_SECRET" in keys


def test_grep_key_search(vault_file: Path) -> None:
    matches = grep_vault(vault_file, PASSPHRASE, "DB_*", search_keys=True)
    keys = {m.key for m in matches}
    assert keys == {"DB_HOST", "DB_PORT", "DB_PASSWORD"}


def test_grep_case_insensitive(vault_file: Path) -> None:
    matches = grep_vault(vault_file, PASSPHRASE, "LOCALHOST", case_sensitive=False)
    assert len(matches) == 1
    assert matches[0].key == "DB_HOST"


def test_grep_case_sensitive_no_match(vault_file: Path) -> None:
    matches = grep_vault(vault_file, PASSPHRASE, "LOCALHOST", case_sensitive=True)
    assert matches == []


def test_grep_regex_pattern(vault_file: Path) -> None:
    matches = grep_vault(vault_file, PASSPHRASE, r"^\d+$", use_regex=True)
    assert len(matches) == 1
    assert matches[0].key == "DB_PORT"


def test_grep_regex_invalid_raises(vault_file: Path) -> None:
    with pytest.raises(GrepError, match="Invalid regex"):
        grep_vault(vault_file, PASSPHRASE, r"[unclosed", use_regex=True)


def test_grep_no_matches_returns_empty(vault_file: Path) -> None:
    matches = grep_vault(vault_file, PASSPHRASE, "zzz_no_match_zzz")
    assert matches == []


def test_grep_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(GrepError, match="Vault not found"):
        grep_vault(tmp_path / "missing.vault", PASSPHRASE, "*")


def test_grep_wrong_passphrase_raises(vault_file: Path) -> None:
    with pytest.raises(GrepError, match="Failed to decrypt"):
        grep_vault(vault_file, "wrong-passphrase", "*")


def test_grep_match_str(vault_file: Path) -> None:
    matches = grep_vault(vault_file, PASSPHRASE, "localhost")
    assert str(matches[0]) == "DB_HOST=localhost"


def test_grep_regex_key_search(vault_file: Path) -> None:
    matches = grep_vault(vault_file, PASSPHRASE, r"^APP_", search_keys=True, use_regex=True)
    keys = {m.key for m in matches}
    assert keys == {"APP_ENV", "APP_SECRET"}
