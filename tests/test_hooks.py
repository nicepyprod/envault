"""Tests for envault.hooks"""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.hooks import (
    HookError,
    load_hooks,
    save_hooks,
    set_hook,
    remove_hook,
    run_hook,
    list_hooks,
)


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_hooks_missing_file_returns_empty(base_dir):
    assert load_hooks(base_dir) == {}


def test_load_hooks_corrupt_file_raises(base_dir):
    (base_dir / ".envault_hooks.json").write_text("not json")
    with pytest.raises(HookError, match="Corrupt"):
        load_hooks(base_dir)


def test_load_hooks_wrong_type_raises(base_dir):
    (base_dir / ".envault_hooks.json").write_text("[1, 2, 3]")
    with pytest.raises(HookError, match="JSON object"):
        load_hooks(base_dir)


def test_set_hook_stores_entry(base_dir):
    set_hook(base_dir, "pre_lock", "echo before_lock")
    hooks = load_hooks(base_dir)
    assert hooks["pre_lock"] == "echo before_lock"


def test_set_hook_invalid_event_raises(base_dir):
    with pytest.raises(HookError, match="Unknown event"):
        set_hook(base_dir, "on_explode", "rm -rf /")


def test_set_hook_overwrites_existing(base_dir):
    set_hook(base_dir, "post_push", "echo v1")
    set_hook(base_dir, "post_push", "echo v2")
    assert load_hooks(base_dir)["post_push"] == "echo v2"


def test_remove_hook_deletes_entry(base_dir):
    set_hook(base_dir, "pre_unlock", "echo hi")
    remove_hook(base_dir, "pre_unlock")
    assert "pre_unlock" not in load_hooks(base_dir)


def test_remove_hook_missing_raises(base_dir):
    with pytest.raises(HookError, match="No hook"):
        remove_hook(base_dir, "pre_lock")


def test_run_hook_no_hook_returns_none(base_dir):
    assert run_hook(base_dir, "pre_lock") is None


def test_run_hook_success(base_dir):
    set_hook(base_dir, "post_lock", "exit 0")
    result = run_hook(base_dir, "post_lock")
    assert result == 0


def test_run_hook_failure_raises(base_dir):
    set_hook(base_dir, "pre_push", "exit 42")
    with pytest.raises(HookError, match="exited with code 42"):
        run_hook(base_dir, "pre_push")


def test_list_hooks_sorted(base_dir):
    set_hook(base_dir, "post_push", "echo b")
    set_hook(base_dir, "pre_lock", "echo a")
    entries = list_hooks(base_dir)
    events = [e["event"] for e in entries]
    assert events == sorted(events)
    assert len(entries) == 2
