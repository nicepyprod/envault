"""Tests for envault.env_fmt."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.crypto import encrypt, decrypt
from envault.env_fmt import FmtError, _parse_env_pairs, _pairs_to_env, format_vault


PASSPHRASE = "test-passphrase"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    """Return a path to a freshly encrypted vault with some env content."""
    content = "DB_HOST=localhost\nDB_PORT=5432\nAPP_SECRET=hunter2\n"
    path = tmp_path / "test.vault"
    path.write_bytes(encrypt(content, PASSPHRASE))
    return path


# ---------------------------------------------------------------------------
# _parse_env_pairs
# ---------------------------------------------------------------------------

def test_parse_skips_comments_and_blanks():
    text = "# comment\n\nKEY=val\n"
    assert _parse_env_pairs(text) == [("KEY", "val")]


def test_parse_strips_quotes():
    text = 'KEY="quoted value"\nOTHER=\'single\'\n'
    pairs = _parse_env_pairs(text)
    assert ("KEY", "quoted value") in pairs
    assert ("OTHER", "single") in pairs


def test_parse_preserves_order():
    text = "Z=1\nA=2\nM=3\n"
    keys = [k for k, _ in _parse_env_pairs(text)]
    assert keys == ["Z", "A", "M"]


# ---------------------------------------------------------------------------
# _pairs_to_env
# ---------------------------------------------------------------------------

def test_pairs_to_env_no_quotes():
    result = _pairs_to_env([("KEY", "value")])
    assert result.strip() == "KEY=value"


def test_pairs_to_env_forces_quotes_for_spaces():
    result = _pairs_to_env([("KEY", "hello world")])
    assert '"hello world"' in result


def test_pairs_to_env_quote_flag():
    result = _pairs_to_env([("KEY", "val")], quote_values=True)
    assert result.strip() == 'KEY="val"'


# ---------------------------------------------------------------------------
# format_vault
# ---------------------------------------------------------------------------

def test_format_vault_roundtrip(vault_file: Path):
    count = format_vault(vault_file, PASSPHRASE)
    assert count == 3  # DB_HOST, DB_PORT, APP_SECRET
    plaintext = decrypt(vault_file.read_bytes(), PASSPHRASE)
    assert "DB_HOST=localhost" in plaintext


def test_format_vault_sort_keys(vault_file: Path):
    format_vault(vault_file, PASSPHRASE, sort_keys=True)
    plaintext = decrypt(vault_file.read_bytes(), PASSPHRASE)
    keys = [line.split("=")[0] for line in plaintext.splitlines() if "=" in line]
    assert keys == sorted(keys, key=str.lower)


def test_format_vault_quote_values(vault_file: Path):
    format_vault(vault_file, PASSPHRASE, quote_values=True)
    plaintext = decrypt(vault_file.read_bytes(), PASSPHRASE)
    for line in plaintext.splitlines():
        if "=" in line:
            _, _, val = line.partition("=")
            assert val.startswith('"') and val.endswith('"')


def test_format_vault_missing_file(tmp_path: Path):
    with pytest.raises(FmtError, match="Vault not found"):
        format_vault(tmp_path / "no_such.vault", PASSPHRASE)


def test_format_vault_wrong_passphrase(vault_file: Path):
    with pytest.raises(FmtError, match="Failed to decrypt"):
        format_vault(vault_file, "wrong-passphrase")
