"""Tests for envault.import_env."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.import_env import ImportError, _parse_dotenv, _parse_json, import_into_vault
from envault.vault import unlock


# ---------------------------------------------------------------------------
# Unit tests for parsers
# ---------------------------------------------------------------------------

def test_parse_dotenv_basic():
    text = "FOO=bar\nBAZ=qux\n"
    assert _parse_dotenv(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_dotenv_strips_quotes():
    text = 'KEY="hello world"\nOTHER=\'value\'\n'
    assert _parse_dotenv(text) == {"KEY": "hello world", "OTHER": "value"}


def test_parse_dotenv_skips_comments_and_blanks():
    text = "# comment\n\nFOO=1\n"
    assert _parse_dotenv(text) == {"FOO": "1"}


def test_parse_json_basic():
    data = {"SECRET": "abc", "PORT": 8080}
    assert _parse_json(json.dumps(data)) == {"SECRET": "abc", "PORT": "8080"}


def test_parse_json_invalid_raises():
    with pytest.raises(ImportError, match="Invalid JSON"):
        _parse_json("not json")


def test_parse_json_non_object_raises():
    with pytest.raises(ImportError, match="object"):
        _parse_json(json.dumps(["a", "b"]))


# ---------------------------------------------------------------------------
# Integration tests for import_into_vault
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp(tmp_path: Path) -> Path:
    return tmp_path


def test_import_dotenv_creates_vault(tmp: Path):
    src = tmp / ".env"
    src.write_text("API_KEY=secret\nDB_URL=postgres://localhost/db\n")
    vault = tmp / "secrets.vault"

    count = import_into_vault(src, vault, passphrase="pass123", fmt="dotenv")

    assert count == 2
    assert vault.exists()
    plaintext = unlock(vault, "pass123")
    assert "API_KEY=secret" in plaintext
    assert "DB_URL=postgres://localhost/db" in plaintext


def test_import_json_creates_vault(tmp: Path):
    src = tmp / "secrets.json"
    src.write_text(json.dumps({"TOKEN": "xyz", "TIMEOUT": 30}))
    vault = tmp / "secrets.vault"

    count = import_into_vault(src, vault, passphrase="s3cr3t", fmt="json")

    assert count == 2
    plaintext = unlock(vault, "s3cr3t")
    assert "TOKEN=xyz" in plaintext


def test_import_merge_preserves_existing_keys(tmp: Path):
    # First import
    src1 = tmp / "first.env"
    src1.write_text("OLD_KEY=old_value\n")
    vault = tmp / "secrets.vault"
    import_into_vault(src1, vault, passphrase="pw", fmt="dotenv")

    # Second import with merge
    src2 = tmp / "second.env"
    src2.write_text("NEW_KEY=new_value\n")
    count = import_into_vault(src2, vault, passphrase="pw", fmt="dotenv", merge=True)

    assert count == 2
    plaintext = unlock(vault, "pw")
    assert "OLD_KEY=old_value" in plaintext
    assert "NEW_KEY=new_value" in plaintext


def test_import_missing_source_raises(tmp: Path):
    with pytest.raises(ImportError, match="not found"):
        import_into_vault(tmp / "ghost.env", tmp / "vault", passphrase="pw")


def test_import_empty_source_raises(tmp: Path):
    src = tmp / "empty.env"
    src.write_text("# only a comment\n")
    with pytest.raises(ImportError, match="No key"):
        import_into_vault(src, tmp / "vault", passphrase="pw")


def test_import_unknown_format_raises(tmp: Path):
    src = tmp / "data.toml"
    src.write_text("key = 'value'\n")
    with pytest.raises(ImportError, match="Unknown format"):
        import_into_vault(src, tmp / "vault", passphrase="pw", fmt="toml")
