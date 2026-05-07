"""Tests for envault.env_watch and envault.cli_watch."""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.env_watch import WatchError, WatchEvent, compute_changes, watch
from envault.cli_watch import cmd_watch, _format_event


# ---------------------------------------------------------------------------
# compute_changes
# ---------------------------------------------------------------------------

def test_compute_diff_added():
    events = compute_changes({}, {"FOO": "bar"})
    assert len(events) == 1
    assert events[0].kind == "added"
    assert events[0].key == "FOO"
    assert events[0].new_value == "bar"


def test_compute_diff_removed():
    events = compute_changes({"FOO": "bar"}, {})
    assert len(events) == 1
    assert events[0].kind == "removed"
    assert events[0].old_value == "bar"


def test_compute_diff_changed():
    events = compute_changes({"FOO": "old"}, {"FOO": "new"})
    assert len(events) == 1
    assert events[0].kind == "changed"
    assert events[0].old_value == "old"
    assert events[0].new_value == "new"


def test_compute_diff_no_changes():
    events = compute_changes({"FOO": "bar"}, {"FOO": "bar"})
    assert events == []


def test_compute_diff_multiple():
    old = {"A": "1", "B": "2"}
    new = {"B": "99", "C": "3"}
    events = compute_changes(old, new)
    kinds = {e.key: e.kind for e in events}
    assert kinds["A"] == "removed"
    assert kinds["B"] == "changed"
    assert kinds["C"] == "added"


# ---------------------------------------------------------------------------
# watch() — file-based polling
# ---------------------------------------------------------------------------

def test_watch_missing_file_raises(tmp_path):
    with pytest.raises(WatchError, match="not found"):
        watch(tmp_path / "missing.env", callback=lambda e: None, interval=0.01, max_iterations=1)


def test_watch_detects_change(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")

    captured: list = []

    def cb(events):
        captured.extend(events)

    # Modify the file after a tiny delay inside a thread-free approach:
    # We use max_iterations=1 but mutate the file before the first poll.
    env.write_text("FOO=bar\nBAZ=qux\n")
    # Force hash change by writing again with different content
    watch(env, callback=cb, interval=0.01, max_iterations=1)

    assert any(e.key == "BAZ" for e in captured)


def test_watch_no_change_no_callback(tmp_path):
    env = tmp_path / ".env"
    env.write_text("FOO=bar\n")
    called = []
    watch(env, callback=lambda e: called.append(e), interval=0.01, max_iterations=2)
    assert called == []


# ---------------------------------------------------------------------------
# _format_event
# ---------------------------------------------------------------------------

def test_format_added():
    ev = WatchEvent("added", "KEY", new_value="val")
    assert "[+]" in _format_event(ev) and "KEY" in _format_event(ev)


def test_format_removed():
    ev = WatchEvent("removed", "KEY", old_value="old")
    assert "[-]" in _format_event(ev)


def test_format_changed():
    ev = WatchEvent("changed", "KEY", old_value="a", new_value="b")
    assert "[~]" in _format_event(ev)


# ---------------------------------------------------------------------------
# cmd_watch
# ---------------------------------------------------------------------------

def _ns(**kwargs):
    defaults = {"env_file": ".env", "interval": 1.0}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_watch_missing_file_returns_1(tmp_path):
    ns = _ns(env_file=str(tmp_path / "ghost.env"))
    assert cmd_watch(ns) == 1


def test_cmd_watch_watch_error_returns_1(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    ns = _ns(env_file=str(env))
    with patch("envault.cli_watch.watch", side_effect=WatchError("gone")):
        assert cmd_watch(ns) == 1


def test_cmd_watch_keyboard_interrupt_returns_0(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1\n")
    ns = _ns(env_file=str(env))
    with patch("envault.cli_watch.watch", side_effect=KeyboardInterrupt):
        assert cmd_watch(ns) == 0
