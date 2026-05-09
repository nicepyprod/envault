"""Tests for envault.env_validate."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.env_validate import validate_vault, ValidateError, ValidationResult

PASSPHRASE = "test-secret"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env_text = "DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=abc123\n"
    env_path = tmp_path / ".env"
    env_path.write_text(env_text)
    vault_path = tmp_path / ".env.vault"
    lock(env_path, vault_path, PASSPHRASE)
    return vault_path


def test_validate_all_present(vault_file: Path):
    result = validate_vault(vault_file, PASSPHRASE, ["DB_HOST", "API_KEY"])
    assert result.ok
    assert result.missing == []
    assert result.invalid_format == []


def test_validate_missing_key(vault_file: Path):
    result = validate_vault(vault_file, PASSPHRASE, ["DB_HOST", "MISSING_KEY"])
    assert not result.ok
    assert "MISSING_KEY" in result.missing
    assert "DB_HOST" not in result.missing


def test_validate_pattern_match(vault_file: Path):
    # DB_PORT value is '5432' — digits only
    result = validate_vault(vault_file, PASSPHRASE, ["DB_PORT"], pattern=r"^\d+$")
    assert result.ok
    assert result.invalid_format == []


def test_validate_pattern_no_match(vault_file: Path):
    # DB_HOST value is 'localhost' — not digits
    result = validate_vault(vault_file, PASSPHRASE, ["DB_HOST"], pattern=r"^\d+$")
    assert not result.ok
    assert "DB_HOST" in result.invalid_format


def test_validate_missing_vault(tmp_path: Path):
    with pytest.raises(ValidateError, match="Vault not found"):
        validate_vault(tmp_path / "nonexistent.vault", PASSPHRASE, ["KEY"])


def test_validate_wrong_passphrase(vault_file: Path):
    with pytest.raises(ValidateError, match="Failed to decrypt"):
        validate_vault(vault_file, "wrong-passphrase", ["DB_HOST"])


def test_validate_empty_required_keys(vault_file: Path):
    result = validate_vault(vault_file, PASSPHRASE, [])
    assert result.ok


def test_validation_result_str_ok(vault_file: Path):
    result = validate_vault(vault_file, PASSPHRASE, ["DB_HOST"])
    assert "passed" in str(result)


def test_validation_result_str_errors(vault_file: Path):
    result = validate_vault(vault_file, PASSPHRASE, ["GHOST_KEY"])
    text = str(result)
    assert "MISSING" in text
    assert "GHOST_KEY" in text
