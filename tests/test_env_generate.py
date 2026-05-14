"""Tests for envault.env_generate."""

import pytest

from envault.env_generate import GenerateError, generate_value, generate_into_vault
from envault.vault import lock, unlock
from envault.env_edit import _parse_env_dict


# ---------------------------------------------------------------------------
# generate_value
# ---------------------------------------------------------------------------

def test_generate_value_default_length():
    val = generate_value()
    assert len(val) == 32


def test_generate_value_custom_length():
    val = generate_value(length=16)
    assert len(val) == 16


def test_generate_value_hex_charset():
    val = generate_value(length=64, charset="hex")
    assert all(c in "0123456789abcdef" for c in val)


def test_generate_value_numeric_charset():
    val = generate_value(length=20, charset="numeric")
    assert val.isdigit()


def test_generate_value_invalid_length_raises():
    with pytest.raises(GenerateError, match="length must be between"):
        generate_value(length=0)


def test_generate_value_length_too_large_raises():
    with pytest.raises(GenerateError, match="length must be between"):
        generate_value(length=257)


def test_generate_value_unknown_charset_raises():
    with pytest.raises(GenerateError, match="unknown charset"):
        generate_value(charset="base64")


def test_two_generated_values_differ():
    """Statistical sanity check — two 32-char values are almost certainly different."""
    assert generate_value() != generate_value()


# ---------------------------------------------------------------------------
# generate_into_vault
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path):
    env = tmp_path / ".env"
    env.write_text("EXISTING=hello\n")
    vault = tmp_path / ".env.vault"
    lock(str(env), str(vault), "secret")
    return vault


def test_generate_into_vault_adds_key(vault_file):
    generate_into_vault(str(vault_file), "secret", "NEW_KEY")
    plaintext = unlock(str(vault_file), "secret")
    env = _parse_env_dict(plaintext)
    assert "NEW_KEY" in env
    assert len(env["NEW_KEY"]) == 32


def test_generate_into_vault_preserves_existing(vault_file):
    generate_into_vault(str(vault_file), "secret", "TOKEN")
    plaintext = unlock(str(vault_file), "secret")
    env = _parse_env_dict(plaintext)
    assert env["EXISTING"] == "hello"


def test_generate_into_vault_returns_value(vault_file):
    value = generate_into_vault(str(vault_file), "secret", "RETURNED")
    plaintext = unlock(str(vault_file), "secret")
    env = _parse_env_dict(plaintext)
    assert env["RETURNED"] == value


def test_generate_into_vault_duplicate_raises(vault_file):
    with pytest.raises(GenerateError, match="already exists"):
        generate_into_vault(str(vault_file), "secret", "EXISTING")


def test_generate_into_vault_overwrite_succeeds(vault_file):
    generate_into_vault(str(vault_file), "secret", "EXISTING", overwrite=True)
    plaintext = unlock(str(vault_file), "secret")
    env = _parse_env_dict(plaintext)
    assert env["EXISTING"] != "hello"


def test_generate_into_vault_custom_length_and_charset(vault_file):
    generate_into_vault(str(vault_file), "secret", "HEX_KEY", length=16, charset="hex")
    plaintext = unlock(str(vault_file), "secret")
    env = _parse_env_dict(plaintext)
    assert len(env["HEX_KEY"]) == 16
    assert all(c in "0123456789abcdef" for c in env["HEX_KEY"])
