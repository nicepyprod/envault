"""Tests for envault.cli_lint"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.cli_lint import cmd_lint, register_subcommands


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"env_file": ".env"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def clean_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n", encoding="utf-8")
    return p


@pytest.fixture()
def dirty_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("123BAD=val\nFOO=bar\nFOO=dup\n", encoding="utf-8")
    return p


def test_cmd_lint_clean_returns_0(clean_env, capsys):
    rc = cmd_lint(_ns(env_file=str(clean_env)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No issues" in out


def test_cmd_lint_errors_returns_1(dirty_env, capsys):
    rc = cmd_lint(_ns(env_file=str(dirty_env)))
    assert rc == 1
    out = capsys.readouterr().out
    assert "ERROR" in out


def test_cmd_lint_missing_file_returns_1(tmp_path, capsys):
    rc = cmd_lint(_ns(env_file=str(tmp_path / "missing.env")))
    assert rc == 1
    err = capsys.readouterr().err
    assert "error" in err


def test_cmd_lint_warnings_only_returns_0(tmp_path, capsys):
    p = tmp_path / ".env"
    p.write_text("FOO=bar#inline\n", encoding="utf-8")
    rc = cmd_lint(_ns(env_file=str(p)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "WARN" in out


def test_register_subcommands_adds_lint():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_subcommands(sub)
    args = parser.parse_args(["lint", "myfile.env"])
    assert args.env_file == "myfile.env"
    assert args.func is cmd_lint


def test_register_subcommands_default_env_file():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register_subcommands(sub)
    args = parser.parse_args(["lint"])
    assert args.env_file == ".env"
