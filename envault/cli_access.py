"""CLI subcommands for vault access control management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.access import (
    AccessError,
    add_user,
    remove_user,
    add_host,
    remove_host,
    load_rules,
    check_access,
)


def cmd_access_add(ns: argparse.Namespace) -> int:
    """Add a user or host to the access list."""
    base_dir = Path(ns.dir)
    try:
        if ns.kind == "user":
            add_user(base_dir, ns.name)
            print(f"[envault] User '{ns.name}' added to access list.")
        else:
            add_host(base_dir, ns.name)
            print(f"[envault] Host '{ns.name}' added to access list.")
        return 0
    except AccessError as exc:
        print(f"[envault] Error: {exc}", file=sys.stderr)
        return 1


def cmd_access_remove(ns: argparse.Namespace) -> int:
    """Remove a user or host from the access list."""
    base_dir = Path(ns.dir)
    try:
        if ns.kind == "user":
            remove_user(base_dir, ns.name)
            print(f"[envault] User '{ns.name}' removed from access list.")
        else:
            remove_host(base_dir, ns.name)
            print(f"[envault] Host '{ns.name}' removed from access list.")
        return 0
    except AccessError as exc:
        print(f"[envault] Error: {exc}", file=sys.stderr)
        return 1


def cmd_access_list(ns: argparse.Namespace) -> int:
    """List current access rules."""
    base_dir = Path(ns.dir)
    try:
        rules = load_rules(base_dir)
    except AccessError as exc:
        print(f"[envault] Error: {exc}", file=sys.stderr)
        return 1
    users = rules["allowed_users"]
    hosts = rules["allowed_hosts"]
    print("Allowed users:", ", ".join(users) if users else "(any)")
    print("Allowed hosts:", ", ".join(hosts) if hosts else "(any)")
    return 0


def cmd_access_check(ns: argparse.Namespace) -> int:
    """Check whether the current user/host has access."""
    base_dir = Path(ns.dir)
    try:
        check_access(base_dir)
        print("[envault] Access granted.")
        return 0
    except AccessError as exc:
        print(f"[envault] Access denied: {exc}", file=sys.stderr)
        return 1


def register_subcommands(sub: argparse._SubParsersAction, common: argparse.ArgumentParser) -> None:  # noqa: SLF001
    p = sub.add_parser("access", help="Manage vault access control")
    sub2 = p.add_subparsers(dest="access_cmd", required=True)

    for action in ("add", "remove"):
        pa = sub2.add_parser(action, parents=[common], add_help=False)
        pa.add_argument("kind", choices=["user", "host"])
        pa.add_argument("name")
        pa.set_defaults(func=cmd_access_add if action == "add" else cmd_access_remove)

    pl = sub2.add_parser("list", parents=[common], add_help=False)
    pl.set_defaults(func=cmd_access_list)

    pc = sub2.add_parser("check", parents=[common], add_help=False)
    pc.set_defaults(func=cmd_access_check)
