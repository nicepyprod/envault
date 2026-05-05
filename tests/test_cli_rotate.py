"""Tests for envault.cli_rotate (rotate subcommand)."""

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.cli_rotate import cmd_rotate, register_subcommands
from envault.vault import lock


PLAINTEXT = b"DB_URL=postgres://localhost/db\n"
OLD_PASS = "old"
NEW_PASS = "new"


def _ns(vault: str, env: str) -> argparse.Namespace:
    return argparse.Namespace(vault=vault, env=env)


@pytest.fixture()
def prepared_vault(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_bytes(PLAINTEXT)
    vault = tmp_path / ".env.vault"
    lock(env_path=env, vault_path=vault, passphrase=OLD_PASS)
    return vault, env, tmp_path


def test_cmd_rotate_success(prepared_vault):
    vault, env, tmp_path = prepared_vault
    side_effects = [OLD_PASS, NEW_PASS, NEW_PASS]
    with patch("envault.cli_rotate._read_passphrase", side_effect=side_effects):
        rc = cmd_rotate(_ns(str(vault), str(tmp_path / ".env")))
    assert rc == 0
    assert vault.exists()


def test_cmd_rotate_mismatched_new_passphrase(prepared_vault):
    vault, env, tmp_path = prepared_vault
    side_effects = [OLD_PASS, NEW_PASS, "different"]
    with patch("envault.cli_rotate._read_passphrase", side_effect=side_effects):
        rc = cmd_rotate(_ns(str(vault), str(tmp_path / ".env")))
    assert rc == 1


def test_cmd_rotate_empty_new_passphrase(prepared_vault):
    vault, env, tmp_path = prepared_vault
    side_effects = [OLD_PASS, "", ""]
    with patch("envault.cli_rotate._read_passphrase", side_effect=side_effects):
        rc = cmd_rotate(_ns(str(vault), str(tmp_path / ".env")))
    assert rc == 1


def test_cmd_rotate_missing_vault(tmp_path: Path):
    side_effects = [OLD_PASS, NEW_PASS, NEW_PASS]
    with patch("envault.cli_rotate._read_passphrase", side_effect=side_effects):
        rc = cmd_rotate(_ns(str(tmp_path / "no.vault"), str(tmp_path / ".env")))
    assert rc == 1


def test_cmd_rotate_keyboard_interrupt(prepared_vault):
    vault, env, tmp_path = prepared_vault
    with patch("envault.cli_rotate._read_passphrase", side_effect=KeyboardInterrupt):
        rc = cmd_rotate(_ns(str(vault), str(tmp_path / ".env")))
    assert rc == 1


def test_register_subcommands_adds_rotate():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_subcommands(sub)
    args = parser.parse_args(["rotate", "--vault", "v.vault", "--env", ".env"])
    assert args.vault == "v.vault"
    assert args.env == ".env"
    assert callable(args.func)
