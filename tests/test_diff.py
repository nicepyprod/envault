"""Tests for envault.diff and envault.cli_diff."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.vault import lock
from envault.diff import (
    DiffError,
    DiffEntry,
    diff_vaults,
    diff_vault_vs_env,
    _compute_diff,
)
from envault.cli_diff import cmd_diff


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

PASS = "s3cr3t"


def _make_vault(tmp_path: Path, name: str, content: str) -> Path:
    env = tmp_path / f"{name}.env"
    env.write_text(content)
    vault = tmp_path / f"{name}.vault"
    lock(env, vault, PASS)
    return vault


# ---------------------------------------------------------------------------
# _compute_diff unit tests
# ---------------------------------------------------------------------------

def test_compute_diff_added():
    entries = _compute_diff({}, {"FOO": "bar"})
    assert entries == [DiffEntry("FOO", "added", None, "bar")]


def test_compute_diff_removed():
    entries = _compute_diff({"FOO": "bar"}, {})
    assert entries == [DiffEntry("FOO", "removed", "bar", None)]


def test_compute_diff_changed():
    entries = _compute_diff({"FOO": "old"}, {"FOO": "new"})
    assert entries == [DiffEntry("FOO", "changed", "old", "new")]


def test_compute_diff_unchanged():
    entries = _compute_diff({"FOO": "same"}, {"FOO": "same"})
    assert entries == [DiffEntry("FOO", "unchanged", "same", "same")]


# ---------------------------------------------------------------------------
# diff_vaults
# ---------------------------------------------------------------------------

def test_diff_vaults_detects_change(tmp_path):
    v1 = _make_vault(tmp_path, "v1", "FOO=old\nBAR=keep\n")
    v2 = _make_vault(tmp_path, "v2", "FOO=new\nBAR=keep\nBAZ=extra\n")
    entries = {e.key: e for e in diff_vaults(v1, v2, PASS)}
    assert entries["FOO"].status == "changed"
    assert entries["BAR"].status == "unchanged"
    assert entries["BAZ"].status == "added"


def test_diff_vaults_missing_file_raises(tmp_path):
    v1 = _make_vault(tmp_path, "v1", "FOO=1\n")
    with pytest.raises(DiffError):
        diff_vaults(v1, tmp_path / "missing.vault", PASS)


# ---------------------------------------------------------------------------
# diff_vault_vs_env
# ---------------------------------------------------------------------------

def test_diff_vault_vs_env(tmp_path):
    vault = _make_vault(tmp_path, "base", "FOO=1\nBAR=2\n")
    env_file = tmp_path / "live.env"
    env_file.write_text("FOO=1\nBAZ=3\n")
    entries = {e.key: e for e in diff_vault_vs_env(vault, env_file, PASS)}
    assert entries["FOO"].status == "unchanged"
    assert entries["BAR"].status == "removed"
    assert entries["BAZ"].status == "added"


# ---------------------------------------------------------------------------
# cli cmd_diff
# ---------------------------------------------------------------------------

def _ns(**kwargs):
    import argparse
    defaults = dict(vault=None, new_vault=None, env=None, show_unchanged=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_diff_vault_vs_env_success(tmp_path, capsys):
    vault = _make_vault(tmp_path, "base", "FOO=old\n")
    env_file = tmp_path / "live.env"
    env_file.write_text("FOO=new\n")
    ns = _ns(vault=str(vault), env=str(env_file))
    with patch("envault.cli_diff._read_passphrase", return_value=PASS):
        rc = cmd_diff(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "FOO" in out
    assert "changed" not in out   # output uses symbols, not words
    assert "~" in out


def test_cmd_diff_empty_passphrase_returns_1(tmp_path):
    vault = _make_vault(tmp_path, "base", "FOO=1\n")
    ns = _ns(vault=str(vault), env=str(tmp_path / "x.env"))
    with patch("envault.cli_diff._read_passphrase", return_value=""):
        rc = cmd_diff(ns)
    assert rc == 1


def test_cmd_diff_no_target_returns_1(tmp_path):
    vault = _make_vault(tmp_path, "base", "FOO=1\n")
    ns = _ns(vault=str(vault))  # neither --env nor --new-vault
    with patch("envault.cli_diff._read_passphrase", return_value=PASS):
        rc = cmd_diff(ns)
    assert rc == 1
