"""CLI subcommands for vault diffing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.diff import DiffError, diff_vaults, diff_vault_vs_env
from envault.cli import _read_passphrase

_STATUS_SYMBOLS = {
    "added":     "+",
    "removed":   "-",
    "changed":   "~",
    "unchanged": " ",
}


def cmd_diff(args: argparse.Namespace) -> int:
    passphrase = _read_passphrase("Passphrase: ")
    if not passphrase:
        print("error: passphrase must not be empty", file=sys.stderr)
        return 1

    try:
        if args.env:
            entries = diff_vault_vs_env(
                Path(args.vault),
                Path(args.env),
                passphrase,
            )
        else:
            if not args.new_vault:
                print(
                    "error: provide --new-vault or --env",
                    file=sys.stderr,
                )
                return 1
            entries = diff_vaults(
                Path(args.vault),
                Path(args.new_vault),
                passphrase,
            )
    except DiffError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    show_unchanged = getattr(args, "show_unchanged", False)
    for entry in entries:
        if entry.status == "unchanged" and not show_unchanged:
            continue
        sym = _STATUS_SYMBOLS[entry.status]
        if entry.status == "added":
            print(f"{sym} {entry.key}=(none) -> {entry.new_value!r}")
        elif entry.status == "removed":
            print(f"{sym} {entry.key}={entry.old_value!r} -> (none)")
        elif entry.status == "changed":
            print(f"{sym} {entry.key}={entry.old_value!r} -> {entry.new_value!r}")
        else:
            print(f"{sym} {entry.key}={entry.old_value!r}")

    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("diff", help="Show differences between vaults or vault vs .env")
    p.add_argument("vault", help="Base (old) vault file")
    p.add_argument("--new-vault", metavar="FILE", help="New vault file to compare against")
    p.add_argument("--env", metavar="FILE", help="Plain .env file to compare against")
    p.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Also print unchanged keys",
    )
    p.set_defaults(func=cmd_diff)
