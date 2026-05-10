"""CLI sub-commands for vault comparison."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.cli import _read_passphrase
from envault.env_compare import CompareError, compare_vaults


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare two vault files and print a human-readable diff."""
    vault_a = Path(args.vault_a)
    vault_b = Path(args.vault_b)

    for p in (vault_a, vault_b):
        if not p.exists():
            print(f"error: vault not found: {p}", file=sys.stderr)
            return 1

    passphrase_a = _read_passphrase(f"Passphrase for {vault_a.name}: ")
    if args.same_passphrase:
        passphrase_b = passphrase_a
    else:
        passphrase_b = _read_passphrase(f"Passphrase for {vault_b.name}: ")

    try:
        result = compare_vaults(vault_a, vault_b, passphrase_a, passphrase_b)
    except CompareError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if result.is_identical:
        print("Vaults are identical.")
        return 0

    print(f"Comparing {vault_a} <-> {vault_b}")
    if result.only_in_a:
        print(f"  Only in A ({len(result.only_in_a)}):")
        for k in result.only_in_a:
            print(f"    - {k}")
    if result.only_in_b:
        print(f"  Only in B ({len(result.only_in_b)}):")
        for k in result.only_in_b:
            print(f"    + {k}")
    if result.changed:
        print(f"  Changed ({len(result.changed)}):")
        for k in result.changed:
            print(f"    ~ {k}")
    if not args.hide_unchanged and result.unchanged:
        print(f"  Unchanged ({len(result.unchanged)}):")
        for k in result.unchanged:
            print(f"    = {k}")

    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("compare", help="Compare two encrypted vault files")
    p.add_argument("vault_a", help="First vault file")
    p.add_argument("vault_b", help="Second vault file")
    p.add_argument(
        "--same-passphrase",
        action="store_true",
        default=False,
        help="Use the same passphrase for both vaults",
    )
    p.add_argument(
        "--hide-unchanged",
        action="store_true",
        default=False,
        help="Do not print unchanged keys",
    )
    p.set_defaults(func=cmd_compare)
