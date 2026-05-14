"""Tests for envault.env_schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envault.vault import lock
from envault.env_schema import (
    SchemaError,
    SchemaResult,
    SchemaViolation,
    load_schema,
    validate_vault,
)

PASSPHRASE = "test-pass"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nDB_PORT=5432\nDEBUG=true\nAPI_KEY=secret\n")
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    return vault


@pytest.fixture()
def schema_file(tmp_path: Path) -> Path:
    schema = {
        "DB_HOST": {"required": True, "type": "str"},
        "DB_PORT": {"required": True, "type": "int"},
        "DEBUG": {"required": False, "type": "bool"},
        "API_KEY": {"required": True, "pattern": r"[a-z]+"},
    }
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(schema))
    return path


def test_load_schema_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SchemaError, match="not found"):
        load_schema(tmp_path / "missing.json")


def test_load_schema_corrupt_file(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("not json{{{")
    with pytest.raises(SchemaError, match="not valid JSON"):
        load_schema(bad)


def test_load_schema_wrong_type(tmp_path: Path) -> None:
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(["not", "a", "dict"]))
    with pytest.raises(SchemaError, match="JSON object"):
        load_schema(path)


def test_validate_all_pass(vault_file: Path, schema_file: Path) -> None:
    result = validate_vault(vault_file, PASSPHRASE, schema_file)
    assert result.ok
    assert "passed" in result.summary()


def test_validate_missing_required_key(tmp_path: Path, schema_file: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("DB_PORT=5432\nDEBUG=true\n")  # DB_HOST missing
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    result = validate_vault(vault, PASSPHRASE, schema_file)
    assert not result.ok
    keys = [v.key for v in result.violations]
    assert "DB_HOST" in keys


def test_validate_wrong_type(tmp_path: Path, schema_file: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nDB_PORT=notanint\nDEBUG=true\nAPI_KEY=secret\n")
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    result = validate_vault(vault, PASSPHRASE, schema_file)
    assert not result.ok
    assert any(v.key == "DB_PORT" for v in result.violations)


def test_validate_pattern_mismatch(tmp_path: Path, schema_file: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nDB_PORT=5432\nDEBUG=true\nAPI_KEY=SECRET123\n")
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    result = validate_vault(vault, PASSPHRASE, schema_file)
    assert not result.ok
    assert any(v.key == "API_KEY" for v in result.violations)


def test_validate_allowed_values(tmp_path: Path) -> None:
    schema = {"ENV": {"required": True, "allowed": ["dev", "prod", "staging"]}}
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))
    env = tmp_path / ".env"
    env.write_text("ENV=test\n")
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    result = validate_vault(vault, PASSPHRASE, schema_path)
    assert not result.ok
    assert result.violations[0].key == "ENV"


def test_schema_result_summary_lists_violations() -> None:
    r = SchemaResult(violations=[SchemaViolation("FOO", "missing"), SchemaViolation("BAR", "bad type")])
    s = r.summary()
    assert "FOO" in s
    assert "BAR" in s
    assert "2 issue" in s


def test_validate_wrong_passphrase_raises(vault_file: Path, schema_file: Path) -> None:
    with pytest.raises(SchemaError, match="decrypt"):
        validate_vault(vault_file, "wrong", schema_file)
