"""Tests for envault.cli_hooks"""
from __future__ import annotations

import argparse
import pytest
from pathlib import Path

from envault.hooks import set_hook, load_hooks
from envault.cli_hooks import cmd_hook_set, cmd_hook_remove, cmd_hook_list


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def _ns(base_dir: Path, **kwargs) -> argparse.Namespace:
    return argparse.Namespace(base_dir=str(base_dir), **kwargs)


def test_cmd_hook_set_success(base_dir, capsys):
    ns = _ns(base_dir, event="pre_lock", command="echo locking")
    rc = cmd_hook_set(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "pre_lock" in out
    assert load_hooks(base_dir)["pre_lock"] == "echo locking"


def test_cmd_hook_set_invalid_event_returns_1(base_dir, capsys):
    ns = _ns(base_dir, event="on_fire", command="echo oops")
    rc = cmd_hook_set(ns)
    assert rc == 1
    assert "error" in capsys.readouterr().err


def test_cmd_hook_remove_success(base_dir, capsys):
    set_hook(base_dir, "post_unlock", "echo done")
    ns = _ns(base_dir, event="post_unlock")
    rc = cmd_hook_remove(ns)
    assert rc == 0
    assert "post_unlock" not in load_hooks(base_dir)


def test_cmd_hook_remove_missing_returns_1(base_dir, capsys):
    ns = _ns(base_dir, event="pre_pull")
    rc = cmd_hook_remove(ns)
    assert rc == 1
    assert "error" in capsys.readouterr().err


def test_cmd_hook_list_empty(base_dir, capsys):
    ns = _ns(base_dir)
    rc = cmd_hook_list(ns)
    assert rc == 0
    assert "No hooks" in capsys.readouterr().out


def test_cmd_hook_list_shows_entries(base_dir, capsys):
    set_hook(base_dir, "pre_lock", "echo a")
    set_hook(base_dir, "post_push", "echo b")
    ns = _ns(base_dir)
    rc = cmd_hook_list(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "pre_lock" in out
    assert "post_push" in out
