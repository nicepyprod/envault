"""CLI sub-commands for profile management (profile add / remove / list)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.profiles import (
    ProfileError,
    add_profile,
    get_profile,
    list_profiles,
    remove_profile,
)


def cmd_profile_add(args: argparse.Namespace) -> int:
    """Register a new named profile."""
    base_dir = Path(args.dir)
    try:
        add_profile(
            base_dir,
            name=args.name,
            env_file=args.env_file,
            vault_file=args.vault_file,
        )
        print(f"Profile '{args.name}' added.")
        return 0
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_profile_remove(args: argparse.Namespace) -> int:
    """Remove a named profile."""
    base_dir = Path(args.dir)
    try:
        remove_profile(base_dir, args.name)
        print(f"Profile '{args.name}' removed.")
        return 0
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_profile_list(args: argparse.Namespace) -> int:
    """List all registered profiles."""
    base_dir = Path(args.dir)
    names = list_profiles(base_dir)
    if not names:
        print("No profiles defined.")
    else:
        for name in names:
            cfg = get_profile(base_dir, name)
            print(f"  {name:20s}  env={cfg['env_file']}  vault={cfg['vault_file']}")
    return 0


def register_subcommands(subparsers: argparse._SubParsersAction, base_dir: str) -> None:
    """Attach profile sub-commands to *subparsers*."""
    p = subparsers.add_parser("profile", help="Manage named profiles")
    p.add_argument("--dir", default=base_dir, help="Base directory for profiles file")
    sub = p.add_subparsers(dest="profile_cmd", required=True)

    # add
    p_add = sub.add_parser("add", help="Register a new profile")
    p_add.add_argument("name", help="Profile name (e.g. dev, staging, prod)")
    p_add.add_argument("--env-file", default=".env", dest="env_file")
    p_add.add_argument("--vault-file", default=".env.vault", dest="vault_file")
    p_add.set_defaults(func=cmd_profile_add)

    # remove
    p_rm = sub.add_parser("remove", help="Remove an existing profile")
    p_rm.add_argument("name", help="Profile name to remove")
    p_rm.set_defaults(func=cmd_profile_remove)

    # list
    p_ls = sub.add_parser("list", help="List all profiles")
    p_ls.set_defaults(func=cmd_profile_list)
