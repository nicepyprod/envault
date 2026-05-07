"""CLI subcommands for managing envault hooks."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.hooks import HookError, set_hook, remove_hook, list_hooks


def cmd_hook_set(args: argparse.Namespace) -> int:
    base_dir = Path(args.base_dir)
    try:
        set_hook(base_dir, args.event, args.command)
        print(f"Hook set: {args.event!r} -> {args.command!r}")
        return 0
    except HookError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_hook_remove(args: argparse.Namespace) -> int:
    base_dir = Path(args.base_dir)
    try:
        remove_hook(base_dir, args.event)
        print(f"Hook removed for event: {args.event!r}")
        return 0
    except HookError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_hook_list(args: argparse.Namespace) -> int:
    base_dir = Path(args.base_dir)
    try:
        hooks = list_hooks(base_dir)
    except HookError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not hooks:
        print("No hooks registered.")
        return 0
    for entry in hooks:
        print(f"{entry['event']:<20} {entry['command']}")
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_hook = subparsers.add_parser("hook", help="Manage pre/post hooks")
    hook_sub = p_hook.add_subparsers(dest="hook_cmd", required=True)

    p_set = hook_sub.add_parser("set", help="Register a hook command for an event")
    p_set.add_argument("event", help="Event name (e.g. pre_lock, post_unlock)")
    p_set.add_argument("command", help="Shell command to run")
    p_set.set_defaults(func=cmd_hook_set)

    p_rm = hook_sub.add_parser("remove", help="Remove a registered hook")
    p_rm.add_argument("event", help="Event name to remove")
    p_rm.set_defaults(func=cmd_hook_remove)

    p_ls = hook_sub.add_parser("list", help="List all registered hooks")
    p_ls.set_defaults(func=cmd_hook_list)
