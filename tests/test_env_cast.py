"""Tests for envault.env_cast."""
from __future__ import annotations

import pytest

from envault.env_cast import CastError, cast_value, cast_key
from envault.vault import lock


# ---------------------------------------------------------------------------
# cast_value unit tests
# ---------------------------------------------------------------------------

def test_cast_str_returns_string():
    assert cast_value("hello", "str") == "hello"


def test_cast_int_valid():
    assert cast_value("42", "int") == 42


def test_cast_int_invalid_raises():
    with pytest.raises(CastError, match="Cannot cast"):
        cast_value("not_a_number", "int")


def test_cast_float_valid():
    assert cast_value("3.14", "float") == pytest.approx(3.14)


def test_cast_bool_truthy_values():
    for v in ("1", "true", "yes", "on", "True", "YES"):
        assert cast_value(v, "bool") is True


def test_cast_bool_falsy_values():
    for v in ("0", "false", "no", "off", "False", "NO"):
        assert cast_value(v, "bool") is False


def test_cast_bool_invalid_raises():
    with pytest.raises(CastError, match="Cannot cast"):
        cast_value("maybe", "bool")


def test_cast_json_object():
    result = cast_value('{"a": 1}', "json")
    assert result == {"a": 1}


def test_cast_json_array():
    result = cast_value('[1, 2, 3]', "json")
    assert result == [1, 2, 3]


def test_cast_json_invalid_raises():
    with pytest.raises(CastError, match="Cannot cast"):
        cast_value("not json", "json")


def test_cast_unsupported_type_raises():
    with pytest.raises(CastError, match="Unsupported type"):
        cast_value("value", "bytes")


# ---------------------------------------------------------------------------
# cast_key integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_file(tmp_path):
    env_path = tmp_path / ".env"
    vault_path = tmp_path / ".env.vault"
    env_path.write_text(
        "COUNT=7\nPRICE=2.50\nDEBUG=true\nTAGS=[\"a\",\"b\"]\nNAME=alice\n"
    )
    lock(str(env_path), str(vault_path), "secret")
    return str(vault_path)


def test_cast_key_int(vault_file):
    assert cast_key(vault_file, "secret", "COUNT", "int") == 7


def test_cast_key_float(vault_file):
    assert cast_key(vault_file, "secret", "PRICE", "float") == pytest.approx(2.50)


def test_cast_key_bool(vault_file):
    assert cast_key(vault_file, "secret", "DEBUG", "bool") is True


def test_cast_key_json(vault_file):
    assert cast_key(vault_file, "secret", "TAGS", "json") == ["a", "b"]


def test_cast_key_missing_key_raises(vault_file):
    with pytest.raises(CastError, match="not found in vault"):
        cast_key(vault_file, "secret", "MISSING", "str")


def test_cast_key_wrong_passphrase_raises(vault_file):
    with pytest.raises(CastError, match="Failed to unlock vault"):
        cast_key(vault_file, "wrong", "NAME", "str")
