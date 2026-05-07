"""CLI subcommands: key-copy and key-rename."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.cli import _read_passphrase
from envault.env_copy import CopyError, copy_key, rename_key


def cmd_key_copy(args: argparse.Namespace) -> int:
    """Copy a key to a new name within the vault."""
    vault_path = Path(args.vault)
    try:
        passphrase = _read_passphrase("Passphrase: ")
        copy_key(
            vault_path,
            passphrase,
            args.src,
            args.dst,
            overwrite=args.overwrite,
        )
        print(f"Copied {args.src!r} -> {args.dst!r} in {vault_path}")
        return 0
    except CopyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_key_rename(args: argparse.Namespace) -> int:
    """Rename a key inside the vault."""
    vault_path = Path(args.vault)
    try:
        passphrase = _read_passphrase("Passphrase: ")
        rename_key(
            vault_path,
            passphrase,
            args.src,
            args.dst,
            overwrite=args.overwrite,
        )
        print(f"Renamed {args.src!r} -> {args.dst!r} in {vault_path}")
        return 0
    except CopyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    _common = argparse.ArgumentParser(add_help=False)
    _common.add_argument("--vault", default=".env.vault", help="Path to vault file")
    _common.add_argument("--overwrite", action="store_true", help="Overwrite dst if it exists")
    _common.add_argument("src", help="Source key name")
    _common.add_argument("dst", help="Destination key name")

    p_copy = subparsers.add_parser("key-copy", parents=[_common], help="Copy a key within the vault")
    p_copy.set_defaults(func=cmd_key_copy)

    p_rename = subparsers.add_parser("key-rename", parents=[_common], help="Rename a key within the vault")
    p_rename.set_defaults(func=cmd_key_rename)
