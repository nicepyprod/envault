"""CLI sub-commands for filtering vault keys."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envault.cli import _read_passphrase
from envault.env_filter import FilterError, filter_vault


def cmd_filter(args: argparse.Namespace) -> int:
    """Print filtered key/value pairs from a vault."""
    vault_path = Path(args.vault)
    passphrase = _read_passphrase("Passphrase: ")

    try:
        results = filter_vault(
            vault_path,
            passphrase,
            prefix=args.prefix or None,
            pattern=args.pattern or None,
            tag=args.tag or None,
            invert=args.invert,
        )
    except FilterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not results:
        print("(no matching keys)")
        return 0

    if args.format == "json":
        print(json.dumps(results, indent=2))
    elif args.format == "shell":
        for k, v in results.items():
            print(f"export {k}={v!r}")
    else:  # dotenv (default)
        for k, v in results.items():
            print(f"{k}={v}")

    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("filter", help="Filter vault keys by prefix, pattern, or tag")
    p.add_argument("vault", help="Path to the encrypted vault file")
    p.add_argument("--prefix", default="", help="Only include keys starting with this prefix")
    p.add_argument("--pattern", default="", help="fnmatch-style glob pattern for key names")
    p.add_argument("--tag", default="", help="Only include keys that have this tag")
    p.add_argument(
        "--invert", action="store_true", help="Invert the filter (exclude matching keys)"
    )
    p.add_argument(
        "--format",
        choices=["dotenv", "json", "shell"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    p.set_defaults(func=cmd_filter)
