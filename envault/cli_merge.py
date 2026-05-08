"""CLI subcommand: envault merge"""

from __future__ import annotations

import argparse
import sys

from envault.cli import _read_passphrase
from envault.env_merge import MergeError, merge_vaults
from pathlib import Path


def cmd_merge(args: argparse.Namespace) -> int:
    base_vault = Path(args.base_vault)
    other_vault = Path(args.other_vault)
    output_vault = Path(args.output_vault)

    print(f"Passphrase for base vault ({base_vault.name}):")
    base_pass = _read_passphrase(confirm=False)
    if not base_pass:
        print("Error: base passphrase must not be empty.", file=sys.stderr)
        return 1

    print(f"Passphrase for other vault ({other_vault.name}):")
    other_pass = _read_passphrase(confirm=False)
    if not other_pass:
        print("Error: other passphrase must not be empty.", file=sys.stderr)
        return 1

    if output_vault == base_vault or output_vault == other_vault:
        print("Passphrase for output vault:")
        out_pass = _read_passphrase(confirm=True)
    else:
        print(f"Passphrase for output vault ({output_vault.name}):")
        out_pass = _read_passphrase(confirm=True)

    if not out_pass:
        print("Error: output passphrase must not be empty.", file=sys.stderr)
        return 1

    try:
        result = merge_vaults(
            base_vault=base_vault,
            base_passphrase=base_pass,
            other_vault=other_vault,
            other_passphrase=other_pass,
            output_vault=output_vault,
            output_passphrase=out_pass,
            strategy=args.strategy,
        )
    except MergeError as exc:
        print(f"Merge error: {exc}", file=sys.stderr)
        return 1

    print(f"Merged vault written to {output_vault}")
    if result.added:
        print(f"  Added keys   : {', '.join(sorted(result.added))}")
    if result.overwritten:
        print(f"  Overwritten  : {', '.join(sorted(result.overwritten))}")
    if result.conflicts and args.strategy == "ours":
        print(f"  Kept ours    : {', '.join(sorted(result.conflicts))}")
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("merge", help="Merge two encrypted vault files")
    p.add_argument("base_vault", help="Path to the base vault file")
    p.add_argument("other_vault", help="Path to the vault file to merge in")
    p.add_argument("output_vault", help="Path to write the merged vault")
    p.add_argument(
        "--strategy",
        choices=["ours", "theirs", "error"],
        default="error",
        help="Conflict resolution strategy (default: error)",
    )
    p.set_defaults(func=cmd_merge)
