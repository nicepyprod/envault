"""CLI subcommand: envault watch — monitor a .env file for live changes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.env_watch import WatchError, WatchEvent, watch


def _format_event(ev: WatchEvent) -> str:
    """Format a single WatchEvent into a human-readable string."""
    if ev.kind == "added":
        return f"  [+] {ev.key} = {ev.new_value}"
    if ev.kind == "removed":
        return f"  [-] {ev.key}  (was: {ev.old_value})"
    if ev.kind == "changed":
        return f"  [~] {ev.key}: {ev.old_value!r} -> {ev.new_value!r}"
    return f"  [=] {ev.key}"


def _on_change(env_path: Path, events: list[WatchEvent]) -> None:
    """Print a summary of detected changes to stdout."""
    print(f"\n{len(events)} change(s) detected in {env_path}:")
    for ev in events:
        print(_format_event(ev))


def cmd_watch(args: argparse.Namespace) -> int:
    """Entry point for the 'watch' subcommand."""
    env_path = Path(args.env_file)

    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 1

    interval: float = args.interval
    print(f"Watching {env_path} (interval={interval}s) — press Ctrl+C to stop.")

    try:
        watch(
            env_path,
            callback=lambda events: _on_change(env_path, events),
            interval=interval,
        )
    except WatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped watching.")

    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "watch",
        help="Monitor a .env file and print changes as they happen.",
    )
    p.add_argument(
        "env_file",
        metavar="ENV_FILE",
        help="Path to the .env file to watch.",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 1.0).",
    )
    p.set_defaults(func=cmd_watch)
