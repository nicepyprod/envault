"""Tests for envault.env_filter."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.tags import add_tag
from envault.env_filter import FilterError, filter_vault

PASS = "s3cr3t"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = "DB_HOST=localhost\nDB_PORT=5432\nAPP_NAME=myapp\nAPP_DEBUG=true\n"
    vf = tmp_path / "test.vault"
    lock(env, vf, PASS)
    return vf


def test_filter_by_prefix(vault_file: Path) -> None:
    result = filter_vault(vault_file, PASS, prefix="DB_")
    assert set(result.keys()) == {"DB_HOST", "DB_PORT"}


def test_filter_by_pattern(vault_file: Path) -> None:
    result = filter_vault(vault_file, PASS, pattern="APP_*")
    assert set(result.keys()) == {"APP_NAME", "APP_DEBUG"}


def test_filter_by_prefix_and_pattern(vault_file: Path) -> None:
    result = filter_vault(vault_file, PASS, prefix="APP_", pattern="APP_D*")
    assert set(result.keys()) == {"APP_DEBUG"}


def test_filter_invert(vault_file: Path) -> None:
    result = filter_vault(vault_file, PASS, prefix="DB_", invert=True)
    assert set(result.keys()) == {"APP_NAME", "APP_DEBUG"}


def test_filter_by_tag(vault_file: Path) -> None:
    add_tag(vault_file, "DB_HOST", "database")
    add_tag(vault_file, "DB_PORT", "database")
    result = filter_vault(vault_file, PASS, tag="database")
    assert set(result.keys()) == {"DB_HOST", "DB_PORT"}


def test_filter_no_criteria_raises(vault_file: Path) -> None:
    with pytest.raises(FilterError, match="At least one"):
        filter_vault(vault_file, PASS)


def test_filter_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(FilterError, match="Vault not found"):
        filter_vault(tmp_path / "missing.vault", PASS, prefix="X")


def test_filter_wrong_passphrase_raises(vault_file: Path) -> None:
    with pytest.raises(FilterError, match="Failed to decrypt"):
        filter_vault(vault_file, "wrong", prefix="DB_")


def test_filter_returns_correct_values(vault_file: Path) -> None:
    result = filter_vault(vault_file, PASS, prefix="DB_")
    assert result["DB_HOST"] == "localhost"
    assert result["DB_PORT"] == "5432"


def test_filter_no_match_returns_empty(vault_file: Path) -> None:
    result = filter_vault(vault_file, PASS, prefix="NONEXISTENT_")
    assert result == {}
