"""Tests for envault.cli_schema."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.vault import lock
from envault.cli_schema import cmd_schema_validate, cmd_schema_check_file

PASSPHRASE = "cli-schema-pass"


def _ns(**kwargs):
    import argparse
    ns = argparse.Namespace(**kwargs)
    return ns


@pytest.fixture()
def prepared_vault(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("PORT=8080\nMODE=production\n")
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    schema = {"PORT": {"required": True, "type": "int"}, "MODE": {"required": True}}
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))
    return vault, schema_path


def test_cmd_schema_validate_success(prepared_vault, capsys):
    vault, schema_path = prepared_vault
    args = _ns(vault=str(vault), schema=str(schema_path))
    with patch("envault.cli_schema._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_schema_validate(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "passed" in out


def test_cmd_schema_validate_failure(tmp_path, capsys):
    env = tmp_path / ".env"
    env.write_text("PORT=notanumber\n")
    vault = tmp_path / ".env.vault"
    lock(env, vault, PASSPHRASE)
    schema = {"PORT": {"required": True, "type": "int"}}
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))
    args = _ns(vault=str(vault), schema=str(schema_path))
    with patch("envault.cli_schema._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_schema_validate(args)
    assert rc == 1
    out = capsys.readouterr().out
    assert "PORT" in out


def test_cmd_schema_validate_empty_passphrase(prepared_vault, capsys):
    vault, schema_path = prepared_vault
    args = _ns(vault=str(vault), schema=str(schema_path))
    with patch("envault.cli_schema._read_passphrase", return_value=""):
        rc = cmd_schema_validate(args)
    assert rc == 1
    err = capsys.readouterr().err
    assert "empty" in err


def test_cmd_schema_validate_missing_vault(tmp_path, capsys):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps({}))
    args = _ns(vault=str(tmp_path / "missing.vault"), schema=str(schema_path))
    with patch("envault.cli_schema._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_schema_validate(args)
    assert rc == 1


def test_cmd_schema_check_file_success(tmp_path, capsys):
    schema = {"KEY": {"required": True}}
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps(schema))
    args = _ns(schema=str(schema_path))
    rc = cmd_schema_check_file(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "OK" in out
    assert "1 key" in out


def test_cmd_schema_check_file_invalid(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("<<<invalid>>>")
    args = _ns(schema=str(bad))
    rc = cmd_schema_check_file(args)
    assert rc == 1
    err = capsys.readouterr().err
    assert "error" in err
