"""CLI subcommands for key pinning."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.env_pin import PinError, pin_key, unpin_key, list_pins, load_pins


def cmd_pin_set(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    try:
        pin_key(vault, args.key, args.value)
        print(f"Pinned {args.key}={args.value}")
        return 0
    except PinError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_pin_remove(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    try:
        unpin_key(vault, args.key)
        print(f"Unpinned '{args.key}'")
        return 0
    except PinError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_pin_list(args: argparse.Namespace) -> int:
    vault = Path(args.vault)
    try:
        pins = load_pins(vault)
    except PinError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    keys = list_pins(vault)
    if not keys:
        print("No pinned keys.")
        return 0
    for k in keys:
        print(f"{k}={pins[k]}")
    return 0


def register_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    # pin set
    p_set = sub.add_parser("pin-set", help="Pin a key to a fixed value")
    p_set.add_argument("vault", help="Path to vault file")
    p_set.add_argument("key", help="Environment variable name")
    p_set.add_argument("value", help="Value to pin")
    p_set.set_defaults(func=cmd_pin_set)

    # pin remove
    p_rm = sub.add_parser("pin-remove", help="Remove a pin from a key")
    p_rm.add_argument("vault", help="Path to vault file")
    p_rm.add_argument("key", help="Environment variable name")
    p_rm.set_defaults(func=cmd_pin_remove)

    # pin list
    p_ls = sub.add_parser("pin-list", help="List all pinned keys")
    p_ls.add_argument("vault", help="Path to vault file")
    p_ls.set_defaults(func=cmd_pin_list)
