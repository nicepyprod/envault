"""CLI subcommands for alias management."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.env_alias import AliasError, add_alias, load_aliases, remove_alias, resolve_alias


def cmd_alias_add(args: argparse.Namespace) -> int:
    base_dir = Path(args.dir)
    try:
        add_alias(base_dir, args.alias, args.key)
        print(f"Alias '{args.alias}' -> '{args.key}' added.")
        return 0
    except AliasError as exc:
        print(f"Error: {exc}")
        return 1


def cmd_alias_remove(args: argparse.Namespace) -> int:
    base_dir = Path(args.dir)
    try:
        remove_alias(base_dir, args.alias)
        print(f"Alias '{args.alias}' removed.")
        return 0
    except AliasError as exc:
        print(f"Error: {exc}")
        return 1


def cmd_alias_list(args: argparse.Namespace) -> int:
    base_dir = Path(args.dir)
    try:
        aliases = load_aliases(base_dir)
    except AliasError as exc:
        print(f"Error: {exc}")
        return 1
    if not aliases:
        print("No aliases defined.")
        return 0
    for alias, key in sorted(aliases.items()):
        print(f"  {alias} -> {key}")
    return 0


def cmd_alias_resolve(args: argparse.Namespace) -> int:
    base_dir = Path(args.dir)
    try:
        key = resolve_alias(base_dir, args.alias)
        print(key)
        return 0
    except AliasError as exc:
        print(f"Error: {exc}")
        return 1


def register_subcommands(sub: argparse._SubParsersAction, parent: argparse.ArgumentParser) -> None:  # noqa: SLF001
    p_add = sub.add_parser("alias-add", parents=[parent], help="Add an alias for a vault key.")
    p_add.add_argument("alias", help="Short alias name.")
    p_add.add_argument("key", help="Vault key the alias points to.")
    p_add.set_defaults(func=cmd_alias_add)

    p_rm = sub.add_parser("alias-remove", parents=[parent], help="Remove an alias.")
    p_rm.add_argument("alias", help="Alias to remove.")
    p_rm.set_defaults(func=cmd_alias_remove)

    p_ls = sub.add_parser("alias-list", parents=[parent], help="List all aliases.")
    p_ls.set_defaults(func=cmd_alias_list)

    p_res = sub.add_parser("alias-resolve", parents=[parent], help="Resolve an alias to its vault key.")
    p_res.add_argument("alias", help="Alias to resolve.")
    p_res.set_defaults(func=cmd_alias_resolve)
