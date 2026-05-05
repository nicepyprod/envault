"""Tests for envault.cli_profiles sub-commands."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.cli_profiles import cmd_profile_add, cmd_profile_list, cmd_profile_remove
from envault.profiles import add_profile, load_profiles


def _ns(base_dir: Path, **kwargs) -> argparse.Namespace:
    defaults = {"dir": str(base_dir), "env_file": ".env", "vault_file": ".env.vault"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_cmd_profile_add_success(base_dir, capsys):
    args = _ns(base_dir, name="dev")
    rc = cmd_profile_add(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "dev" in out
    assert "dev" in load_profiles(base_dir)


def test_cmd_profile_add_duplicate_returns_1(base_dir, capsys):
    add_profile(base_dir, "dev", ".env", ".env.vault")
    args = _ns(base_dir, name="dev")
    rc = cmd_profile_add(args)
    assert rc == 1
    assert "error" in capsys.readouterr().err


def test_cmd_profile_remove_success(base_dir, capsys):
    add_profile(base_dir, "staging", ".env.staging", ".env.staging.vault")
    args = _ns(base_dir, name="staging")
    rc = cmd_profile_remove(args)
    assert rc == 0
    assert "staging" not in load_profiles(base_dir)


def test_cmd_profile_remove_missing_returns_1(base_dir, capsys):
    args = _ns(base_dir, name="ghost")
    rc = cmd_profile_remove(args)
    assert rc == 1
    assert "error" in capsys.readouterr().err


def test_cmd_profile_list_empty(base_dir, capsys):
    args = _ns(base_dir)
    rc = cmd_profile_list(args)
    assert rc == 0
    assert "No profiles" in capsys.readouterr().out


def test_cmd_profile_list_shows_profiles(base_dir, capsys):
    add_profile(base_dir, "prod", ".env.prod", ".env.prod.vault")
    add_profile(base_dir, "dev", ".env", ".env.vault")
    args = _ns(base_dir)
    rc = cmd_profile_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "dev" in out
    assert "prod" in out
