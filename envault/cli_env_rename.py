"""CLI sub-commands for bulk key renaming (add-prefix / strip-prefix)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .env_rename import RenameError, add_prefix, strip_prefix
from .cli import _read_passphrase


def cmd_add_prefix(args: argparse.Namespace) -> int:
    passphrase = _read_passphrase(confirm=False)
    try:
        pairs = add_prefix(Path(args.vault), passphrase, args.prefix)
    except RenameError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for old, new in pairs:
        if old != new:
            print(f"  {old}  ->  {new}")
        else:
            print(f"  {old}  (unchanged)")
    print(f"Done. {sum(1 for o, n in pairs if o != n)} key(s) renamed.")
    return 0


def cmd_strip_prefix(args: argparse.Namespace) -> int:
    passphrase = _read_passphrase(confirm=False)
    try:
        pairs = strip_prefix(Path(args.vault), passphrase, args.prefix)
    except RenameError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for old, new in pairs:
        if old != new:
            print(f"  {old}  ->  {new}")
        else:
            print(f"  {old}  (unchanged)")
    print(f"Done. {sum(1 for o, n in pairs if o != n)} key(s) renamed.")
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_add = subparsers.add_parser(
        "add-prefix",
        help="Add a prefix to every key in the vault.",
    )
    p_add.add_argument("vault", help="Path to the encrypted vault file.")
    p_add.add_argument("prefix", help="Prefix string to prepend.")
    p_add.set_defaults(func=cmd_add_prefix)

    p_strip = subparsers.add_parser(
        "strip-prefix",
        help="Remove a prefix from every matching key in the vault.",
    )
    p_strip.add_argument("vault", help="Path to the encrypted vault file.")
    p_strip.add_argument("prefix", help="Prefix string to remove.")
    p_strip.set_defaults(func=cmd_strip_prefix)
