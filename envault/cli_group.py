"""CLI sub-commands for key-group management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.env_group import GroupError, add_group, extract_group, load_groups, remove_group
from envault.cli import _read_passphrase


def cmd_group_add(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    if not keys:
        print("Error: provide at least one key.", file=sys.stderr)
        return 1
    try:
        add_group(vault, args.name, keys)
        print(f"Group '{args.name}' saved with {len(keys)} key(s).")
        return 0
    except GroupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_group_remove(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    try:
        remove_group(vault, args.name)
        print(f"Group '{args.name}' removed.")
        return 0
    except GroupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_group_list(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    try:
        groups = load_groups(vault)
    except GroupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if not groups:
        print("No groups defined.")
        return 0
    for name, keys in sorted(groups.items()):
        print(f"{name}: {', '.join(keys)}")
    return 0


def cmd_group_extract(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    passphrase = _read_passphrase("Passphrase: ")
    out = Path(args.output) if args.output else None
    try:
        path = extract_group(vault, args.name, passphrase, out)
        print(f"Extracted group '{args.name}' -> {path}")
        return 0
    except GroupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def register_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p_add = sub.add_parser("group-add", help="Create or overwrite a key group")
    p_add.add_argument("vault")
    p_add.add_argument("name", help="Group name")
    p_add.add_argument("keys", help="Comma-separated list of keys")
    p_add.set_defaults(func=cmd_group_add)

    p_rm = sub.add_parser("group-remove", help="Remove a key group")
    p_rm.add_argument("vault")
    p_rm.add_argument("name")
    p_rm.set_defaults(func=cmd_group_remove)

    p_ls = sub.add_parser("group-list", help="List all key groups")
    p_ls.add_argument("vault")
    p_ls.set_defaults(func=cmd_group_list)

    p_ex = sub.add_parser("group-extract", help="Extract a group into a new vault")
    p_ex.add_argument("vault")
    p_ex.add_argument("name")
    p_ex.add_argument("--output", default=None)
    p_ex.set_defaults(func=cmd_group_extract)
