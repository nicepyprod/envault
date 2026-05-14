"""CLI sub-commands for vault formatting."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.cli import _read_passphrase
from envault.env_fmt import FmtError, format_vault


def cmd_fmt(args: argparse.Namespace) -> int:
    """Normalise the formatting of a vault file in-place."""
    vault_path = Path(args.vault)

    passphrase = _read_passphrase("Passphrase: ")
    if not passphrase:
        print("error: passphrase must not be empty", file=sys.stderr)
        return 1

    try:
        count = format_vault(
            vault_path,
            passphrase,
            sort_keys=args.sort,
            quote_values=args.quote,
        )
    except FmtError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Formatted {count} key(s) in {vault_path}")
    if args.sort:
        print("  Keys sorted alphabetically.")
    if args.quote:
        print("  All values quoted.")
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "fmt",
        help="Normalise / pretty-print the contents of a vault in-place",
    )
    p.add_argument("vault", help="Path to the encrypted vault file")
    p.add_argument(
        "--sort",
        action="store_true",
        default=False,
        help="Sort keys alphabetically",
    )
    p.add_argument(
        "--quote",
        action="store_true",
        default=False,
        help="Quote all values with double-quotes",
    )
    p.set_defaults(func=cmd_fmt)
