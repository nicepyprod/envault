"""CLI subcommand: envault grep — search vault values by pattern."""

from __future__ import annotations

import argparse
import sys

from envault.cli import _read_passphrase
from envault.env_grep import GrepError, grep_vault


def cmd_grep(args: argparse.Namespace) -> int:
    """Entry point for ``envault grep``."""
    passphrase = _read_passphrase("Passphrase: ")
    if not passphrase:
        print("error: passphrase must not be empty", file=sys.stderr)
        return 1

    try:
        matches = grep_vault(
            args.vault,
            passphrase,
            args.pattern,
            search_keys=args.keys,
            case_sensitive=not args.ignore_case,
            use_regex=args.regex,
        )
    except GrepError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not matches:
        if not args.quiet:
            print("No matches found.")
        return 1

    for m in matches:
        if args.keys_only:
            print(m.key)
        elif args.values_only:
            print(m.value)
        else:
            print(str(m))

    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "grep",
        help="Search vault entries by value (or key) pattern.",
    )
    p.add_argument("pattern", help="Glob or regex pattern to search for.")
    p.add_argument(
        "--vault",
        default=".env.vault",
        type=__import__("pathlib").Path,
        help="Path to the vault file (default: .env.vault).",
    )
    p.add_argument(
        "-k", "--keys",
        action="store_true",
        help="Match against keys instead of values.",
    )
    p.add_argument(
        "-i", "--ignore-case",
        action="store_true",
        help="Case-insensitive matching.",
    )
    p.add_argument(
        "-E", "--regex",
        action="store_true",
        help="Treat pattern as a regular expression.",
    )
    p.add_argument(
        "--keys-only",
        action="store_true",
        help="Print only matching key names.",
    )
    p.add_argument(
        "--values-only",
        action="store_true",
        help="Print only matching values.",
    )
    p.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress 'no matches' message; exit 1 silently.",
    )
    p.set_defaults(func=cmd_grep)
