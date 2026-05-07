"""CLI subcommands for environment variable change history."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from envault.env_history import HistoryError, load_history, record_change, clear_history


def cmd_history_list(args: argparse.Namespace) -> int:
    """List recorded changes for a vault file."""
    try:
        entries = load_history(args.vault)
    except HistoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not entries:
        print("No history recorded.")
        return 0

    # Optionally limit output
    limit = getattr(args, "limit", None)
    if limit and limit > 0:
        entries = entries[-limit:]

    for entry in entries:
        ts_raw = entry.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_raw).astimezone()
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S %Z")
        except (ValueError, TypeError):
            ts_str = ts_raw

        action = entry.get("action", "unknown")
        key = entry.get("key", "?")
        user = entry.get("user", "")
        note = entry.get("note", "")

        parts = [f"[{ts_str}]", f"{action.upper():8s}", key]
        if user:
            parts.append(f"by {user}")
        if note:
            parts.append(f"({note})")

        print(" ".join(parts))

    return 0


def cmd_history_clear(args: argparse.Namespace) -> int:
    """Clear the change history for a vault file."""
    try:
        clear_history(args.vault)
    except HistoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"History cleared for {args.vault}")
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register 'history' subcommands onto the given subparsers action."""

    # ── history list ─────────────────────────────────────────────────────────
    p_list = subparsers.add_parser(
        "history-list",
        help="Show change history for a vault file",
    )
    p_list.add_argument(
        "vault",
        help="Path to the encrypted vault file (e.g. .env.vault)",
    )
    p_list.add_argument(
        "-n",
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Show only the last N entries (0 = all)",
    )
    p_list.set_defaults(func=cmd_history_list)

    # ── history clear ─────────────────────────────────────────────────────────
    p_clear = subparsers.add_parser(
        "history-clear",
        help="Delete all recorded history for a vault file",
    )
    p_clear.add_argument(
        "vault",
        help="Path to the encrypted vault file (e.g. .env.vault)",
    )
    p_clear.set_defaults(func=cmd_history_clear)
