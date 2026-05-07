"""CLI sub-commands for vault change history."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from envault.env_history import HistoryError, load_history, clear_history


def cmd_history_list(args: argparse.Namespace) -> int:
    """Print the change history for a vault file."""
    vault_path = Path(args.vault)
    try:
        entries = load_history(vault_path)
    except HistoryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not entries:
        print("No history recorded for this vault.")
        return 0

    fmt = args.format if hasattr(args, "format") else "table"
    if fmt == "json":
        import json
        print(json.dumps(entries, indent=2))
    else:
        print(f"{'TIMESTAMP':<22} {'OP':<8} {'KEY':<30} ACTOR")
        print("-" * 70)
        for entry in entries:
            ts = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(entry.get("timestamp", 0))
            )
            print(
                f"{ts:<22} {entry.get('operation','?'):<8} "
                f"{entry.get('key','?'):<30} {entry.get('actor','?')}"
            )
    return 0


def cmd_history_clear(args: argparse.Namespace) -> int:
    """Clear the change history for a vault file."""
    vault_path = Path(args.vault)
    if not vault_path.exists():
        print(f"error: vault file not found: {vault_path}", file=sys.stderr)
        return 1
    clear_history(vault_path)
    print(f"History cleared for {vault_path}.")
    return 0


def register_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # history list
    p_list = sub.add_parser("history-list", help="Show vault change history")
    p_list.add_argument("vault", help="Path to the .vault file")
    p_list.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table)",
    )
    p_list.set_defaults(func=cmd_history_list)

    # history clear
    p_clear = sub.add_parser("history-clear", help="Clear vault change history")
    p_clear.add_argument("vault", help="Path to the .vault file")
    p_clear.set_defaults(func=cmd_history_clear)
