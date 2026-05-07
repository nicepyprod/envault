"""Pre/post hook support for envault operations."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional


class HookError(Exception):
    pass


def _hooks_path(base_dir: Path) -> Path:
    return base_dir / ".envault_hooks.json"


def load_hooks(base_dir: Path) -> dict:
    p = _hooks_path(base_dir)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise HookError(f"Corrupt hooks file: {exc}") from exc
    if not isinstance(data, dict):
        raise HookError("Hooks file must be a JSON object")
    return data


def save_hooks(base_dir: Path, hooks: dict) -> None:
    _hooks_path(base_dir).write_text(json.dumps(hooks, indent=2))


def set_hook(base_dir: Path, event: str, command: str) -> None:
    """Register *command* for *event* (e.g. 'pre_lock', 'post_unlock')."""
    valid_events = {
        "pre_lock", "post_lock",
        "pre_unlock", "post_unlock",
        "pre_push", "post_push",
        "pre_pull", "post_pull",
    }
    if event not in valid_events:
        raise HookError(f"Unknown event '{event}'. Valid events: {sorted(valid_events)}")
    hooks = load_hooks(base_dir)
    hooks[event] = command
    save_hooks(base_dir, hooks)


def remove_hook(base_dir: Path, event: str) -> None:
    hooks = load_hooks(base_dir)
    if event not in hooks:
        raise HookError(f"No hook registered for event '{event}'")
    del hooks[event]
    save_hooks(base_dir, hooks)


def run_hook(base_dir: Path, event: str) -> Optional[int]:
    """Run the hook for *event* if one is registered. Returns exit code or None."""
    hooks = load_hooks(base_dir)
    command = hooks.get(event)
    if not command:
        return None
    result = subprocess.run(command, shell=True, cwd=str(base_dir))
    if result.returncode != 0:
        raise HookError(
            f"Hook for '{event}' exited with code {result.returncode}: {command!r}"
        )
    return result.returncode


def list_hooks(base_dir: Path) -> List[dict]:
    hooks = load_hooks(base_dir)
    return [{"event": k, "command": v} for k, v in sorted(hooks.items())]
