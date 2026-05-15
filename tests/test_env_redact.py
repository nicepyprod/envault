"""Tests for envault.env_redact."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.vault import lock
from envault.env_redact import (
    RedactError,
    RedactResult,
    REDACT_PLACEHOLDER,
    _should_redact,
    redact_vault,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env_content = (
        "DB_HOST=localhost\n"
        "DB_PASSWORD=supersecret\n"
        "API_KEY=abc123\n"
        "APP_TOKEN=tok_xyz\n"
        "DEBUG=true\n"
        "PRIVATE_KEY=-----BEGIN RSA-----\n"
    )
    env_path = tmp_path / ".env"
    env_path.write_text(env_content)
    vault_path = tmp_path / ".env.vault"
    lock(env_path, vault_path, "hunter2")
    return vault_path


# ---------------------------------------------------------------------------
# Unit tests for _should_redact
# ---------------------------------------------------------------------------

def test_should_redact_password():
    assert _should_redact("DB_PASSWORD", [r".*password.*"])


def test_should_redact_case_insensitive():
    assert _should_redact("My_Secret_Value", [r".*secret.*"])


def test_should_not_redact_plain_key():
    assert not _should_redact("DEBUG", [r".*secret.*", r".*password.*"])


def test_should_redact_api_key():
    assert _should_redact("API_KEY", [r".*api[_-]?key.*"])


# ---------------------------------------------------------------------------
# Integration tests for redact_vault
# ---------------------------------------------------------------------------

def test_redact_vault_returns_result(vault_file: Path):
    result = redact_vault(vault_file, "hunter2")
    assert isinstance(result, RedactResult)


def test_redact_vault_masks_password(vault_file: Path):
    result = redact_vault(vault_file, "hunter2")
    assert result.entries["DB_PASSWORD"] == REDACT_PLACEHOLDER


def test_redact_vault_masks_token(vault_file: Path):
    result = redact_vault(vault_file, "hunter2")
    assert result.entries["APP_TOKEN"] == REDACT_PLACEHOLDER


def test_redact_vault_keeps_plain_keys(vault_file: Path):
    result = redact_vault(vault_file, "hunter2")
    assert result.entries["DB_HOST"] == "localhost"
    assert result.entries["DEBUG"] == "true"


def test_redact_vault_counts_redacted(vault_file: Path):
    result = redact_vault(vault_file, "hunter2")
    assert result.redacted_count >= 3  # password, api_key, token, private_key
    assert result.total == 6


def test_redact_vault_show_keys_overrides(vault_file: Path):
    result = redact_vault(vault_file, "hunter2", show_keys=["DB_PASSWORD"])
    assert result.entries["DB_PASSWORD"] == "supersecret"
    assert "DB_PASSWORD" not in result.redacted_keys


def test_redact_vault_extra_patterns(vault_file: Path):
    result = redact_vault(vault_file, "hunter2", extra_patterns=[r"debug"])
    assert result.entries["DEBUG"] == REDACT_PLACEHOLDER


def test_redact_vault_missing_file(tmp_path: Path):
    with pytest.raises(RedactError, match="Vault not found"):
        redact_vault(tmp_path / "nonexistent.vault", "pass")


def test_redact_vault_wrong_passphrase(vault_file: Path):
    with pytest.raises(RedactError, match="Failed to decrypt"):
        redact_vault(vault_file, "wrongpass")
