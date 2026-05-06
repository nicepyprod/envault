"""Tests for envault.cli_export."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.vault import lock
from envault.cli_export import cmd_export, register_subcommands


PASSPHRASE = "cli-export-pass"
ENV_CONTENT = "API_KEY=abc123\nDEBUG=true\n"


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"vault": ".env.vault", "format": "dotenv", "output": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def prepared_vault(tmp_path: Path) -> Path:
    env = tmp_path / ".env"
    vault = tmp_path / ".env.vault"
    env.write_text(ENV_CONTENT, encoding="utf-8")
    lock(env, vault, PASSPHRASE)
    return vault


def test_cmd_export_dotenv_stdout(prepared_vault: Path, capsys) -> None:
    ns = _ns(vault=str(prepared_vault), format="dotenv")
    with patch("envault.cli_export._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_export(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "API_KEY=abc123" in out


def test_cmd_export_json_stdout(prepared_vault: Path, capsys) -> None:
    ns = _ns(vault=str(prepared_vault), format="json")
    with patch("envault.cli_export._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_export(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert '"API_KEY"' in out


def test_cmd_export_to_file(prepared_vault: Path, tmp_path: Path) -> None:
    out_file = tmp_path / "out.env"
    ns = _ns(vault=str(prepared_vault), format="dotenv", output=str(out_file))
    with patch("envault.cli_export._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_export(ns)
    assert rc == 0
    assert out_file.exists()
    assert "API_KEY=abc123" in out_file.read_text()


def test_cmd_export_missing_vault(tmp_path: Path) -> None:
    ns = _ns(vault=str(tmp_path / "missing.vault"))
    with patch("envault.cli_export._read_passphrase", return_value=PASSPHRASE):
        rc = cmd_export(ns)
    assert rc == 1


def test_cmd_export_wrong_passphrase(prepared_vault: Path) -> None:
    ns = _ns(vault=str(prepared_vault))
    with patch("envault.cli_export._read_passphrase", return_value="wrong"):
        rc = cmd_export(ns)
    assert rc == 1


def test_register_subcommands_adds_export() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_subcommands(sub)
    args = parser.parse_args(["export", "--format", "json"])
    assert args.format == "json"
    assert args.func is cmd_export
