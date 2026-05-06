"""Tests for envault.search."""

from __future__ import annotations

from pathlib import Path

import pytest

from envault.vault import lock
from envault.search import SearchError, SearchResult, search_vault


PASSPHRASE = "hunter2"
ENV_CONTENT = """\
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=supersecret
API_KEY=abc123
DEBUG=true
"""


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text(ENV_CONTENT)
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    return vault


def test_search_by_key_exact(vault_file: Path) -> None:
    results = search_vault(vault_file, PASSPHRASE, "DB_HOST")
    assert len(results) == 1
    assert results[0].key == "DB_HOST"
    assert results[0].matched_by == "key"


def test_search_by_key_wildcard(vault_file: Path) -> None:
    results = search_vault(vault_file, PASSPHRASE, "DB_*")
    keys = {r.key for r in results}
    assert keys == {"DB_HOST", "DB_PORT", "DB_PASSWORD"}


def test_search_case_insensitive(vault_file: Path) -> None:
    results = search_vault(vault_file, PASSPHRASE, "db_host", case_sensitive=False)
    assert len(results) == 1
    assert results[0].key == "DB_HOST"


def test_search_case_sensitive_no_match(vault_file: Path) -> None:
    results = search_vault(vault_file, PASSPHRASE, "db_host", case_sensitive=True)
    assert results == []


def test_search_by_value(vault_file: Path) -> None:
    results = search_vault(
        vault_file, PASSPHRASE, "*secret*",
        search_keys=False, search_values=True
    )
    assert len(results) == 1
    assert results[0].key == "DB_PASSWORD"
    assert results[0].matched_by == "value"


def test_search_both_key_and_value(vault_file: Path) -> None:
    # pattern matches key 'DEBUG' and value 'abc123' won't overlap; use wildcard '*'
    results = search_vault(
        vault_file, PASSPHRASE, "*",
        search_keys=True, search_values=True
    )
    for r in results:
        assert r.matched_by == "both"
    assert len(results) == 5


def test_search_no_results(vault_file: Path) -> None:
    results = search_vault(vault_file, PASSPHRASE, "NONEXISTENT_*")
    assert results == []


def test_search_missing_vault(tmp_path: Path) -> None:
    with pytest.raises(SearchError, match="Vault file not found"):
        search_vault(tmp_path / "missing.vault", PASSPHRASE, "*")


def test_search_wrong_passphrase(vault_file: Path) -> None:
    with pytest.raises(SearchError, match="Failed to decrypt vault"):
        search_vault(vault_file, "wrongpassphrase", "*")


def test_search_neither_key_nor_value_raises(vault_file: Path) -> None:
    with pytest.raises(SearchError, match="At least one"):
        search_vault(
            vault_file, PASSPHRASE, "*",
            search_keys=False, search_values=False
        )
